import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

o = Options()
o.add_argument("--headless=new")
o.add_argument("--disable-gpu")
o.add_argument("--blink-settings=imagesEnabled=false")
profile = Path("d:/uit-confession-sentiment/.temp_test_profile")
o.add_argument(f"--user-data-dir={profile}")
driver = webdriver.Chrome(options=o)

EXTRACT_SCRIPT = """
const res = {
    post_text: '',
    post_author: '',
    comments: [],
    debug: {}
};

// 1. Expand all "See more" / "Xem thêm" buttons
const expandButtons = Array.from(document.querySelectorAll('div[role="button"], span'))
    .filter(el => {
        const txt = (el.innerText || '').trim();
        return txt.match(/^(Xem thêm|See more)$/i) ||
               txt.match(/^Xem thêm bình luận/i) ||
               txt.match(/^Xem (\\d+ )?phản hồi/i) ||
               txt.match(/^View (\\d+ )?replies/i);
    });

for (const b of expandButtons) {
    try { b.click(); } catch(e) {}
}

// 2. Identify the main post container
// In Facebook, the main post is the first role="article" that is NOT a comment (does not have "bình luận" or "comment" in aria-label)
const articles = Array.from(document.querySelectorAll('div[role="article"]'));
const postArticle = articles.find(a => {
    const aria = (a.getAttribute('aria-label') || '').toLowerCase();
    return !aria.includes('bình luận') && !aria.includes('comment') && !aria.includes('trả lời');
}) || articles[0];

if (postArticle) {
    // A. Post Author
    const authorEl = postArticle.querySelector('h2 a, h3 a, strong a, a[role="link"][href*="/user/"]');
    if (authorEl && authorEl.innerText.trim()) {
        res.post_author = authorEl.innerText.trim();
    }
    const h2 = postArticle.querySelector('h2');
    if (h2 && h2.innerText.includes('ẩn danh')) {
        res.post_author = 'Người tham gia ẩn danh';
    }

    // B. Post Message
    // Specific message container
    const msgContainer = postArticle.querySelector('div[data-ad-preview="message"], div[data-ad-comet-preview="message"]');
    if (msgContainer && msgContainer.innerText.trim()) {
        res.post_text = msgContainer.innerText.trim();
    } else {
        // Fallback: look for dir="auto" inside postArticle that is NOT inside a comment article
        const candidateDirs = Array.from(postArticle.querySelectorAll('div[dir="auto"]'))
            .filter(d => {
                // Must not be inside a child comment article
                const parentArticle = d.closest('div[role="article"]');
                if (parentArticle && parentArticle !== postArticle) return false;
                if (d.closest('h2') || d.closest('h3')) return false;
                const txt = d.innerText.trim();
                if (txt.length < 5) return false;
                if (['Thích', 'Bình luận', 'Chia sẻ', 'Like', 'Comment', 'Share', 'Gửi'].includes(txt)) return false;
                if (txt === res.post_author) return false;
                return true;
            });
        if (candidateDirs.length > 0) {
            candidateDirs.sort((a, b) => b.innerText.length - a.innerText.length);
            res.post_text = candidateDirs[0].innerText.trim();
        }
    }
}

// 3. Comments extraction
const commentArticles = articles.filter(a => {
    if (a === postArticle) return false;
    const aria = (a.getAttribute('aria-label') || '').toLowerCase();
    return aria.includes('bình luận') || aria.includes('comment') || a.innerText.includes('Trả lời') || a.innerText.includes('Reply');
});

res.debug.totalArticles = articles.length;
res.debug.commentArticles = commentArticles.length;

return res;
"""

test_pids = ['1139837498578978', '1078186371410758', '1070946592134736']

try:
    for pid in test_pids:
        url = f"https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/{pid}/"
        driver.get(url)
        time.sleep(3.0)
        data = driver.execute_script(EXTRACT_SCRIPT)
        print(f"\n================ PID: {pid} ================")
        print("Author   :", data.get("post_author"))
        print("Text Len :", len(data.get("post_text", "")))
        print("Text Snip:", repr(data.get("post_text", "")[:120]))
        print("Text End :", repr(data.get("post_text", "")[-60:]))
        print("Debug    :", data.get("debug"))
finally:
    driver.quit()

