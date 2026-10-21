"""
run_master_overnight.py
========================
HỆ THỐNG ĐIỀU PHỐI CÀO DỮ LIỆU QUA ĐÊM TỰ ĐỘNG (AUTONOMOUS OVERNIGHT CRAWLER):
1. Giữ máy tính không bị ngủ (Windows Keep-Alive API: SetThreadExecutionState).
2. Giai đoạn 1: Tăng tốc cào trọn vẹn toàn bộ các bài viết còn lại trong CSDL hiện tại.
3. Giai đoạn 2: Tự động chạy Feed Discovery đào tiếp lùi về ngày 01/01/2026.
4. Giai đoạn 3: Tự động cào chi tiết bình luận, cảm xúc cho toàn bộ các bài mới được đào.
5. Tự động đồng bộ (WAL checkpoint), tự động gán nhãn chuẩn và tự động xuất file Excel/CSV định kỳ.
6. Tự phục hồi lỗi (Self-healing) khi mất kết nối trình duyệt hoặc gặp sự cố mạng.
"""

import os
import sys
import time
import ctypes
import random
import logging
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

# Đảm bảo mã hóa UTF-8 cho console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "master_overnight.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("MasterOvernight")

# Cấu hình Windows Keep-Alive chống sleep khi cắm máy qua đêm
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_AWAYMODE_REQUIRED = 0x00000040

def set_keep_awake(enable=True):
    try:
        if enable:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED)
            log.info("[System] Đã kích hoạt chế độ chống Sleep Windows (Keep-Awake ON).")
        else:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            log.info("[System] Đã tắt chế độ chống Sleep Windows.")
    except Exception as e:
        log.warning(f"[System] Không thể cài đặt chế độ chống Sleep: {e}")

def cleanup_chrome():
    """Dọn dẹp các tiến trình Chrome/ChromeDriver mồ côi để giải phóng Profile lock."""
    try:
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe", "/T"], capture_output=True)
        time.sleep(1)
    except Exception:
        pass

def checkpoint_db():
    try:
        db_path = BASE_DIR / "data" / "raw" / "raw.sqlite"
        if db_path.exists():
            con = sqlite3.connect(str(db_path))
            cur = con.cursor()
            cur.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            res = cur.fetchall()
            con.close()
            log.info(f"[DB] Checkpoint WAL thành công: {res}")
    except Exception as e:
        log.warning(f"[DB] Lỗi khi checkpoint WAL: {e}")

def run_export_and_relabel():
    try:
        log.info("[Export] Đang tự động gán nhãn và xuất bản cập nhật Excel/CSV...")
        py_exe = sys.executable
        p1 = subprocess.run([py_exe, str(BASE_DIR / "scripts" / "relabel_dataset_accurately.py")], 
                            cwd=str(BASE_DIR.parent), capture_output=True, text=True, encoding="utf-8")
        p2 = subprocess.run([py_exe, str(BASE_DIR / "scripts" / "export_excel_dataset.py")], 
                            cwd=str(BASE_DIR.parent), capture_output=True, text=True, encoding="utf-8")
        log.info("[Export] Hoàn tất cập nhật bộ nhãn chuẩn và file Excel dataset.")
    except Exception as e:
        log.warning(f"[Export] Lỗi khi xuất dữ liệu: {e}")

def get_uncompleted_posts_count():
    db_path = BASE_DIR / "data" / "raw" / "raw.sqlite"
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM posts WHERE status != 'comments_full' AND status != 'inaccessible' AND permalink IS NOT NULL AND permalink != ''")
    cnt = cur.fetchone()[0]
    con.close()
    return cnt

def get_total_posts_count():
    db_path = BASE_DIR / "data" / "raw" / "raw.sqlite"
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM posts")
    cnt = cur.fetchone()[0]
    con.close()
    return cnt

def run_deep_crawl_phase():
    """Chạy cào sâu bình luận cho toàn bộ bài viết còn chưa cào."""
    from crawl_full_dataset import run_full_crawler
    uncompleted = get_uncompleted_posts_count()
    if uncompleted == 0:
        log.info("[DeepCrawl] Hiện tại không có bài nào cần cào bình luận.")
        return
    
    total = get_total_posts_count()
    log.info(f"[DeepCrawl] Bắt đầu cào sâu bình luận cho {uncompleted} bài viết còn lại (Mục tiêu tổng: {total} bài)...")
    try:
        run_full_crawler(target_posts=total, headless=True)
    except Exception as e:
        log.error(f"[DeepCrawl] Ngoại lệ khi cào: {e}", exc_info=True)

