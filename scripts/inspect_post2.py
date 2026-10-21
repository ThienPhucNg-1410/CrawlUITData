import sys
import os
import time
import json

sys.path.insert(0, 'src')
import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
driver = make_driver(cfg, headless=True, enable_images=False)
try:
    test_url = 'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1135150639047664/'
    driver.get(test_url)
    time.sleep(6)
    
    js = """
    const main = document.querySelector('div[role="main"]');
    const arts = Array.from(document.querySelectorAll('div[role="article"]'));
    return {
        mainFound: !!main,
        mainTextSnippet: main ? main.innerText.slice(0, 1000) : '',
        artsCount: arts.length,
        arts: arts.map((a, i) => ({
            i: i,
            textLen: a.innerText.length,
            snippet: a.innerText.slice(0, 250),
            aria: a.getAttribute('aria-label') || ''
        }))
    };
    """
    res = driver.execute_script(js)
    with open('test_post_inspect2.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print('Done inspect2')
finally:
    driver.quit()

