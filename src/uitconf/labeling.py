"""Gán nhãn (phần 7): lấy mẫu phân tầng, tách file cho 2 người gán, tính Cohen's kappa."""
import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

COLS = ["unit_id", "unit_type", "month", "permalink", "context", "text", "label", "sarcasm", "aspects", "note"]

def stratified_sample(df, n, seed=42):
    """Phân tầng theo tháng × tertile tương tác (+ loại đơn vị). Không lấy ngẫu nhiên đơn thuần."""
    df = df.copy()
    df["eng"] = pd.qcut(df["reactions"].rank(method="first"), 3, labels=["low", "mid", "high"])
    df["stratum"] = df["month"].astype(str) + "|" + df["eng"].astype(str) + "|" + df["unit_type"]
    k = max(1, n // df["stratum"].nunique())
    parts = [g.sample(min(len(g), k), random_state=seed) for _, g in df.groupby("stratum")]
    out = pd.concat(parts)
    if len(out) < n:  # bù phần thiếu
        rest = df.drop(out.index).sample(min(n - len(out), len(df) - len(out)), random_state=seed)
        out = pd.concat([out, rest])
    return out.sample(frac=1, random_state=seed).head(n)

def export_batches(sample, out_dir, overlap=0.3, seed=42):
    """A gán toàn bộ; B gán phần overlap (20–30%) để tính kappa. Người thứ ba xử lý bất đồng."""
    for c in ("label", "sarcasm", "aspects", "note"):
        sample[c] = ""
    s = sample[COLS]
    s.to_csv(f"{out_dir}/annotator_A.csv", index=False, encoding="utf-8-sig")
    s.sample(frac=overlap, random_state=seed).to_csv(f"{out_dir}/annotator_B.csv", index=False, encoding="utf-8-sig")

def kappa(path_a, path_b, col="label"):
    a, b = pd.read_csv(path_a), pd.read_csv(path_b)
    m = a.merge(b, on="unit_id", suffixes=("_a", "_b"))
    m = m.dropna(subset=[f"{col}_a", f"{col}_b"])
    k = cohen_kappa_score(m[f"{col}_a"], m[f"{col}_b"])
    dis = m[m[f"{col}_a"] != m[f"{col}_b"]][["unit_id", f"{col}_a", f"{col}_b"]]
    return k, len(m), dis
