"""CLI: python -m uitconf.cli <lệnh>   (chạy từ thư mục gốc dự án, PYTHONPATH=src)"""
import argparse
import json
import sys
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

import pandas as pd

from . import config as C
from .db import connect


def _recent_session_gap_ok(conn, hours):
    r = conn.execute("SELECT MAX(started_at) m FROM sessions").fetchone()
    if not r or not r["m"]:
        return True, None
    wait = datetime.fromisoformat(r["m"]) + timedelta(hours=hours) - datetime.now()
    return wait.total_seconds() <= 0, wait


def _scrape_prechecks(cfg, conn):
    from .scraper.guard import cooldown_remaining
    cd = cooldown_remaining(cfg["paths"]["cooldown_file"])
    if cd:
        raise SystemExit(f"Đang trong thời gian nghỉ sau hard-stop, còn {cd}. Không chạy.")
    ok, wait = _recent_session_gap_ok(conn, cfg["session"]["min_gap_hours"])
    if not ok:
        raise SystemExit(f"Chưa đủ giãn cách giữa 2 phiên, còn {wait}.")


def _run_scrape(args, cfg, stage):
    from .scraper import crawler
    from .scraper.driver import make_driver
    from .scraper.guard import HardStop, set_cooldown
    from .scraper.timer import Throttle
    from .relevance import RuleTagger
    conn = connect(cfg["paths"]["raw_db"])
    _scrape_prechecks(cfg, conn)
    limit = cfg["session"]["warmup_max_posts"] if args.warmup else cfg["session"]["max_posts"]
    throttle = Throttle(cfg)
    driver = make_driver(cfg)
    try:
        ok, msg = crawler.health_check(driver, cfg)
        if not ok:
            raise SystemExit(f"Health-check selector THẤT BẠI: {msg}. Sửa configs/config.yaml rồi chạy lại.")
        if stage == "discover":
            n = crawler.discover(driver, conn, cfg, throttle, limit)
            print(f"Thu mới {n} bài.")
        else:
            tagger = RuleTagger(C.load_aspects())
            posts = crawler.select_posts_for_comments(conn, cfg, args.round, limit, tagger.is_relevant)
            n = crawler.collect_comments(driver, conn, cfg, throttle, posts)
            print(f"Thu {n} bình luận từ {len(posts)} bài.")
    except HardStop as e:
        conn.execute("INSERT INTO warnings(at,session_id,kind,last_action) VALUES(?,?,?,?)",
                     (datetime.now().isoformat(), "-", f"HARD_STOP:{e}", throttle.last_action))
        conn.commit()
        set_cooldown(cfg["paths"]["cooldown_file"], cfg["hard_stop_cooldown_hours"])
        print(f"!! HARD STOP ({e}). Nghỉ {cfg['hard_stop_cooldown_hours']}h. KHÔNG né captcha/đổi IP.")
    finally:
        driver.quit()
        conn.close()


