"""AI4I 2020 Predictive Maintenance — UCI #601 loader."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ingestion.paths import RAW_DIR, ensure_dirs, ingestion_metadata, new_batch_id

SOURCE_NAME = "ai4i_2020"
URL = "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip"
CSV_FALLBACK = "https://archive.ics.uci.edu/ml/machine-learning-databases/00601/ai4i2020.csv"

COL_RENAME = {
    "UDI": "udi",
    "Product ID": "product_id",
    "Type": "product_type",
    "Air temperature [K]": "air_temperature_k",
    "Process temperature [K]": "process_temperature_k",
    "Rotational speed [rpm]": "rotational_speed_rpm",
    "Torque [Nm]": "torque_nm",
    "Tool wear [min]": "tool_wear_min",
    "Machine failure": "machine_failure",
    "TWF": "failure_twf",
    "HDF": "failure_hdf",
    "PWF": "failure_pwf",
    "OSF": "failure_osf",
    "RNF": "failure_rnf",
}


def download(raw_dir: Path | None = None) -> Path:
    """Download ai4i2020.csv into data/raw/ (idempotent)."""
    import urllib.request
    import zipfile

    ensure_dirs()
    raw_dir = raw_dir or RAW_DIR
    target = raw_dir / "ai4i2020.csv"
    if target.exists():
        return target

    zip_path = raw_dir / "ai4i2020.zip"
    try:
        urllib.request.urlretrieve(URL, zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
            with zf.open(name) as src, open(target, "wb") as dst:
                dst.write(src.read())
        zip_path.unlink(missing_ok=True)
    except Exception:
        urllib.request.urlretrieve(CSV_FALLBACK, target)
    return target


def load(csv_path: Path | None = None) -> pd.DataFrame:
    path = csv_path or download()
    df = pd.read_csv(path)
    df = df.rename(columns=COL_RENAME)
    return df


def load_bronze() -> pd.DataFrame:
    """Load with ingestion metadata columns (Bronze contract)."""
    df = load()
    meta = ingestion_metadata(SOURCE_NAME, new_batch_id())
    for k, v in meta.items():
        df[k] = v
    return df


if __name__ == "__main__":
    frame = load_bronze()
    print(f"{SOURCE_NAME}: {len(frame)} rows, {len(frame.columns)} cols")
    print(frame.head(3).to_string())
