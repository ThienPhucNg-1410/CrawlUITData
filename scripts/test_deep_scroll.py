import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'src')
import uitconf.config as C
from uitconf.scraper.driver import make_driver
import time

cfg = C.load()
driver = make_driver(cfg, headless=True, enable_images=False)
try:
    url = cfg['page_url']
    print(f"Opening: {url}")
    driver.get(url)
    time.sleep(5)
    
    print("\n--- FAST SCROLLING TO TEST DEEP FEED BEHAVIOR ---")
    seen_posts = set()
    oldest_seen_time = None
    
    for i in range(25):
        driver.execute_script("window.scrollBy(0, 3000);")
        time.sleep(1.2)
        
        js_info = """
        const links = Array.from(document.querySelectorAll('a[href*="/posts/"], a[href*="pfbid"]')).map(a => ({
            href: a.href,
            text: a.innerText.trim()
        }));
        const buttons = Array.from(document.querySelectorAll('div[role="button"]')).map(b => b.innerText.trim()).filter(t => t.length > 0 && t.length < 30);
        return {
            links: links,
            buttons: buttons.slice(0, 5),
            scrollHeight: document.body.scrollHeight,
            scrollY: window.scrollY
        };
        """
        info = driver.execute_script(js_info)
        new_in_scroll = 0
        for l in info["links"]:
            h = l["href"].split("?")[0]
            if h not in seen_posts:
                seen_posts.add(h)
                new_in_scroll += 1
                if l["text"]:
                    oldest_seen_time = l["text"]
                    
        print(f"Scroll {i+1:2d} | ScrollY: {info['scrollY']:6d} | BodyHeight: {info['scrollHeight']:6d} | Total posts seen: {len(seen_posts):3d} | Latest time text: {oldest_seen_time}")
        
    print(f"\nFinished test: Saw {len(seen_posts)} posts in 25 scrolls.")
finally:
    driver.quit()

