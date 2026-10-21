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
    print(f'Testing extraction without closing modal on: {test_url}')
    driver.get(test_url)
    time.sleep(6)

    extract_post_js = """
    // Không bấm nút Đóng/Close vì đó là nút tắt post modal!
    const res = {
        reactions: 0,
        comments_count: 0,
        shares_count: 0,
        post_text: '',
        comments: []
    };

    const articles = Array.from(document.querySelectorAll('div[role="article"]'));
    
    // Tìm bài viết chính (post) và các comment
    // Bài chính thường là article không có aria-label chứa 'bình luận' hoặc là article đầu tiên có nội dung bài
    const postArticle = articles.find(a => {
        const aria = (a.getAttribute('aria-label') || '').toLowerCase();
        return !aria.includes('bình luận') && !aria.includes('comment') && a.innerText.length > 50;
    }) || articles[0];

    if (postArticle) {
        res.post_text = postArticle.innerText.trim();
    }

    const bodyText = document.body.innerText;
    
    // 1. Phân tích số lượng bình luận và lượt chia sẻ
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

    // 3. Lấy tất cả comments
    const commentArticles = articles.filter(a => {
        const aria = (a.getAttribute('aria-label') || '').toLowerCase();
        return aria.includes('bình luận') || aria.includes('comment') || a.innerText.includes('Trả lời') || a.innerText.includes('Reply');
    });

    res.comments = commentArticles.map((ca, idx) => {
        const aria = ca.getAttribute('aria-label') || '';
        const lines = ca.innerText.split('\\n').map(l => l.trim()).filter(Boolean);
        
        // Tách tác giả, thời gian, nội dung
        let author = '';
        let commentText = '';
        if (lines.length > 0) {
            author = lines[0];
            // Các dòng nội dung nằm giữa tác giả/thời gian và nút Trả lời/Thích
            const contentLines = lines.filter(l => !['Trả lời', 'Thích', 'Chia sẻ', 'Theo dõi', 'Reply', 'Like', 'Share'].includes(l) && !l.match(/^\\d+\\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y)/i) && l !== '·' && l !== author);
            commentText = contentLines.join(' ');
        }
        return {
            idx: idx,
            aria: aria,
            author: author,
            text: commentText || ca.innerText.trim(),
            raw: ca.innerText.trim()
        };
    });

    return res;
    """
    
    data = driver.execute_script(extract_post_js)
    with open('extracted_sample2.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"SUCCESS: extracted {len(data['comments'])} comments, reactions={data['reactions']}, comments_count={data['comments_count']}, shares_count={data['shares_count']}")

finally:
    driver.quit()

