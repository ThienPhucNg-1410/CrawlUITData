"""
scripts/repair_dataset_posts_and_comments.py
=============================================
Khắc phục triệt để 3 vấn đề dữ liệu bài viết & bình luận:
1. Bài viết gốc bị cắt ngắn (do nút "Xem thêm" chưa bấm hoặc lấy từ document.title bị Facebook cắt).
2. Bài viết gốc bị sai nội dung / sai tác giả (do selector lọc nhầm bài chia sẻ, tên nhóm hoặc bài lân cận).
3. Bình luận bị trống nội dung (do là sticker/ảnh/GIF hoặc loading skeleton).
"""

import sys
import os
import time
import random
import logging
import sqlite3
import argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "repair_dataset.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("RepairDataset")

DB_PATH = BASE_DIR / "data" / "raw" / "raw.sqlite"

EXTRACT_JS = """
const res = {
    post_text: '',
    post_author: '',
    comments: [],
    reactions: 0,
    shares: 0,
    is_inaccessible: false
};

const bodyText = document.body.innerText || '';
if (bodyText.includes('Nội dung này hiện không khả dụng') || bodyText.includes("This content isn't available right now")) {
    res.is_inaccessible = true;
    return res;
}

// 1. Mở rộng toàn bộ nút "Xem thêm" / "See more" của bài viết và bình luận
const seeMoreButtons = Array.from(document.querySelectorAll('div[role="button"], span'))
    .filter(el => {
        const txt = (el.innerText || '').trim();
        return txt.match(/^(Xem thêm|See more)$/i) ||
               txt.match(/^Xem thêm bình luận/i) ||
               txt.match(/^Xem (\\d+ )?phản hồi/i) ||
               txt.match(/^View (\\d+ )?replies/i);
    });

for (const b of seeMoreButtons) {
    try { b.click(); } catch(e) {}
}

// 2. Xác định container bài viết chính
const articles = Array.from(document.querySelectorAll('div[role="article"]'));
const postArticle = articles.find(a => {
    const aria = (a.getAttribute('aria-label') || '').toLowerCase();
    return !aria.includes('bình luận') && !aria.includes('comment') && !aria.includes('trả lời');
}) || articles[0];

if (!postArticle) {
    return res;
}

// 3. Trích xuất Tác giả bài viết chính xác
let author = '';
// Kiểm tra ẩn danh
const h2 = postArticle.querySelector('h2');
if (h2 && (h2.innerText.includes('ẩn danh') || h2.innerText.toLowerCase().includes('anonymous'))) {
    author = 'Người tham gia ẩn danh';
} else {
    // Tìm link tác giả (bỏ qua tên nhóm và từ khóa phụ)
    const authorLinks = Array.from(postArticle.querySelectorAll('h2 a, h3 a, strong a, a[role="link"][href*="/user/"], a[role="link"][href*="profile.php"]'))
        .map(a => a.innerText.trim())
        .filter(t => t.length > 0 && 
                     !t.includes('Cộng Đồng Sinh Viên Đại Học Công Nghệ Thông Tin (UIT)') &&
                     !['Mới', 'Trước đó', 'New', 'Previous', 'Join', 'Tham gia'].includes(t));
    if (authorLinks.length > 0) {
        author = authorLinks[0];
    } else if (h2) {
        author = h2.innerText.replace(/^(Bài viết của|Post by)\\s+/i, '').trim();
        if (author.includes('Cộng Đồng Sinh Viên') || author.length > 40) {
            author = 'Người tham gia ẩn danh';
        }
    }
}
if (!author) author = 'Người tham gia ẩn danh';
res.post_author = author;

// 4. Trích xuất Nội dung bài viết chính (toàn văn, chuẩn xác)
let full_text = '';
// Thử thẻ data-ad-preview chuẩn của Facebook
const msgNode = postArticle.querySelector('div[data-ad-preview="message"], div[data-ad-comet-preview="message"]');
if (msgNode && msgNode.innerText.trim()) {
    full_text = msgNode.innerText.trim();
} else {
    // Tìm các thẻ dir="auto" thuộc postArticle nhưng không thuộc comment con
    const candidateDirs = Array.from(postArticle.querySelectorAll('div[dir="auto"]'))
        .filter(d => {
            const parentArt = d.closest('div[role="article"]');
            if (parentArt && parentArt !== postArticle) return false;
            if (d.closest('h2') || d.closest('h3')) return false;
            const txt = d.innerText.trim();
            if (txt.length < 5) return false;
            if (['Thích', 'Bình luận', 'Chia sẻ', 'Like', 'Comment', 'Share', 'Gửi', 'Viết bình luận...', 'Write a comment...'].includes(txt)) return false;
            if (txt === author) return false;
            return true;
        });

    if (candidateDirs.length > 0) {
        candidateDirs.sort((a, b) => b.innerText.length - a.innerText.length);
        full_text = candidateDirs[0].innerText.trim();
    }
}
res.post_text = full_text;

// 5. Trích xuất Bình luận
const commentArticles = articles.filter(a => {
    if (a === postArticle) return false;
    const aria = (a.getAttribute('aria-label') || '').toLowerCase();
    return aria.includes('bình luận') || aria.includes('comment') || a.innerText.includes('Trả lời') || a.innerText.includes('Reply');
});

for (const ca of commentArticles) {
    // Comment ID
    let commentId = '';
    const cLink = ca.querySelector('a[href*="comment_id="]');
    if (cLink) {
        const m = cLink.href.match(/comment_id=(\\d+)/);
        if (m) commentId = m[1];
    }

    // Comment Author
    let cAuthor = '';
    const cAuthorEl = ca.querySelector('a[role="link"][tabindex="0"], a[href*="/user/"], a[role="link"] > span, span[dir="auto"] > strong');
    if (cAuthorEl && cAuthorEl.innerText.trim()) {
        cAuthor = cAuthorEl.innerText.trim();
    }
    if (!cAuthor) {
        const firstLine = (ca.innerText || '').split('\\n')[0].trim();
        if (firstLine && firstLine.length < 40 && !firstLine.includes('·')) {
            cAuthor = firstLine;
        }
    }

    // Comment Text
    let cText = '';
    const dirNodes = Array.from(ca.querySelectorAll('div[dir="auto"], span[dir="auto"]'))
        .filter(d => {
            const t = d.innerText.trim();
            if (!t) return false;
            if (['Thích', 'Trả lời', 'Chia sẻ', 'Like', 'Reply', 'Share', 'Xem bản dịch', 'See translation'].includes(t)) return false;
            if (t === cAuthor) return false;
            if (t.match(/^\\d+\\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y)(\\s*(trước|ago))?$/i)) return false;
            return true;
        });

    if (dirNodes.length > 0) {
        dirNodes.sort((a, b) => b.innerText.length - a.innerText.length);
        cText = dirNodes[0].innerText.trim();
    }

    // Nếu không có text, nhận diện Sticker / GIF / Ảnh
    if (!cText) {
        if (ca.querySelector('img[src*="sticker"], img[src*="emote"], div[aria-label*="sticker"]')) {
            cText = '[Sticker]';
        } else if (ca.querySelector('img[src*="gif"], div[aria-label*="gif"]')) {
            cText = '[GIF]';
        } else if (ca.querySelector('img, div[aria-label*="hình ảnh"], div[aria-label*="photo"]')) {
            cText = '[Hình ảnh]';
        } else {
            cText = '[Tệp đính kèm]';
        }
    }

    // Parent ID
    let parentId = null;
    let p = ca.parentElement;
    while (p) {
        if (p.getAttribute && p.getAttribute('role') === 'article' && p !== ca) {
            const pLink = p.querySelector('a[href*="comment_id="]');
            if (pLink) {
                const pm = pLink.href.match(/comment_id=(\\d+)/);
                if (pm && pm[1] !== commentId) {
                    parentId = pm[1];
                    break;
                }
            }
        }
        p = p.parentElement;
    }

    // Reactions
    let rxCount = 0;
    const rxEl = ca.querySelector('span[aria-label*="reaction"], span[aria-label*="cảm xúc"], div[aria-label*="reaction"], div[aria-label*="cảm xúc"]');
    if (rxEl) {
        const rxText = rxEl.innerText.trim() || rxEl.getAttribute('aria-label') || '';
        const numMatch = rxText.match(/(\\d+)/);
        if (numMatch) rxCount = parseInt(numMatch[1], 10);
        else rxCount = 1;
    }

    if (commentId) {
        res.comments.push({
            comment_id: commentId,
            author: cAuthor || 'Ẩn danh',
            text: cText,
            parent_id: parentId,
            reactions: rxCount
        });
    }
}

return res;
"""


