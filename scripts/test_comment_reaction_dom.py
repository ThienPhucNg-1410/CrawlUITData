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
    driver.get("https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1139837498578978/")
    time.sleep(5)
    js = """
    const btns = Array.from(document.querySelectorAll('*'))
        .filter(el => (el.getAttribute('aria-label') || '').includes('Thích: 1 người'));
    if (btns.length === 0) return { error: 'Not found' };
    
    const b = btns[0];
    let parent = b.parentElement;
    while (parent && !parent.innerText.includes('Anh nói em') && !parent.innerText.includes('Học ít')) {
        parent = parent.parentElement;
    }
    return {
        matchedParentTag: parent ? parent.tagName : 'NONE',
        matchedParentRole: parent ? parent.getAttribute('role') : 'NONE',
        matchedParentText: parent ? parent.innerText.slice(0, 120).replace(/\\n/g, ' ') : 'NONE'
    };
    """
    res = driver.execute_script(js)
    print("Matched parent:", res)
finally:
    driver.quit()
