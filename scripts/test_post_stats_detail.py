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
    url = 'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1135150639047664/'
    driver.get(url)
    time.sleep(5)

    js = """
    // Tìm phần tử chứa "Phù hợp nhất"
    const allDivs = Array.from(document.querySelectorAll('div, span'));
    const target = allDivs.find(d => d.innerText && d.innerText.trim() === 'Phù hợp nhất');
    
    // Tìm container cha chứa cả post và comments
    let curr = target;
    let postContainer = null;
    while (curr && curr !== document.body) {
        if (curr.innerText && curr.innerText.includes('Đã có lịch') && curr.innerText.includes('EnergeticRabbit2074')) {
            postContainer = curr;
            break;
        }
        curr = curr.parentElement;
    }

    if (!postContainer) {
        return { error: 'Not found container' };
    }

    // Lấy thông tin các nút, các số trên container
    // Tìm dòng số lượng phản hồi (reactions, comments, shares)
    const children = Array.from(postContainer.querySelectorAll('*'))
        .filter(el => {
            const txt = el.innerText ? el.innerText.trim() : '';
            return txt.match(/^\\d+$/) || txt.match(/^\\d+\\s*(bình luận|chia sẻ)/i);
        })
        .map(el => ({
            tag: el.tagName,
            text: el.innerText.trim(),
            aria: el.getAttribute('aria-label') || '',
            role: el.getAttribute('role') || '',
            parentTag: el.parentElement ? el.parentElement.tagName : ''
        }));

    return {
        postContainerFound: true,
        numbersFound: children,
        containerTextSnippets: postContainer.innerText.split('\\n').filter(Boolean).slice(0, 30)
    };
    """
    res = driver.execute_script(js)
    with open('test_post_stats_detail.json', 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("Exported test_post_stats_detail.json")
finally:
    driver.quit()

