import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

p = Path("browser_profile").resolve()
print("Thử nghiệm với profile:", p)
o = Options()
o.add_argument(f"--user-data-dir={p}")
try:
    dr = webdriver.Chrome(options=o)
    print("Mở Chrome với profile thành công!")
    dr.quit()
    print("Đóng thành công.")
except Exception as e:
    print("LỖI KHI DÙNG PROFILE:")
    print(type(e).__name__, ":", e)
