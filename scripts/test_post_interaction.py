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
    print(f"Loading {test_url} ...")
    driver.get(test_url)
    time.sleep(5)

    # 1. Thử click chuyển sang 'Tất cả bình luận'
    switch_filter_js = """
    // Tìm dropdown Phù hợp nhất
    const buttons = Array.from(document.querySelectorAll('div[role="button"], span'));
    const filterBtn = buttons.find(b => b.innerText && (b.innerText.trim() === 'Phù hợp nhất' || b.innerText.trim() === 'Most relevant'));
    if (filterBtn) {
        filterBtn.click();
        return { clicked: true, text: filterBtn.innerText.trim() };
    }
    return { clicked: false };
    """
    filter_res = driver.execute_script(switch_filter_js)
    print("Filter click:", filter_res)
    time.sleep(1.5)

    if filter_res.get('clicked'):
        select_all_js = """
        // Tìm menu item 'Tất cả bình luận'
        const menuItems = Array.from(document.querySelectorAll('div[role="menuitem"], div[role="button"], span'));
        const allCommentsOpt = menuItems.find(m => m.innerText && (m.innerText.includes('Tất cả bình luận') || m.innerText.includes('All comments')));
        if (allCommentsOpt) {
            allCommentsOpt.click();
            return { selected: true, text: allCommentsOpt.innerText.trim() };
        }
        return { selected: false };
        """
        sel_res = driver.execute_script(select_all_js)
        print("Select all comments click:", sel_res)
        time.sleep(3)

    # 2. Thử click mở rộng 'Xem thêm bình luận' và 'Xem phản hồi'
    expand_js = """
    let clickedCount = 0;
    const expandButtons = Array.from(document.querySelectorAll('div[role="button"], span'))
        .filter(el => {
            const txt = el.innerText ? el.innerText.trim() : '';
            return txt.match(/^Xem thêm bình luận/i) || 
                   txt.match(/^Xem các bình luận trước/i) || 
                   txt.match(/^Xem (\\d+ )?phản hồi/i) ||
                   txt.match(/^Xem thêm phản hồi/i) ||
                   txt.match(/^View (more )?comments/i) ||
                   txt.match(/^View (\\d+ )?replies/i);
        });

    for (const btn of expandButtons) {
        try {
            btn.click();
            clickedCount++;
        } catch (e) {}
    }
    return { clickedCount: clickedCount, totalFound: expandButtons.length };
    """
    expand_res = driver.execute_script(expand_js)
    print("Expand comments clicked:", expand_res)
    time.sleep(3)

    # 3. Trích xuất toàn bộ dữ liệu bài viết
    extract_all_js = """
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

    // B. Post Author & Content
    // Tìm author từ link group user hoặc heading
    let author = '';
    const userLinks = Array.from(document.querySelectorAll('a[role="link"]'))
        .filter(a => {
            const h = a.getAttribute('href') || '';
            return h.includes('/user/') && a.innerText.trim().length > 1;
        });
    if (userLinks.length > 0) {
        author = userLinks[0].innerText.trim();
    }

    // Post text
    let post_text = '';
    const allDirs = Array.from(document.querySelectorAll('div[dir="auto"]'));
    const postCandidates = allDirs.filter(d => {
        const inArticle = !!d.closest('div[role="article"]');
        return !inArticle && d.innerText.trim().length > 10;
    });
    if (postCandidates.length > 0) {
        // Bài viết chính là bài có nội dung dài nhất trong các candidates không thuộc comment
        postCandidates.sort((a, b) => b.innerText.length - a.innerText.length);
        post_text = postCandidates[0].innerText.trim();
    }

    // Time / Created
    let time_raw = '';
    const timeLinks = Array.from(document.querySelectorAll('a[role="link"] span'))
        .filter(s => {
            const t = s.innerText.trim();
            return t.match(/^\\d+\\s*(ngày|giờ|phút|tuần|tháng|năm|d|h|m|w|y)/i) || t.includes('trước');
        });
    if (timeLinks.length > 0) {
        time_raw = timeLinks[0].innerText.trim();
    }

    // C. Comments
    const commentArticles = Array.from(document.querySelectorAll('div[role="article"]'))
        .filter(a => {
            const aria = (a.getAttribute('aria-label') || '').toLowerCase();
            return aria.includes('bình luận') || aria.includes('comment') || a.innerText.includes('Trả lời') || a.innerText.includes('Reply');
        });

    const parsedComments = [];
    for (let i = 0; i < commentArticles.length; i++) {
        const ca = commentArticles[i];
        const aria = ca.getAttribute('aria-label') || '';
        const lines = ca.innerText.split('\\n').map(l => l.trim()).filter(Boolean);

        let commentAuthor = '';
        let commentTime = '';
        let commentBodyLines = [];
        let commentReactions = 0;

        // Tác giả bình luận
        if (lines.length > 0) {
            commentAuthor = lines[0];
        }

        // Tách thời gian và body
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
                // Có thể là số like của comment
                const rVal = parseCount(line);
                if (rVal > 0) commentReactions = rVal;
                continue;
            }
            commentBodyLines.push(line);
        }

        const commentText = commentBodyLines.join('\\n').trim();

        // Tìm link hoặc ID bình luận nếu có
        let commentId = '';
        const cLinks = Array.from(ca.querySelectorAll('a[href*="comment_id="]'));
        if (cLinks.length > 0) {
            const m = cLinks[0].href.match(/comment_id=(\\d+)/);
            if (m) commentId = m[1];
        }
        if (!commentId) {
            // Fallback tạo unique id từ index
            commentId = 'c_' + i;
        }

        parsedComments.push({
            comment_id: commentId,
            author: commentAuthor,
            text: commentText || ca.innerText.trim(),
            time_raw: commentTime,
            reactions: commentReactions,
            raw: ca.innerText.trim()
        });
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
    final_data = driver.execute_script(extract_all_js)
    with open('test_post_final_extracted.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    print("SUCCESS! Post Extracted:")
    print(f"- Author: {final_data.get('post_author')}")
    print(f"- Text len: {len(final_data.get('post_text', ''))}")
    print(f"- Reactions: {final_data.get('reactions')}")
    print(f"- Shares: {final_data.get('shares')}")
    print(f"- Comments recorded: {final_data.get('n_comments')}")
    print(f"- Comments extracted: {final_data.get('comments_count_extracted')}")
finally:
    driver.quit()

