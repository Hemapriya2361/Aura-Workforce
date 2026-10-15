"""Write one CSV file per table into exports/.

    python -m scripts.export_csv

employees comes from the database. salary_structures and attendance have no tables
yet (Tasks 6 and 7), so they are copied from the master dataset until then.
"""
import shutil
from pathlib import Path

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.core.database import engine
from scripts.export_sheets import csv_path, ensure_csvs

EXPORT_DIR = Path(__file__).resolve().parent.parent / "exports"
DATASETS = ("employees", "salary_structures", "attendance")


def export_dataset(name: str, eng: Engine, out_dir: Path) -> tuple[int, str]:
    """Write out_dir/<name>.csv. Returns (rows, where the data came from)."""
    if name not in DATASETS:
        raise ValueError(f"Unknown dataset: {name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{name}.csv"

    if inspect(eng).has_table(name):
        # the name is checked against DATASETS above, so it is safe to put in the query
        df = pd.read_sql(text(f"SELECT * FROM {name} ORDER BY 1"), eng)
        df.to_csv(target, index=False, encoding="utf-8")
        return len(df), "database"

    ensure_csvs([name])
    shutil.copyfile(csv_path(name), target)
    return sum(1 for _ in open(target, encoding="utf-8")) - 1, "master dataset"


def main() -> None:
    for name in DATASETS:
        rows, source = export_dataset(name, engine, EXPORT_DIR)
        print(f"{name:<18} {rows:>8,} rows  ({source})  -> exports/{name}.csv")


if __name__ == "__main__":
    main()