"""
scripts/enrich_comment_hierarchy.py
====================================
Bổ sung cấu trúc phân cấp Cha - Con (parent_id) và Lượt cảm xúc (reactions)
cho toàn bộ 7.009 bình luận hiện có trong cơ sở dữ liệu raw.sqlite.
"""

import sys
import os
import time
import json
import sqlite3
import random
import logging
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Cấu hình logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "enrich_comment_hierarchy.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("EnrichCommentHierarchy")


JS_PARSE_COMMENTS = """
// 1. Mở rộng xem thêm bình luận
const buttons = Array.from(document.querySelectorAll('div[role="button"], span'))
    .filter(el => {
        const txt = el.innerText ? el.innerText.trim() : '';
        return txt.match(/^Xem thêm bình luận/i) || 
               txt.match(/^Xem các bình luận trước/i) || 
               txt.match(/^Xem (\\d+ )?phản hồi/i) ||
               txt.match(/^Xem thêm phản hồi/i) ||
               txt.match(/^View (\\d+ )?replies/i);
    });
for (const b of buttons) {
    try { b.click(); } catch(e){}
}

const articles = Array.from(document.querySelectorAll('div[role="article"]'))
    .filter(a => {
        const aria = (a.getAttribute('aria-label') || '').toLowerCase();
        return aria.includes('bình luận') || aria.includes('comment') || a.innerText.includes('Trả lời') || a.innerText.includes('Reply');
    });

const results = [];

for (let i = 0; i < articles.length; i++) {
    const art = articles[i];
    
    // Comment ID
    let cid = '';
    const cLink = art.querySelector('a[href*="comment_id="]');
    if (cLink) {
        const m = cLink.href.match(/comment_id=(\\d+)/);
        if (m) cid = m[1];
    }
    if (!cid) continue;

    // Parent ID
    let parentCid = null;
    let p = art.parentElement;
    while (p) {
        if (p.getAttribute && p.getAttribute('role') === 'article' && p !== art) {
            const pLink = p.querySelector('a[href*="comment_id="]');
            if (pLink) {
                const pm = pLink.href.match(/comment_id=(\\d+)/);
                if (pm && pm[1] !== cid) {
                    parentCid = pm[1];
                    break;
                }
            }
        }
        if (p.tagName === 'UL' && p.parentElement && p.parentElement.closest('div[role="article"]')) {
            const parentBlock = p.parentElement.closest('div[role="article"]');
            const pLink = parentBlock.querySelector('a[href*="comment_id="]');
            if (pLink) {
                const pm = pLink.href.match(/comment_id=(\\d+)/);
                if (pm && pm[1] !== cid) {
                    parentCid = pm[1];
                    break;
                }
            }
        }
        p = p.parentElement;
    }

    // Reaction Count
    let rxCount = 0;
    const rxEl = art.querySelector('span[aria-label*="reaction"], span[aria-label*="cảm xúc"], div[aria-label*="reaction"], div[aria-label*="cảm xúc"]');
    if (rxEl) {
        const rxText = rxEl.innerText.trim() || rxEl.getAttribute('aria-label') || '';
        const numMatch = rxText.match(/(\\d+)/);
        if (numMatch) rxCount = parseInt(numMatch[1], 10);
        else rxCount = 1;
    }

    results.push({
        cid: cid,
        parent_id: parentCid,
        reactions: rxCount
    });
}
return results;
"""


def enrich_hierarchy(limit=None):
    db_path = BASE_DIR / "data" / "raw" / "raw.sqlite"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Lấy các bài viết có bình luận
    query = """
    SELECT post_id, permalink, n_comments
    FROM posts 
    WHERE status = 'comments_full' AND permalink IS NOT NULL AND permalink != '' AND n_comments > 0
    ORDER BY rowid ASC
    """
    if limit:
        query += f" LIMIT {int(limit)}"

    cur.execute(query)
    posts = cur.fetchall()
    log.info(f"Tìm thấy {len(posts)} bài viết có bình luận cần cập nhật phân cấp cha-con & biểu cảm.")

    # Sử dụng profile độc lập để không xung đột với crawler nền
    profile_dir = BASE_DIR.parent / ".temp_hierarchy_profile"
    o = Options()
    o.add_argument(f"--user-data-dir={profile_dir}")
    o.add_argument("--window-size=1280,900")
    o.add_argument("--disable-gpu")
    o.add_argument("--disable-dev-shm-usage")
    o.add_argument("--headless=new")
    o.page_load_strategy = "eager"

    driver = webdriver.Chrome(options=o)
    driver.set_page_load_timeout(35)
    driver.set_script_timeout(15)

    try:
        updated_posts = 0
        updated_comments = 0
        replies_linked = 0

        for idx, (post_id, permalink, n_comm) in enumerate(posts, start=1):
            log.info(f"[{idx}/{len(posts)}] Đang phân tích bình luận post_id={post_id} ({n_comm} cmt) ...")
            try:
                driver.get(permalink)
                time.sleep(random.uniform(2.5, 3.5))

                data = driver.execute_script(JS_PARSE_COMMENTS)
                if not isinstance(data, list):
                    continue

                for c in data:
                    cid = c.get("cid")
                    pid = c.get("parent_id")
                    rx = c.get("reactions") or 0

                    if cid:
                        cur.execute(
                            "UPDATE comments SET parent_id = ?, reactions = ? WHERE comment_id = ?",
                            (pid, rx, str(cid))
                        )
                        updated_comments += 1
                        if pid:
                            replies_linked += 1

                conn.commit()
                updated_posts += 1
                log.info(f"  ✓ Đã cập nhật {len(data)} cmt (Phát hiện {sum(1 for x in data if x.get('parent_id'))} replies con)")

            except Exception as e:
                log.error(f"  ✗ Lỗi khi xử lý post {post_id}: {e}")
                time.sleep(2)

        log.info(f"\n[Hoàn thành] Đã cập nhật {updated_comments} bình luận ({replies_linked} phản hồi con) qua {updated_posts} bài viết!")

    finally:
        driver.quit()
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Số lượng post cần quét (0 là quét hết)")
    args = parser.parse_args()
    limit_val = None if args.limit <= 0 else args.limit
    enrich_hierarchy(limit=limit_val)

