"""Load a raw Upworthy CSV into DuckDB and build the clean tables."""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def load(dataset: str = "exploratory") -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    csv = ROOT / "data" / f"{dataset}.csv"
    con.execute(f"CREATE VIEW raw AS SELECT * FROM read_csv_auto('{csv}')")
    con.execute((ROOT / "sql" / "01_clean.sql").read_text())
    return con


if __name__ == "__main__":
    for ds in ["exploratory", "confirmatory"]:
        con = load(ds)
        print(f"\n== {ds} ==")
        print(con.sql("""
            SELECT
              (SELECT COUNT(*) FROM raw)                              AS raw_rows,
              (SELECT COUNT(*) FROM packages)                         AS packages,
              (SELECT COUNT(*) FROM arms)                             AS arms,
              (SELECT COUNT(DISTINCT test_id) FROM arms)              AS tests,
              (SELECT COUNT(DISTINCT test_id) FROM arms
                 WHERE bad_randomization)                             AS tests_bad_window,
              (SELECT COUNT(*) FROM headline_strata)                  AS headline_arms,
              (SELECT COUNT(DISTINCT test_id || image_id)
                 FROM headline_strata)                                AS headline_strata,
              (SELECT SUM(impressions) FROM arms)                     AS impressions
        """))
