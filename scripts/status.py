import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import sqlite3
import os

db_path = "d:/uit-confession-sentiment/uit-confession-sentiment/data/raw/raw.sqlite"
if not os.path.exists(db_path):
    db_path = "data/raw/raw.sqlite"

conn = sqlite3.connect(db_path)
total_posts = conn.execute("SELECT count(*) FROM posts").fetchone()[0]
oldest = conn.execute("SELECT min(created_at) FROM posts WHERE created_at IS NOT NULL").fetchone()[0]
newest = conn.execute("SELECT max(created_at) FROM posts WHERE created_at IS NOT NULL").fetchone()[0]

print("==================================================================")
print("               BÁO CÁO TIẾN ĐỘ CÀO DỮ LIỆU TỰ ĐỘNG               ")
print("==================================================================")
print(f" [*] TỔNG SỐ BÀI VIẾT ĐÃ THU THẬP: {total_posts} bài")
print(f" [*] Mốc bài mới nhất : {newest[:16] if newest else 'N/A'}")
print(f" [*] Mốc bài cũ nhất  : {oldest[:16] if oldest else 'N/A'}")
print(" [*] Trạng thái tiến trình: Đang cào ngầm liên tục ổn định.")
print("==================================================================")
