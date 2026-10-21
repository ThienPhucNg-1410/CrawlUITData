"""
scripts/crawl_comments_june_july.py
===================================
Cào sâu toàn bộ bình luận (comments), cảm xúc (reactions), lượt chia sẻ (shares)
và nội dung/tác giả chuẩn cho các bài viết thuộc THÁNG 6 và THÁNG 7 NĂM 2026.
- Sử dụng bộ bóc tách chuẩn WAI-ARIA (tránh lỗi feed nền).
- Ghi dữ liệu trực tiếp vào SQLite (raw.sqlite) sau từng bài.
- Định kỳ tự động xuất đè sang file Excel và CSV mỗi 50 bài.
- Tự động phục hồi trình duyệt nếu bị gián đoạn mạng.
"""

import sys
import os
import time
import random
import logging
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR))

import uitconf.config as C
from uitconf.db import connect
from uitconf.scraper.driver import make_driver
from uitconf.scraper.guard import check_blocked, HardStop
from crawl_full_dataset import extract_post_and_comments
from scripts.fix_all_posts import export_dataset

# Cấu hình logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "crawl_comments_june_july.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("CrawlJuneJuly")

DB_PATH = BASE_DIR / "data" / "raw" / "raw.sqlite"


def run_crawler(months=("2026-06", "2026-07"), limit=0, headless=True):
    cfg = C.load()
    conn = connect(str(DB_PATH))
    c = conn.cursor()

    # 1. Lọc danh sách bài viết tháng 6 & 7 cần cào chi tiết
    months_placeholder = ",".join("?" for _ in months)
    query = f"""
        SELECT post_id, permalink, text, created_at, time_raw
        FROM posts
        WHERE substr(created_at, 1, 7) IN ({months_placeholder})
          AND status != 'comments_full'
          AND status != 'inaccessible'
          AND permalink IS NOT NULL
          AND permalink != ''
        ORDER BY created_at DESC
    """
    c.execute(query, months)
    targets = c.fetchall()

    if limit > 0:
        targets = targets[:limit]

    total_targets = len(targets)
    log.info("=" * 65)
    log.info("🚀 KHỞI ĐỘNG CÀO SÂU BÌNH LUẬN & TƯƠNG TÁC THÁNG 6 & 7")
    log.info(f"- Các tháng mục tiêu : {', '.join(months)}")
    log.info(f"- Tổng số bài cần cào: {total_targets} bài")
    log.info(f"- Database           : {DB_PATH}")
    log.info("=" * 65)

    if total_targets == 0:
        log.info("[✓] Không còn bài nào trong tháng 6 & 7 cần cào bình luận!")
        conn.close()
        return

    session_id = f"cmt_jj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    conn.execute(
        "INSERT INTO sessions (session_id, started_at, stage, note) VALUES (?, ?, ?, ?)",
        (session_id, datetime.now().isoformat(), "crawl_comments_june_july", f"targets={total_targets}")
    )
    conn.commit()

    driver = None
    success_count = 0
    fail_count = 0

    try:
        driver = make_driver(cfg, headless=headless, enable_images=False)
        log.info("[Driver] Trình duyệt Chrome đã khởi chạy thành công.")

        for idx, row in enumerate(targets, 1):
            pid = row["post_id"]
            permalink = row["permalink"]
            original_text = row["text"] or ""
            created_at = row["created_at"] or ""
            date_str = created_at[:10] if created_at else "N/A"

            url = permalink if permalink and "facebook.com" in permalink else f"https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/{pid}/"

            log.info(f"[{idx}/{total_targets}] Đang cào Post {pid} ({date_str}) ...")

            try:
                driver.get(url)
            except Exception as e:
                log.error(f"[!] Lỗi khi truy cập {url}: {e}")
                try:
                    driver.quit()
                except Exception:
                    pass
                time.sleep(5)
                driver = make_driver(cfg, headless=headless, enable_images=False)
                continue

            # Kiểm tra chặn tài khoản
            try:
                check_blocked(driver)
            except HardStop as hs:
                log.error(f"[CRITICAL] Phát hiện chặn/checkpoint: {hs}")
                break

            # Bóc tách dữ liệu
            try:
                data = extract_post_and_comments(driver)
            except Exception as ex:
                log.error(f"[!] Lỗi khi bóc tách Post {pid}: {ex}")
                time.sleep(2.5)
                continue

            if data.get("is_inaccessible"):
                log.warning(f"[-] Post {pid} không khả dụng trên Facebook. Đánh dấu 'inaccessible'.")
                conn.execute("UPDATE posts SET status = 'inaccessible' WHERE post_id = ?", (pid,))
                conn.commit()
                fail_count += 1
                continue

            # Dữ liệu trích xuất chuẩn
            post_text = data.get("post_text") or original_text
            author = data.get("post_author") or "Người tham gia ẩn danh"
            reactions = int(data.get("reactions") or 0)
            shares = int(data.get("shares") or 0)
            n_comments = int(data.get("n_comments") or 0)
            comments = data.get("comments", [])
            now_iso = datetime.now().isoformat()

            # Cập nhật bảng posts
            conn.execute("""
                UPDATE posts 
                SET text = ?,
                    author = ?,
                    reactions = ?,
                    shares = ?,
                    n_comments = ?,
                    status = 'comments_full',
                    collected_at = ?
                WHERE post_id = ?
            """, (post_text, author, reactions, shares, n_comments, now_iso, pid))

            # Chèn bình luận vào bảng comments
            comments_saved = 0
            for c_idx, cmt in enumerate(comments):
                c_id = cmt.get("comment_id")
                if not c_id:
                    c_id = f"{pid}_c_{c_idx}"
                c_author = cmt.get("author") or ""
                c_text = cmt.get("text") or ""
                c_time = cmt.get("time_raw") or ""
                c_react = int(cmt.get("reactions") or 0)

                conn.execute("""
                    INSERT OR REPLACE INTO comments 
                    (comment_id, post_id, parent_id, text, author, time_raw, reactions, collected_at, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (c_id, pid, None, c_text, c_author, c_time, c_react, now_iso, session_id))
                comments_saved += 1

            conn.commit()
            success_count += 1

            snippet = post_text.replace('\n', ' ')[:45]
            log.info(f"   => OK! Tác giả: '{author}' | React: {reactions} | Share: {shares} | Cmt: {n_comments} (Lưu {comments_saved} cmt) | {snippet!r}")

            # Định kỳ mỗi 50 bài xuất Excel/CSV một lần
            if success_count % 50 == 0:
                export_dataset()

            # Nghỉ ngẫu nhiên an toàn giữa các bài
            time.sleep(random.uniform(2.5, 4.0))

            # Nghỉ ngắn định kỳ mỗi 25 bài
            if success_count % 25 == 0:
                pause = random.uniform(10.0, 15.0)
                log.info(f"[Break] Đã hoàn thành {success_count}/{total_targets} bài. Tạm nghỉ {pause:.1f}s giữ nhịp an toàn...")
                time.sleep(pause)

    except Exception as e:
        log.error(f"[FATAL] Lỗi ngoài dự kiến: {e}", exc_info=True)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

        conn.execute("UPDATE sessions SET ended_at=?, n_new=? WHERE session_id=?", 
                     (datetime.now().isoformat(), success_count, session_id))
        conn.commit()
        conn.close()

        log.info("=" * 65)
        log.info("📊 HOÀN TẤT PHIÊN CÀO BÌNH LUẬN THÁNG 6 & 7:")
        log.info(f"- Thành công: {success_count} bài")
        log.info(f"- Lỗi/Không khả dụng: {fail_count} bài")
        log.info("=" * 65)

        # Xuất dữ liệu cuối cùng
        export_dataset()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl comments, reactions, shares for June & July posts.")
    parser.add_argument("--limit", type=int, default=0, help="Giới hạn số bài cần cào (0 = toàn bộ)")
    parser.add_argument("--headful", action="store_true", help="Chạy Chrome có giao diện thay vì headless")
    args = parser.parse_args()

    run_crawler(limit=args.limit, headless=not args.headful)

