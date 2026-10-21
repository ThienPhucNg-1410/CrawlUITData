import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from selenium import webdriver

print("Python version:", sys.version)
options = webdriver.ChromeOptions()
# Thử khởi động Chrome trắng hoàn toàn, không add-on, không custom profile
print("Đang khởi tạo webdriver.Chrome(options=options)...")
try:
    driver = webdriver.Chrome(options=options)
    print("Khởi động Chrome thành công!")
    driver.get("https://www.google.com")
    print("Mở trang google.com thành công. Title:", driver.title)
    driver.quit()
    print("Đóng Chrome thành công.")
except Exception as e:
    print("LỖI KHỞI ĐỘNG CHROME:")
    print(type(e).__name__, ":", e)