def main():
    ap = argparse.ArgumentParser("uitconf")
    ap.add_argument("--config", default="configs/config.yaml")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("init")
    sp.add_parser("login")
    d = sp.add_parser("discover"); d.add_argument("--warmup", action="store_true")
    c = sp.add_parser("comments"); c.add_argument("--round", type=int, default=1); c.add_argument("--warmup", action="store_true")
    b = sp.add_parser("build"); b.add_argument("--ner", action="store_true"); b.add_argument("--segment", action="store_true")
    s = sp.add_parser("sample"); s.add_argument("--n", type=int, default=2000)
    k = sp.add_parser("kappa"); k.add_argument("a"); k.add_argument("b"); k.add_argument("--col", default="label")
    m = sp.add_parser("baseline"); m.add_argument("--gold", default="data/labeled/gold.csv"); m.add_argument("--task", choices=["relevance", "sentiment"], default="sentiment")
    f = sp.add_parser("finetune"); f.add_argument("--gold", default="data/labeled/gold.csv"); f.add_argument("--model", choices=["phobert", "visobert"], default="visobert"); f.add_argument("--task", choices=["relevance", "sentiment"], default="sentiment")
    a = sp.add_parser("analyze"); a.add_argument("--pred", default="data/labeled/predictions.csv")
    sp.add_parser("status")
    args = ap.parse_args()
    cfg = C.load(args.config)
    C.ensure_dirs(cfg)

    if args.cmd == "init":
        connect(cfg["paths"]["raw_db"]).close(); print("Đã tạo DB:", cfg["paths"]["raw_db"])
    elif args.cmd == "login":
        from .scraper.driver import make_driver, manual_login
        dr = make_driver(cfg); manual_login(dr); dr.quit()
    elif args.cmd == "discover":
        _run_scrape(args, cfg, "discover")
    elif args.cmd == "comments":
        _run_scrape(args, cfg, "comments")
    elif args.cmd == "status":
        from .analysis import completeness
        conn = connect(cfg["paths"]["raw_db"])
        print(completeness(conn).to_string(index=False))
        print(pd.read_sql("SELECT * FROM warnings ORDER BY id DESC LIMIT 10", conn).to_string(index=False))
    elif args.cmd == "build":
        from .build_units import build
        conn = connect(cfg["paths"]["raw_db"])
        df = build(conn, C.load_aspects(), f"{cfg['paths']['clean_dir']}/units.csv", args.ner, args.segment,
               cfg["start_date"], cfg["end_date"])
        print("units:", len(df))
    elif args.cmd == "sample":
        from .labeling import export_batches, stratified_sample
        df = pd.read_csv(f"{cfg['paths']['clean_dir']}/units.csv")
        export_batches(stratified_sample(df, args.n), cfg["paths"]["labeled_dir"])
        print("Đã xuất annotator_A.csv / annotator_B.csv")
    elif args.cmd == "kappa":
        from .labeling import kappa
        kv, n, dis = kappa(args.a, args.b, args.col)
        print(f"kappa={kv:.3f} (n={n})"); print(dis.head(30).to_string(index=False))
    elif args.cmd in ("baseline", "finetune"):
        from .models.splits import make_splits
        gold = pd.read_csv(args.gold)
        if args.task == "relevance":
            gold["y"] = (gold["label"] != "khong_lien_quan").map({True: "lien_quan", False: "khong_lien_quan"})
        else:
            gold = gold[gold["label"].isin(["tieu_cuc", "trung_tinh", "tich_cuc", "hoi_dap"])].copy(); gold["y"] = gold["label"]
        sc = cfg["split"]
        tr, va, te = make_splits(gold, sc["test_time_fraction"], sc["val_group_fraction"], sc["seed"])
        if args.cmd == "baseline":
            from .models import baseline
            _, _, res = baseline.run(tr, va, te, label_col="y", out_json=f"{cfg['paths']['labeled_dir']}/baseline_{args.task}.json")
            print({k: round(v["macro_f1"], 4) for k, v in res.items()})
        else:
            from .models import finetune
            col = "text_seg" if args.model == "phobert" else "text_norm"
            print(finetune.run(tr, va, te, args.model, sorted(gold["y"].unique()), col, "y"))
    elif args.cmd == "analyze":
        from .analysis import aspect_table, plot_trend, proportions
        df = pd.read_csv(args.pred)           # cần cột: pred, month, aspects_rule, ...
        out = cfg["paths"]["labeled_dir"]
        proportions(df).to_csv(f"{out}/prop_overall.csv", index=False)
        proportions(df, groups="month").to_csv(f"{out}/prop_by_month.csv", index=False)
        aspect_table(df).to_csv(f"{out}/aspect_x_sentiment.csv")
        plot_trend(df, path=f"{out}/trend.png")
        print("Đã xuất bảng + biểu đồ vào", out, "— nhớ ghi: 'trong dữ liệu confession'.")


if __name__ == "__main__":
    main()