def run_discovery_phase():
    """Chạy Feed Discovery để đào bài lùi về 01/01/2026."""
    from scripts.crawl_until_january import run_discovery_to_january
    log.info("[Discovery] Bắt đầu tiến trình đào bài mới qua Feed nhóm lùi về tháng 1/2026...")
    try:
        run_discovery_to_january(headless=True)
    except Exception as e:
        log.error(f"[Discovery] Ngoại lệ khi đào bài qua Feed: {e}", exc_info=True)

def run_search_phase(max_kw=4):
    """Chạy Group Search Discovery để tìm bài viết lịch sử từ tháng 1 đến tháng 6/2026."""
    from scripts.discover_by_search import run_search_discovery
    log.info(f"[SearchPhase] Kích hoạt tìm kiếm qua từ khóa sinh viên UIT (lấy {max_kw} từ khóa)...")
    try:
        n_new = run_search_discovery(headless=True, max_keywords=max_kw)
        log.info(f"[SearchPhase] Kết quả tìm kiếm đợt này: +{n_new} bài mới.")
        return n_new
    except Exception as e:
        log.error(f"[SearchPhase] Ngoại lệ khi tìm kiếm qua search: {e}", exc_info=True)
        return 0


def main():
    log.info("==================================================================")
    log.info("   🚀 KHỞI ĐỘNG HỆ THỐNG CÀO DỮ LIỆU QUA ĐÊM TỰ ĐỘNG TOÀN DIỆN")
    log.info("   - Mục tiêu: Cào sạch bài viết hiện có + Đào sâu về tháng 1/2026")
    log.info("   - Cơ chế: Feed Scroll + Group Search Discovery + Tự xuất Excel")
    log.info("==================================================================")

    set_keep_awake(True)

    iteration = 0
    try:
        while True:
            iteration += 1
            log.info(f"\n{'='*30} [VÒNG LẶP QUA ĐÊM #{iteration}] {'='*30}")

            # 1. Cào hết bình luận của các bài đang chờ trong CSDL
            uncompleted = get_uncompleted_posts_count()
            if uncompleted > 0:
                log.info(f"[Bước 1] Tìm thấy {uncompleted} bài chưa cào bình luận. Tiến hành cào sâu...")
                cleanup_chrome()
                run_deep_crawl_phase()
                checkpoint_db()
                run_export_and_relabel()

            # 2. Đào bài mới lùi về tháng 1/2026 qua cuộn Feed
            log.info("[Bước 2] Đào bài qua cuộn Feed...")
            cleanup_chrome()
            run_discovery_phase()
            checkpoint_db()

            # 3. Đào bài qua Group Search (từ khóa sinh viên UIT từ tháng 1 đến tháng 6)
            log.info("[Bước 3] Đào bài qua Facebook Group Search...")
            cleanup_chrome()
            run_search_phase(max_kw=4)
            checkpoint_db()

            # 4. Kiểm tra xem có bài mới nào được đào không
            new_uncompleted = get_uncompleted_posts_count()
            log.info(f"[Bước 4] Sau khi đào, tổng số bài mới cần cào bình luận: {new_uncompleted} bài.")

            if new_uncompleted > 0:
                log.info(f"[Bước 5] Lập tức cào chi tiết bình luận cho {new_uncompleted} bài mới này...")
                run_deep_crawl_phase()
                checkpoint_db()
                run_export_and_relabel()
            else:
                log.info("[Bước 5] Chưa có thêm bài mới trong lượt này. Nghỉ 5 phút trước chu kỳ kế tiếp...")
                time.sleep(300)

            # Nghỉ ngắn giữa các chu kỳ lớn để thả lỏng session
            time.sleep(120)

    except KeyboardInterrupt:
        log.info("[Main] Nhận tín hiệu dừng từ người dùng.")
    except Exception as e:
        log.error(f"[FATAL] Ngoại lệ ngoài vòng lặp chính: {e}", exc_info=True)
    finally:
        set_keep_awake(False)
        checkpoint_db()
        run_export_and_relabel()
        log.info("[Main] Đã đóng hệ thống an toàn và xuất file đầy đủ.")


if __name__ == "__main__":
    main()
