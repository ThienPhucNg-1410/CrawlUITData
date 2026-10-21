import sys
import os
import time
import json
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, 'src')
import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
driver = make_driver(cfg, headless=True, enable_images=False)
try:
    test_url = 'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1135150639047664/'
    print(f'Testing extraction on: {test_url}')
    driver.get(test_url)
    time.sleep(6)
    
    # 1. Close popups
    driver.execute_script("""
    for (const b of document.querySelectorAll('div[aria-label="Đóng"], div[aria-label="Close"], div[role="button"][aria-label="Close"]')) {
        try { b.click(); } catch(e) {}
    }
    """)
    time.sleep(1)

    # 2. Extract post details: text, reactions, comments count, shares count
    extract_post_js = """
    const res = {
        reactions: 0,
        comments_count: 0,
        shares_count: 0,
        post_text: '',
        comments: []
    };

    const bodyText = document.body.innerText;
    
    // 1. Phân tích số lượng bình luận và lượt chia sẻ từ text toàn trang
    const commentMatch = bodyText.match(/([0-9.,]+[KkMm]?)\\s*(?:bình luận|comments?)/i);
    if (commentMatch) res.comments_count = commentMatch[1];
    
    const shareMatch = bodyText.match(/([0-9.,]+[KkMm]?)\\s*(?:lượt chia sẻ|chia sẻ|shares?)/i);
    if (shareMatch) res.shares_count = shareMatch[1];

    // 2. Tìm số reactions
    const rxSpans = Array.from(document.querySelectorAll('span[role="toolbar"] span, div[aria-label*="cảm xúc"], span[aria-label*="cảm xúc"]'));
    for (const s of rxSpans) {
        const aria = s.getAttribute('aria-label') || '';
        const txt = s.innerText.trim();
        const m = aria.match(/([0-9.,]+[KkMm]?)\\s*(?:người khác|cảm xúc)/i) || txt.match(/^([0-9.,]+[KkMm]?)$/);
        if (m) {
            res.reactions = m[1];
            break;
        }
    }
    if (!res.reactions) {
        const allReactionButtons = Array.from(document.querySelectorAll('div[role="button"]'))
            .filter(b => (b.getAttribute('aria-label') || '').includes('cảm xúc') || (b.getAttribute('aria-label') || '').includes('người khác'));
        if (allReactionButtons.length > 0) {
            res.reactions = allReactionButtons[0].innerText.trim() || allReactionButtons[0].getAttribute('aria-label');
        }
    }

    // 3. Lấy tất cả comments
    const articles = Array.from(document.querySelectorAll('div[role="article"]'));
    const commentArticles = articles.filter(a => {
        const aria = a.getAttribute('aria-label') || '';
        return aria.toLowerCase().includes('bình luận') || aria.toLowerCase().includes('comment') || a.innerText.includes('Trả lời') || a.innerText.includes('Reply');
    });

    res.comments = commentArticles.map((ca, idx) => {
        const aria = ca.getAttribute('aria-label') || '';
        const rawText = ca.innerText.trim();
        return {
            idx: idx,
            aria: aria,
            rawText: rawText
        };
    });

    return res;
    """
    
    data = driver.execute_script(extract_post_js)
    with open('extracted_sample.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("SUCCESS: saved to extracted_sample.json")

finally:
    driver.quit()

