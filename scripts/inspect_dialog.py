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
    // 1. Tìm Dialog hoặc Container chính chứa bài viết
    const dialog = document.querySelector('div[role="dialog"]');
    const container = dialog || document.querySelector('div[role="main"]') || document.body;

    // 2. Tìm tất cả text trong container
    const allText = container.innerText;

    // 3. Tìm số cảm xúc (Reactions)
    // Facebook thường hiển thị icon cảm xúc + số lượng (ví dụ: '12' hoặc '1,2K')
    // hoặc span có aria-label='12 người khác', 'Thích: 10'
    const reactionNodes = Array.from(container.querySelectorAll('span, div[role="button"]'))
        .filter(e => {
            const aria = e.getAttribute('aria-label') || '';
            const t = e.innerText.trim();
            return (aria.includes('cảm xúc') || aria.includes('người khác') || aria.includes('reaction') || 
                    aria.match(/^(Thích|Yêu thích|Haha|Wow|Buồn|Phẫn nộ):?\\s*\\d+/i) ||
                    (t.match(/^[0-9.,]+[KkMm]?$/) && e.closest('span[role="toolbar"], div[role="button"]')));
        })
        .map(e => ({ text: e.innerText.trim(), aria: e.getAttribute('aria-label') }));

    // 4. Tìm số bình luận và lượt chia sẻ
    // Thường có dạng 'X bình luận', 'Y lượt chia sẻ'
    const commentCountMatches = Array.from(allText.matchAll(/(\\d+[\\d.,]*[kKmM]?)\\s*(bình luận|comment|lượt chia sẻ|chia sẻ|share)/gi))
        .map(m => m[0]);

    // 5. Tìm các bình luận
    // Các div[role="article"] hoặc div[aria-label*="Bình luận dưới tên"]
    const comments = Array.from(container.querySelectorAll('div[role="article"]'))
        .filter(a => a.getAttribute('aria-label') || a.innerText.includes('Trả lời') || a.innerText.includes('Thích'))
        .map((a, i) => ({
            idx: i,
            aria: a.getAttribute('aria-label') || '',
            fullText: a.innerText
        }));

    return {
        hasDialog: !!dialog,
        matchedStats: commentCountMatches,
        reactionNodes: reactionNodes,
        commentsCount: comments.length,
        commentsSample: comments.slice(0, 5),
        containerTextSample: allText.slice(0, 800)
    };
    """
    res = driver.execute_script(js)
    with open('test_post_dialog.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print('Done test_post_dialog.json')
finally:
    driver.quit()

