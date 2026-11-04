"""Care units of a local MIMIC-IV installation and how the E6 ward definition classifies them.

    python3 sim2/e6_units.py --mimic-root ~/physionet/mimiciv/3.1

Run it next to credentialed data, like sim2/e6_mimic_cohort.py: it reads
hosp/transfers and icu/icustays and prints counts only, with counts under 10
suppressed. For every care unit with admit or transfer events: the number of
such events, the ICU stays that begin and end there (icustays.first_careunit
and last_careunit), the ICU stays begun per event (the share the cohort
script compares with ICU_UNIT_SHARE), and the class the cohort script gives
it (ward, excluded by name, or excluded as an ICU unit). If a query fails,
only the step and the exception type are printed, since DuckDB messages can
quote a data row.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e6_mimic_cohort import EXCLUDED_UNITS, ICU_UNIT_SHARE, SMALL_CELL, Steps, create_unit_tables, icu_units


def count(n):
    return f"<{SMALL_CELL}" if 0 < n < SMALL_CELL else f"{n:,}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mimic-root", required=True)
    parser.add_argument("--show-errors", action="store_true", help="full errors; for the open demo or the fixture only")
    args = parser.parse_args()
    import duckdb

    con = duckdb.connect()
    run = Steps(con)
    root = args.mimic_root
    excluded = "|".join(EXCLUDED_UNITS)
    try:
        create_unit_tables(run, root)
        icu = icu_units(run)
        rows = run("summary", f"""
            WITH t AS (SELECT careunit, count(*) AS n FROM tr GROUP BY careunit),
                 f AS (SELECT first_careunit AS careunit, count(*) AS n_first FROM icu GROUP BY 1),
                 l AS (SELECT last_careunit AS careunit, count(*) AS n_last FROM icu GROUP BY 1)
            SELECT t.careunit, t.n, coalesce(f.n_first, 0), coalesce(l.n_last, 0),
                   regexp_matches(lower(t.careunit), '({excluded})')
            FROM t LEFT JOIN f USING (careunit) LEFT JOIN l USING (careunit)
            ORDER BY t.n DESC""").fetchall()
    except Exception as exc:  # noqa: BLE001  report without quoting data
        if args.show_errors:
            raise
        print(f"failed at step '{run.current}' ({type(exc).__name__}); rerun with --show-errors only on open data",
              file=sys.stderr)
        sys.exit(1)
    print(f"ICU unit: ICU stays begin for at least {ICU_UNIT_SHARE:.0%} of the unit's admit and transfer events")
    print(f"{'care unit':48s} {'events':>9s} {'ICU first':>10s} {'ICU last':>9s} {'share':>7s}  class")
    for unit, n, n_first, n_last, by_name in rows:
        cls = "excluded by name" if by_name else ("excluded as ICU unit" if unit in icu else "ward")
        share = f"{n_first / n:.1%}" if n_first >= SMALL_CELL else ("0" if n_first == 0 else "small")
        print(f"{unit[:48]:48s} {count(n):>9s} {count(n_first):>10s} {count(n_last):>9s} {share:>7s}  {cls}")


if __name__ == "__main__":
    main()
