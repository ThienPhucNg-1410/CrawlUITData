import sqlite3, sys, re
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect('data/raw/raw.sqlite')
cursor = conn.cursor()

# Kiểm tra xem có bao nhiêu bài có chữ "comment_id" hoặc liên quan trong sessions hay raw
rows = cursor.execute("SELECT post_id, permalink, time_raw, text FROM posts").fetchall()
print(f"Tổng số bản ghi trong posts table: {len(rows)}")

# Kiểm tra các post_id trùng lặp hoặc cấu trúc
print("\nTop 15 bài ngắn nhất:")
for r in sorted(rows, key=lambda x: len(x[3]))[:15]:
    print(f"PID: {r[0]} | Time: {r[2]} | Text: {repr(r[3])}")

conn.close()

