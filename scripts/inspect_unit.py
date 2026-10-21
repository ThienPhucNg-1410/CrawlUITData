import sqlite3, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect('data/raw/raw.sqlite')
cursor = conn.cursor()
p = cursor.execute("SELECT post_id, permalink, time_raw, text FROM posts WHERE post_id='1139837498578978'").fetchone()
print("Post record:", p)

# Check comments count in DB
c_count = cursor.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
p_count = cursor.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
print(f"Total in posts table: {p_count}, Total in comments table: {c_count}")

# Check sample 5 records in posts table that look like comments
short_posts = cursor.execute("SELECT post_id, text, permalink FROM posts WHERE LENGTH(text) < 40 LIMIT 10").fetchall()
print("\nSample short text in posts table:")
for sp in short_posts:
    print(f"ID: {sp[0]} | Link: {sp[2]} | Text: {sp[1]}")

conn.close()
