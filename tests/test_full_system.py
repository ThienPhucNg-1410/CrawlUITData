import os
import sys
import tempfile
import sqlite3
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, "src")

from uitconf import config as C
from uitconf.db import connect
from uitconf.anonymize import anonymize, regex_layer
from uitconf.preprocess import normalize, is_valid, load_teencode
from uitconf.relevance import RuleTagger
from uitconf.scraper.guard import HardStop, check_blocked, set_cooldown, cooldown_remaining
from uitconf.scraper.timer import Throttle
from uitconf.scraper.parse import (
    post_id_from_href,
    bucket_of,
    round_of,
    parse_count,
    comment_id,
)
from uitconf.build_units import build
from uitconf.labeling import stratified_sample, export_batches, kappa
from uitconf.models.splits import make_splits
from uitconf.models.baseline import run as run_baseline
from uitconf.analysis import bootstrap_ci, proportions, aspect_table, plot_trend, completeness


def test_regex_anonymization_comprehensive():
    # Test phone numbers
    cases_phone = [
        ("Gọi 0912345678 ngay", "[SDT]"),
        ("SĐT +84 987 654 321 nè", "[SDT]"),
        ("Liên hệ 090-123-4567", "[SDT]"),
    ]
    for text, tag in cases_phone:
        res = anonymize(text)
        assert tag in res

    # Test emails
    cases_email = [
        ("Email: test.user@gm.uit.edu.vn", "[EMAIL]"),
        ("Gửi qua abc_123@yahoo.com", "[EMAIL]"),
    ]
    for text, tag in cases_email:
        res = anonymize(text)
        assert tag in res

    # Test MSSV (8 digits)
    cases_mssv = [
        ("Em là sinh viên 21520001", "[MSSV]"),
        ("MSSV: 20521234 lớp CNTT", "[MSSV]"),
    ]
    for text, tag in cases_mssv:
        res = anonymize(text)
        assert tag in res
        assert "21520001" not in res
        assert "20521234" not in res

    # Test URLs & @mentions
    cases_url_mxh = [
        ("Xem tại https://www.facebook.com/groups/uit.confession", "[URL]"),
        ("Vào link bit.ly/abc xyz", "[URL]"),
        ("Follow @admin_uit trên mạng", "[MXH]"),
    ]
    for text, tag in cases_url_mxh:
        res = anonymize(text)
        assert tag in res

    # Test lecturer titles + names
    cases_gv = [
        ("Cảm ơn thầy Nguyễn Văn A rất nhiều", "thầy [GV]"),
        ("Cô Lê Thị Mai dạy dễ hiểu", "cô [GV]"),
        ("ThS. Trần Đình Trọng hướng dẫn", "ThS [GV]"),
        ("Giảng viên Phạm Đức C rất nhiệt tình", "giảng viên [GV]"),
    ]
    for text, expected in cases_gv:
        res = anonymize(text)
        assert expected.lower() in res.lower()
        for name_part in ("Nguyễn Văn A", "Lê Thị Mai", "Trần Đình Trọng", "Phạm Đức C"):
            if name_part in text:
                assert name_part not in res


def test_guard_hardstop_markers():
    class DummyDriver:
        def __init__(self, url="", source=""):
            self.current_url = url
            self.page_source = source

    # Normal page should not raise
    normal_driver = DummyDriver("https://www.facebook.com/uit.confession", "<html><body>Normal content</body></html>")
    check_blocked(normal_driver)

    # Checkpoint in URL
    cp_driver = DummyDriver("https://www.facebook.com/checkpoint/15000", "<html></html>")
    with pytest.raises(HardStop, match="url marker: checkpoint"):
        check_blocked(cp_driver)

    # Captcha in URL
    captcha_driver = DummyDriver("https://www.facebook.com/captcha/verify", "<html></html>")
    with pytest.raises(HardStop, match="url marker: captcha"):
        check_blocked(captcha_driver)

    # Blocked in text
    blocked_driver = DummyDriver("https://www.facebook.com/somepage", "Tài khoản của bạn đã bị hạn chế 180 ngày")
    with pytest.raises(HardStop, match="text marker"):
        check_blocked(blocked_driver)

    # Unusual activity text
    ua_driver = DummyDriver("https://www.facebook.com/somepage", "Chúng tôi phát hiện hoạt động bất thường")
    with pytest.raises(HardStop, match="text marker"):
        check_blocked(ua_driver)


