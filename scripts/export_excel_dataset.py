import os
import sys
import sqlite3
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "raw", "raw.sqlite")
ROOT_DIR = os.path.dirname(BASE_DIR)

import json

conn = sqlite3.connect(DB_PATH)

def unpack_reactions(df, prefix=""):
    if "reactions_detail" in df.columns:
        def parse_rx(val):
            if not val or not isinstance(val, str):
                return {}
            try:
                return json.loads(val)
            except Exception:
                return {}
        rx_series = df["reactions_detail"].apply(parse_rx)
        df[f"{prefix}so_thich"] = rx_series.apply(lambda d: d.get("like", 0))
        df[f"{prefix}so_tim"] = rx_series.apply(lambda d: d.get("love", 0))
        df[f"{prefix}so_thuong_thuong"] = rx_series.apply(lambda d: d.get("care", 0))
        df[f"{prefix}so_haha"] = rx_series.apply(lambda d: d.get("haha", 0))
        df[f"{prefix}so_wow"] = rx_series.apply(lambda d: d.get("wow", 0))
        df[f"{prefix}so_buon"] = rx_series.apply(lambda d: d.get("sad", 0))
        df[f"{prefix}so_phan_no"] = rx_series.apply(lambda d: d.get("angry", 0))
        df.drop(columns=["reactions_detail"], inplace=True)
    return df

# 1. Đọc bảng posts (toàn bộ bài viết đã cào full)
query_posts = """
SELECT 
    post_id,
    author as tac_gia_bai_viet,
    text as noi_dung_bai_viet,
    reactions as so_luot_cam_xuc,
    reactions_detail,
    shares as so_luot_chia_se,
    n_comments as so_luong_binh_luan_ghi_nhan,
    time_raw as thoi_gian_dang_bai,
    permalink as link_bai_viet,
    collected_at as thoi_gian_thu_thap
FROM posts 
WHERE status = 'comments_full'
ORDER BY rowid ASC
"""
df_posts = pd.read_sql_query(query_posts, conn)
df_posts = unpack_reactions(df_posts)

# 2. Đọc bảng comments (toàn bộ bình luận)
query_comments = """
SELECT 
    comment_id,
    post_id,
    author as tac_gia_binh_luan,
    text as noi_dung_binh_luan,
    reactions as so_cam_xuc_binh_luan,
    reactions_detail,
    time_raw as thoi_gian_binh_luan,
    collected_at as thoi_gian_thu_thap
FROM comments
ORDER BY rowid ASC
"""
df_comments = pd.read_sql_query(query_comments, conn)
df_comments = unpack_reactions(df_comments)
conn.close()

print(f"Loaded {len(df_posts)} posts and {len(df_comments)} comments.")

# Xuất ra file Excel
excel_path_inner = os.path.join(BASE_DIR, "data", "raw", "dataset_uit_posts_and_comments.xlsx")
excel_path_root = os.path.join(ROOT_DIR, "dataset_uit_posts_and_comments.xlsx")

sheet_posts = f"Bai_Viet_{len(df_posts)}"
sheet_comments = f"Binh_Luan_{len(df_comments)}"

with pd.ExcelWriter(excel_path_inner, engine='openpyxl') as writer:
    df_posts.to_excel(writer, sheet_name=sheet_posts[:30], index=False)
    df_comments.to_excel(writer, sheet_name=sheet_comments[:30], index=False)

# Copy sang thư mục gốc để người dùng dễ mở
import shutil
shutil.copyfile(excel_path_inner, excel_path_root)

# Xuất bản CSV UTF-8 BOM phản ánh đúng số lượng thực tế
n_posts = len(df_posts)
n_comments = len(df_comments)

csv_posts_dynamic = os.path.join(ROOT_DIR, f"{n_posts}_bai_viet_posts.csv")
csv_comments_dynamic = os.path.join(ROOT_DIR, f"{n_comments}_binh_luan_comments.csv")
csv_posts_standard = os.path.join(ROOT_DIR, "dataset_uit_posts.csv")
csv_comments_standard = os.path.join(ROOT_DIR, "dataset_uit_comments.csv")

df_posts.to_csv(csv_posts_dynamic, index=False, encoding='utf-8-sig')
df_comments.to_csv(csv_comments_dynamic, index=False, encoding='utf-8-sig')
df_posts.to_csv(csv_posts_standard, index=False, encoding='utf-8-sig')
df_comments.to_csv(csv_comments_standard, index=False, encoding='utf-8-sig')

# Dọn dẹp các tệp mang tên số lượng cũ (nếu có và khác tên hiện tại)
old_files = [
    os.path.join(ROOT_DIR, "1500_bai_viet_posts.csv"),
    os.path.join(ROOT_DIR, "5520_binh_luan_comments.csv"),
    os.path.join(ROOT_DIR, "dataset_uit_1500_posts_and_comments.xlsx")
]
for old_f in old_files:
    if os.path.exists(old_f) and old_f not in (csv_posts_dynamic, csv_comments_dynamic):
        try:
            os.remove(old_f)
            print(f"Removed outdated file: {os.path.basename(old_f)}")
        except Exception as e:
            print(f"Could not remove {old_f}: {e}")

print(f"\n[OK] Xuất dữ liệu thành công:")
print(f" - Excel: {excel_path_root}")
print(f" - CSV Bài viết: {csv_posts_dynamic} (chuẩn: {csv_posts_standard})")
print(f" - CSV Bình luận: {csv_comments_dynamic} (chuẩn: {csv_comments_standard})")

