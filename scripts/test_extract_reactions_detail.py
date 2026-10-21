import sys
import os
import time
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
driver = make_driver(cfg, headless=True, enable_images=False)
try:
    url = "https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1139837498578978/"
    print(f"Loading {url} ...")
    driver.get(url)
    time.sleep(5)

    extract_js = """
    function parseCount(str) {
        if (!str) return 0;
        str = str.replace(/\\s+/g, '').replace(',', '.');
        let multiplier = 1;
        if (/k/i.test(str)) { multiplier = 1000; str = str.replace(/k/i, ''); }
        else if (/m/i.test(str)) { multiplier = 1000000; str = str.replace(/m/i, ''); }
        const val = parseFloat(str);
        return isNaN(val) ? 0 : Math.round(val * multiplier);
    }

    function parseReactionsFromContainer(container) {
        const detail = {
            like: 0,
            love: 0,
            care: 0,
            haha: 0,
            wow: 0,
            sad: 0,
            angry: 0,
            total: 0
        };

        const buttons = Array.from(container.querySelectorAll('div[role="button"][aria-label], span[aria-label]'));
        for (const btn of buttons) {
            const aria = btn.getAttribute('aria-label') || '';
            // Khớp các mẫu: 'Thích: 8 người', 'Yêu thích: 3 người', 'Haha: 1 người'
            const m = aria.match(/^(Thích|Yêu thích|Thương thương|Haha|Wow|Buồn|Phẫn nộ):?\\s*([0-9.,]+[KkMm]?)\\s*người?/i);
            if (m) {
                const rType = m[1].toLowerCase();
                const count = parseCount(m[2]);
                if (rType === 'thích') detail.like += count;
                else if (rType === 'yêu thích') detail.love += count;
                else if (rType === 'thương thương') detail.care += count;
                else if (rType === 'haha') detail.haha += count;
                else if (rType === 'wow') detail.wow += count;
                else if (rType === 'buồn') detail.sad += count;
                else if (rType === 'phẫn nộ') detail.angry += count;
            }
        }
        detail.total = detail.like + detail.love + detail.care + detail.haha + detail.wow + detail.sad + detail.angry;
        return detail;
    }

    // 1. Phân tách biểu cảm Post gốc
    // Post toolbar thường là span[role="toolbar"] đầu tiên ngoài comment articles
    const toolbars = Array.from(document.querySelectorAll('span[role="toolbar"]'));
    let postReactions = { like: 0, love: 0, care: 0, haha: 0, wow: 0, sad: 0, angry: 0, total: 0 };
    if (toolbars.length > 0) {
        postReactions = parseReactionsFromContainer(toolbars[0]);
    }

    // 2. Phân tách biểu cảm từng Comment
    const commentArticles = Array.from(document.querySelectorAll('div[role="article"]'))
        .filter(a => {
            const aria = (a.getAttribute('aria-label') || '').toLowerCase();
            return aria.includes('bình luận') || aria.includes('comment') || a.innerText.includes('Trả lời');
        });

    const commentsData = [];
    for (const ca of commentArticles) {
        // Tìm link lấy comment_id
        let commentId = '';
        const cLink = ca.querySelector('a[href*="comment_id="]');
        if (cLink) {
            const match = cLink.href.match(/comment_id=(\\d+)/);
            if (match) commentId = match[1];
        }

        const commReactions = parseReactionsFromContainer(ca);
        commentsData.push({
            comment_id: commentId,
            reactions_detail: commReactions,
            snippet: ca.innerText.slice(0, 50).replace(/\\n/g, ' ')
        });
    }

    return {
        post_reactions: postReactions,
        comments_count: commentsData.length,
        comments_sample: commentsData.slice(0, 5)
    };
    """
    res = driver.execute_script(extract_js)
    print("Post Reactions Detail:")
    print(json.dumps(res["post_reactions"], indent=2, ensure_ascii=False))
    print(f"\nComments parsed: {res['comments_count']}")
    for c in res["comments_sample"]:
        print(f" - [{c['comment_id']}] {c['reactions_detail']} | {c['snippet']}")

finally:
    driver.quit()

