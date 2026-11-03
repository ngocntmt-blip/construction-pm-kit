#!/usr/bin/env python3
"""
Validate provenance of every row in drawings.db (learning #3): the
database's one silent failure mode is a value attributed to the wrong
sheet. This script checks that every `source_sheet` value actually exists
in the `sheets` inventory table, flags orphaned/unknown references, and
flags obviously-wrong patterns (e.g. inline count notation like "F10 x2"
in a `tag` field instead of a clean tag + separate integer count).

Usage:
    python validate_provenance.py <project_folder>

Requires drawings.db (from init_db.py) with a `sheets` table populated —
see references/schema_guidance.md for the universal `sheets` table.
Prints a report; does not modify the database. Re-source or fix any row it
flags before trusting the database.
"""
import re
import sqlite3
import sys
from pathlib import Path

# Tables (beyond `sheets`) that carry a `source_sheet` column to check.
TABLES_WITH_SOURCE = [
    "schedules", "instances", "relationships", "notes",
    "footing_schedule", "members", "slabs", "grids", "levels",
    "fixtures", "connections", "waste_routing",
    "boards", "circuits", "luminaires",
    "equipment", "placeholders",
]

# Catches things like "F10 x2", "2x F10", "F10 (2)" in a tag field —
# ambiguous inline counts that should be a separate integer column instead.
INLINE_COUNT_PATTERN = re.compile(r"\bx\s*\d+\b|\b\d+\s*x\b|\(\s*\d+\s*\)", re.IGNORECASE)


def table_exists(conn, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def get_known_sheets(conn) -> set[str]:
    if not table_exists(conn, "sheets"):
        return set()
    rows = conn.execute("SELECT sheet_id FROM sheets").fetchall()
    return {str(r[0]) for r in rows}


def validate(conn) -> dict:
    known_sheets = get_known_sheets(conn)
    report = {"orphaned_source_sheet": [], "inline_count_suspects": [], "tables_checked": []}

    for table in TABLES_WITH_SOURCE:
        if not table_exists(conn, table):
            continue
        report["tables_checked"].append(table)
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table})")]
        if "source_sheet" not in cols:
            continue

        id_col = "id" if "id" in cols else cols[0]
        rows = conn.execute(f"SELECT {id_col}, source_sheet FROM {table}").fetchall()
        for row_id, source_sheet in rows:
            if known_sheets and (source_sheet is None or str(source_sheet) not in known_sheets):
                report["orphaned_source_sheet"].append({
                    "table": table, "row_id": row_id, "source_sheet": source_sheet,
                })

        if "tag" in cols:
            tag_rows = conn.execute(f"SELECT {id_col}, tag FROM {table}").fetchall()
            for row_id, tag in tag_rows:
                if tag and INLINE_COUNT_PATTERN.search(str(tag)):
                    report["inline_count_suspects"].append({
                        "table": table, "row_id": row_id, "tag": tag,
                    })

    return report


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_provenance.py <project_folder>")
        sys.exit(1)

    db_path = Path(sys.argv[1]) / "drawings.db"
    if not db_path.exists():
        print(f"No database found at {db_path}. Run init_db.py first.", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    report = validate(conn)
    conn.close()

    print(f"Checked tables: {', '.join(report['tables_checked']) or '(none found)'}")

    if report["orphaned_source_sheet"]:
        print(f"\n{len(report['orphaned_source_sheet'])} row(s) with unknown/missing source_sheet:")
        for item in report["orphaned_source_sheet"]:
            print(f"  - {item['table']} id={item['row_id']}: source_sheet={item['source_sheet']!r}")
        print("  -> Re-check these against the actual sheet before trusting them.")
    else:
        print("\nNo orphaned source_sheet references found.")

    if report["inline_count_suspects"]:
        print(f"\n{len(report['inline_count_suspects'])} tag(s) with suspected inline count notation:")
        for item in report["inline_count_suspects"]:
            print(f"  - {item['table']} id={item['row_id']}: tag={item['tag']!r}")
        print("  -> Split into a clean tag + a separate integer count column.")
    else:
        print("No inline-count-notation suspects found.")


if __name__ == "__main__":
    main()
