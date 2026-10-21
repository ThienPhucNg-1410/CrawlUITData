import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, 'src')
import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
driver = make_driver(cfg, headless=True)

test_pids = [
    '1139252691970792', # Aula f75pro
    '1126425899920138', # 2k8 giai thuong
    '1126425519920176', # IT007 nop thuc hanh
    '1125898673306194', # Thu vien group sample 1
    '1125854393310622', # Thu vien group sample 2
]

extract_js = """
const res = { text: '', author: '', title: document.title, is_inaccessible: false };

const bodyText = document.body.innerText || '';
if (bodyText.includes('Nội dung này hiện không khả dụng') || bodyText.includes("This content isn't available right now")) {
    res.is_inaccessible = true;
    return res;
}

// 1. Locate container
let container = document.querySelector('div[role="dialog"]') || document.querySelector('div[role="main"]');

// 2. Author extraction
let author = '';
if (container) {
    const postH2 = Array.from(container.querySelectorAll('h2')).find(h => {
        const t = h.innerText.trim();
        return t.startsWith('Bài viết của') || t.startsWith('Post by') || t.includes('ẩn danh') || t.includes('Anonymous');
    });
    
    if (postH2) {
        const h2Link = postH2.querySelector('a');
        if (h2Link && h2Link.innerText.trim()) {
            author = h2Link.innerText.trim();
        } else {
            author = postH2.innerText.trim().replace(/^(Bài viết của|Post by)\s+/i, '').trim();
        }
    }
    
    if (author.toLowerCase().includes('người tham gia ẩn danh') || author.toLowerCase().includes('anonymous')) {
        author = 'Người tham gia ẩn danh';
    }
    
    if (!author || author === 'Cộng Đồng Sinh Viên Đại Học Công Nghệ Thông Tin (UIT)' || ['Mới', 'Trước đó'].includes(author)) {
        const userLinks = Array.from(container.querySelectorAll('h3 a, strong a, a[role="link"][href*="/user/"]'))
            .filter(a => {
                const t = a.innerText.trim();
                return t.length > 0 && !['Mới', 'Trước đó', 'New', 'Previous', 'Cộng Đồng Sinh Viên Đại Học Công Nghệ Thông Tin (UIT)'].includes(t);
            });
        if (userLinks.length > 0) {
            author = userLinks[0].innerText.trim();
        }
    }
}
if (!author) {
    author = 'Người tham gia ẩn danh';
}
res.author = author;

// 3. Post text extraction
let post_text = '';
if (container) {
    const dirs = Array.from(container.querySelectorAll('div[dir="auto"]'))
        .filter(d => {
            if (d.closest('div[role="article"]')) return false;
            if (d.closest('h2') || d.closest('h3')) return false;
            const txt = d.innerText.trim();
            if (txt.length === 0) return false;
            if (['Thích', 'Bình luận', 'Chia sẻ', 'Like', 'Comment', 'Share', 'Gửi', 'Xem thêm bình luận'].includes(txt)) return false;
            if (txt === author) return false;
            return true;
        });
    
    if (dirs.length > 0) {
        const topCandidates = dirs.slice(0, 3);
        topCandidates.sort((a, b) => b.innerText.length - a.innerText.length);
        post_text = topCandidates[0].innerText.trim();
    }
}

// 4. Fallback from title
const title = document.title || '';
let titlePostText = '';
if (title && title.includes('|')) {
    const parts = title.split('|').map(p => p.trim());
    if (parts.length >= 3) {
        titlePostText = parts.slice(1, -1).join(' | ').trim();
    } else if (parts.length === 2 && parts[1].toLowerCase().includes('facebook')) {
        titlePostText = parts[0].replace(/^.*Cộng Đồng Sinh Viên Đại Học Công Nghệ Thông Tin \(UIT\)\s*/i, '').trim();
    }
}

if (!post_text && titlePostText) {
    post_text = titlePostText;
} else if (post_text && titlePostText) {
    const cleanPost = post_text.slice(0, 30).toLowerCase();
    const cleanTitle = titlePostText.slice(0, 30).toLowerCase();
    if (!cleanPost.includes(cleanTitle) && !cleanTitle.includes(cleanPost)) {
        post_text = titlePostText;
    }
}

res.text = post_text;
return res;
"""

try:
    for pid in test_pids:
        driver.get(f'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/{pid}/')
        time.sleep(2.5)
        res = driver.execute_script(extract_js)
        print(f"PID {pid}:")
        print(f"  Author: {res['author']}")
        print(f"  Text  : {res['text'][:100]!r}")
        print("-" * 50)
finally:
    driver.quit()

