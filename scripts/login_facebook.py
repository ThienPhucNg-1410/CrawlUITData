import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

import uitconf.config as C
from uitconf.scraper.driver import make_driver

def main():
    cfg = C.load()
    print("=" * 65)
    print("      HỆ THỐNG ĐĂNG NHẬP FACEBOOK LƯU PROFILE RIÊNG")
    print("=" * 65)
    print("[*] Đang mở trình duyệt Chrome với thư mục hồ sơ 'browser_profile'...")
    print("[*] LƯU Ý: Khuyến nghị dùng TÀI KHOẢN PHỤ (clone) để bảo đảm an toàn.")
    print("=" * 65)

    driver = make_driver(cfg, headless=False, enable_images=True)
    target_url = "https://www.facebook.com/"
    driver.get(target_url)

    print("\n[+] Đã mở trang đăng nhập Facebook.")
    print("[*] Hãy nhập tài khoản/mật khẩu và hoàn tất đăng nhập trực tiếp trên cửa sổ Chrome vừa hiện lên.")
    print("[*] Phiên đăng nhập sẽ được lưu vĩnh viễn vào thư mục 'browser_profile'.")
    print("\n>>> Khi bạn đã đăng nhập xong và nhìn thấy trang chủ / Bảng tin Facebook:")
    print("    Nhấn ENTER tại đây để hoàn tất và lưu cấu hình...")

    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass

    # Kiểm tra URL hoặc cookie sau khi đăng nhập
    current_url = driver.current_url
    print(f"\n[+] URL hiện tại của trình duyệt: {current_url}")
    cookies = driver.get_cookies()
    has_c_user = any(c.get("name") == "c_user" for c in cookies)
    
    if has_c_user:
        print("[THÀNH CÔNG] Đã phát hiện cookie đăng nhập (c_user)! Hồ sơ đã được lưu an toàn.")
    else:
        print("[!] Lưu ý: Chưa phát hiện cookie 'c_user' chuẩn, nhưng toàn bộ dữ liệu duyệt web đã được lưu vào 'browser_profile'.")

    print("[*] Đang đóng trình duyệt...")
    try:
        driver.quit()
    except Exception:
        pass

    print("\n==================================================================")
    print("  ĐÃ LƯU PHIÊN ĐĂNG NHẬP THÀNH CÔNG VÀO HỒ SƠ 'browser_profile'!")
    print("  Bây giờ bạn có thể chạy: run_continuous_crawler.bat")
    print("  Trình duyệt sẽ tự động duy trì đăng nhập và lướt sâu không giới hạn.")
    print("==================================================================")

if __name__ == "__main__":
    main()
