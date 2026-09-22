"""NASA CMAPSS FD001 — turbofan run-to-failure loader."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ingestion.paths import RAW_DIR, ensure_dirs, ingestion_metadata, new_batch_id

SOURCE_NAME = "cmapss_fd001"
# NASA Prognostics mirror (public zip used widely in PHM papers)
URL = "https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip"

COLUMN_NAMES = (
    ["unit_id", "cycle"]
    + [f"setting_{i}" for i in (1, 2, 3)]
    + [f"sensor_{i}" for i in range(1, 22)]
)

SENSOR_LABELS = {
    "sensor_1": "total_temp_fan_inlet_degR",
    "sensor_2": "total_temp_lpc_outlet_degR",
    "sensor_3": "total_temp_hpc_outlet_degR",
    "sensor_4": "total_temp_lpt_outlet_degR",
    "sensor_5": "pressure_fan_inlet_psia",
    "sensor_6": "total_pressure_bypass_duct_psia",
    "sensor_7": "total_pressure_hpc_outlet_psia",
    "sensor_8": "physical_fan_speed_rpm",
    "sensor_9": "physical_core_speed_rpm",
    "sensor_10": "engine_pressure_ratio_p50_p2",
    "sensor_11": "static_pressure_hpc_outlet_psia",
    "sensor_12": "ratio_fuel_flow_to_ps30_pps_psi",
    "sensor_13": "corrected_fan_speed_rpm",
    "sensor_14": "corrected_core_speed_rpm",
    "sensor_15": "bypass_ratio",
    "sensor_16": "burner_fuel_air_ratio",
    "sensor_17": "bleed_enthalpy",
    "sensor_18": "demanded_fan_speed_rpm",
    "sensor_19": "demanded_corrected_fan_speed_rpm",
    "sensor_20": "hpt_coolant_bleed_lbm_s",
    "sensor_21": "lpt_coolant_bleed_lbm_s",
}


def _download_from_nasa_zip(raw_dir: Path) -> tuple[Path, Path] | None:
    """Try the common PHM S3 zip; extract train/RUL FD001 files."""
    import urllib.request
    import zipfile

    zip_path = raw_dir / "cmapss.zip"
    try:
        urllib.request.urlretrieve(URL, zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            train_name = next(n for n in names if "train_FD001" in n)
            rul_name = next(n for n in names if "RUL_FD001" in n)
            train_path = raw_dir / "train_FD001.txt"
            rul_path = raw_dir / "RUL_FD001.txt"
            with zf.open(train_name) as src, open(train_path, "wb") as dst:
                dst.write(src.read())
            with zf.open(rul_name) as src, open(rul_path, "wb") as dst:
                dst.write(src.read())
        zip_path.unlink(missing_ok=True)
        return train_path, rul_path
    except Exception:
        return None


def _download_github_mirror(raw_dir: Path) -> tuple[Path, Path] | None:
    """Fallback: commit-pinned / stable raw mirrors of FD001 train + RUL."""
    import urllib.request

    bases = [
        (
            "https://huggingface.co/datasets/SoyVitou/NASA-C-MAPSS-Turbofan-Engine/resolve/main/data/train_FD001.txt",
            "https://huggingface.co/datasets/SoyVitou/NASA-C-MAPSS-Turbofan-Engine/resolve/main/data/RUL_FD001.txt",
        ),
        (
            "https://raw.githubusercontent.com/mapr-demos/predictive-maintenance/master/notebooks/jupyter/Dataset/CMAPSSData/train_FD001.txt",
            "https://raw.githubusercontent.com/mapr-demos/predictive-maintenance/master/notebooks/jupyter/Dataset/CMAPSSData/RUL_FD001.txt",
        ),
        (
            "https://raw.githubusercontent.com/edwardzjl/CMAPSSData/master/train_FD001.txt",
            "https://raw.githubusercontent.com/edwardzjl/CMAPSSData/master/RUL_FD001.txt",
        ),
    ]
    train_path = raw_dir / "train_FD001.txt"
    rul_path = raw_dir / "RUL_FD001.txt"
    for train_url, rul_url in bases:
        try:
            urllib.request.urlretrieve(train_url, train_path)
            urllib.request.urlretrieve(rul_url, rul_path)
            if train_path.stat().st_size > 1000:
                return train_path, rul_path
        except Exception:
            continue
    return None


def download(raw_dir: Path | None = None) -> tuple[Path, Path]:
    ensure_dirs()
    raw_dir = raw_dir or RAW_DIR
    train_path = raw_dir / "train_FD001.txt"
    rul_path = raw_dir / "RUL_FD001.txt"
    if train_path.exists() and rul_path.exists():
        return train_path, rul_path

    result = _download_from_nasa_zip(raw_dir) or _download_github_mirror(raw_dir)
    if result is None:
        raise RuntimeError("Could not download CMAPSS FD001 from known mirrors")
    return result


def load(raw_dir: Path | None = None) -> pd.DataFrame:
    train_path, _ = download(raw_dir)
    df = pd.read_csv(train_path, sep=r"\s+", header=None, names=COLUMN_NAMES)
    df = df.rename(columns=SENSOR_LABELS)
    # RUL for training = max cycle per unit - current cycle
    df["rul"] = df.groupby("unit_id")["cycle"].transform("max") - df["cycle"]
    df["failed"] = (df.groupby("unit_id")["cycle"].transform("max") == df["cycle"]).astype(int)
    return df


def load_bronze() -> pd.DataFrame:
    df = load()
    meta = ingestion_metadata(SOURCE_NAME, new_batch_id())
    for k, v in meta.items():
        df[k] = v
    return df


if __name__ == "__main__":
    frame = load_bronze()
    n_units = frame["unit_id"].nunique()
    print(f"{SOURCE_NAME}: {len(frame)} rows, {len(frame.columns)} cols, units={n_units}")
    print(frame.head(3).to_string())
