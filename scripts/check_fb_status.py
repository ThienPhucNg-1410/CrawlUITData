import os, sys, time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
print("[+] Đang mở Chrome kiểm tra tài khoản...")
driver = make_driver(cfg, headless=False, enable_images=True)
try:
    url = "https://www.facebook.com/groups/congdongsinhvien.hcmuit/?sorting_setting=CHRONOLOGICAL"
    driver.get(url)
    time.sleep(6)
    print("URL hiện tại:", driver.current_url)
    print("Tiêu đề trang:", driver.title)
    
    os.makedirs("logs", exist_ok=True)
    driver.save_screenshot("logs/fb_status.png")
    print("Đã lưu ảnh chụp màn hình vào logs/fb_status.png")
    
    body_text = driver.page_source.lower()
    markers = [
        "checkpoint", "xác nhận danh tính", "confirm your identity",
        "tạm thời bị chặn", "temporarily blocked", "hoạt động bất thường",
        "unusual activity", "tài khoản của bạn đã bị hạn chế"
    ]
    found = [m for m in markers if m in body_text]
    if found:
        print(f"[!] CẢNH BÁO: Phát hiện các dấu hiệu: {found}")
    else:
        print("[✓] TUYỆT VỜI: Trang hoạt động hoàn toàn bình thường, không có dấu hiệu bị chặn!")
finally:
    # Không đóng ngay, giữ 5 giây rồi thoát
    time.sleep(3)
    driver.quit()
