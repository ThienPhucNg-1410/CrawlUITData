import sqlite3

conn = sqlite3.connect('data/raw/raw.sqlite')
c = conn.cursor()
c.execute('SELECT count(*) FROM posts')
total = c.fetchone()[0]
c.execute('SELECT max(collected_at) FROM posts')
latest_collected = c.fetchone()[0]
c.execute("SELECT count(*) FROM posts WHERE collected_at >= '2026-10-07'")
today_count = c.fetchone()[0]
c.execute("SELECT session_id, count(*) FROM posts WHERE collected_at >= '2026-10-07' GROUP BY session_id")
sessions_today = c.fetchall()

print("Total posts:", total)
print("Latest collected_at in DB:", latest_collected)
print("Posts collected today (2026-10-07):", today_count)
print("Sessions today:", sessions_today)

