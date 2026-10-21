import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/raw/raw.sqlite')
c = conn.cursor()

c.execute("SELECT COUNT(post_id) FROM posts WHERE status = 'comments_full'")
total_full = c.fetchone()[0]

c.execute("SELECT COUNT(comment_id) FROM comments")
total_cmts = c.fetchone()[0]

print(f"Tổng số bài đã full cmt trong DB: {total_full}")
print(f"Tổng số bình luận trong DB: {total_cmts}")

c.execute("""
    SELECT substr(created_at, 1, 7) as ym, 
           count(case when status='comments_full' then 1 end) as full_cnt,
           count(case when status='post_only' then 1 end) as post_only_cnt
    FROM posts 
    WHERE substr(created_at, 1, 7) IN ('2026-06', '2026-07')
    GROUP BY ym
""")
for r in c.fetchall():
    print(f"  Tháng {r[0]}: Đã hoàn tất cmt: {r[1]:4d} bài | Còn lại: {r[2]:4d} bài")

c.execute("SELECT COUNT(comment_id) FROM comments WHERE session_id LIKE 'cmt_jj_%'")
new_cmts = c.fetchone()[0]
print(f"Bình luận mới thu thập thêm từ phiên tháng 6-7 này: {new_cmts} comments")

# Lấy 5 bài vừa cào gần nhất
c.execute("""
    SELECT post_id, created_at, text, author, reactions, n_comments, shares
    FROM posts
    WHERE substr(created_at, 1, 7) IN ('2026-06', '2026-07') AND status = 'comments_full'
    ORDER BY collected_at DESC
    LIMIT 5
""")
print("\nTop 5 bài viết vừa hoàn tất gần nhất:")
for row in c.fetchall():
    pid, cat, txt, auth, rx, cm, sh = row
    snip = txt.replace('\n', ' ')[:60]
    print(f"  - [{cat[:10]}] Post {pid} | React: {rx:2d} | Cmt: {cm:2d} | Share: {sh:2d} | '{snip}...'")

