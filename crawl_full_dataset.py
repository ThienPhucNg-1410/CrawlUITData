"""
crawl_full_dataset.py
=====================
Thu thập dữ liệu thô chi tiết Facebook Group:
- Mục tiêu: 1.500 bài viết (không bao gồm comment).
- Với mỗi bài viết: Lấy nội dung gốc, tác giả, lượt cảm xúc (reactions), lượt chia sẻ (shares),
  và TOÀN BỘ bình luận (comments) bao gồm cả phản hồi con (replies).
- Khóa chính: post_id cho bài viết, comment_id cho bình luận.
- KHÔNG mã hóa ẩn danh: Giữ nguyên văn bản, tên người dùng, MSSV.
- Lưu trữ liên tục vào SQLite (raw.sqlite) với chế độ WAL, commit sau từng bài.
"""

import sys
import os
import time
import random
import logging
import argparse
import sqlite3
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

# Thêm src vào đường dẫn
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "src"))

import uitconf.config as C
from uitconf.scraper.driver import make_driver
from uitconf.scraper.guard import check_blocked, HardStop
from uitconf.db import connect

# Cấu hình logging
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "crawl_full_dataset.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("CrawlFullDataset")


def extract_post_and_comments(driver):
    """
    Trích xuất toàn bộ thông tin bài viết và comments từ trang Facebook hiện tại bằng JavaScript.
    """
    time.sleep(1.2)

    # 1. Đổi bộ lọc bình luận sang 'Tất cả bình luận' (All comments) nếu có
    try:
        switch_filter_js = """
        const buttons = Array.from(document.querySelectorAll('div[role="button"], span'));
        const filterBtn = buttons.find(b => b.innerText && (b.innerText.trim() === 'Phù hợp nhất' || b.innerText.trim() === 'Most relevant'));
        if (filterBtn) {
            filterBtn.click();
            return true;
        }
        return false;
        """
        if driver.execute_script(switch_filter_js):
            time.sleep(0.35)
            select_all_js = """
            const menuItems = Array.from(document.querySelectorAll('div[role="menuitem"], div[role="button"], span'));
            const allCommentsOpt = menuItems.find(m => m.innerText && (m.innerText.includes('Tất cả bình luận') || m.innerText.includes('All comments')));
            if (allCommentsOpt) {
                allCommentsOpt.click();
                return true;
            }
            return false;
            """
            driver.execute_script(select_all_js)
            time.sleep(0.5)
    except Exception:
        pass

    # 2. Click mở rộng các bình luận và phản hồi con (tối đa 4 vòng lặp)
    try:
        for _ in range(4):
            expand_js = """
            let clicked = 0;
            const buttons = Array.from(document.querySelectorAll('div[role="button"], span'))
                .filter(el => {
                    const txt = el.innerText ? el.innerText.trim() : '';
                    return txt.match(/^Xem thêm bình luận/i) || 
                           txt.match(/^Xem các bình luận trước/i) || 
                           txt.match(/^Xem (\\d+ )?phản hồi/i) ||
                           txt.match(/^Xem thêm phản hồi/i) ||
                           txt.match(/^View (more )?comments/i) ||
                           txt.match(/^View (\\d+ )?replies/i);
                });
            for (const b of buttons) {
                try { b.click(); clicked++; } catch(e){}
            }
            return clicked;
            """
            clicks = driver.execute_script(expand_js)
            if clicks > 0:
                time.sleep(0.4)
            else:
                break
    except Exception:
        pass

    # 3. Trích xuất dữ liệu chi tiết
    extract_js = """
    function parseCount(str) {
        if (!str) return 0;
        str = str.replace(/\\s+/g, '').replace(',', '.');
        let multiplier = 1;
        if (/k/i.test(str)) { multiplier = 1000; str = str.replace(/k/i, ''); }
        else if (/m/i.test(str)) { multiplier = 1000000; str = str.replace(/m/i, ''); }
        const val = parseFloat(str);
        return isNaN(val) ? 0 : Math.round(val * multiplier);
    }

    // A. Kiểm tra trạng thái bài viết không khả dụng
    const bodyText = document.body.innerText || '';
    if (bodyText.includes('Nội dung này hiện không khả dụng') || bodyText.includes("This content isn't available right now")) {
        return { is_inaccessible: true };
    }

    // B. Thống kê tương tác (Reactions, Comments, Shares)
    let reactions = 0;
    let n_comments = 0;
    let shares = 0;

    const actionButtons = Array.from(document.querySelectorAll('div[role="button"]'));
    for (const btn of actionButtons) {
        const aria = btn.getAttribute('aria-label') || '';
        const txt = btn.innerText.trim();
        const numMatch = txt.match(/^([0-9.,]+[KkMm]?)$/);
        const val = numMatch ? parseCount(numMatch[1]) : 0;

        if (aria.toLowerCase().includes('thích') || aria.toLowerCase().includes('like')) {
            if (val > 0) reactions = val;
        } else if (aria.toLowerCase().includes('bình luận') || aria.toLowerCase().includes('comment')) {
            if (val > 0) n_comments = val;
        } else if (aria.toLowerCase().includes('gửi nội dung này') || aria.toLowerCase().includes('chia sẻ') || aria.toLowerCase().includes('share')) {
            if (val > 0) shares = val;
        }
    }

    // Fallback tìm reactions nếu action button chưa có
    if (reactions === 0) {
        const rxNodes = Array.from(document.querySelectorAll('span[role="toolbar"] ~ span, span[aria-label*="cảm xúc"], div[aria-label*="cảm xúc"]'));
        for (const r of rxNodes) {
            const v = parseCount(r.innerText);
            if (v > 0) { reactions = v; break; }
        }
    }

    // 1. Tìm container chính của bài viết
    let container = document.querySelector('div[role="dialog"]') || document.querySelector('div[role="main"]');

    // C. Tác giả bài viết chuẩn WAI-ARIA
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

    // D. Nội dung bài viết chính (Chuẩn xác, toàn văn qua data-ad-preview)
    let post_text = '';
    const msgNode = document.querySelector('div[data-ad-preview="message"], div[data-ad-comet-preview="message"]');
    if (msgNode && msgNode.innerText.trim()) {
        post_text = msgNode.innerText.trim();
    }

    if (!post_text && container) {
        const commentArticles = Array.from(document.querySelectorAll('div[role="article"]'))
            .filter(a => {
                const aria = (a.getAttribute('aria-label') || '').toLowerCase();
                return aria.includes('bình luận') || aria.includes('comment') || a.innerText.includes('Trả lời');
            });

        const dirs = Array.from(container.querySelectorAll('div[dir="auto"]'))
            .filter(d => {
                if (commentArticles.some(ca => ca.contains(d))) return false;
                if (d.closest('h2') || d.closest('h3')) return false;
                const txt = d.innerText.trim();
                if (txt.length < 5) return false;
                if (['Thích', 'Bình luận', 'Chia sẻ', 'Like', 'Comment', 'Share', 'Gửi', 'Xem thêm bình luận'].includes(txt)) return false;
                if (txt === author) return false;
                return true;
            });
        
        if (dirs.length > 0) {
            dirs.sort((a, b) => b.innerText.length - a.innerText.length);
            post_text = dirs[0].innerText.trim();
        }
    }

    // Fallback chỉ dùng title nếu DOM hoàn toàn không có text
    if (!post_text) {
        const title = document.title || '';
        if (title && title.includes('|')) {
            const parts = title.split('|').map(p => p.trim());
            if (parts.length >= 3) {
                post_text = parts.slice(1, -1).join(' | ').trim();
            } else if (parts.length === 2 && parts[1].toLowerCase().includes('facebook')) {
                post_text = parts[0].replace(/^.*Cộng Đồng Sinh Viên Đại Học Công Nghệ Thông Tin \\(UIT\\)\\s*/i, '').trim();
            }
        }
    }

    // E. Thời gian bài viết
    let time_raw = '';
    const timeLinks = Array.from(document.querySelectorAll('a[role="link"] span'))
        .filter(s => {
            const t = s.innerText.trim();
            return t.match(/^\\d+\\s*(ngày|giờ|phút|tuần|tháng|năm|d|h|m|w|y)/i) || t.includes('trước');
        });
    if (timeLinks.length > 0) {
        time_raw = timeLinks[0].innerText.trim();
    }

    // F. Danh sách Bình luận (Comments)
    // Ưu tiên tìm trong dialog nếu bài hiển thị dưới dạng dialog modal
    const dialogs = Array.from(document.querySelectorAll('div[role="dialog"]'));
    let commentScope = document;
    for (const d of dialogs) {
        if (d.querySelectorAll('div[role="article"]').length > 0) {
            commentScope = d;
            break;
        }
    }

    const allArticles = Array.from(commentScope.querySelectorAll('div[role="article"]'))
        .filter(a => {
            const aria = (a.getAttribute('aria-label') || '').toLowerCase();
            return aria.includes('bình luận') || aria.includes('comment') || a.innerText.includes('Trả lời') || a.innerText.includes('Reply');
        });

    // Chỉ chọn article là nút lá (không chứa article con lồng vào nhau)
    const leafArticles = allArticles.filter(a => a.querySelectorAll('div[role="article"]').length === 0);

    const parsedComments = [];
    const seenCommentKeys = new Set();

    for (let i = 0; i < leafArticles.length; i++) {
        const ca = leafArticles[i];
        
        // Trích xuất các khối text bên trong article
        const dirNodes = Array.from(ca.querySelectorAll('div[dir="auto"], span[dir="auto"]'))
            .map(d => d.innerText.trim())
            .filter(t => t.length > 0 && !['Trả lời', 'Thích', 'Chia sẻ', 'Theo dõi', 'Reply', 'Like', 'Share'].includes(t));

        let commentAuthor = '';
        let commentTime = '';
        let commentText = '';

        if (dirNodes.length > 0) {
            // Tác giả là phần tử đầu tiên
            commentAuthor = dirNodes[0];
            
            // Tìm thời gian
            let contentStartIndex = 1;
            if (dirNodes.length > 1 && (dirNodes[1].match(/^\\d+\\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y)/i) || dirNodes[1].includes('trước'))) {
                commentTime = dirNodes[1];
                contentStartIndex = 2;
            }

            // Phần còn lại là nội dung bình luận
            if (contentStartIndex < dirNodes.length) {
                // Lấy nội dung dài nhất trong các node còn lại (thường là node chứa toàn bộ text)
                const remaining = dirNodes.slice(contentStartIndex);
                remaining.sort((a, b) => b.length - a.length);
                commentText = remaining[0];
            }
        }

        // Fallback nếu dirNodes chưa tách được
        if (!commentText || !commentAuthor) {
            const lines = ca.innerText.split('\\n').map(l => l.trim()).filter(Boolean);
            if (!commentAuthor && lines.length > 0) commentAuthor = lines[0];
            const contentLines = lines.filter(l => !['Trả lời', 'Thích', 'Chia sẻ', 'Theo dõi', 'Reply', 'Like', 'Share'].includes(l) 
                && !l.match(/^\\d+\\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y)/i) 
                && l !== '·' && l !== commentAuthor);
            if (!commentText) commentText = contentLines.join(' ');
        }

        // Lấy comment_id từ link bài
        let commentId = '';
        const cLinks = Array.from(ca.querySelectorAll('a[href*="comment_id="]'));
        for (const cl of cLinks) {
            const m = cl.href.match(/comment_id=(\\d+)/);
            if (m) { commentId = m[1]; break; }
        }

        // Xác định Parent ID nếu là bình luận phản hồi (Reply lồng nhau)
        let parentCid = null;
        let p = ca.parentElement;
        while (p) {
            if (p.getAttribute && p.getAttribute('role') === 'article' && p !== ca) {
                const pLink = p.querySelector('a[href*="comment_id="]');
                if (pLink) {
                    const pm = pLink.href.match(/comment_id=(\\d+)/);
                    if (pm && pm[1] !== commentId) {
                        parentCid = pm[1];
                        break;
                    }
                }
            }
            if (p.tagName === 'UL' && p.parentElement && p.parentElement.closest('div[role="article"]')) {
                const parentBlock = p.parentElement.closest('div[role="article"]');
                const pLink = parentBlock.querySelector('a[href*="comment_id="]');
                if (pLink) {
                    const pm = pLink.href.match(/comment_id=(\\d+)/);
                    if (pm && pm[1] !== commentId) {
                        parentCid = pm[1];
                        break;
                    }
                }
            }
            p = p.parentElement;
        }

        // Bóc tách số lượng cảm xúc của bình luận
        let rxCount = 0;
        const rxEl = ca.querySelector('span[aria-label*="reaction"], span[aria-label*="cảm xúc"], div[aria-label*="reaction"], div[aria-label*="cảm xúc"]');
        if (rxEl) {
            const rxText = rxEl.innerText.trim() || rxEl.getAttribute('aria-label') || '';
            const numMatch = rxText.match(/(\\d+)/);
            if (numMatch) rxCount = parseInt(numMatch[1], 10);
            else rxCount = 1;
        }

        const key = commentAuthor + '::' + commentText;
        if (!seenCommentKeys.has(key) && commentText.length > 0) {
            seenCommentKeys.add(key);
            parsedComments.push({
                comment_id: commentId,
                parent_id: parentCid,
                author: commentAuthor,
                text: commentText,
                time_raw: commentTime,
                reactions: rxCount
            });
        }
    }

    return {
        is_inaccessible: false,
        post_author: author,
        post_text: post_text,
        time_raw: time_raw,
        reactions: reactions,
        n_comments: n_comments || parsedComments.length,
        shares: shares,
        comments: parsedComments
    };
    """
    return driver.execute_script(extract_js)


