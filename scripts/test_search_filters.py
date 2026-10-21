import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, 'src')
import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
driver = make_driver(cfg, headless=True, enable_images=False)
try:
    url = "https://www.facebook.com/groups/congdongsinhvien.hcmuit/search/?q=thầy"
    driver.get(url)
    time.sleep(5)
    
    js = """
    const items = Array.from(document.querySelectorAll('span, div[role="button"], div[role="checkbox"], div[role="radio"]'))
        .filter(e => e.innerText && (e.innerText.includes('Ngày đăng') || e.innerText.includes('Mới đây nhất') || e.innerText.includes('Năm')));
    return items.map(e => ({ tag: e.tagName, text: e.innerText.trim(), role: e.getAttribute('role') }));
    """
    res = driver.execute_script(js)
    print("Filter items found:", res)
finally:
    driver.quit()

