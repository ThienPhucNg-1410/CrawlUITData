from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def make_driver(cfg, headless=False, enable_images=False):
    o = Options()
    profile_dir = Path(cfg.get("browser_profile_dir", "browser_profile")).resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = (profile_dir.parent / ".chrome_cache").resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)
    o.add_argument(f"--user-data-dir={profile_dir}")
    o.add_argument(f"--disk-cache-dir={cache_dir}")
    o.add_argument(f"--lang={cfg.get('ui_language','vi')}")
    o.add_argument("--window-size=1280,900")
    # Cấu hình ổn định, tắt hoàn toàn GPU và tối ưu VRAM/RAM theo chuẩn Chrome Windows:
    o.add_argument("--disable-gpu")
    o.add_argument("--disable-gpu-compositing")
    o.add_argument("--disable-software-rasterizer")
    o.add_argument("--disable-accelerated-2d-canvas")
    o.add_argument("--disable-accelerated-video-decode")
    o.add_argument("--disable-gpu-rasterization")
    o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage")
    o.add_argument("--js-flags=--max-old-space-size=256")
    if not enable_images:
        o.add_argument("--blink-settings=imagesEnabled=false")
    o.add_argument("--disable-notifications")
    
    o.page_load_strategy = "eager"
    if headless:
        o.add_argument("--headless=new")
    driver = webdriver.Chrome(options=o)
    driver.set_page_load_timeout(35)
    driver.set_script_timeout(15)
    return driver

def manual_login(driver, url="https://www.facebook.com/"):
    driver.get(url)
    input("Đăng nhập TÀI KHOẢN PHỤ thủ công trong cửa sổ trình duyệt, xong nhấn Enter...")
