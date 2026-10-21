import sqlite3, sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect('data/raw/raw.sqlite')
cursor = conn.cursor()

p = cursor.execute("SELECT post_id, permalink, time_raw, text FROM posts WHERE post_id='1139829868579741'").fetchone()
print("Post 1139829868579741:")
if p:
    print(f"ID: {p[0]}")
    print(f"Permalink: {p[1]}")
    print(f"Time: {p[2]}")
    print(f"Text:\n{p[3]}")
else:
    print("Not found")

conn.close()

