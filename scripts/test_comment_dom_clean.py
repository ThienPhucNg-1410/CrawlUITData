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
try:
    url = 'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1139837498578978/'
    driver.get(url)
    time.sleep(4)

    js = """
    const articles = Array.from(document.querySelectorAll('div[role="article"]'))
        .filter(a => a.querySelectorAll('div[role="article"]').length === 0);

    return articles.map(a => {
        // Tìm author từ link người dùng hoặc span đầu tiên
        const authorLink = a.querySelector('a[role="link"]');
        const author = authorLink ? authorLink.innerText.trim() : '';

        // Tìm nội dung comment: các div/span dir="auto"
        const dirNodes = Array.from(a.querySelectorAll('div[dir="auto"], span[dir="auto"]'))
            .map(d => d.innerText.trim())
            .filter(t => t.length > 0 && t !== author && !['Trả lời', 'Thích', 'Chia sẻ', 'Like', 'Reply'].includes(t));

        // Thời gian
        const timeNode = Array.from(a.querySelectorAll('a[role="link"] span, span'))
            .find(s => {
                const t = s.innerText.trim();
                return t.match(/^\\d+\\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y)/i) || t.includes('trước');
            });

        return {
            author: author,
            textNodes: dirNodes,
            time: timeNode ? timeNode.innerText.trim() : '',
            raw: a.innerText
        };
    });
    """
    res = driver.execute_script(js)
    with open('test_comment_dom_clean.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("Done test_comment_dom_clean.json")
finally:
    driver.quit()

