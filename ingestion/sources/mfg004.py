"""MFG-004 Quality Control sample — Hugging Face loader."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ingestion.paths import RAW_DIR, ensure_dirs, ingestion_metadata, new_batch_id

SOURCE_NAME = "mfg004_quality"
REPO = "xpertsystems/mfg004-sample"
FILE = "mfg004_inspection_records.csv"
RAW_NAME = "mfg004_inspection_records.csv"


def download(raw_dir: Path | None = None) -> Path:
    ensure_dirs()
    raw_dir = raw_dir or RAW_DIR
    target = raw_dir / RAW_NAME
    if target.exists():
        return target

    try:
        from huggingface_hub import hf_hub_download

        path = hf_hub_download(repo_id=REPO, filename=FILE, repo_type="dataset")
        target.write_bytes(Path(path).read_bytes())
        return target
    except Exception:
        # Fallback: direct resolve URL
        import urllib.request

        url = f"https://huggingface.co/datasets/{REPO}/resolve/main/{FILE}"
        urllib.request.urlretrieve(url, target)
        return target


def load(csv_path: Path | None = None) -> pd.DataFrame:
    path = csv_path or download()
    return pd.read_csv(path)


def load_bronze() -> pd.DataFrame:
    df = load()
    meta = ingestion_metadata(SOURCE_NAME, new_batch_id())
    for k, v in meta.items():
        df[k] = v
    return df


if __name__ == "__main__":
    frame = load_bronze()
    print(f"{SOURCE_NAME}: {len(frame)} rows, {len(frame.columns)} cols")
    print(list(frame.columns)[:30])
    print(frame.head(2).to_string())
