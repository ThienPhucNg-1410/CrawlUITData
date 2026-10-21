import sqlite3

conn = sqlite3.connect("data/raw/raw.sqlite")
res = conn.execute("""
    UPDATE posts 
    SET status = 'post_only' 
    WHERE status = 'comments_full' 
      AND post_id NOT IN (SELECT DISTINCT post_id FROM comments)
""")
conn.commit()
print("Reset posts back to post_only:", res.rowcount)

rows = conn.execute("SELECT status, count(*) FROM posts GROUP BY status").fetchall()
print("Current statuses:", rows)
