import sys
import time
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, 'src')
import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
driver = make_driver(cfg, headless=True)
try:
    url = 'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1139252691970792/'
    driver.get(url)
    time.sleep(5)

    js = """
    // Tìm phần tử chứa "Có anh em nào pass aula"
    const allDivs = Array.from(document.querySelectorAll('div[dir="auto"], span[dir="auto"]'));
    const target = allDivs.find(d => d.innerText && d.innerText.includes('Có anh em nào pass aula'));
    
    if (!target) return { found: false };

    // Tìm tổ tiên chứa cả post và comments
    let el = target;
    const path = [];
    while (el && el !== document.body) {
        path.push({
            tag: el.tagName,
            role: el.getAttribute('role'),
            aria: el.getAttribute('aria-label'),
            className: el.className
        });
        el = el.parentElement;
    }

    return {
        found: true,
        text: target.innerText,
        path: path.slice(0, 8)
    };
    """
    res = driver.execute_script(js)
    print(json.dumps(res, ensure_ascii=False, indent=2))
finally:
    driver.quit()

