import sqlite3, sys, re
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect('data/raw/raw.sqlite')
cursor = conn.cursor()

posts = cursor.execute("SELECT post_id, permalink, time_raw, text FROM posts").fetchall()
print(f"Tổng số trong bảng posts: {len(posts)}")

# Phân tích các đặc điểm của Comment
# 1. Câu xưng hô với người hỏi ("...đi em", "...nha em", "...nha bạn", "...nhé bạn", "...nha b", "...nhé b", "...ạ bạn", "...hả bạn", "...đâu em", "...đc nha", "...được nha", "...chưa em", "...chưa bạn")
# 2. Bắt đầu bằng câu trả lời: "Có...", "Không...", "Được...", "Dạ...", "Mình nghĩ...", "Tùy...", "Lên...", "Vào...", "Ib...", "Mail..."
# 3. Câu quá ngắn kết thúc bằng dấu hỏi về một thứ đang nói dở ("Tái bản mấy ạ?", "bạn tìm tôi à?", "lớp thầy [GV] hả bạn?")
# 4. Tag tên bạn bè

COMMENT_INDICATORS = re.compile(
    r"(\b(nha em|nhé em|đi em|nha bạn|nhé bạn|nha b|nhé b|đâu em|đâu bạn|hả bạn|hả e|hả em|chưa em|chưa b|chưa bạn|vậy bạn|vậy em|nhé chủ tus|nha chủ tus|v bạn|nha og|nha ông|nè bạn|nè em|nè b)\b|"
    r"^(có|không|kh|k|được|đc|tùy|lên|vào|ib|inbox|mail|qua|gửi|check|xem|mua|học|tìm|chắc|thấy|nghe)\s+(nha|nhé|nè|ạ|đó|rồi|luôn|đi|được|bạn|em|b|đc)\b|"
    r"^(tái bản mấy|bạn tìm tôi|lớp thầy .* hả|đã có đi nhận|có môn .* chưa|bạn học .* à|đi hc nhóm có|bạn khách có|đã qua phòng|hảo hoàng|trong kỳ này còn|tui tham gia|ụa sinh viên|up lên đi|quần dài đi|hoàng gia bảo|em lên a101|nhà văn hoá sinh viên|mình có điểm pk|cho tui xin slot|cho mình xin slot|bạn liên hệ|đăng ký ở|đợi thông báo|liên hệ ctsv|lên phòng đào tạo|vào daa|vào portal|lên web trường)\b)",
    re.I
)

comments_found = []
genuine_posts = []

for p in posts:
    t = p[3].strip()
    if not t or t in ('.', '..', '...'):
        continue
    
    # Kiểm tra tag bạn bè
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    first_line = lines[0] if lines else ""
    words = first_line.split()
    is_tag = (len(words) in (2, 3, 4) and len(lines) >= 2 and len(t) < 120 and words[0][0].isupper() and words[1][0].isupper() and not first_line.endswith("?"))
    
    # Kiểm tra dấu hiệu câu trả lời/comment
    is_reply = bool(COMMENT_INDICATORS.search(t))
    
    # Nếu bài ngắn dưới 70 ký tự mà mang tính trả lời
    is_short_reply = (len(t) < 70 and not any(k in t.lower() for k in ["cho em hỏi", "cho mình hỏi", "mn cho em hỏi", "mọi người cho em hỏi", "review", "confession", "cfs", "#"]))
    
    if is_tag or is_reply or is_short_reply:
        comments_found.append(p)
    else:
        genuine_posts.append(p)

print(f"Số bài nhận diện là BÀI GỐC: {len(genuine_posts)}")
print(f"Số bài nhận diện là BÌNH LUẬN: {len(comments_found)}")

print("\n--- 15 bài đầu tiên bị nhận diện là Comment ---")
for c in comments_found[:15]:
    print(f"[{c[0]}]: {c[3][:80]}")

print("\n--- 15 bài đầu tiên được giữ là Bài Gốc ---")
for g in genuine_posts[:15]:
    print(f"[{g[0]}]: {g[3][:80]}")

conn.close()

