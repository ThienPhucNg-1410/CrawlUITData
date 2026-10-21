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
    driver.get('https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1139252691970792/')
    time.sleep(2.5)
    js = """
    return Array.from(document.querySelectorAll('h2')).map(h => ({
        text: h.innerText.trim(),
        hasA: !!h.querySelector('a'),
        aText: h.querySelector('a') ? h.querySelector('a').innerText.trim() : '',
        inDialog: !!h.closest('div[role="dialog"]'),
        inMain: !!h.closest('div[role="main"]')
    }));
    """
    res = driver.execute_script(js)
    print("H2s:", res)
finally:
    driver.quit()

