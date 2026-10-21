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
    url = "https://www.facebook.com/groups/congdongsinhvien.hcmuit/search/?q=tháng 6"
    driver.get(url)
    time.sleep(4)
    print("Page title:", driver.title)
    
    js = """
    const links = Array.from(document.querySelectorAll('a[href*="/posts/"], a[href*="pfbid"]')).map(a => a.href);
    return {
        count: links.length,
        links: links.slice(0, 10),
        bodySnippet: document.body.innerText.slice(0, 500)
    };
    """
    res = driver.execute_script(js)
    print("Links count:", res['count'])
    for l in res['links']:
        print(" ", l)
    print("Snippet:", repr(res['bodySnippet'][:200]))
finally:
    driver.quit()

