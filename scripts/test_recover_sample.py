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

test_pids = ['1126425899920138', '1126425519920176', '1139252691970792']

try:
    for pid in test_pids:
        url = f'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/{pid}/'
        driver.get(url)
        time.sleep(4)
        
        js = """
        const title = document.title;
        let post_text = '';
        let author = '';
        
        // Find comment header / button
        const commentHeader = Array.from(document.querySelectorAll('div, span'))
            .find(e => e.innerText && (e.innerText.trim() === 'Phù hợp nhất' || e.innerText.trim() === 'Tất cả bình luận' || e.innerText.trim() === 'Most relevant'));
        
        let container = null;
        if (commentHeader) {
            container = commentHeader.closest('div[role="dialog"]') || commentHeader.closest('div[role="main"]');
            if (!container) {
                let p = commentHeader.parentElement;
                while (p && p !== document.body && !container) {
                    if (p.querySelectorAll('div[role="article"]').length > 0 && p.querySelectorAll('div[dir="auto"]').length > 1) {
                        container = p;
                        break;
                    }
                    p = p.parentElement;
                }
            }
        }
        
        if (container) {
            // Find post text before comment section
            const dirs = Array.from(container.querySelectorAll('div[dir="auto"]'))
                .filter(d => !d.closest('div[role="article"]') && d.innerText.trim().length > 0);
            if (dirs.length > 0) {
                post_text = dirs[0].innerText.trim();
            }
            // Find author
            const authorLink = container.querySelector('h2 a, h3 a, strong a, a[role="link"][href*="/user/"]');
            if (authorLink) author = authorLink.innerText.trim();
        }
        
        return {
            pid: arguments[0],
            title: title,
            text: post_text,
            author: author
        };
        """
        res = driver.execute_script(js, pid)
        print(f"PID: {pid}")
        print(f"  Title: {res['title']}")
        print(f"  Extracted Text: {res['text']}")
        print(f"  Extracted Author: {res['author']}")
        print("-" * 50)
finally:
    driver.quit()

