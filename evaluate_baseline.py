import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
from uitconf import config as C
from uitconf.models.splits import make_splits
from uitconf.models import baseline

cfg = C.load("configs/config.yaml")
gold = pd.read_csv("data/labeled/gold.csv")

# Filter sentiment classes (loại khong_lien_quan theo pipeline chuẩn)
sentiment_df = gold[gold["label"].isin(["tieu_cuc", "trung_tinh", "tich_cuc", "hoi_dap"])].copy()
sentiment_df["y"] = sentiment_df["label"]

sc = cfg["split"]
tr, va, te = make_splits(sentiment_df, sc["test_time_fraction"], sc["val_group_fraction"], sc["seed"])

clf, (w, c), res = baseline.run(tr, va, te, label_col="y", out_json="data/labeled/baseline_sentiment.json")

print("="*68)
print("  KẾT QUẢ ĐÁNH GIÁ MÔ HÌNH BASELINE (TF-IDF + LOGISTIC REGRESSION)")
print("="*68)
print(f"Tổng số mẫu đánh giá: {len(sentiment_df)}")
print(f"Phân chia tập dữ liệu: Train = {len(tr)} | Val = {len(va)} | Test = {len(te)}")
print(f"Macro F1 (Validation): {res['val']['macro_f1']:.4f}")
print(f"Macro F1 (Test):       {res['test']['macro_f1']:.4f}")
print("-"*68)
print(f"{'Nhãn cảm xúc':<18} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Số lượng'}")
print("-"*68)

rep = res['test']['report']
for k, v in rep.items():
    if isinstance(v, dict):
        p = f"{v['precision']:.2f}"
        r = f"{v['recall']:.2f}"
        f = f"{v['f1-score']:.2f}"
        s = v['support']
        print(f"{k:<18} {p:<12} {r:<12} {f:<12} {s}")

print("="*68)
