import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'src')
import uitconf.config as C
from uitconf.scraper.driver import make_driver
import json
import time

cfg = C.load()
driver = make_driver(cfg, headless=True, enable_images=False)
try:
    driver.get(cfg['page_url'])
    print("Page opened, waiting 5s...")
    time.sleep(5)
    
    # Check feeds and articles before scroll
    count_before = driver.execute_script("return document.querySelectorAll('div[role=\"article\"]').length")
    print(f"Articles before scroll: {count_before}")
    
    # Scroll down 3 times
    for s in range(3):
        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(2)
        c = driver.execute_script("return document.querySelectorAll('div[role=\"article\"]').length")
        links_c = driver.execute_script("return document.querySelectorAll('a[href*=\"/posts/\"], a[href*=\"pfbid\"]').length")
        print(f"Scroll {s+1}: Articles = {c}, Post links = {links_c}")

    # Inspect all post links
    js = """
    const allLinks = Array.from(document.querySelectorAll('a[href*="/posts/"], a[href*="pfbid"]')).map(a => ({
        href: a.href,
        text: a.innerText.trim(),
        closestArticle: !!a.closest('div[role="article"]'),
        closestFeed: !!a.closest('div[role="feed"]')
    }));
    return {
        totalLinks: allLinks.length,
        samples: allLinks.slice(0, 5)
    };
    """
    res = driver.execute_script(js)
    print("Result:", json.dumps(res, indent=2, ensure_ascii=False))
finally:
    driver.quit()
