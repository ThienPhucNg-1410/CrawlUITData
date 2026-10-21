"""
run_continuous_crawler.py
=========================
Cào liên tục từ 2026-01-01 đến 2026-10-06.
- Mở Chrome MỘT LẦN và giữ nguyên trong suốt quá trình.
- Khi bị throttle/rate-limit: sleep 30 phút, KHÔNG đóng browser.
- Báo cáo tiến độ mỗi 1 tiếng.
- Dừng khi đã lướt qua đến ngày 1/1/2026 (old_streak >= 10 liên tục).
- Chỉ đóng browser khi gặp HardStop hoặc Ctrl+C.
"""
import os
import sys
import time
import sqlite3
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

import uitconf.config as C
from uitconf.db import connect
from uitconf.scraper import crawler
from uitconf.scraper.driver import make_driver
from uitconf.scraper.guard import HardStop

# ─── Hằng số ───────────────────────────────────────────────────────────
POSTS_PER_BATCH   = 60       # Số bài mục tiêu mỗi đợt cuộn
SLEEP_BETWEEN     = 20       # Giây nghỉ giữa các đợt bình thường
THROTTLE_SLEEP    = 30 * 60  # Giây nghỉ khi bị throttle (30 phút)
REPORT_INTERVAL   = 3600     # Báo cáo tiến độ mỗi 3600 giây (1 tiếng)
LOG_FILE          = "logs/crawl_progress.log"

