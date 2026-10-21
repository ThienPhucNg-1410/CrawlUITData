"""
scripts/clean_comments_text.py
==============================
Làm sạch văn bản bình luận trong cơ sở dữ liệu:
1. Tách và loại bỏ tên tác giả, mốc thời gian bị dính vào đầu bình luận.
2. Loại bỏ các nút giao diện Facebook bị dính ở đuôi (Thích, Trả lời, Chia sẻ, Xem bản dịch).
3. Thêm dấu cách giữa các từ/câu bị dính liền sau dấu chấm/dấu phẩy/dấu ngoặc kép.
4. Chuẩn hóa khoảng trắng.
"""
import re
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "raw" / "raw.sqlite"


def clean_single_comment_text(text, author="", time_raw=""):
    if not text:
        return ""

    original = text

    # 1. Bỏ boilerplate các nút bấm ở đuôi
    text = re.sub(r'[\s\xa0]*(Thích|Trả lời|Chia sẻ|Xem bản dịch|Like|Reply|Share)+[\s\xa0]*$', '', text, flags=re.IGNORECASE)

    # 2. Bỏ phần đầu bị dính "Tác giả · Thời gian"
    # Ví dụ: "Nguyen Binh · 1 ngàyHọc ít thội em" -> "Học ít thội em"
    # Ví dụ: "Thích Cà Rốt · 1 ngàyAnh nói..." -> "Anh nói..."
    text = re.sub(r'^.*?[·•]\s*\d+\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y|gi)(\s*(trước|ago))?\s*', '', text, flags=re.IGNORECASE)

    # Nếu còn dính tên tác giả ở đầu:
    if author and author != 'Ẩn danh' and text.startswith(author):
        text = text[len(author):].strip()
        text = re.sub(r'^[·•\s\xa0]+', '', text)
        text = re.sub(r'^\d+\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y)(\s*(trước|ago))?\s*', '', text, flags=re.IGNORECASE)

    # 3. Tách từ dính liền sau dấu câu: "chữ.Chữ" -> "chữ. Chữ"
    # Tránh tách số thập phân như 3.14 hay 4.0
    text = re.sub(r'([a-zA-Z\u00C0-\u024F\u1EA0-\u1EF9])([\.?!,:;])([A-ZÀ-Ỹ"“a-zà-ỹ])', r'\1\2 \3', text)
    # Tách dấu ngoặc kép dính liền chữ: '""Trời' -> '"" Trời'
    text = re.sub(r'([”"])([A-ZÀ-Ỹa-zà-ỹ0-9])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z0-9\u00C0-\u024F\u1EA0-\u1EF9])([“"])', r'\1 \2', text)

    # 4. Tách các nút bấm còn sót lại ở đuôi lần 2
    text = re.sub(r'[\s\xa0]*(Thích|Trả lời|Chia sẻ|Xem bản dịch|Like|Reply|Share)+[\s\xa0]*$', '', text, flags=re.IGNORECASE)

    # 5. Chuẩn hóa khoảng trắng thừa
    text = re.sub(r'[ \t\xa0]+', ' ', text).strip()

    return text


def run():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT comment_id, author, time_raw, text FROM comments")
    rows = cur.fetchall()
    print(f"Total comments: {len(rows)}")

    cleaned_count = 0
    updates = []

    for cid, author, time_raw, text in rows:
        cleaned = clean_single_comment_text(text, author, time_raw)
        if cleaned != text:
            cleaned_count += 1
            updates.append((cleaned, cid))

    print(f"Comments needing cleaning: {cleaned_count}")

    if updates:
        cur.executemany("UPDATE comments SET text = ? WHERE comment_id = ?", updates)
        conn.commit()
        print(f"[✓] Đã cập nhật thành công {cleaned_count} bình luận trong SQLite!")

    # Làm sạch bài viết posts
    cur.execute("SELECT post_id, text FROM posts WHERE status = 'comments_full'")
    post_rows = cur.fetchall()
    post_updates = []
    for pid, text in post_rows:
        if not text:
            continue
        cleaned_p = re.sub(r'([a-zA-Z\u00C0-\u024F\u1EA0-\u1EF9])([\.?!,:;])([A-ZÀ-Ỹ"“a-zà-ỹ])', r'\1\2 \3', text)
        cleaned_p = re.sub(r'([”"])([A-ZÀ-Ỹa-zà-ỹ0-9])', r'\1 \2', cleaned_p)
        cleaned_p = re.sub(r'([a-zA-Z0-9\u00C0-\u024F\u1EA0-\u1EF9])([“"])', r'\1 \2', cleaned_p)
        cleaned_p = re.sub(r'[\s\xa0]*(Xem thêm|See more)+[\s\xa0]*$', '', cleaned_p, flags=re.IGNORECASE)
        cleaned_p = re.sub(r'[ \t\xa0]+', ' ', cleaned_p).strip()
        if cleaned_p != text:
            post_updates.append((cleaned_p, pid))

    if post_updates:
        cur.executemany("UPDATE posts SET text = ? WHERE post_id = ?", post_updates)
        conn.commit()
        print(f"[✓] Đã cập nhật thành công {len(post_updates)} bài viết bị dính chữ trong SQLite!")

    conn.close()


if __name__ == "__main__":
    run()
