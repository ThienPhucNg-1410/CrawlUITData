"""
scripts/crawl_until_january.py
==============================
Tiến trình cào khám phá (Feed Discovery) lùi tiếp về ngày 01/01/2026:
- Điểm xuất phát: Mốc cũ nhất hiện tại trong DB (16/07/2026).
- Phạm vi cào: Từ 16/07/2026 lùi dần qua tháng 6, 5, 4, 3, 2 và hết tháng 1/2026 (trọn vẹn toàn bộ HK2).
- Fast-Skip: Lướt nhanh qua các bài đã có trong CSDL (tháng 10 -> tháng 7).
- Dừng an toàn khi chuỗi bài cũ hơn 01/01/2026 đạt mốc liên tục.
- Tự động bảo vệ RAM và giải phóng bộ nhớ DOM.
"""

import sys
import os
import time
import random
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

import uitconf.config as C
from uitconf.db import connect
from uitconf.scraper.driver import make_driver
from uitconf.scraper.guard import check_blocked, HardStop
from uitconf.scraper.parse import parse_time, post_id_from_href, bucket_of, round_of

# Cấu hình logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "crawl_until_january.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("CrawlUntilJanuary")

TARGET_START_DATE = "2026-01-01"  # Cào trọn vẹn toàn bộ HK2 đến đầu năm 01/01/2026


