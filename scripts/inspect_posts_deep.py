import pandas as pd, sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

df = pd.read_csv("data/labeled/review_labeled.csv")
posts = df[df["unit_type"] == "post"].copy()
print(f"Tổng số post hiện tại: {len(posts)}")

# Kiểm tra các bài ngắn hoặc có dấu hiệu quảng cáo hoặc có dấu hiệu là comment
print("\n--- 25 bài post ngắn nhất (< 100 ký tự) ---")
for idx, r in enumerate(posts.sort_values(by="text", key=lambda x: x.str.len()).head(25).itertuples(), 1):
    print(f"{idx}. [{r.unit_id}] ({r.label}): {r.text}")

print("\n--- Các bài chứa từ khóa tiếng Anh/quảng cáo ---")
ads = posts[posts["text"].str.contains(r"(ares|toeic|ielts|tiếng anh|khóa học|trung tâm|buddies|izone)", case=False, na=False)]
print(f"Tìm thấy {len(ads)} bài liên quan tiếng anh / quảng cáo:")
for idx, r in enumerate(ads.head(15).itertuples(), 1):
    print(f"{idx}. [{r.unit_id}] ({r.label}): {r.text[:90]}...")

