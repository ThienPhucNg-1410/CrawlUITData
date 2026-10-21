"""Phân tích & trực quan (phần 9): tỉ lệ + bootstrap CI, xu hướng tháng, aspect × cảm xúc."""
import numpy as np
import pandas as pd

def bootstrap_ci(values, n_boot=2000, seed=0, alpha=0.05):
    """values: mảng 0/1. Trả (mean, lo, hi)."""
    rng = np.random.default_rng(seed)
    v = np.asarray(values, dtype=float)
    if len(v) == 0:
        return np.nan, np.nan, np.nan
    bs = rng.choice(v, size=(n_boot, len(v)), replace=True).mean(axis=1)
    return v.mean(), np.quantile(bs, alpha / 2), np.quantile(bs, 1 - alpha / 2)

def proportions(df, label_col="pred", groups=None):
    rows = []
    for key, g in (df.groupby(groups) if groups else [("all", df)]):
        for lab in sorted(df[label_col].unique()):
            m, lo, hi = bootstrap_ci((g[label_col] == lab).astype(int))
            rows.append({"group": key, "label": lab, "n": len(g), "prop": m, "ci_lo": lo, "ci_hi": hi})
    return pd.DataFrame(rows)

def aspect_table(df, label_col="pred"):
    d = df.assign(aspect=df["aspects_rule"].fillna("").str.split("|")).explode("aspect")
    d = d[d["aspect"].astype(bool)]
    return pd.crosstab(d["aspect"], d[label_col], normalize="index").round(3)

def plot_trend(df, label_col="pred", path="trend.png"):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t = pd.crosstab(df["month"], df[label_col], normalize="index")
    ax = t.plot(figsize=(10, 4), marker="o")
    ax.set_ylabel("Tỉ lệ"); ax.set_title("Xu hướng cảm xúc theo tháng (trong dữ liệu confession)")
    plt.tight_layout(); plt.savefig(path, dpi=150); plt.close()

def completeness(conn):
    return pd.read_sql("SELECT round, status, COUNT(*) n FROM posts GROUP BY round, status", conn)
