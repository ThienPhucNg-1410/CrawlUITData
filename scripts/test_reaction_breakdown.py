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
    time.sleep(6)

    # 1. Tìm tất cả các phần tử có chứa thông tin reaction
    js_inspect = """
    const results = [];
    const elements = Array.from(document.querySelectorAll('*'));
    
    // Tìm các phần tử có aria-label liên quan đến cảm xúc
    for (const el of elements) {
        const aria = (el.getAttribute('aria-label') || '').toLowerCase();
        const role = el.getAttribute('role') || '';
        const txt = el.innerText ? el.innerText.trim() : '';

        if (aria.includes('cảm xúc') || aria.includes('thích') || aria.includes('yêu thích') || 
            aria.includes('haha') || aria.includes('phẫn nộ') || aria.includes('buồn') ||
            aria.includes('thương thương') || aria.includes('wow') || aria.includes('reaction') ||
            aria.includes('người khác')) {
            results.push({
                tag: el.tagName,
                role: role,
                aria: el.getAttribute('aria-label'),
                text: txt.slice(0, 100),
                className: (el.className || '').toString().slice(0, 80)
            });
        }
    }
    return results.slice(0, 30);
    """
    found = driver.execute_script(js_inspect)
    print(f"Found {len(found)} candidate reaction elements:")
    for f in found:
        print(f"  [{f['tag']}|role={f['role']}] aria='{f['aria']}' | text='{f['text']}'")

finally:
    driver.quit()

