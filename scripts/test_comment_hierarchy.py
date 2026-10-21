import sys
import time
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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
driver.get(url)
time.sleep(5)

# Bấm 'Xem tất cả bình luận'
expand_js = """
const buttons = Array.from(document.querySelectorAll('div[role="button"], span'))
    .filter(el => {
        const txt = el.innerText ? el.innerText.trim() : '';
        return txt.match(/^Xem thêm bình luận/i) || 
               txt.match(/^Xem các bình luận trước/i) || 
               txt.match(/^Xem (\\d+ )?phản hồi/i) ||
               txt.match(/^Xem thêm phản hồi/i) ||
               txt.match(/^View (\\d+ )?replies/i);
    });
let count = 0;
for (const b of buttons) {
    try { b.click(); count++; } catch(e){}
}
return count;
"""
driver.execute_script(expand_js)
time.sleep(3)

js_parse = """
function parseCount(str) {
    if (!str) return 0;
    str = str.replace(/\\s+/g, '').replace(',', '.');
    let m = 1;
    if (/k/i.test(str)) { m = 1000; str = str.replace(/k/i, ''); }
    const v = parseFloat(str);
    return isNaN(v) ? 0 : Math.round(v * m);
}

// Lấy tất cả container bình luận
const articles = Array.from(document.querySelectorAll('div[role="article"]'))
    .filter(a => {
        const aria = (a.getAttribute('aria-label') || '').toLowerCase();
        return aria.includes('bình luận') || aria.includes('comment') || a.innerText.includes('Trả lời') || a.innerText.includes('Reply');
    });

const comments = [];

for (let i = 0; i < articles.length; i++) {
    const art = articles[i];
    
    // Tác giả & Text
    const dirNodes = Array.from(art.querySelectorAll('div[dir="auto"], span[dir="auto"]'))
        .map(d => d.innerText.trim())
        .filter(t => t.length > 0 && !['Trả lời', 'Thích', 'Chia sẻ', 'Reply', 'Like', 'Share'].includes(t));
    
    let author = dirNodes.length > 0 ? dirNodes[0] : '';
    let text = dirNodes.length > 1 ? dirNodes[dirNodes.length - 1] : '';

    // Comment ID
    let cid = '';
    const cLink = art.querySelector('a[href*="comment_id="]');
    if (cLink) {
        const m = cLink.href.match(/comment_id=(\\d+)/);
        if (m) cid = m[1];
    }

    // Xác định Parent ID (Nếu bài này là reply lồng trong một bình luận khác)
    let parentCid = null;
    let p = art.parentElement;
    while (p) {
        if (p.getAttribute && p.getAttribute('role') === 'article' && p !== art) {
            const pLink = p.querySelector('a[href*="comment_id="]');
            if (pLink) {
                const pm = pLink.href.match(/comment_id=(\\d+)/);
                if (pm && pm[1] !== cid) {
                    parentCid = pm[1];
                    break;
                }
            }
        }
        // Kiểm tra danh sách ul/li lồng nhau
        if (p.tagName === 'UL' && p.parentElement && p.parentElement.closest('div[role="article"]')) {
            const parentBlock = p.parentElement.closest('div[role="article"]');
            const pLink = parentBlock.querySelector('a[href*="comment_id="]');
            if (pLink) {
                const pm = pLink.href.match(/comment_id=(\\d+)/);
                if (pm && pm[1] !== cid) {
                    parentCid = pm[1];
                    break;
                }
            }
        }
        p = p.parentElement;
    }

    // Bóc tách Reaction của comment
    let rxCount = 0;
    const rxEl = art.querySelector('span[aria-label*="reaction"], span[aria-label*="cảm xúc"], div[aria-label*="reaction"], div[aria-label*="cảm xúc"]');
    if (rxEl) {
        const rxText = rxEl.innerText.trim() || rxEl.getAttribute('aria-label') || '';
        const numMatch = rxText.match(/(\\d+)/);
        if (numMatch) rxCount = parseInt(numMatch[1], 10);
        else rxCount = 1;
    }

    if (author && text) {
        comments.push({
            cid: cid,
            parent_id: parentCid,
            author: author,
            text: text.slice(0, 80),
            reactions: rxCount
        });
    }
}
return comments;
"""

res = driver.execute_script(js_parse)
print(f"Extracted {len(res)} parsed comments:")
for c in res[:12]:
    p_str = f"-> Reply to {c['parent_id']}" if c['parent_id'] else "Root Comment"
    print(f"[{p_str}] CID: {c['cid']} | Reacts: {c['reactions']} | {c['author']}: {c['text']}")

driver.quit()

