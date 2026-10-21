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
    for pid in ['1126425899920138', '1139252691970792']:
        url = f'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/{pid}/'
        driver.get(url)
        time.sleep(3.5)
        js = """
        const commentHeader = Array.from(document.querySelectorAll('div, span'))
            .find(e => e.innerText && (e.innerText.trim() === 'Phù hợp nhất' || e.innerText.trim() === 'Tất cả bình luận' || e.innerText.trim() === 'Most relevant'));
        let container = commentHeader ? commentHeader.closest('div[role="dialog"]') || commentHeader.closest('div[role="main"]') : null;
        if (!container) container = document;
        
        // Find headings / user links
        const items = Array.from(container.querySelectorAll('h2, h3, h4, strong span, a[role="link"][href*="/user/"], a[role="link"]'))
            .map(e => ({ tag: e.tagName, text: e.innerText.trim(), href: e.getAttribute('href') || '' }))
            .filter(e => e.text.length > 0 && e.text.length < 60)
            .slice(0, 15);
        return { pid: arguments[0], items: items };
        """
        res = driver.execute_script(js, pid)
        print(f"=== PID {pid} ===")
        for it in res['items']:
            print(" ", it)
finally:
    driver.quit()

