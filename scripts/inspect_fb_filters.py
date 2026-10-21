import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, 'src')
import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
driver = make_driver(cfg, headless=True)
try:
    url = "https://www.facebook.com/groups/congdongsinhvien.hcmuit/search/?q=2026"
    driver.get(url)
    time.sleep(5)
    print("Search URL title:", driver.title)
    
    # Check filters on page
    js = """
    const buttons = Array.from(document.querySelectorAll('div[role="button"], span, div[role="radio"], div[role="checkbox"]'))
        .map(e => e.innerText.trim())
        .filter(t => t.length > 0 && t.length < 40)
        .slice(0, 30);
    return {
        url: window.location.href,
        buttons: buttons
    };
    """
    res = driver.execute_script(js)
    print("Filters/Buttons:", res['buttons'])
finally:
    driver.quit()

