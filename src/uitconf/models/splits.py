"""Chia dữ liệu tránh rò rỉ (8.5): theo bài + theo thời gian. Test chỉ dùng một lần ở cuối."""
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

def make_splits(df, test_time_fraction=0.2, val_group_fraction=0.15, seed=42):
    df = df.copy()
    df["_t"] = pd.to_datetime(df["created_at"], errors="coerce")
    dated = df.dropna(subset=["_t"])
    cut = dated["_t"].quantile(1 - test_time_fraction)
    # theo bài: mọi bình luận của một bài cùng tập -> dùng thời gian của bài
    post_time = dated.groupby("post_id")["_t"].min()
    test_posts = set(post_time[post_time > cut].index)
    test = df[df["post_id"].isin(test_posts)]
    rest = df[~df["post_id"].isin(test_posts)]
    gss = GroupShuffleSplit(n_splits=1, test_size=val_group_fraction, random_state=seed)
    tr_idx, va_idx = next(gss.split(rest, groups=rest["post_id"]))
    return rest.iloc[tr_idx].drop(columns="_t"), rest.iloc[va_idx].drop(columns="_t"), test.drop(columns="_t")
