import sys
import os
import sqlite3
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "raw", "raw.sqlite")

def main():
    if not os.path.exists(DB_PATH):
        print(f"Chưa tìm thấy database tại: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    total_posts = c.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    completed_posts = c.execute("SELECT COUNT(*) FROM posts WHERE status = 'comments_full'").fetchone()[0]
    inaccessible_posts = c.execute("SELECT COUNT(*) FROM posts WHERE status = 'inaccessible'").fetchone()[0]
    total_comments = c.execute("SELECT COUNT(*) FROM comments").fetchone()[0]
    
    stats = c.execute("""
        SELECT 
            COALESCE(SUM(reactions), 0) as total_reactions,
            COALESCE(SUM(shares), 0) as total_shares,
            COALESCE(AVG(reactions), 0) as avg_reactions,
            COALESCE(AVG(n_comments), 0) as avg_comments
        FROM posts 
        WHERE status = 'comments_full'
    """).fetchone()

    target = 1500
    percent = (completed_posts / target) * 100 if target > 0 else 0

    print("=" * 65)
    print(" BÁO CÁO TIẾN ĐỘ THU THẬP DỮ LIỆU FACEBOOK CHI TIẾT")
    print(f" Thời gian kiểm tra: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)
    print(f"🎯 Mục tiêu bài viết       : {target:,} bài")
    print(f"✅ Đã cào hoàn tất         : {completed_posts:,} / {target:,} bài ({percent:.1f}%)")
    print(f"💬 Tổng số comments đã lưu : {total_comments:,} bình luận")
    print(f"❤️ Tổng lượt cảm xúc        : {stats['total_reactions']:,} reactions (tb: {stats['avg_reactions']:.1f}/bài)")
    print(f"🔄 Tổng lượt chia sẻ       : {stats['total_shares']:,} shares")
    print(f"📦 Tổng bài viết trong DB  : {total_posts:,} bài (bài không truy cập được: {inaccessible_posts})")
    print("-" * 65)
    
    # Danh sách 5 bài cào gần nhất
    recent = c.execute("""
        SELECT post_id, author, reactions, shares, n_comments, substr(text, 1, 60) as text_snippet, collected_at 
        FROM posts 
        WHERE status = 'comments_full' 
        ORDER BY collected_at DESC 
        LIMIT 5
    """).fetchall()

    if recent:
        print("📋 5 BÀI VIẾT VỪA CÀO GẦN ĐÂY NHẤT:")
        for r in recent:
            snippet = (r["text_snippet"] or "").replace("\n", " ")
            print(f"  • Post {r['post_id']} | Tác giả: {r['author'] or 'N/A'}")
            print(f"    - {r['reactions']} reacts | {r['shares']} shares | {r['n_comments']} comments")
            print(f"    - Nội dung: \"{snippet}...\"")
    else:
        print("Chưa có bài viết nào hoàn thành bóc tách chi tiết.")

    print("=" * 65)
    conn.close()

if __name__ == "__main__":
    main()

