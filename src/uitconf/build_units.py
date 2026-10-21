"""raw.sqlite -> units.csv đã ẩn danh + chuẩn hóa (phần 2, 5, 6). Ẩn danh TRƯỚC mọi phân tích."""
import pandas as pd
from .anonymize import anonymize
from .preprocess import is_valid, load_teencode, normalize, segment
from .relevance import RuleTagger

def _in_date_window(values, start_date, end_date):
    dates = pd.to_datetime(values, format="ISO8601", errors="coerce", utc=True)
    keep = dates.notna()
    if start_date:
        keep &= dates >= pd.Timestamp(start_date, tz="UTC")
    if end_date:
        keep &= dates < pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    return keep

def build(conn, aspects_cfg, out_csv, use_ner=False, do_segment=False, start_date=None, end_date=None):
    teen, tagger = load_teencode(), RuleTagger(aspects_cfg)
    posts = pd.read_sql("SELECT post_id, created_at, text, reactions, n_comments, status, round, permalink FROM posts", conn)
    coms = pd.read_sql("SELECT comment_id, post_id, parent_id, text, created_at FROM comments", conn)
    if start_date or end_date:
        posts = posts.loc[_in_date_window(posts["created_at"], start_date, end_date)].copy()
        coms = coms[coms["post_id"].isin(posts["post_id"])].copy()
    ctx = dict(zip(posts.post_id, posts.text))
    plinks = dict(zip(posts.post_id, posts.permalink))
    rows = []
    for r in posts.itertuples():
        rows.append(dict(unit_id=r.post_id, unit_type="post", post_id=r.post_id, parent_id=None,
                         created_at=r.created_at, text=r.text, reactions=r.reactions or 0,
                         status=r.status, round=r.round, context="", permalink=r.permalink or ""))
    pdate = dict(zip(posts.post_id, posts.created_at))
    com_counters = {}
    for r in coms.itertuples():
        p_id = str(r.post_id)
        com_counters[p_id] = com_counters.get(p_id, 0) + 1
        sub_id = f"{p_id}_{com_counters[p_id]}"
        rows.append(dict(unit_id=sub_id, unit_type="comment", post_id=r.post_id, parent_id=r.parent_id,
                         created_at=r.created_at or pdate.get(r.post_id), text=r.text, reactions=0,
                         status=None, round=None, context=ctx.get(r.post_id, ""), permalink=plinks.get(r.post_id, "")))
    df = pd.DataFrame(rows)
    if df.empty:
        df.to_csv(out_csv, index=False); return df
    if start_date or end_date:
        df = df.loc[_in_date_window(df["created_at"], start_date, end_date)].copy()
    df["text"] = df["text"].fillna("").map(lambda t: anonymize(t, use_ner))
    df["context"] = df["context"].fillna("").map(lambda t: anonymize(t, use_ner))
    df = df[df["text"].map(is_valid)].drop_duplicates(subset=["unit_type", "text"]).copy()
    # Làm gọn khoảng trắng thừa để người đọc dễ xem trên bảng
    df["text_clean"] = df["text"].map(lambda t: " ".join(t.split()))
    df["text_norm"] = df["text"].map(lambda t: normalize(t, teen))
    if do_segment:
        df["text_seg"] = df["text_norm"].map(segment)
    df["relevant_rule"] = df["text"].map(tagger.is_relevant)
    df["aspects_rule"] = df["text"].map(lambda t: "|".join(tagger.aspects(t)))
    
    # Kế thừa khía cạnh từ bài viết gốc cho bình luận nếu bình luận ngắn gọn (vd: "đúng rồi", "chuẩn", "thầy dạy hay")
    post_aspects = dict(zip(posts.post_id, posts["text"].map(lambda t: "|".join(tagger.aspects(t)))))
    post_relevant = dict(zip(posts.post_id, posts["text"].map(tagger.is_relevant)))
    
    for idx, row in df.iterrows():
        if row["unit_type"] == "comment":
            p_id = row["post_id"]
            # Nếu bài gốc KHÔNG liên quan -> bình luận bên dưới cũng KHÔNG liên quan
            if p_id in post_relevant and not post_relevant[p_id]:
                df.at[idx, "relevant_rule"] = False
            # Nếu bình luận không bắt được aspect riêng, kế thừa aspect từ bài gốc
            if not df.at[idx, "aspects_rule"] and p_id in post_aspects:
                df.at[idx, "aspects_rule"] = post_aspects[p_id]
                
    df["month"] = df["created_at"].astype(str).str[:7]
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    # Đồng thời xuất file dữ liệu định dạng dễ đọc cho người dùng
    readable_cols = ["created_at", "unit_type", "post_id", "permalink", "text_clean", "relevant_rule", "aspects_rule", "context"]
    readable_cols = [c for c in readable_cols if c in df.columns]
    readable_path = out_csv.replace(".csv", "_readable.csv")
    df[readable_cols].to_csv(readable_path, index=False, encoding="utf-8-sig")
    return df
