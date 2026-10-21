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
    url = 'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1139252691970792/'
    driver.get(url)
    time.sleep(5)
    print("URL:", driver.current_url)
    print("Title:", driver.title)
    
    # Check dialogs and articles
    js = """
    return {
        allDirs: Array.from(document.querySelectorAll('div[dir="auto"]')).map(d => d.innerText.trim()).filter(Boolean).slice(0, 10),
        articles: Array.from(document.querySelectorAll('div[role="article"]')).map(a => a.innerText.trim().slice(0, 100)),
        bodySnippet: document.body.innerText.slice(0, 1000)
    };
    """
    res = driver.execute_script(js)
    print("Dirs:", res['allDirs'])
    print("Articles count:", len(res['articles']))
    print("Body snippet:", res['bodySnippet'][:400])
finally:
    driver.quit()

