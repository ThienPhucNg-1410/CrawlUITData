import sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('data/raw/raw.sqlite')
conn.row_factory = sqlite3.Row
total = conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
newest = conn.execute('SELECT MAX(created_at) FROM posts WHERE created_at IS NOT NULL').fetchone()[0]
oldest = conn.execute('SELECT MIN(created_at) FROM posts WHERE created_at IS NOT NULL').fetchone()[0]
print(f'Tong bai trong DB: {total}')
print(f'Bai moi nhat     : {str(newest or "N/A")[:16]}')
print(f'Bai cu nhat      : {str(oldest or "N/A")[:16]}')
conn.close()

