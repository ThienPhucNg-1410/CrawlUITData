import sys
import time
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

o = Options()
o.add_argument("--user-data-dir=d:\\uit-confession-sentiment\\.temp_debug_profile")
o.add_argument("--window-size=1280,900")
o.add_argument("--disable-gpu")
o.add_argument("--disable-dev-shm-usage")
o.add_argument("--headless=new")
driver = webdriver.Chrome(options=o)

url = "https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1139837221912339/"
print("Loading URL:", url)
driver.get(url)
time.sleep(5)

js_code = """
const articles = Array.from(document.querySelectorAll('div[role="article"]'));
const results = [];

for (let i = 0; i < articles.length; i++) {
    const a = articles[i];
    const aria = a.getAttribute('aria-label') || '';
    const text = (a.innerText || '').slice(0, 80).replace(/\\n/g, ' ');
    
    // Tìm comment ID
    const cLinks = Array.from(a.querySelectorAll('a[href*="comment_id="]'));
    const commentIds = [];
    const replyIds = [];
    for (const l of cLinks) {
        const m1 = l.href.match(/comment_id=(\\d+)/);
        if (m1) commentIds.push(m1[1]);
        const m2 = l.href.match(/reply_comment_id=(\\d+)/);
        if (m2) replyIds.push(m2[1]);
    }

    // Kiểm tra xem article này có nằm trong một article khác (nested reply) không
    let parentArt = null;
    let curr = a.parentElement;
    while (curr) {
        if (curr.getAttribute && curr.getAttribute('role') === 'article') {
            parentArt = curr;
            break;
        }
        curr = curr.parentElement;
    }

    let parentCommentId = null;
    if (parentArt) {
        const pLinks = Array.from(parentArt.querySelectorAll('a[href*="comment_id="]'));
        for (const pl of pLinks) {
            const m = pl.href.match(/comment_id=(\\d+)/);
            if (m) { parentCommentId = m[1]; break; }
        }
    }

    // Kiểm tra các phần tử hiển thị reaction/like của comment
    const rxElements = Array.from(a.querySelectorAll('span[aria-label], div[aria-label], span[role="toolbar"]'))
        .map(el => ({
            tag: el.tagName,
            aria: el.getAttribute('aria-label') || '',
            text: el.innerText.trim()
        }))
        .filter(el => el.aria || el.text);

    results.push({
        index: i,
        aria: aria,
        text: text,
        commentIds: Array.from(new Set(commentIds)),
        replyIds: Array.from(new Set(replyIds)),
        isNested: !!parentArt,
        parentCommentId: parentCommentId,
        rxElements: rxElements.slice(0, 8)
    });
}
return results;
"""

res = driver.execute_script(js_code)
print(f"Total articles found on page: {len(res)}")
for r in res[:8]:
    print("---")
    print(f"Index: {r['index']} | isNested: {r['isNested']} | ParentCID: {r['parentCommentId']}")
    print(f"Aria: {r['aria']}")
    print(f"Text: {r['text']}")
    print(f"CIDs: {r['commentIds']} | ReplyIDs: {r['replyIds']}")
    print(f"RxElements: {r['rxElements']}")

driver.quit()
