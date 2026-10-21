import sqlite3
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/raw/raw.sqlite')
c = conn.cursor()

# 1. Inspect posts
c.execute('SELECT COUNT(*) FROM posts')
total_posts = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM posts WHERE status = 'comments_full'")
full_posts = c.fetchone()[0]

print(f"Total posts in DB: {total_posts}")
print(f"Posts with status='comments_full': {full_posts}")

# Check duplicate texts across all posts
c.execute('''
    SELECT text, COUNT(*) as cnt, GROUP_CONCAT(post_id, ', ')
    FROM posts
    WHERE text IS NOT NULL AND text != ''
    GROUP BY text
    HAVING cnt > 1
    ORDER BY cnt DESC
''')
dup_texts = c.fetchall()
print(f"\n--- DUPLICATE TEXT GROUPS (Total groups: {len(dup_texts)}) ---")
total_dup_post_count = 0
for text, cnt, post_ids in dup_texts:
    total_dup_post_count += cnt
    ids_preview = post_ids.split(', ')[:4]
    snippet = text.replace('\n', ' ')[:70]
    print(f"Count: {cnt:4d} | Snippet: {snippet!r} | IDs: {ids_preview}...")

print(f"\nTotal posts with duplicated text: {total_dup_post_count}")
c.execute("SELECT COUNT(DISTINCT text) FROM posts WHERE text IS NOT NULL AND text != ''")
distinct_texts = c.fetchone()[0]
print(f"Distinct texts: {distinct_texts} out of {total_posts}")

# 2. Check the specific 1,500 posts exported
# Let's see how many of the exported 1,500 posts have duplicate text
c.execute('''
    SELECT post_id, text, author, permalink 
    FROM posts 
    WHERE status = 'comments_full' 
    ORDER BY rowid ASC 
    LIMIT 1500
''')
exported_1500 = c.fetchall()
text_counts_1500 = Counter(row[1] for row in exported_1500)
dups_in_1500 = {k: v for k, v in text_counts_1500.items() if v > 1}
num_dup_posts_in_1500 = sum(dups_in_1500.values())
unique_in_1500 = len(exported_1500) - num_dup_posts_in_1500

print(f"\n--- AUDIT TRÊN 1.500 BÀI VIẾT ĐÃ XUẤT ---")
print(f"Tổng số bài xuất: {len(exported_1500)}")
print(f"Số bài có nội dung độc nhất (chuẩn): {unique_in_1500} bài ({unique_in_1500/1500*100:.1f}%)")
print(f"Số bài bị dính văn bản trùng lặp (bốc nhầm từ feed nền/bài ghim): {num_dup_posts_in_1500} bài ({num_dup_posts_in_1500/1500*100:.1f}%)")
print(f"Số nhóm nội dung bị lặp lại trong 1.500 bài: {len(dups_in_1500)} nhóm")
for txt, cnt in sorted(dups_in_1500.items(), key=lambda x: x[1], reverse=True)[:10]:
    s = txt.replace('\n', ' ')[:65]
    print(f"  + Lặp {cnt:3d} lần: {s!r}")

# 3. Check authors with very high counts
c.execute('''
    SELECT author, COUNT(*) as cnt
    FROM posts
    WHERE author IS NOT NULL AND author != ''
    GROUP BY author
    ORDER BY cnt DESC
    LIMIT 15
''')
top_authors = c.fetchall()
print(f"\n--- TOP AUTHORS TRONG POSTS ---")
for author, cnt in top_authors:
    print(f"{author:40s}: {cnt}")

# 4. Check comments table
c.execute('SELECT COUNT(*) FROM comments')
total_comments = c.fetchone()[0]
c.execute('SELECT COUNT(DISTINCT comment_id) FROM comments')
distinct_comments = c.fetchone()[0]
c.execute('SELECT COUNT(DISTINCT post_id) FROM comments')
comment_posts = c.fetchone()[0]
print(f"\n--- AUDIT BẢNG COMMENTS (BÌNH LUẬN) ---")
print(f"Tổng số bình luận: {total_comments}")
print(f"Số comment_id độc nhất: {distinct_comments}")
print(f"Số bài viết có bình luận: {comment_posts}")

# Check comments in the 1500 set
exported_post_ids = set(row[0] for row in exported_1500)
c.execute("SELECT post_id, comment_id, author, text FROM comments")
all_cmts = c.fetchall()
cmts_in_1500 = [cm for cm in all_cmts if cm[0] in exported_post_ids]
print(f"Số bình luận thuộc 1.500 bài viết: {len(cmts_in_1500)}")

# Are there duplicate comments across different post_ids?
c.execute('''
    SELECT text, COUNT(DISTINCT post_id) as p_cnt, COUNT(*) as c_cnt
    FROM comments
    WHERE text IS NOT NULL AND text != '' AND length(text) > 10
    GROUP BY text
    HAVING c_cnt > 5
    ORDER BY c_cnt DESC
    LIMIT 10
''')
dup_cmts = c.fetchall()
print(f"\n--- BÌNH LUẬN TRÙNG LẶP TRÊN NHIỀU BÀI (Check xem comments có bị bốc nhầm không) ---")
for t, pc, cc in dup_cmts:
    sn = t.replace('\n', ' ')[:60]
    print(f"Xuất hiện {cc} lần trên {pc} bài: {sn!r}")

