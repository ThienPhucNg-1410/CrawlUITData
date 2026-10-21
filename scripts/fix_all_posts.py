"""
scripts/fix_all_posts.py
========================
Tự động rà soát và cập nhật lại chính xác Text (Nội dung) và Author (Tác giả)
cho toàn bộ các bài viết bị gán nhầm nội dung từ feed nền trong 1.500 bài viết.
- Ghi trực tiếp vào SQLite (raw.sqlite) sau từng bài.
- Tự động xuất đè Excel và CSV sau khi hoàn thành.
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

import uitconf.config as C
from uitconf.scraper.driver import make_driver

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "fix_all_posts.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("FixAllPosts")

DB_PATH = BASE_DIR / "data" / "raw" / "raw.sqlite"

EXTRACT_JS = """
const res = { text: '', author: '', title: document.title, is_inaccessible: false };

const bodyText = document.body.innerText || '';
if (bodyText.includes('Nội dung này hiện không khả dụng') || bodyText.includes("This content isn't available right now")) {
    res.is_inaccessible = true;
    return res;
}

// 1. Tìm container chính của bài viết
let container = document.querySelector('div[role="dialog"]') || document.querySelector('div[role="main"]');

// 2. Trích xuất Tác giả chuẩn
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
            author = postH2.innerText.trim().replace(/^(Bài viết của|Post by)\\s+/i, '').trim();
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

// 3. Trích xuất Nội dung bài viết chính
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

// 4. Fallback và đối chiếu với document.title
const title = document.title || '';
let titlePostText = '';
if (title && title.includes('|')) {
    const parts = title.split('|').map(p => p.trim());
    if (parts.length >= 3) {
        titlePostText = parts.slice(1, -1).join(' | ').trim();
    } else if (parts.length === 2 && parts[1].toLowerCase().includes('facebook')) {
        titlePostText = parts[0].replace(/^.*Cộng Đồng Sinh Viên Đại Học Công Nghệ Thông Tin \\(UIT\\)\\s*/i, '').trim();
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


def export_dataset():
    """Gọi export_excel_dataset.py để làm mới file Excel và CSV."""
    try:
        import subprocess
        script = BASE_DIR / "scripts" / "export_excel_dataset.py"
        subprocess.run([sys.executable, str(script)], check=True, capture_output=True)
        log.info("--> Đã tự động xuất đè dữ liệu mới sang Excel & CSV.")
    except Exception as e:
        log.warning(f"Lỗi khi export dataset: {e}")


def main():
    parser = argparse.ArgumentParser(description="Fix all mismatched post texts and authors.")
    parser.add_argument("--limit", type=int, default=0, help="Giới hạn số bài cần fix (0 = toàn bộ)")
    parser.add_argument("--delay", type=float, default=2.2, help="Thời gian chờ sau mỗi page load (giây)")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Xác định các bài viết trong bộ 1.500 bài cần sửa
    c.execute("""
        SELECT post_id, permalink, text, author
        FROM posts
        WHERE status = 'comments_full'
        ORDER BY rowid ASC
        LIMIT 1500
    """)
    posts_1500 = c.fetchall()

    # Nhóm các nội dung bị trùng lặp > 1 lần
    c.execute("""
        SELECT text
        FROM posts
        WHERE status = 'comments_full'
        GROUP BY text
        HAVING COUNT(*) > 1
    """)
    dup_texts = set(row[0] for row in c.fetchall() if row[0])

    targets = [p for p in posts_1500 if p[2] in dup_texts]
    if args.limit > 0:
        targets = targets[:args.limit]

    log.info(f"Tổng số bài cần kiểm tra và sửa trong đợt này: {len(targets)} bài.")
    if not targets:
        log.info("Không có bài nào cần sửa!")
        conn.close()
        return

    # 2. Khởi tạo Selenium Driver
    cfg = C.load()
    driver = make_driver(cfg, headless=True)

    success_count = 0
    fail_count = 0

    try:
        for idx, (pid, permalink, old_text, old_author) in enumerate(targets, 1):
            url = permalink if permalink and 'facebook.com' in permalink else f"https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/{pid}/"
            
            try:
                driver.get(url)
                time.sleep(args.delay)

                res = driver.execute_script(EXTRACT_JS)

                if res.get('is_inaccessible'):
                    log.warning(f"[{idx}/{len(targets)}] Post {pid} không khả dụng trên Facebook.")
                    fail_count += 1
                    continue

                new_text = (res.get('text') or '').strip()
                new_author = (res.get('author') or '').strip()

                if not new_text:
                    log.warning(f"[{idx}/{len(targets)}] Post {pid} không bóc tách được text (giữ nguyên).")
                    fail_count += 1
                    continue

                # Cập nhật vào DB
                c.execute("""
                    UPDATE posts 
                    SET text = ?, author = ?
                    WHERE post_id = ?
                """, (new_text, new_author, pid))
                conn.commit()

                success_count += 1
                snippet = new_text.replace('\n', ' ')[:50]
                log.info(f"[{idx}/{len(targets)}] ĐÃ CẬP NHẬT Post {pid} | Tác giả: {new_author} | Nội dung: {snippet!r}")

                # Định kỳ mỗi 50 bài xuất Excel một lần để cập nhật dần
                if success_count % 50 == 0:
                    export_dataset()

                # Nghỉ ngắn tránh nghẽn
                time.sleep(random.uniform(0.8, 1.4))

            except Exception as e:
                log.error(f"[{idx}/{len(targets)}] Lỗi khi xử lý post {pid}: {e}")
                fail_count += 1
                time.sleep(2.0)

    finally:
        driver.quit()
        conn.close()

    log.info(f"=== HOÀN TẤT ĐỢT FIX ===")
    log.info(f"Thành công: {success_count} bài | Bỏ qua/Lỗi: {fail_count} bài.")

    # Xuất lại dataset cuối cùng
    export_dataset()


if __name__ == "__main__":
    main()

