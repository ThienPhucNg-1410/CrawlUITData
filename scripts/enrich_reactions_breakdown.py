"""
enrich_reactions_breakdown.py
==============================
Bổ sung chi tiết các loại cảm xúc (Thích, Tim, Thương thương, Haha, Wow, Buồn, Phẫn nộ)
cho cả bài viết gốc và bình luận trong cơ sở dữ liệu raw.sqlite.
"""
import sys
import os
import time
import random
import json
import sqlite3
import argparse
import logging
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

import uitconf.config as C
from uitconf.scraper.driver import make_driver
from uitconf.scraper.guard import check_blocked, HardStop

# Thiết lập logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "enrich_reactions.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("EnrichReactions")

EXTRACT_REACTIONS_JS = """
function parseCount(str) {
    if (!str) return 0;
    str = str.replace(/\\s+/g, '').replace(',', '.');
    let multiplier = 1;
    if (/k/i.test(str)) { multiplier = 1000; str = str.replace(/k/i, ''); }
    else if (/m/i.test(str)) { multiplier = 1000000; str = str.replace(/m/i, ''); }
    const val = parseFloat(str);
    return isNaN(val) ? 0 : Math.round(val * multiplier);
}

function parseReactionsFromNodes(nodes) {
    const detail = { like: 0, love: 0, care: 0, haha: 0, wow: 0, sad: 0, angry: 0, total: 0 };
    for (const el of nodes) {
        const aria = el.getAttribute('aria-label') || '';
        const m = aria.match(/^(Thích|Yêu thích|Thương thương|Haha|Wow|Buồn|Phẫn nộ):?\\s*([0-9.,]+[KkMm]?)\\s*người?/i);
        if (m) {
            const rType = m[1].toLowerCase();
            const count = parseCount(m[2]);
            if (rType === 'thích') detail.like += count;
            else if (rType === 'yêu thích') detail.love += count;
            else if (rType === 'thương thương') detail.care += count;
            else if (rType === 'haha') detail.haha += count;
            else if (rType === 'wow') detail.wow += count;
            else if (rType === 'buồn') detail.sad += count;
            else if (rType === 'phẫn nộ') detail.angry += count;
        }
    }
    detail.total = detail.like + detail.love + detail.care + detail.haha + detail.wow + detail.sad + detail.angry;
    return detail;
}

// 1. Post reactions
// Lấy tất cả nút trong toolbar phản hồi chính của bài viết
const allReactionButtons = Array.from(document.querySelectorAll('div[role="button"][aria-label], span[aria-label]'))
    .filter(el => (el.getAttribute('aria-label') || '').match(/^(Thích|Yêu thích|Thương thương|Haha|Wow|Buồn|Phẫn nộ):/i));

// Tách các reaction thuộc bài viết gốc (không nằm trong bình luận)
const postReactionButtons = allReactionButtons.filter(b => {
    const p = b.parentElement;
    const txt = p ? (p.innerText || '') : '';
    // Thường toolbar bài viết nằm gần nút Chia sẻ/Bình luận của bài gốc
    return !b.closest('ul') && !b.closest('div[role="listitem"]');
});

const postReactions = parseReactionsFromNodes(postReactionButtons.length > 0 ? postReactionButtons : allReactionButtons.slice(0, 3));

// 2. Comments reactions
const commentsData = [];
const commentArticles = Array.from(document.querySelectorAll('div[role="article"]'))
    .filter(a => {
        const aria = (a.getAttribute('aria-label') || '').toLowerCase();
        return aria.includes('bình luận') || aria.includes('comment') || a.innerText.includes('Trả lời');
    });

for (const ca of commentArticles) {
    let commentId = '';
    const cLink = ca.querySelector('a[href*="comment_id="]');
    if (cLink) {
        const m = cLink.href.match(/comment_id=(\\d+)/);
        if (m) commentId = m[1];
    }

    // Tìm reaction button thuộc comment này
    let parent = ca;
    let commentRxButtons = [];
    for (let step = 0; step < 7 && parent; step++) {
        const rx = Array.from(parent.querySelectorAll('div[role="button"][aria-label], span[aria-label]'))
            .filter(el => (el.getAttribute('aria-label') || '').match(/^(Thích|Yêu thích|Thương thương|Haha|Wow|Buồn|Phẫn nộ):/i));
        if (rx.length > 0) {
            commentRxButtons = rx;
            break;
        }
        parent = parent.parentElement;
    }

    const cDetail = parseReactionsFromNodes(commentRxButtons);
    if (commentId) {
        commentsData.push({
            comment_id: commentId,
            reactions_detail: cDetail
        });
    }
}

return {
    post_reactions: postReactions,
    comments: commentsData
};
"""


import subprocess

def kill_browser_processes():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
    except Exception:
        pass
    try:
        subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe", "/T"], capture_output=True)
    except Exception:
        pass

