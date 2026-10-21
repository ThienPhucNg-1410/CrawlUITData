import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, "uit-confession-sentiment/src")
import uitconf.config as C
from uitconf.scraper.driver import make_driver
from uitconf.scraper.parse import parse_time, post_id_from_href

cfg = C.load()
driver = make_driver(cfg, headless=True, enable_images=False)
try:
    url = "https://www.facebook.com/groups/congdongsinhvien.hcmuit/search/?q=thi"
    driver.get(url)
    time.sleep(4)
    driver.execute_script("window.scrollBy(0, 2000);")
    time.sleep(2)
    js = """
    const links = Array.from(document.querySelectorAll('a[href*="/posts/"], a[href*="pfbid"]'));
    return links.map(a => ({
        href: a.href,
        text: (a.innerText || '').trim(),
        aria: a.getAttribute('aria-label') || ''
    }));
    """
    res = driver.execute_script(js)
    print(f"Found {len(res)} link candidates")
    for r in res[:10]:
        pid = post_id_from_href(r['href'])
        t = r['aria'] or r['text']
        iso = parse_time(t)
        print(f"PID: {pid} | Time: {t} -> {iso} | Link: {r['href'][:60]}")
finally:
    driver.quit()