def test_cooldown_file_management(tmp_path):
    cd_file = str(tmp_path / ".cooldown")
    assert cooldown_remaining(cd_file) is None

    # Set cooldown for 36 hours
    set_cooldown(cd_file, 36)
    rem = cooldown_remaining(cd_file)
    assert rem is not None
    assert rem.total_seconds() > 35 * 3600

    # Expired cooldown
    set_cooldown(cd_file, -1)
    assert cooldown_remaining(cd_file) is None


def test_aspect_tagger():
    aspects_cfg = C.load_aspects("configs/aspects.yaml")
    tagger = RuleTagger(aspects_cfg)

    # Relevance check
    assert tagger.is_relevant("Hôm nay trường UIT có thông báo mới")
    assert tagger.is_relevant("Học phí kỳ này tăng bao nhiêu?")
    assert not tagger.is_relevant("Ký túc xá khu B có cúp nước không?")
    assert not tagger.is_relevant("Hôm nay trời đẹp đi uống trà sữa")

    # Specific aspects
    assert "hoc_phi" in tagger.aspects("học phí kỳ này đóng ở đâu?")
    assert "chuong_trinh" in tagger.aspects("chương trình môn học này có bài tập lớn không?")
    assert "hanh_chinh" in tagger.aspects("phòng đào tạo daa xử lý đăng ký môn học")
    assert "giang_vien" in tagger.aspects("thầy cô dạy môn này rất nhiệt tình")
    assert "co_so_vat_chat" in tagger.aspects("wifi phòng học yếu quá")


def test_database_integrity(tmp_path):
    db_path = str(tmp_path / "test.sqlite")
    conn = connect(db_path)

    # Test primary key constraint on posts
    conn.execute(
        "INSERT INTO posts(post_id, text, round, status) VALUES (?, ?, ?, ?)",
        ("post_1", "Bài đăng 1", 1, "post_only")
    )
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO posts(post_id, text, round, status) VALUES (?, ?, ?, ?)",
            ("post_1", "Bài trùng", 1, "post_only")
        )

    # Test comments table
    conn.execute(
        "INSERT INTO comments(comment_id, post_id, text) VALUES (?, ?, ?)",
        ("c_1", "post_1", "Bình luận 1")
    )
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO comments(comment_id, post_id, text) VALUES (?, ?, ?)",
            ("c_1", "post_1", "Bình luận trùng")
        )

    # Test sessions and warnings
    conn.execute("INSERT INTO sessions(session_id, stage, n_new) VALUES (?, ?, ?)", ("s1", "discover", 10))
    conn.execute("INSERT INTO warnings(session_id, kind, last_action) VALUES (?, ?, ?)", ("s1", "warn", "scroll"))
    conn.commit()

    s = conn.execute("SELECT * FROM sessions WHERE session_id='s1'").fetchone()
    assert s["n_new"] == 10
    w = conn.execute("SELECT * FROM warnings WHERE session_id='s1'").fetchone()
    assert w["kind"] == "warn"

    comp = completeness(conn)
    assert len(comp) == 1
    assert comp.iloc[0]["round"] == 1
    assert comp.iloc[0]["n"] == 1

    conn.close()


