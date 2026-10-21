import yaml
from pathlib import Path

def load(path="configs/config.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_aspects(path="configs/aspects.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_dirs(cfg):
    for k in ("clean_dir", "labeled_dir", "log_dir"):
        Path(cfg["paths"][k]).mkdir(parents=True, exist_ok=True)
    Path(cfg["paths"]["raw_db"]).parent.mkdir(parents=True, exist_ok=True)
