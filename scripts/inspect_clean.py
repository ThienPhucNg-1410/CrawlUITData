import sys
import os
import time
import json
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

sys.path.insert(0, 'src')
import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
driver = make_driver(cfg, headless=True, enable_images=False)
try:
    test_url = 'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1135150639047664/'
    driver.get(test_url)
    time.sleep(5)
    
    # Send ESC to close any notification or popup
    body = driver.find_element(By.TAG_NAME, 'body')
    body.send_keys(Keys.ESCAPE)
    time.sleep(1)
    body.send_keys(Keys.ESCAPE)
    time.sleep(1)
    
    js = """
    // Tìm bài viết trên trang
    // Bài viết trong group permalink có thể nằm trong div[role="main"] hoặc article
    const articles = Array.from(document.querySelectorAll('div[role="article"]'));
    const allText = document.body.innerText;
    
    // Tìm các chuỗi bình luận
    const comments = articles.filter(a => a.innerText.includes('Trả lời') || a.innerText.includes('Reply'));
    
    // Tìm reaction & stats trên toàn trang
    const statsMatches = Array.from(allText.matchAll(/([0-9.,]+[KkMm]?)\\s*(bình luận|chia sẻ|lượt chia sẻ|comment|share)/gi))
        .map(m => m[0]);
        
    // Tìm số cảm xúc (toolbar/like count)
    const reactionSpans = Array.from(document.querySelectorAll('span[role="toolbar"] span, div[aria-label*="cảm xúc"], span[aria-label*="cảm xúc"]'))
        .map(e => ({ text: e.innerText, aria: e.getAttribute('aria-label') }));

    return {
        totalArticles: articles.length,
        commentsCount: comments.length,
        commentsSample: comments.slice(0, 3).map(c => c.innerText.slice(0, 150)),
        statsMatches: statsMatches,
        reactionSpans: reactionSpans,
        bodyTextSnippet: allText.slice(0, 500)
    };
    """
    res = driver.execute_script(js)
    with open('test_post_clean.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print('Done test_post_clean.json')
finally:
    driver.quit()

