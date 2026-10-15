"""Turn sheets of the master workbook into CSV files, once.

Reading the Excel file is slow (the attendance sheet alone takes about 20 seconds),
so the seed reads these CSV files instead.

    python -m scripts.export_sheets                 # the sheets Task 4 needs
    python -m scripts.export_sheets roles holidays  # only the sheets you name
"""
import sys
from pathlib import Path

import pandas as pd

SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "seed"
WORKBOOK = SEED_DIR / "01_LedgerForge_Python_Master_Dataset.xlsx"
CSV_DIR = SEED_DIR / "csv"

DEFAULT_SHEETS = ["departments", "roles", "employees", "salary_structures", "attendance"]


def csv_path(sheet: str) -> Path:
    return CSV_DIR / f"{sheet}.csv"


def _is_current(sheet: str) -> bool:
    path = csv_path(sheet)
    return path.exists() and path.stat().st_mtime >= WORKBOOK.stat().st_mtime


def ensure_csvs(sheets: list[str]) -> None:
    """Create the CSV for each sheet if it is missing or older than the workbook."""
    missing = [s for s in sheets if not _is_current(s)]
    if not missing:
        return
    if not WORKBOOK.exists():
        raise FileNotFoundError(f"Master workbook not found: {WORKBOOK}")
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    workbook = pd.ExcelFile(WORKBOOK)
    for sheet in missing:
        # read everything as text so ids like EMP-0001 and values like 08:51 stay as they are
        df = workbook.parse(sheet, dtype=str, keep_default_na=False)
        # Excel keeps dates as date-times; we only want the date part
        df = df.replace(r" 00:00:00$", "", regex=True)
        df.to_csv(csv_path(sheet), index=False, encoding="utf-8")
        print(f"  {sheet}: {len(df):,} rows -> {csv_path(sheet).relative_to(SEED_DIR.parent.parent)}")


if __name__ == "__main__":
    ensure_csvs(sys.argv[1:] or DEFAULT_SHEETS)