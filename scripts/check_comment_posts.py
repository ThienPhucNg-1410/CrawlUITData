import sqlite3, sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect('data/raw/raw.sqlite')
cursor = conn.cursor()

ids_to_check = ['1139837498578978', '1139837221912339', '1139318895297505', '1138542162041845', '1138348508727877']
for cid in ids_to_check:
    r = cursor.execute("SELECT post_id, permalink, time_raw, text FROM posts WHERE post_id=?", (cid,)).fetchone()
    if r:
        print(f"ID: {r[0]}\nPermalink: {r[1]}\nTimeRaw: {r[2]}\nText: {r[3]}\n{'-'*50}")

conn.close()

