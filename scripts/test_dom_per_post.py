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
    url = 'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1135150639047664/'
    print(f"Opening {url} ...")
    driver.get(url)
    time.sleep(5)

    js = """
    // Trả về phân tích chi tiết các khối chính
    const result = {
        title: document.title,
        url: window.location.href,
        feedPost: null,
        reactions: 0,
        comments_count: 0,
        shares_count: 0,
        post_author: '',
        post_text: '',
        comments: []
    };

    // 1. Tìm tác giả và nội dung bài viết
    // Trên giao diện permalink, thường có h2 hoặc h3 hoặc strong hoặc span chứa tên người đăng
    // Tìm phần tử chứa "Toeic - Speaking Ms Ngọc" hoặc bài viết tương tự
    // Hãy quét tất cả div[dir="auto"]
    const allDirs = Array.from(document.querySelectorAll('div[dir="auto"]'));
    
    // Bài viết chính thường là div[dir="auto"] không nằm trong comment (không có ancestor role="article")
    // và có độ dài text đáng kể hoặc đứng trước khu vực bình luận
    const postCandidates = allDirs.filter(d => {
        const inArticle = !!d.closest('div[role="article"]');
        return !inArticle && d.innerText.trim().length > 0;
    });

    result.postCandidates = postCandidates.map(d => ({
        text: d.innerText.trim(),
        tag: d.tagName,
        className: d.className,
        parentTag: d.parentElement ? d.parentElement.tagName : ''
    }));

    // 2. Tìm tác giả bài viết
    // Trong bài viết trên Facebook, tên tác giả thường nằm trong thẻ h1/h2/h3 hoặc span font-bold hoặc link tới trang cá nhân
    const authorCandidates = Array.from(document.querySelectorAll('h2, h3, strong, a[role="link"]'))
        .filter(a => {
            const href = a.getAttribute('href') || '';
            const t = a.innerText.trim();
            return (href.includes('/user/') || href.includes('facebook.com/') || a.closest('div[role="heading"]')) && t.length > 2 && t.length < 50;
        })
        .map(a => ({ text: a.innerText.trim(), href: a.getAttribute('href') }));
    result.authorCandidates = authorCandidates.slice(0, 15);

    // 3. Tìm các nút tương tác (Reactions, Comments count, Shares count)
    // Quét toàn bộ text xung quanh
    const bodyText = document.body.innerText;
    
    // Số reactions: tìm span/div có aria-label chứa cảm xúc hoặc số
    const rxEls = Array.from(document.querySelectorAll('span[aria-label*="cảm xúc"], span[aria-label*="người khác"], div[aria-label*="cảm xúc"], span[role="toolbar"] ~ span, span[data-visualcompletion="ignore-dynamic"]'));
    result.rxEls = rxEls.map(e => ({ text: e.innerText.trim(), aria: e.getAttribute('aria-label') }));

    return result;
    """
    res = driver.execute_script(js)
    with open('test_dom_per_post.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("Exported test_dom_per_post.json")
finally:
    driver.quit()

