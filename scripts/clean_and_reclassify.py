import sqlite3, sys, re
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect('data/raw/raw.sqlite')
cursor = conn.cursor()

print("Schema of comments table:")
print(cursor.execute("PRAGMA table_info(comments)").fetchall())

# Tìm các bài trong posts thực chất là comment
# Đặc trưng của comment bị cào nhầm:
# 1. Trả lời cụt lủn (Xài vina đi bạn, Tháng 11 bạn, Học ít thội em, Được nha cùng tuyến là được, Cho tui chơi với:))), Bá khí quá...)
# 2. Tag tên người ở đầu dòng hoặc cuối dòng
# 3. Quá ngắn (< 60 ký tự) và không có cấu trúc câu hỏi hay confession

REPLY_REGEX = re.compile(
    r"^(được nha|đc nha|được bạn|đc bạn|k nha|không nha|kh nha|ko nha|có nha|có bạn|đúng rồi|chuẩn rồi|ib mình|inbox mình|inbox nha|mình có nè|mình có nha|qua môn|học ít|xài vina|tháng 11|cho tui chơi|bá khí quá|vào portal|lên daa|mail cho thầy|thầy dạy hay|chuẩn bị sắm|lúc mất|bạn ông|nếu được|của ai quên|nhặt được|pass lại|dạ còn|dạ có|mình dư|chắc nước|qua tòa|không cần nộp|năm 2 mới|lên bhtcnpm|trên portal|đóng ở ktx|săn giá|rút môn|cho hôn|update:|heo đét|áo gió|google classroom|đang chill|khoa khác|thiếu 0\.05|đậu tkvm|dưới 5 là|thật ko để|nguyên cái cmt|chuyển trường|bạn thông cảm|bạn chơi boardgame|t đi học|dịch cabin|ê kevin|phung domamine|chuyển sang mmt|bốc đầu|đừng có dốc|ib\b|k biết phải|vắng học|đánh ở đâu|mình khuyên|mình chơi|bạn hỏi mấy cô|phd là|bóng đá|có bán cháo|nếu ko cần|thì ra là|sừng j mà|toi biet|vấn đề không|trần thiện|mermaid|vũ nguyễn|đỗ huy|hướng 1|vào thoải mái|ms chơi|đki học|mún tập|phòng y tế|lê hướng|nói bản thân|năm nhất toàn|nguyễn minh|năm nay tuyển|phan hoàng|sợ đi học|nerd|hdh k thi|bạn k ngại|là s b|bạn ib|nếu gv có|083|trg mình đrl|ib liền|thiếu bá khí|ước tìm|tt thể dục|ông nào iu|có tui|ngô vân|không biết em|bạn post|em theo dõi|web bhtcnpm|csdl có điểm|\.\.\.|\.|\bpass\b)\b",
    re.I
)

posts = cursor.execute("SELECT post_id, permalink, time_raw, text, created_at, session_id FROM posts").fetchall()
to_move = []

for p in posts:
    pid, plink, time_raw, text, created_at, sid = p
    t = text.strip()
    
    # 1. Các bài rỗng hoặc chỉ có dấu chấm
    if not t or t in ('.', '..', '...', '....'):
        to_move.append((p, "Rỗng / Dấu chấm"))
        continue
        
    lines = t.split("\n")
    first_line = lines[0].strip()
    
    # 2. Khớp mẫu câu trả lời đặc trưng của comment
    if REPLY_REGEX.search(first_line) and len(t) < 180:
        to_move.append((p, "Mẫu câu trả lời (Reply)"))
        continue
        
    # 3. Dòng đầu tag tên người dạng "Nguyễn Văn A" + câu ngắn
    words = first_line.split()
    if len(words) in (2, 3, 4) and len(lines) >= 2 and len(t) < 100 and words[0][0].isupper() and words[1][0].isupper():
        to_move.append((p, "Tag tên bạn bè (Mention)"))
        continue

print(f"\nTìm thấy {len(to_move)} bản ghi trong posts thực chất là comment/rác.")

# Di chuyển sang comments table hoặc xóa khỏi posts
migrated = 0
for p, reason in to_move:
    pid, plink, time_raw, text, created_at, sid = p
    if text.strip() and text.strip() not in ('.', '..', '...'):
        # Lưu vào bảng comments với comment_id là pid
        cid = f"c_{pid}"
        cursor.execute(
            "INSERT OR IGNORE INTO comments(comment_id, post_id, parent_id, text, collected_at, session_id) VALUES(?,?,?,?,?,?)",
            (cid, pid, None, text, created_at, sid)
        )
        migrated += 1
    # Xóa khỏi posts table
    cursor.execute("DELETE FROM posts WHERE post_id=?", (pid,))

conn.commit()
print(f"Đã di chuyển {migrated} bình luận sang bảng comments, và làm sạch bảng posts!")
remaining = cursor.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
total_comms = cursor.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
print(f"Hiện tại trong DB: {remaining} bài viết gốc chuẩn, {total_comms} bình luận.")
conn.close()