def test_cli_full_workflow(tmp_path, monkeypatch):
    """Giả lập toàn bộ quy trình CLI tuần tự: init -> build -> sample -> kappa -> baseline -> analyze."""
    # 1. Tạo cấu hình test tùy chỉnh
    test_db = str(tmp_path / "raw.sqlite")
    clean_dir = str(tmp_path / "clean")
    labeled_dir = str(tmp_path / "labeled")
    cd_file = str(tmp_path / ".cooldown")

    cfg = C.load("configs/config.yaml")
    cfg["paths"]["raw_db"] = test_db
    cfg["paths"]["clean_dir"] = clean_dir
    cfg["paths"]["labeled_dir"] = labeled_dir
    cfg["paths"]["cooldown_file"] = cd_file
    cfg["start_date"] = "2024-01-01"
    cfg["end_date"] = "2024-12-31"

    test_cfg_path = str(tmp_path / "test_config.yaml")
    import yaml
    with open(test_cfg_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)

    from uitconf import cli

    # Bước 1: init
    monkeypatch.setattr("sys.argv", ["uitconf", "--config", test_cfg_path, "init"])
    cli.main()
    assert Path(test_db).exists()

    # Thêm dữ liệu giả lập vào DB
    conn = connect(test_db)
    for i in range(50):
        m = (i % 12) + 1
        conn.execute(
            "INSERT INTO posts(post_id, created_at, text, reactions, n_comments, bucket, round, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (f"post_{i}", f"2024-{m:02d}-10T12:00:00", f"Học phí UIT năm 2024 tăng cao quá thầy Nguyễn Văn {i} ơi SĐT 0912345678", i * 3, 5, i, (i % 3) + 1, "post_only")
        )
        conn.execute(
            "INSERT INTO comments(comment_id, post_id, parent_id, text, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"comm_{i}", f"post_{i}", None, f"Đồng ý với bài viết {i}, cơ sở vật chất cần cải thiện", f"2024-{m:02d}-10T12:30:00")
        )
    conn.commit()
    conn.close()

    # Bước 2: status
    monkeypatch.setattr("sys.argv", ["uitconf", "--config", test_cfg_path, "status"])
    cli.main()

    # Bước 3: build units
    monkeypatch.setattr("sys.argv", ["uitconf", "--config", test_cfg_path, "build"])
    cli.main()
    units_csv = Path(clean_dir) / "units.csv"
    assert units_csv.exists()
    df_units = pd.read_csv(units_csv)
    assert len(df_units) > 0
    # Đảm bảo ẩn danh SĐT và tên GV
    assert not df_units["text"].str.contains("0912345678").any()
    assert not df_units["text"].str.contains("Nguyễn Văn").any()
    assert (df_units["text"].str.contains(r"\[SDT\]")).any()

    # Bước 4: sample
    monkeypatch.setattr("sys.argv", ["uitconf", "--config", test_cfg_path, "sample", "--n", "30"])
    cli.main()
    ann_a = Path(labeled_dir) / "annotator_A.csv"
    ann_b = Path(labeled_dir) / "annotator_B.csv"
    assert ann_a.exists() and ann_b.exists()

    # Bước 5: Giả lập kết quả gán nhãn của 2 người và tính kappa
    df_a = pd.read_csv(ann_a)
    df_b = pd.read_csv(ann_b)
    # Gán nhãn mẫu
    df_a["label"] = ["tieu_cuc" if i % 2 == 0 else "tich_cuc" for i in range(len(df_a))]
    # Người B đồng ý 90%
    labels_b = []
    for i, row in df_b.iterrows():
        a_label = df_a.loc[df_a["unit_id"] == row["unit_id"], "label"].values[0]
        labels_b.append(a_label if i % 5 != 0 else "trung_tinh")
    df_b["label"] = labels_b

    df_a.to_csv(ann_a, index=False, encoding="utf-8-sig")
    df_b.to_csv(ann_b, index=False, encoding="utf-8-sig")

    monkeypatch.setattr("sys.argv", ["uitconf", "--config", test_cfg_path, "kappa", str(ann_a), str(ann_b)])
    cli.main()

    # Bước 6: Tạo gold.csv và chạy baseline cho 2 task (relevance & sentiment)
    gold_path = Path(labeled_dir) / "gold.csv"
    df_gold = df_a.copy()
    # Thêm các cột cần thiết cho baseline (created_at, text_norm) từ units.csv (month đã có sẵn trong df_a)
    df_gold = df_gold.merge(df_units[["unit_id", "post_id", "created_at", "text_norm", "aspects_rule"]], on="unit_id")
    df_gold.to_csv(gold_path, index=False, encoding="utf-8-sig")

    monkeypatch.setattr("sys.argv", ["uitconf", "--config", test_cfg_path, "baseline", "--gold", str(gold_path), "--task", "sentiment"])
    cli.main()
    assert (Path(labeled_dir) / "baseline_sentiment.json").exists()

    # Bước 7: Phân tích và biểu đồ (analyze)
    df_gold["pred"] = df_gold["label"]
    pred_path = Path(labeled_dir) / "predictions.csv"
    df_gold.to_csv(pred_path, index=False, encoding="utf-8-sig")

    monkeypatch.setattr("sys.argv", ["uitconf", "--config", test_cfg_path, "analyze", "--pred", str(pred_path)])
    cli.main()
    assert (Path(labeled_dir) / "prop_overall.csv").exists()
    assert (Path(labeled_dir) / "prop_by_month.csv").exists()
    assert (Path(labeled_dir) / "aspect_x_sentiment.csv").exists()
    assert (Path(labeled_dir) / "trend.png").exists()
