"""Download all Phase-1 datasets into data/raw/."""
from __future__ import annotations

from ingestion.sources import ai4i, cmapss, mfg004


def main() -> None:
    p1 = ai4i.download()
    print(f"AI4I: {p1}")
    train, rul = cmapss.download()
    print(f"CMAPSS: {train} | {rul}")
    p3 = mfg004.download()
    print(f"MFG004: {p3}")


if __name__ == "__main__":
    main()
