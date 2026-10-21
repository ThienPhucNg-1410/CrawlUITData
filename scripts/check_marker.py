import sqlite3
conn = sqlite3.connect('data/raw/raw.sqlite')
r = conn.execute("SELECT post_id, created_at, text FROM posts WHERE text LIKE '%hoạt động bất thường%'").fetchall()
print(f"Posts found: {len(r)}")
for x in r:
    print(x[0], x[1], x[2][:100])
conn.close()
