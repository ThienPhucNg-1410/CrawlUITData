import sys
import os
import time
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, 'src')
import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
driver = make_driver(cfg, headless=True, enable_images=False)

def extract_current_post(driver):
    time.sleep(4)

    # 1. Switch to 'All comments' if available
    try:
        switch_filter_js = """
        const buttons = Array.from(document.querySelectorAll('div[role="button"], span'));
        const filterBtn = buttons.find(b => b.innerText && (b.innerText.trim() === 'Phù hợp nhất' || b.innerText.trim() === 'Most relevant'));
        if (filterBtn) {
            filterBtn.click();
            return true;
        }
        return false;
        """
        if driver.execute_script(switch_filter_js):
            time.sleep(1.2)
            select_all_js = """
            const menuItems = Array.from(document.querySelectorAll('div[role="menuitem"], div[role="button"], span'));
            const allCommentsOpt = menuItems.find(m => m.innerText && (m.innerText.includes('Tất cả bình luận') || m.innerText.includes('All comments')));
            if (allCommentsOpt) {
                allCommentsOpt.click();
                return true;
            }
            return false;
            """
            driver.execute_script(select_all_js)
            time.sleep(2.0)
    except Exception as e:
        pass

    # 2. Expand hidden comments
    try:
        for _ in range(3):
            expand_js = """
            let clicked = 0;
            const buttons = Array.from(document.querySelectorAll('div[role="button"], span'))
                .filter(el => {
                    const txt = el.innerText ? el.innerText.trim() : '';
                    return txt.match(/^Xem thêm bình luận/i) || 
                           txt.match(/^Xem các bình luận trước/i) || 
                           txt.match(/^Xem (\\d+ )?phản hồi/i) ||
                           txt.match(/^Xem thêm phản hồi/i) ||
                           txt.match(/^View (more )?comments/i) ||
                           txt.match(/^View (\\d+ )?replies/i);
                });
            for (const b of buttons) {
                try { b.click(); clicked++; } catch(e){}
            }
            return clicked;
            """
            c = driver.execute_script(expand_js)
            if c > 0:
                time.sleep(1.5)
            else:
                break
    except Exception:
        pass

    # 3. Extract post & comments
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

    // A. Stats (Reactions, Comments, Shares)
    let reactions = 0;
    let n_comments = 0;
    let shares = 0;

    const actionButtons = Array.from(document.querySelectorAll('div[role="button"]'));
    for (const btn of actionButtons) {
        const aria = btn.getAttribute('aria-label') || '';
        const txt = btn.innerText.trim();
        const numMatch = txt.match(/^([0-9.,]+[KkMm]?)$/);
        const val = numMatch ? parseCount(numMatch[1]) : 0;

        if (aria.toLowerCase().includes('thích') || aria.toLowerCase().includes('like')) {
            if (val > 0) reactions = val;
        } else if (aria.toLowerCase().includes('bình luận') || aria.toLowerCase().includes('comment')) {
            if (val > 0) n_comments = val;
        } else if (aria.toLowerCase().includes('gửi nội dung này') || aria.toLowerCase().includes('chia sẻ') || aria.toLowerCase().includes('share')) {
            if (val > 0) shares = val;
        }
    }

    // Nếu không thấy qua actionButtons, fallback tìm text tổng quát
    if (reactions === 0) {
        const rxNodes = Array.from(document.querySelectorAll('span[role="toolbar"] ~ span, span[aria-label*="cảm xúc"]'));
        for (const r of rxNodes) {
            const v = parseCount(r.innerText);
            if (v > 0) { reactions = v; break; }
        }
    }

    // B. Post Author & Post Text
    let author = '';
    const userLinks = Array.from(document.querySelectorAll('a[role="link"]'))
        .filter(a => {
            const h = a.getAttribute('href') || '';
            return h.includes('/user/') && a.innerText.trim().length > 1;
        });
    if (userLinks.length > 0) {
        author = userLinks[0].innerText.trim();
    }

    let post_text = '';
    const allDirs = Array.from(document.querySelectorAll('div[dir="auto"]'));
    const postCandidates = allDirs.filter(d => {
        const inArticle = !!d.closest('div[role="article"]');
        return !inArticle && d.innerText.trim().length > 10;
    });
    if (postCandidates.length > 0) {
        postCandidates.sort((a, b) => b.innerText.length - a.innerText.length);
        post_text = postCandidates[0].innerText.trim();
    }

    let time_raw = '';
    const timeLinks = Array.from(document.querySelectorAll('a[role="link"] span'))
        .filter(s => {
            const t = s.innerText.trim();
            return t.match(/^\\d+\\s*(ngày|giờ|phút|tuần|tháng|năm|d|h|m|w|y)/i) || t.includes('trước');
        });
    if (timeLinks.length > 0) {
        time_raw = timeLinks[0].innerText.trim();
    }

    // C. Comments (chỉ lấy leaf articles để tránh trùng lặp container)
    const allArticles = Array.from(document.querySelectorAll('div[role="article"]'))
        .filter(a => {
            const aria = (a.getAttribute('aria-label') || '').toLowerCase();
            return aria.includes('bình luận') || aria.includes('comment') || a.innerText.includes('Trả lời') || a.innerText.includes('Reply');
        });

    // Chỉ chọn article là nút lá (không chứa article con)
    const leafArticles = allArticles.filter(a => a.querySelectorAll('div[role="article"]').length === 0);

    const parsedComments = [];
    const seenCommentKeys = new Set();

    for (let i = 0; i < leafArticles.length; i++) {
        const ca = leafArticles[i];
        const lines = ca.innerText.split('\\n').map(l => l.trim()).filter(Boolean);

        let commentAuthor = '';
        let commentTime = '';
        let commentBodyLines = [];
        let commentReactions = 0;

        if (lines.length > 0) {
            commentAuthor = lines[0];
        }

        for (let j = 1; j < lines.length; j++) {
            const line = lines[j];
            if (line === '·' || line === '•') continue;
            if (line.match(/^\\d+\\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y)/i) || line.includes('trước')) {
                if (!commentTime) commentTime = line;
                continue;
            }
            if (['Trả lời', 'Thích', 'Chia sẻ', 'Theo dõi', 'Reply', 'Like', 'Share'].includes(line)) {
                continue;
            }
            if (line.match(/^[0-9.,]+[KkMm]?$/)) {
                const rVal = parseCount(line);
                if (rVal > 0) commentReactions = rVal;
                continue;
            }
            commentBodyLines.push(line);
        }

        const commentText = commentBodyLines.join('\\n').trim() || ca.innerText.trim();

        // Lấy comment_id
        let commentId = '';
        const cLinks = Array.from(ca.querySelectorAll('a[href*="comment_id="]'));
        for (const cl of cLinks) {
            const m = cl.href.match(/comment_id=(\\d+)/);
            if (m) { commentId = m[1]; break; }
        }
        if (!commentId) {
            // Hash key
            commentId = 'c_' + i + '_' + Math.random().toString(36).substr(2, 6);
        }

        const key = commentAuthor + '::' + commentText;
        if (!seenCommentKeys.has(key)) {
            seenCommentKeys.add(key);
            parsedComments.push({
                comment_id: commentId,
                author: commentAuthor,
                text: commentText,
                time_raw: commentTime,
                reactions: commentReactions
            });
        }
    }

    return {
        post_author: author,
        post_text: post_text,
        time_raw: time_raw,
        reactions: reactions,
        n_comments: n_comments || parsedComments.length,
        shares: shares,
        comments_count_extracted: parsedComments.length,
        comments: parsedComments
    };
    """
    return driver.execute_script(extract_js)

try:
    test_urls = [
        'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1138296438733084/',
        'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1138645378698190/'
    ]
    for url in test_urls:
        print(f"\n--- Loading {url} ---")
        driver.get(url)
        data = extract_current_post(driver)
        print(f"Author: {data.get('post_author')}")
        print(f"Text ({len(data.get('post_text', ''))} chars): {data.get('post_text', '')[:100]}...")
        print(f"Reactions: {data.get('reactions')} | Shares: {data.get('shares')} | Comments recorded: {data.get('n_comments')}")
        print(f"Comments extracted: {data.get('comments_count_extracted')}")
        for c in data.get('comments', [])[:3]:
            print(f"  - [{c.get('author')}]: {c.get('text')[:60]} (react={c.get('reactions')}, id={c.get('comment_id')})")
finally:
    driver.quit()

