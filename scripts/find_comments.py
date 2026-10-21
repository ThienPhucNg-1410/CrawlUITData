import sqlite3, sys, re
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect('data/raw/raw.sqlite')
cursor = conn.cursor()

rows = cursor.execute("SELECT post_id, permalink, time_raw, text FROM posts").fetchall()

# Các bài có dấu hiệu rõ rệt là comment (câu trả lời cụt lủn, tag tên, trả lời cho câu hỏi)
comment_like = []
post_like = []

# Dấu hiệu câu trả lời/comment
REPLY_PATTERNS = re.compile(r"^(được nha|đc nha|được bạn|đc bạn|k nha|không nha|kh nha|ko nha|có nha|có bạn|đúng rồi|chuẩn rồi|ib mình|inbox mình|inbox nha|mình có nè|mình có nha|qua môn|học ít|xài vina|tháng 11|cho tui chơi|bá khí quá|vào portal|lên daa|mail cho thầy|thầy dạy hay|chuẩn bị sắm|lúc mất|bạn ông|nếu được|của ai quên|nhặt được|pass lại)\b", re.I)

for r in rows:
    t = r[3].strip()
    # Nếu bài ngắn dưới 60 ký tự và mang tính chất câu trả lời hoặc tag tên người
    lines = t.split("\n")
    first_line = lines[0].strip() if lines else ""
    
    # Kiểm tra tag tên (dòng 1 là tên người 2-3 từ, dòng 2 là câu nói ngắn)
    has_tag_mention = (len(lines) == 2 and len(lines[0].split()) in (2, 3, 4) and len(lines[1]) < 80)
    
    if REPLY_PATTERNS.search(first_line) or has_tag_mention:
        comment_like.append(r)
    else:
        post_like.append(r)

print(f"Tổng số bản ghi: {len(rows)}")
print(f"Bản ghi giống Post gốc: {len(post_like)}")
print(f"Bản ghi có đặc trưng Comment: {len(comment_like)}")

print("\n--- Ví dụ 10 bản ghi giống Comment ---")
for c in comment_like[:10]:
    print(f"[{c[0]}] {c[3][:80]}")

conn.close()

