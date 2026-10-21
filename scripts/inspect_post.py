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
    print(f'Opening test post: {test_url}')
    driver.get(test_url)
    time.sleep(6)
    
    # 1. Search for reactions, comments count, shares
    js = """
    const postArticle = document.querySelector('div[role="article"]') || document.querySelector('div[role="main"]');
    const textAll = postArticle ? postArticle.innerText : document.body.innerText;
    
    // Tìm các phần tử chứa reaction, comment, share
    const allSpans = Array.from(document.querySelectorAll('span, div[role="button"]'))
        .map(e => ({
            text: e.innerText.trim(),
            aria: e.getAttribute('aria-label') || '',
            tag: e.tagName
        }))
        .filter(e => (e.text && e.text.length < 60) || e.aria);

    // Tìm các comment elements
    const commentNodes = Array.from(document.querySelectorAll('div[role="article"]'))
        .map((a, i) => ({
            idx: i,
            text: a.innerText.slice(0, 100),
            aria: a.getAttribute('aria-label') || ''
        }));

    return {
        title: document.title,
        url: window.location.href,
        allSpansSample: allSpans.slice(0, 60),
        commentNodesCount: commentNodes.length,
        commentNodesSample: commentNodes.slice(0, 5)
    };
    """
    res = driver.execute_script(js)
    with open('test_post_dom.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print('Done dumping test_post_dom.json')
finally:
    driver.quit()

