import sys
sys.path.insert(0, "src")
import pandas as pd
from uitconf.db import connect
from uitconf.config import load_aspects
from uitconf.build_units import build
from uitconf.labeling import stratified_sample
from uitconf.models.splits import make_splits
from uitconf.models.baseline import run

def test_end_to_end(tmp_path):
    conn = connect(str(tmp_path / "t.sqlite"))
    for i in range(60):
        conn.execute("INSERT INTO posts(post_id,created_at,text,reactions,n_comments,bucket,round) VALUES(?,?,?,?,?,?,?)",
                     (f"p{i}", f"2024-{(i%12)+1:02d}-15T00:00:00", f"học phí trường tăng quá cao thầy Nguyễn Văn B {i} gọi 0912345678", i, 5, i, 1))
        conn.execute("INSERT INTO comments(comment_id,post_id,parent_id,text) VALUES(?,?,?,?)",
                     (f"c{i}", f"p{i}", None, f"đồng ý với bạn, khoa này tốt lắm {i}"))
    conn.execute("INSERT INTO posts(post_id,created_at,text) VALUES(?,?,?)",
                 ("outside_window", "2026-10-01T12:00:00", "out of range post"))
    conn.execute("INSERT INTO comments(comment_id,post_id,parent_id,text) VALUES(?,?,?,?)",
                 ("outside_comment", "outside_window", None, "out of range comment"))
    conn.commit()
    df = build(conn, load_aspects(), str(tmp_path / "u.csv"), start_date="2024-01-01", end_date="2024-12-31")
    assert "outside_window" not in set(df.post_id)
    assert not df.text.str.contains("0912345678|Nguyễn").any()
    assert df.relevant_rule.any() and (df.aspects_rule.str.contains("hoc_phi")).any()
    s = stratified_sample(df, 40); assert 0 < len(s) <= 40
    df["label"] = ["tieu_cuc" if "học phí" in t else "tich_cuc" for t in df.text]
    tr, va, te = make_splits(df)
    assert set(tr.post_id).isdisjoint(te.post_id) and set(tr.post_id).isdisjoint(va.post_id)
    clf, _, res = run(tr, va, te)
    assert "val" in res