def run_discovery_to_january(headless=True):
    cfg = C.load()
    db_path = BASE_DIR / cfg["paths"]["raw_db"]
    conn = connect(str(db_path))

    # Đọc thông tin hiện tại trong DB
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM posts")
    initial_total = c.fetchone()[0]
    c.execute("SELECT MIN(created_at) FROM posts WHERE created_at IS NOT NULL")
    oldest_initial = c.fetchone()[0] or "N/A"
    c.execute("SELECT post_id FROM posts")
    existing_pids = {row[0] for row in c.fetchall()}

    log.info("=" * 68)
    log.info("🚀 BẮT ĐẦU TIẾN TRÌNH ĐÀO BÀI VỀ HẾT THÁNG 1/2026 (TRỌN VẸN HK2)")
    log.info(f"- Tổng số bài hiện có trong DB : {initial_total}")
    log.info(f"- Mốc bài cũ nhất hiện tại     : {oldest_initial[:16]}")
    log.info(f"- Mốc đích cần đào tới        : {TARGET_START_DATE} (Hết tháng 1/2026)")
    log.info(f"- URL nhóm                   : {cfg['page_url']}")
    log.info("=" * 68)

    session_id = f"disc_jan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    conn.execute(
        "INSERT INTO sessions (session_id, started_at, stage, note) VALUES (?, ?, ?, ?)",
        (session_id, datetime.now().isoformat(), "discover_until_january", f"target={TARGET_START_DATE}")
    )
    conn.commit()

    driver = None
    target_url = cfg["page_url"]
    if "sorting_setting" not in target_url:
        target_url += ("&" if "?" in target_url else "?") + "sorting_setting=CHRONOLOGICAL"

    try:
        driver = make_driver(cfg, headless=headless, enable_images=False)
        log.info("[Driver] Trình duyệt Chrome đã sẵn sàng.")
        log.info(f"[Driver] Đang tải trang feed nhóm: {target_url}")
        driver.get(target_url)
        time.sleep(5)

        seen_on_page = set()
        new_posts_count = 0
        old_streak = 0
        scroll_count = 0
        empty_streak = 0
        last_seen_count = 0
        consecutive_scroll_errors = 0

        # JavaScript trích xuất danh sách bài viết từ feed
        js_extract_feed = """
        const articles = Array.from(document.querySelectorAll('div[role="article"]'));
        const results = [];
        
        for (let i = 0; i < articles.length; i++) {
            const art = articles[i];
            const link = art.querySelector('a[href*="/posts/"], a[href*="pfbid"]');
            if (!link || !link.href) continue;
            
            // Tìm thời gian
            const timeRaw = (link.getAttribute('aria-label') || link.innerText || '').trim();
            
            // Tìm nội dung tóm tắt
            const textNodes = Array.from(art.querySelectorAll('div[dir="auto"]'))
                .filter(n => !n.closest('a') && !n.closest('div[aria-label*="Bình luận"]') && !n.closest('div[aria-label*="Comment"]'));
            const text = textNodes.map(n => n.innerText.trim()).filter(Boolean).join('\\n');
            
            results.push({
                href: link.href.split('?')[0],
                time_raw: timeRaw,
                text: text
            });
        }
        return results;
        """

        while old_streak < 10:
            # 1. Trích xuất các bài viết hiện diện trên trang
            items = []
            try:
                raw_items = driver.execute_script(js_extract_feed)
                if isinstance(raw_items, list):
                    items = raw_items
            except Exception as e:
                log.warning(f"[!] Lỗi khi extract feed items: {e}")
                time.sleep(2)

            # 2. Xử lý từng bài viết
            for it in items:
                href = it.get("href", "")
                pid = post_id_from_href(href)
                if not pid or pid in seen_on_page:
                    continue
                seen_on_page.add(pid)

                # Fast-skip nếu bài đã có trong CSDL
                if pid in existing_pids:
                    continue

                time_raw = it.get("time_raw", "")
                iso_time = parse_time(time_raw)
                post_text = it.get("text", "")

                # Kiểm tra mốc ngày dừng
                if iso_time and iso_time[:10] < TARGET_START_DATE:
                    old_streak += 1
                    log.info(f"  [-] Bài {pid} ({iso_time[:10]}) đã cũ hơn {TARGET_START_DATE} (chuỗi chạm đích: {old_streak}/10)")
                    if old_streak >= 10:
                        log.info(f"🎉 ĐÃ CHẠM VÀ QUA MỐC {TARGET_START_DATE}! Toàn bộ HK2 năm 2026 đã được đào hoàn tất!")
                        break
                    continue
                
                # Nếu bài nằm trong khoảng hợp lệ, reset old_streak
                if iso_time and iso_time[:10] >= TARGET_START_DATE:
                    old_streak = 0

                # Lưu bài mới vào DB
                bucket = bucket_of(pid)
                round_num = round_of(bucket, cfg["rounds"])
                now_iso = datetime.now().isoformat()

                conn.execute("""
                    INSERT OR IGNORE INTO posts 
                    (post_id, created_at, time_raw, text, bucket, round, permalink, collected_at, session_id, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'post_only')
                """, (pid, iso_time, time_raw, post_text, bucket, round_num, href, now_iso, session_id))
                conn.commit()

                existing_pids.add(pid)
                new_posts_count += 1

                month_str = iso_time[:7] if iso_time else "Chưa rõ"
                snippet = post_text.replace('\n', ' ')[:50]
                log.info(f"  [+] [MỚI #{new_posts_count}] PID: {pid} | Tháng: {month_str} ({iso_time[:10] if iso_time else time_raw}) | {snippet!r}")

            if old_streak >= 10:
                break

            # 3. Quản lý cuộn và kiểm tra tiến độ
            scroll_count += 1
            if len(seen_on_page) > last_seen_count:
                empty_streak = 0
            else:
                empty_streak += 1
            last_seen_count = len(seen_on_page)

            # Xử lý gỡ kẹt feed
            if empty_streak in (4, 8, 14, 20):
                log.info(f"  [!] Feed chậm tải thêm bài (chuỗi trống {empty_streak}). Đang gỡ kẹt lazy-load...")
                try:
                    driver.execute_script("window.scrollBy(0, -2500);")
                    time.sleep(1.0)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    driver.execute_script("window.dispatchEvent(new Event('scroll'));")
                    time.sleep(2.0)
                except Exception:
                    pass

            if empty_streak >= 35:
                log.warning(f"[!] Đã cuộn 35 lần liên tiếp không thấy bài mới (đạt đáy feed phiên này).")
                break

            # Tốc độ cuộn: Fast-skip nếu chưa gặp bài mới, cuộn cẩn thận hơn khi đang đào bài mới
            try:
                if new_posts_count == 0:
                    driver.execute_script("window.scrollBy(0, 3200);")
                    time.sleep(0.9)
                    if scroll_count % 20 == 0:
                        log.info(f"  [Fast-Skip] Đang lướt nhanh qua các bài đã có: {len(seen_on_page)} bài...")
                else:
                    driver.execute_script("window.scrollBy(0, 2200);")
                    time.sleep(random.uniform(2.0, 3.2))
                    if scroll_count % 15 == 0:
                        log.info(f"  [~] Đang đào sâu: Lượt cuộn #{scroll_count} | Đã thêm {new_posts_count} bài mới | Tổng bài quét: {len(seen_on_page)}")

                # DOM Pruning để giải phóng RAM renderer, chống đơ tab
                if scroll_count % 5 == 0:
                    prune_js = """
                    const arts = Array.from(document.querySelectorAll('div[role="article"]'));
                    if (arts.length > 35) {
                        for (let j = 0; j < arts.length - 20; j++) {
                            arts[j].remove();
                        }
                    }
                    """
                    driver.execute_script(prune_js)
                consecutive_scroll_errors = 0
            except Exception as scroll_err:
                consecutive_scroll_errors += 1
                log.warning(f"[!] Thao tác cuộn gặp độ trễ ({scroll_err}). Đợi 3s và tiếp tục... (Lỗi {consecutive_scroll_errors}/4)")
                time.sleep(3)
                if consecutive_scroll_errors >= 4:
                    log.warning("[!] Đã gặp 4 lỗi cuộn/timeout liên tiếp (đạt giới hạn tải DOM của feed). Kết thúc phiên cuộn feed.")
                    break

            # Kiểm tra trạng thái tài khoản
            try:
                check_blocked(driver)
            except HardStop as hs:
                log.error(f"[CRITICAL] Bị checkpoint hoặc rate-limit: {hs}")
                break

    except Exception as e:
        log.error(f"[ERROR] Lỗi không mong đợi trong quá trình đào bài: {e}", exc_info=True)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

        # Tổng kết phiên
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM posts")
        final_total = c.fetchone()[0]
        c.execute("SELECT MIN(created_at) FROM posts WHERE created_at IS NOT NULL")
        final_oldest = c.fetchone()[0] or "N/A"
        c.execute("""
            SELECT substr(created_at, 1, 7) as ym, count(*) 
            FROM posts 
            WHERE created_at IS NOT NULL 
            GROUP BY ym 
            ORDER BY ym ASC
        """)
        monthly_stats = c.fetchall()

        conn.execute("UPDATE sessions SET ended_at=?, n_new=? WHERE session_id=?", 
                     (datetime.now().isoformat(), new_posts_count, session_id))
        conn.commit()
        conn.close()

        log.info("=" * 68)
        log.info("📊 TỔNG KẾT PHIÊN ĐÀO BÀI VỀ THÁNG 1:")
        log.info(f"- Số bài cào mới thêm trong đợt này : {new_posts_count}")
        log.info(f"- Tổng số bài hiện có trong DB      : {final_total}")
        log.info(f"- Mốc bài cũ nhất đã lưu            : {final_oldest[:16]}")
        log.info("- Phân bố bài viết theo tháng hiện tại:")
        for ym, cnt in monthly_stats:
            log.info(f"    Tháng {ym}: {cnt:4d} bài")
        log.info("=" * 68)


if __name__ == "__main__":
    run_discovery_to_january(headless=True)

