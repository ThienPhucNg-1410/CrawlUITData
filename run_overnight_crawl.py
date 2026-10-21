import time
import os
import sys
import subprocess
from datetime import datetime, timedelta

PYTHON_EXE = sys.executable
PROJECT_DIR = r"d:\uit-confession-sentiment\uit-confession-sentiment"
TARGET_END_HOUR = 5  # 5h00 sáng

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def log(msg):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now_str}] {msg}"
    print(line, flush=True)
    with open(os.path.join(PROJECT_DIR, "logs", "overnight_crawler.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_current_stats():
    import sqlite3
    db_path = os.path.join(PROJECT_DIR, "data", "raw", "raw.sqlite")
    if not os.path.exists(db_path):
        return 0, "N/A"
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        cnt = c.execute("SELECT count(*) FROM posts").fetchone()[0]
        oldest = c.execute("SELECT min(created_at) FROM posts WHERE created_at IS NOT NULL").fetchone()[0]
        conn.close()
        return cnt, oldest
    except Exception as e:
        return 0, str(e)

def rebuild_clean_and_export():
    """Tự động rebuild data/clean/units.csv và cập nhật dữ liệu gán nhãn sau mỗi mẻ"""
    try:
        log("--> Đang tự động rebuild clean units và cập nhật bộ dữ liệu...")
        cmd = f'python -m uitconf.cli build'
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        res = subprocess.run(cmd, cwd=PROJECT_DIR, env=env, shell=True, capture_output=True, text=True)
        log("--> Cập nhật clean units thành công!")
    except Exception as e:
        log(f"Lỗi rebuild: {e}")

def main():
    os.makedirs(os.path.join(PROJECT_DIR, "logs"), exist_ok=True)
    log("=================================================================")
    log(" BẮT ĐẦU CHƯƠNG TRÌNH ĐIỀU PHỐI CÀO DỮ LIỆU ĐÊM (HẾT TRƯỚC 5H SÁNG)")
    log("=================================================================")
    
    # Tính thời gian mục tiêu 5h sáng ngày hôm sau
    now = datetime.now()
    if now.hour >= TARGET_END_HOUR:
        deadline = (now + timedelta(days=1)).replace(hour=TARGET_END_HOUR, minute=0, second=0, microsecond=0)
    else:
        deadline = now.replace(hour=TARGET_END_HOUR, minute=0, second=0, microsecond=0)
    
    total_remaining_seconds = (deadline - now).total_seconds()
    log(f"Thời gian hiện tại: {now.strftime('%H:%M:%S')}")
    log(f"Hạn chót hoàn tất:  {deadline.strftime('%Y-%m-%d %H:%M:%S')} (Còn {total_remaining_seconds/3600:.1f} giờ)")
    
    batch_num = 0
    cooldown_path = os.path.join(PROJECT_DIR, "data", "raw", ".cooldown")

    while datetime.now() < deadline:
        batch_num += 1
        cnt_before, oldest_before = get_current_stats()
        log(f"\n--- [PHIÊN {batch_num}] Bắt đầu chạy cào mẻ mới | Hiện có: {cnt_before} bài (mốc cũ nhất: {oldest_before[:16] if oldest_before else 'N/A'}) ---")

        # Kiểm tra cooldown file nếu có
        if os.path.exists(cooldown_path):
            log(f"Phát hiện file cooldown! Tạm nghỉ 15 phút trước khi thử lại...")
            time.sleep(900)
            continue

        cmd = 'python -m uitconf.cli discover'
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        
        start_t = time.time()
        try:
            # Chạy mẻ cào
            proc = subprocess.run(cmd, cwd=PROJECT_DIR, env=env, shell=True, capture_output=True, text=True)
            elapsed = time.time() - start_t
            cnt_after, oldest_after = get_current_stats()
            new_gathered = cnt_after - cnt_before
            
            log(f"Kết thúc phiên {batch_num} sau {elapsed/60:.1f} phút.")
            log(f"Số bài mới thu thêm: +{new_gathered} bài | Tổng CSDL: {cnt_after} bài | Mốc ngày mới nhất: {oldest_after[:16] if oldest_after else 'N/A'}")
            
            if "HARD STOP" in proc.stdout or "HARD STOP" in proc.stderr:
                log(f"[CẢNH BÁO] Facebook phát hiện tần suất cao (HardStop). Nghỉ ngơi 25 phút để thả lỏng nick...")
                time.sleep(1500)
            elif new_gathered == 0:
                log(f"Không có thêm bài mới trong lượt này (có thể đã chạm đáy feed). Nghỉ 10 phút trước khi quét sâu hơn...")
                time.sleep(600)
            else:
                rebuild_clean_and_export()
                # Nghỉ giải lao an toàn giữa 2 phiên (8-12 phút)
                sleep_min = 10
                log(f"Nghỉ giãn cách sinh lý người dùng {sleep_min} phút trước khi mở phiên tiếp theo...")
                time.sleep(sleep_min * 60)

        except Exception as e:
            log(f"Lỗi phiên {batch_num}: {e}. Nghỉ 5 phút...")
            time.sleep(300)

        # Kiểm tra thời gian còn lại
        remaining = (deadline - datetime.now()).total_seconds()
        if remaining <= 1800: # Còn dưới 30 phút trước 5h sáng
            log(f"Đã chạm ngưỡng cận hạn chót 5h sáng (còn {remaining/60:.1f} phút). Hoàn tất toàn bộ chiến dịch cào!")
            break

    rebuild_clean_and_export()
    log("=================================================================")
    log(" CHIẾN DỊCH CÀO QUA ĐÊM ĐÃ HOÀN TẤT TRƯỚC 5H00 SÁNG!")
    log("=================================================================")

if __name__ == "__main__":
    main()