def repair_posts(limit=0, target_pids=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if target_pids:
        placeholders = ",".join("?" for _ in target_pids)
        query = f"SELECT post_id, permalink, text, author FROM posts WHERE post_id IN ({placeholders})"
        cur.execute(query, target_pids)
    else:
        # Lấy các bài có vấn đề về text: ngắn < 70 ký tự, kết thúc ..., sai tác giả hoặc từ khóa cụt
        query = """
        SELECT post_id, permalink, text, author FROM posts 
        WHERE status = 'comments_full' 
          AND permalink IS NOT NULL AND permalink != ''
          AND (
            length(trim(text)) < 75
            OR text LIKE '%...'
            OR text LIKE '%…'
            OR text LIKE '%Xem thêm%'
            OR text LIKE '%See more%'
            OR text LIKE '%Cộng Đồng Sinh Viên%'
            OR author IS NULL
            OR author = 'None'
            OR author = 'Cộng Đồng Sinh Viên Đại Học Công Nghệ Thông Tin (UIT)'
            OR text IN ('Chào mn.', 'Thắc mắc!', 'Chào mọi người', 'Góc tâm sự!', 'Dạ cho e hỏi', 'Điểm rèn luyện', 'Em chào anh/chị', 'Hello anh chị..', 'Đã có lịch')
          )
        ORDER BY rowid ASC
        """
        if limit > 0:
            query += f" LIMIT {int(limit)}"
        cur.execute(query)

    posts_to_fix = cur.fetchall()
    log.info(f"Tìm thấy {len(posts_to_fix)} bài viết cần sửa đổi nội dung và kiểm tra bình luận.")

    if not posts_to_fix:
        conn.close()
        return

    profile_dir = BASE_DIR.parent / ".temp_repair_profile"
    o = Options()
    o.add_argument(f"--user-data-dir={profile_dir}")
    o.add_argument("--window-size=1280,900")
    o.add_argument("--disable-gpu")
    o.add_argument("--blink-settings=imagesEnabled=false")
    o.add_argument("--headless=new")
    o.page_load_strategy = "eager"

    driver = webdriver.Chrome(options=o)
    driver.set_page_load_timeout(35)
    driver.set_script_timeout(15)

    fixed_count = 0
    cmts_updated = 0

    try:
        for idx, (pid, permalink, old_text, old_author) in enumerate(posts_to_fix, start=1):
            log.info(f"[{idx}/{len(posts_to_fix)}] Đang sửa post_id={pid} (Text cũ: {len(old_text or '')} ký tự)...")
            try:
                driver.get(permalink)
                time.sleep(random.uniform(2.5, 3.5))

                data = driver.execute_script(EXTRACT_JS)
                if not data or data.get("is_inaccessible"):
                    log.warning(f"  Post {pid} không truy cập được hoặc bị ẩn.")
                    continue

                new_text = data.get("post_text") or ""
                new_author = data.get("post_author") or old_author

                # Cập nhật bài viết nếu bóc tách được text dài hơn hoặc chính xác hơn
                if len(new_text) > len(old_text or "") or (new_text and old_text in ('Chào mn.', 'Thắc mắc!', 'Góc tâm sự!')):
                    cur.execute(
                        "UPDATE posts SET text = ?, author = ? WHERE post_id = ?",
                        (new_text, new_author, pid)
                    )
                    fixed_count += 1
                    log.info(f"  ✓ Đã cập nhật text post {pid}: {len(old_text or '')} -> {len(new_text)} ký tự | Tác giả: {new_author}")
                elif new_author and new_author != old_author:
                    cur.execute("UPDATE posts SET author = ? WHERE post_id = ?", (new_author, pid))
                    log.info(f"  ✓ Đã sửa tác giả post {pid}: '{old_author}' -> '{new_author}'")

                # Cập nhật bình luận của bài này
                comments = data.get("comments", [])
                for c in comments:
                    cid = c.get("comment_id")
                    c_text = c.get("text")
                    c_author = c.get("author")
                    c_parent = c.get("parent_id")
                    c_rx = c.get("reactions") or 0

                    if cid and c_text:
                        # Cập nhật text và author bình luận
                        cur.execute("""
                            UPDATE comments 
                            SET text = ?, author = CASE WHEN author IS NULL OR author = '' OR author = 'Ẩn danh' THEN ? ELSE author END,
                                parent_id = COALESCE(?, parent_id),
                                reactions = MAX(reactions, ?)
                            WHERE comment_id = ?
                        """, (c_text, c_author, c_parent, c_rx, cid))
                        cmts_updated += 1

                conn.commit()

            except Exception as e:
                log.error(f"  ✗ Lỗi khi xử lý post {pid}: {e}")
                time.sleep(2)

        log.info(f"\n[Hoàn thành sửa đổi] Đã cập nhật {fixed_count} bài viết và đồng bộ {cmts_updated} bình luận!")

    finally:
        driver.quit()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Số bài cần sửa (0 là toàn bộ bài bị nghi ngờ)")
    parser.add_argument("--pids", type=str, default="", help="Danh sách post_id cụ thể, cách nhau dấu phẩy")
    args = parser.parse_args()

    pids_list = [p.strip() for p in args.pids.split(",") if p.strip()] if args.pids else None
    repair_posts(limit=args.limit, target_pids=pids_list)