def safe_restart_driver(old_driver, cfg, headless=True):
    try:
        if old_driver:
            try:
                old_driver.quit()
            except Exception:
                pass
    except Exception:
        pass
    kill_browser_processes()
    time.sleep(4)
    for attempt in range(1, 4):
        try:
            return make_driver(cfg, headless=headless, enable_images=False)
        except Exception as err:
            log.warning(f"  [!] Khởi động lại Chrome thất bại (lần {attempt}/3): {err}. Đợi 4s...")
            kill_browser_processes()
            time.sleep(4)
    raise RuntimeError("Không thể khởi động lại ChromeDriver sau 3 lần thử.")


def enrich(limit=None, headless=True):
    db_path = BASE_DIR / "data" / "raw" / "raw.sqlite"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Lấy các bài viết chưa có reactions_detail
    query = """
    SELECT post_id, permalink, reactions
    FROM posts 
    WHERE status = 'comments_full' AND (reactions_detail IS NULL OR reactions_detail = '')
    ORDER BY rowid ASC
    """
    if limit:
        query += f" LIMIT {int(limit)}"

    cur.execute(query)
    posts = cur.fetchall()
    log.info(f"Tìm thấy {len(posts)} bài viết cần bổ sung chi tiết biểu cảm.")

    if not posts:
        log.info("Tất cả bài viết đã có dữ liệu biểu cảm chi tiết!")
        conn.close()
        return

    cfg = C.load()
    driver = make_driver(cfg, headless=headless, enable_images=False)

    try:
        enriched_count = 0
        for idx, (post_id, permalink, total_rx) in enumerate(posts, start=1):
            if not permalink:
                continue

            log.info(f"[{idx}/{len(posts)}] Đang bóc tách post_id={post_id} ...")
            try:
                driver.get(permalink)
                time.sleep(random.uniform(3.0, 4.5))

                check_blocked(driver)

                # Bóc tách qua JS
                data = driver.execute_script(EXTRACT_REACTIONS_JS)
                post_rx = data.get("post_reactions", {})
                comments_rx = data.get("comments", [])

                # Cập nhật vào DB
                cur.execute(
                    "UPDATE posts SET reactions_detail = ? WHERE post_id = ?",
                    (json.dumps(post_rx, ensure_ascii=False), str(post_id))
                )

                for c in comments_rx:
                    c_id = c.get("comment_id")
                    c_rx = c.get("reactions_detail", {})
                    if c_id:
                        cur.execute(
                            "UPDATE comments SET reactions_detail = ? WHERE comment_id = ?",
                            (json.dumps(c_rx, ensure_ascii=False), str(c_id))
                        )

                conn.commit()
                enriched_count += 1
                log.info(f"  ✓ Post reactions: {post_rx} | Comments updated: {len(comments_rx)}")

            except HardStop as hs:
                log.warning(f"[!] DỪNG CỨNG (HardStop): {hs}. Dừng tiến trình để bảo vệ tài khoản.")
                break
            except Exception as e:
                log.error(f"  ✗ Lỗi khi xử lý post {post_id}: {e}")
                # Kiểm tra xem trình duyệt còn hoạt động hay đã bị crash
                driver_alive = False
                try:
                    _ = driver.current_url
                    driver_alive = True
                except Exception:
                    driver_alive = False

                if not driver_alive:
                    log.info("  [*] Trình duyệt mất kết nối, đang khởi động lại phiên làm việc...")
                    time.sleep(4)
                    driver = safe_restart_driver(driver, cfg, headless=headless)
                else:
                    log.info("  [*] Trình duyệt vẫn ổn định, tiếp tục bài tiếp theo...")
                    time.sleep(2)

        log.info(f"\n[Hoàn thành] Đã cập nhật thành công {enriched_count}/{len(posts)} bài viết!")

    finally:
        try:
            if driver:
                try:
                    if hasattr(driver, "service") and hasattr(driver.service, "process") and driver.service.process:
                        driver.service.process.kill()
                except Exception:
                    pass
                driver.quit()
        except Exception:
            pass
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bổ sung chi tiết cảm xúc Facebook cho bài viết và bình luận")
    parser.add_argument("--limit", type=int, default=10, help="Số lượng bài viết cần bổ sung (mặc định: 10 bài test, dùng --limit 0 để chạy hết)")
    parser.add_argument("--headless", action="store_true", default=True, help="Chạy chế độ headless")
    args = parser.parse_args()

    limit_val = None if args.limit <= 0 else args.limit
    while True:
        try:
            enrich(limit=limit_val, headless=args.headless)
            break
        except HardStop as hs:
            log.warning(f"[!] DỪNG CỨNG: {hs}")
            break
        except Exception as e:
            log.error(f"[!] Gặp sự cố không mong muốn ({e}). Đang tự động dọn dẹp và kết nối lại sau 10s...")
            kill_browser_processes()
            time.sleep(10)

