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
    test_url = 'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1135150639047664/'
    driver.get(test_url)
    time.sleep(6)

    js = """
    // Tìm phần tử chứa nội dung bài đăng
    // Tìm tất cả các div có dir="auto"
    const dirNodes = Array.from(document.querySelectorAll('div[dir="auto"]'))
        .map((d, i) => ({
            i: i,
            text: d.innerText.slice(0, 200),
            len: d.innerText.length,
            parentRole: d.parentElement ? d.parentElement.getAttribute('role') : '',
            ancestorArticle: !!d.closest('div[role="article"]')
        }))
        .filter(d => d.len > 15);

    // Tìm tất cả các button hoặc link có chữ Thích, Bình luận, Chia sẻ
    const actionBars = Array.from(document.querySelectorAll('div[role="button"], span, div'))
        .map(e => e.innerText.trim())
        .filter(t => t.includes('Thích') || t.includes('bình luận') || t.includes('chia sẻ') || t.includes('Like') || t.includes('Comment') || t.includes('Share'))
        .slice(0, 40);

    return {
        dirNodes: dirNodes.slice(0, 20),
        actionBars: actionBars
    };
    """
    data = driver.execute_script(js)
    with open('test_post_structure.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("SUCCESS: structure dumped")
finally:
    driver.quit()

