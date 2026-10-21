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
    
    # Inspect the main post article element specifically
    js = """
    // Lấy bài viết chính (thường là div[role="article"] đầu tiên hoặc div[role="main"] article)
    const arts = Array.from(document.querySelectorAll('div[role="article"]'));
    const post = arts[0];
    
    // Tìm các chuỗi văn bản trong post
    const textAll = post ? post.innerText : '';
    
    // Tìm các phần tử chứa số cảm xúc (toolbar/reactions)
    const reactionElements = Array.from(post.querySelectorAll('span[role="toolbar"], div[aria-label*="cảm xúc"], div[aria-label*="reaction"], span[aria-label*="cảm xúc"]'))
        .map(e => ({ text: e.innerText, aria: e.getAttribute('aria-label') }));
        
    // Tìm thanh thống kê (stats row: X bình luận, Y lượt chia sẻ, số lượt thích)
    // Thường chứa text có "bình luận", "chia sẻ", hoặc nằm trước nút Thích/Bình luận
    const statSpans = Array.from(post.querySelectorAll('span'))
        .map(s => s.innerText.trim())
        .filter(t => t.match(/(\\d+.*(bình luận|comment|chia sẻ|share)|^[0-9.,]+$)/i));

    return {
        postTextSnippet: textAll.slice(0, 300),
        reactionElements: reactionElements,
        statSpans: statSpans,
        postFullText: textAll
    };
    """
    res = driver.execute_script(js)
    with open('test_post_stats.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print('Done dumping test_post_stats.json')
finally:
    driver.quit()