def run_full_crawler(target_posts=1500, headless=True):
    cfg = C.load()
    db_path = BASE_DIR / cfg["paths"]["raw_db"]
    conn = connect(str(db_path))

    # Đếm số bài đã có status = 'comments_full'
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM posts WHERE status = 'comments_full'")
    done_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM comments")
    total_comments_in_db = cursor.fetchone()[0]

    log.info("=" * 65)
    log.info("KHỞI ĐỘNG HỆ THỐNG CÀO DỮ LIỆU ĐẦY ĐỦ (FULL CRAWLER)")
    log.info(f"- Mục tiêu: {target_posts} bài viết chi tiết")
    log.info(f"- Hiện đã hoàn tất: {done_count} bài ({done_count/target_posts*100:.1f}%)")
    log.info(f"- Tổng số comments hiện có trong DB: {total_comments_in_db}")
    log.info(f"- Cơ sở dữ liệu: {db_path}")
    log.info("=" * 65)

    if done_count >= target_posts:
        log.info(f"[DONE] Đã đạt chỉ tiêu {target_posts} bài viết! Không cần cào thêm.")
        conn.close()
        return

    session_id = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    cursor.execute(
        "INSERT INTO sessions (session_id, started_at, stage, note) VALUES (?, ?, ?, ?)",
        (session_id, datetime.now().isoformat(), "crawl_full_dataset", f"target={target_posts}")
    )
    conn.commit()

    driver = None
    try:
        driver = make_driver(cfg, headless=headless, enable_images=False)
        log.info("[Driver] Trình duyệt Chrome đã khởi chạy thành công.")

        while True:
            # Kiểm tra tiến độ tổng
            cursor.execute("SELECT COUNT(*) FROM posts WHERE status = 'comments_full'")
            done_count = cursor.fetchone()[0]
            if done_count >= target_posts:
                log.info(f"===> ĐÃ ĐẠT CHỈ TIÊU {target_posts} BÀI VIẾT THÀNH CÔNG! <===")
                break

            # Lấy danh sách bài viết cần cào tiếp
            needed = target_posts - done_count
            batch_size = min(needed, 50)
            cursor.execute("""
                SELECT post_id, permalink, text 
                FROM posts 
                WHERE status != 'comments_full' 
                  AND status != 'inaccessible'
                  AND permalink IS NOT NULL 
                  AND permalink != ''
                ORDER BY rowid ASC 
                LIMIT ?
            """, (batch_size,))
            batch = cursor.fetchall()

            if not batch:
                log.warning("[!] Hết bài viết chưa cào trong database `posts`.")
                break

            for row in batch:
                post_id = row["post_id"]
                permalink = row["permalink"]
                original_text = row["text"] or ""

                cursor.execute("SELECT COUNT(*) FROM posts WHERE status = 'comments_full'")
                curr_done = cursor.fetchone()[0]
                if curr_done >= target_posts:
                    break

                log.info(f"[{curr_done + 1}/{target_posts}] Đang cào post {post_id} ...")
                
                try:
                    driver.get(permalink)
                except Exception as e:
                    log.error(f"[!] Lỗi khi mở URL {permalink}: {e}")
                    # Khởi động lại driver nếu bị đơ
                    try:
                        driver.quit()
                    except Exception:
                        pass
                    time.sleep(5)
                    driver = make_driver(cfg, headless=headless, enable_images=False)
                    continue

                # Kiểm tra chặn (checkpoint/guard)
                try:
                    check_blocked(driver)
                except HardStop as hs:
                    log.error(f"[CRITICAL] Phát hiện chặn tài khoản: {hs}")
                    cursor.execute("UPDATE sessions SET ended_at=?, note=? WHERE session_id=?", 
                                   (datetime.now().isoformat(), f"HardStop: {hs}", session_id))
                    conn.commit()
                    return

                # Bóc tách
                try:
                    data = extract_post_and_comments(driver)
                except Exception as ex:
                    log.error(f"[!] Lỗi khi extract post {post_id}: {ex}")
                    time.sleep(3)
                    continue

                if data.get("is_inaccessible"):
                    log.warning(f"[-] Post {post_id} không khả dụng (đã bị xóa hoặc hạn chế). Đánh dấu 'inaccessible'.")
                    cursor.execute("UPDATE posts SET status = 'inaccessible' WHERE post_id = ?", (post_id,))
                    conn.commit()
                    continue

                # Dữ liệu bài viết
                post_text = data.get("post_text") or original_text
                author = data.get("post_author") or ""
                time_raw = data.get("time_raw") or ""
                reactions = int(data.get("reactions") or 0)
                shares = int(data.get("shares") or 0)
                n_comments = int(data.get("n_comments") or 0)
                comments = data.get("comments", [])
                now_iso = datetime.now().isoformat()

                # Cập nhật bảng posts
                cursor.execute("""
                    UPDATE posts 
                    SET text = ?,
                        author = CASE WHEN length(?) > 0 THEN ? ELSE author END,
                        time_raw = CASE WHEN length(?) > 0 THEN ? ELSE time_raw END,
                        reactions = ?,
                        shares = ?,
                        n_comments = ?,
                        status = 'comments_full',
                        collected_at = ?
                    WHERE post_id = ?
                """, (post_text, author, author, time_raw, time_raw, reactions, shares, n_comments, now_iso, post_id))

                # Chèn các comments vào bảng comments
                comments_saved = 0
                for idx, c in enumerate(comments):
                    c_id = c.get("comment_id")
                    if not c_id:
                        c_id = f"{post_id}_c_{idx}"
                    
                    c_author = c.get("author") or ""
                    c_text = c.get("text") or ""
                    c_time = c.get("time_raw") or ""
                    c_react = int(c.get("reactions") or 0)

                    cursor.execute("""
                        INSERT OR REPLACE INTO comments 
                        (comment_id, post_id, parent_id, text, author, time_raw, reactions, collected_at, session_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (c_id, post_id, c.get("parent_id"), c_text, c_author, c_time, c_react, now_iso, session_id))
                    comments_saved += 1

                conn.commit()

                log.info(f"   => OK! Tác giả: '{author or 'N/A'}' | React: {reactions} | Share: {shares} | Comments ghi nhận: {n_comments} | Saved {comments_saved} comments")

                # Giãn cách an toàn (tối ưu tốc độ cao qua đêm)
                sleep_secs = random.uniform(0.5, 1.2)
                time.sleep(sleep_secs)

                # Nghỉ ngắn định kỳ mỗi 50 bài
                if (curr_done + 1) % 50 == 0:
                    long_pause = random.uniform(3, 5)
                    log.info(f"[Break] Đã hoàn thành mốc {curr_done + 1} bài. Tạm nghỉ {long_pause:.1f}s giữ an toàn session...")
                    time.sleep(long_pause)

    except Exception as e:
        log.error(f"[FATAL] Lỗi trong quá trình chạy: {e}", exc_info=True)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        cursor.execute("UPDATE sessions SET ended_at=?, note=? WHERE session_id=?", 
                       (datetime.now().isoformat(), "finished", session_id))
        conn.commit()
        conn.close()
        log.info("[Shutdown] Hoàn tất phiên thu thập dữ liệu.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full Dataset Crawler: 1500 posts + comments + shares + reactions")
    parser.add_argument("--target", type=int, default=1500, help="Số lượng bài viết mục tiêu (mặc định 1500)")
    parser.add_argument("--headful", action="store_true", help="Chạy Chrome hiển thị giao diện thay vì headless")
    args = parser.parse_args()

    run_full_crawler(target_posts=args.target, headless=not args.headful)