def log(msg: str):
    """In ra stdout VÀ ghi vào log file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def report_progress(conn):
    """In báo cáo tiến độ."""
    total = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    newest = conn.execute("SELECT MAX(created_at) FROM posts WHERE created_at IS NOT NULL").fetchone()[0]
    oldest = conn.execute("SELECT MIN(created_at) FROM posts WHERE created_at IS NOT NULL").fetchone()[0]
    log("=" * 60)
    log(f"  📊 BÁO CÁO TIẾN ĐỘ")
    log(f"  Tổng bài trong DB : {total}")
    log(f"  Bài mới nhất      : {(newest or 'N/A')[:16]}")
    log(f"  Bài cũ nhất       : {(oldest or 'N/A')[:16]}")
    log("=" * 60)

def main():
    cfg  = C.load()
    conn = connect(cfg["paths"]["raw_db"])

    log("==================================================================")
    log("   CRAWLER LIÊN TỤC - PHIÊN MỚI BẮT ĐẦU")
    log(f"   Phạm vi: {cfg['start_date']} → {cfg['end_date']}")
    log(f"   Mục tiêu: {POSTS_PER_BATCH} bài/đợt | Nghỉ giữa đợt: {SLEEP_BETWEEN}s")
    log(f"   Khi throttle: sleep {THROTTLE_SLEEP//60} phút (GIỮ NGUYÊN BROWSER)")
    log("==================================================================")

    driver = None
    session_idx = 1
    t_last_report = time.time()
    reached_start = False
    consecutive_zeros = 0

    try:
        # ─── Khởi động Chrome MỘT LẦN DUY NHẤT ─────────────────────────
        log("[+] Khởi động Chrome (browser_profile, headless=False)...")
        # Xóa file cooldown cũ nếu còn
        cooldown_f = cfg["paths"].get("cooldown_file", "data/raw/.cooldown")
        if os.path.exists(cooldown_f):
            try:
                os.remove(cooldown_f)
            except Exception:
                pass
        driver = make_driver(cfg, headless=False, enable_images=False)
        log("[+] Chrome đã sẵn sàng. Bắt đầu cào...")

        consecutive_zeros = 0
        while not reached_start:
            t_batch_start = time.time()
            log(f"\n{'>'*7} [ĐỢT {session_idx}] BẮT ĐẦU LÚC {datetime.now().strftime('%H:%M:%S')} {'<'*7}")

            # ─── TỰ ĐỘNG BẢO VỆ & TỰ PHỤC HỒI KHI TREO MÁY QUA ĐÊM ───
            # Cấp 1: Định kỳ 25 đợt cào (~2.5-3 tiếng) reload một lần để giải phóng RAM/DOM ảo của Facebook
            # Cấp 2: Nếu 2-3 đợt liên tiếp không có bài mới (n_new == 0), tự động reload trang và kích hoạt Fast-Skip
            # Cấp 3: Nếu 4 đợt liên tiếp không có bài mới, tự động tắt Chrome và tạo phiên WebDriver hoàn toàn mới
            # Cấp 4: Nếu 6 đợt liên tiếp không có bài mới, tạm nghỉ 15 phút dưỡng nick rồi thử lại
            should_reload = (consecutive_zeros in (2, 3)) or (session_idx > 1 and session_idx % 25 == 0)

            if consecutive_zeros >= 6:
                log(f"[!] Đã {consecutive_zeros} đợt liên tiếp không có bài mới. Tạm nghỉ 15 phút dưỡng nick phòng rate-limit...")
                time.sleep(15 * 60)
                consecutive_zeros = 3  # Giảm mức để cấp 3 kích hoạt khởi động lại Chrome

            if consecutive_zeros >= 4:
                log(f"[!] Đã {consecutive_zeros} đợt liên tiếp không có bài mới. Tự động tái khởi động toàn bộ Chrome để giải phóng RAM & làm mới kết nối...")
                try:
                    driver.quit()
                except Exception:
                    pass
                time.sleep(5)
                driver = make_driver(cfg, headless=False, enable_images=False)
                should_reload = True
                consecutive_zeros = 1  # Sau khi khởi động lại, đợt tiếp theo sẽ cuộn bình thường
            elif should_reload:
                if consecutive_zeros >= 2:
                    log(f"[!] Phát hiện chuỗi {consecutive_zeros} đợt không có bài mới. Tự động làm mới trang (force_reload) và kích hoạt Fast-Skip...")
                else:
                    log(f"[~] Định kỳ dọn dẹp bộ nhớ Chrome (đợt {session_idx}). Tự động làm mới trang và Fast-Skip...")

            try:
                res = crawler.discover(driver, conn, cfg, _make_throttle(cfg), POSTS_PER_BATCH, force_reload=should_reload, return_stats=True)
                if isinstance(res, tuple):
                    n_new, total_scanned = res
                else:
                    n_new, total_scanned = res, 0

                log(f"[+] Đợt {session_idx}: Cào được {n_new} bài mới (đã quét qua {total_scanned} bài).")

                # Cập nhật chuỗi không có bài mới
                if n_new == 0:
                    consecutive_zeros += 1
                    log(f"[!] Cảnh báo: Đợt này không cào được bài mới nào. Chuỗi không tiến triển: {consecutive_zeros}/4.")
                else:
                    consecutive_zeros = 0

                # Kiểm tra đã chạm ngày start_date chưa
                oldest = conn.execute(
                    "SELECT MIN(created_at) FROM posts WHERE created_at IS NOT NULL"
                ).fetchone()[0]
                if oldest and oldest[:10] <= cfg["start_date"]:
                    log(f"[✓] Đã cào đến ngày {oldest[:10]} (≤ start_date {cfg['start_date']}). Hoàn tất!")
                    reached_start = True

                # Báo cáo tiến độ mỗi 1 tiếng
                if time.time() - t_last_report >= REPORT_INTERVAL:
                    report_progress(conn)
                    t_last_report = time.time()

                if not reached_start:
                    log(f"[~] Nghỉ {SLEEP_BETWEEN}s giữa các đợt (GIỮ NGUYÊN TRÌNH DUYỆT & TỌA ĐỘ CUỘN, KHÔNG TẢI LẠI TRANG)...")
                    time.sleep(SLEEP_BETWEEN)

            except HardStop as hs:
                log(f"\n[!!!] HARD STOP: {hs}")
                log("[!!!] Facebook yêu cầu xác minh hoặc phát hiện bất thường.")
                log("[!!!] TẠM DỪNG TIẾN TRÌNH NHƯNG GIỮ NGUYÊN TRÌNH DUYỆT ĐỂ BẠN KIỂM TRA TRÊN MÀN HÌNH (KHÔNG ĐÓNG CHROME)...")
                while True:
                    time.sleep(3600)

            except Exception as e:
                err_type = type(e).__name__
                err_msg  = str(e)[:200]
                log(f"\n[!] LỖI KHÔNG MONG ĐỢI ({err_type}): {err_msg}")

                # Kiểm tra phiên browser có bị chết / mất kết nối không
                session_dead_keywords = ["invalid session", "no such window", "disconnected", "chrome not reachable", "session deleted"]
                is_dead = any(k in err_msg.lower() for k in session_dead_keywords)

                throttle_keywords = ["rate limit", "too many requests", "spam", "chặn", "tạm thời", "bị hạn chế"]
                is_throttle = any(k in err_msg.lower() for k in throttle_keywords)

                if is_dead:
                    log("[!] Trình duyệt bị mất phiên kết nối. Tự động tái khởi động Chrome an toàn...")
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    time.sleep(3)
                    driver = make_driver(cfg, headless=False, enable_images=False)
                    consecutive_zeros = 0
                elif is_throttle:
                    log(f"[!] Phát hiện rate-limit/throttle. Sleep {THROTTLE_SLEEP//60} phút, GIỮ NGUYÊN BROWSER...")
                    time.sleep(THROTTLE_SLEEP)
                    log("[+] Hết thời gian chờ, tiếp tục cào...")
                else:
                    log(f"[!] Lỗi thông thường, nghỉ 20 giây rồi tiếp tục (GIỮ NGUYÊN BROWSER)...")
                    time.sleep(20)

            session_idx += 1

    except KeyboardInterrupt:
        log("\n[DỪNG] Ctrl+C nhận được. Lưu DB và thoát...")

    finally:
        # Báo cáo cuối
        report_progress(conn)
        conn.close()
        if driver is not None:
            log("[INFO] Browser vẫn đang mở. Đóng browser...")
            try:
                driver.quit()
            except Exception:
                pass
        log("[HOÀN TẤT] Chương trình kết thúc.")


def _make_throttle(cfg):
    """Tạo Throttle object mới cho mỗi batch."""
    from uitconf.scraper.timer import Throttle
    return Throttle(cfg)


if __name__ == "__main__":
    main()

