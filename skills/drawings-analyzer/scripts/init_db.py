#!/usr/bin/env python3
"""
Initialize the drawings.db SQLite database for the drawings-analyzer skill.

Usage:
    python init_db.py <project_folder>

Creates <project_folder>/drawings.db with the schema described in
references/schema.md (schedules, instances, relationships, notes).
Safe to re-run — uses CREATE TABLE IF NOT EXISTS.
"""
import sqlite3
import sys
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT NOT NULL,
    discipline TEXT,
    description TEXT,
    spec TEXT,
    source_sheet TEXT,
    reliability TEXT CHECK(reliability IN ('confirmed','inferred','uncertain'))
);

CREATE TABLE IF NOT EXISTS instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER,
    tag TEXT NOT NULL,
    gridline_ref TEXT,
    sheet_no TEXT,
    coordinates TEXT,
    source_sheet TEXT,
    reliability TEXT CHECK(reliability IN ('confirmed','inferred','uncertain')),
    FOREIGN KEY(schedule_id) REFERENCES schedules(id)
);

CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_tag TEXT NOT NULL,
    to_tag TEXT NOT NULL,
    relation_type TEXT,
    source_sheet TEXT,
    reliability TEXT CHECK(reliability IN ('confirmed','inferred','uncertain'))
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT,
    note TEXT,
    source_sheet TEXT,
    reliability TEXT CHECK(reliability IN ('confirmed','inferred','uncertain'))
);

CREATE INDEX IF NOT EXISTS idx_instances_tag ON instances(tag);
CREATE INDEX IF NOT EXISTS idx_schedules_tag ON schedules(tag);
CREATE INDEX IF NOT EXISTS idx_rel_from ON relationships(from_tag);
CREATE INDEX IF NOT EXISTS idx_rel_to ON relationships(to_tag);
"""

def main():
    if len(sys.argv) != 2:
        print("Usage: python init_db.py <project_folder>")
        sys.exit(1)

    project_folder = Path(sys.argv[1])
    project_folder.mkdir(parents=True, exist_ok=True)
    db_path = project_folder / "drawings.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

    print(f"Database ready at {db_path}")

if __name__ == "__main__":
    main()
