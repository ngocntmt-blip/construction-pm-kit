# Drawings Database Schema

SQLite database created by `scripts/init_db.py`. Four core tables, all
sharing the same traceability/reliability columns.

## schedules
Type catalogue — one row per component *type* (not per instance).

| column        | type | notes                                          |
|---------------|------|-------------------------------------------------|
| id            | INTEGER PK | |
| tag           | TEXT | e.g. "F10", "B-2", "AHU-2"                     |
| discipline    | TEXT | structural / mep / architectural               |
| description   | TEXT | short spec description                         |
| spec          | TEXT | size/material/rating, free text                |
| source_sheet  | TEXT | sheet number this was read from                |
| reliability   | TEXT | confirmed / inferred / uncertain               |

## instances
One row per physical occurrence of a component.

| column        | type | notes                                          |
|---------------|------|-------------------------------------------------|
| id            | INTEGER PK | |
| schedule_id   | INTEGER FK -> schedules.id | nullable if type unknown |
| tag           | TEXT | as-labeled on the sheet                        |
| gridline_ref  | TEXT | e.g. "A-3", "col line 5/C"                     |
| sheet_no      | TEXT | plan sheet where it appears                     |
| coordinates   | TEXT | optional x,y or IFC-style ref if available     |
| source_sheet  | TEXT | |
| reliability   | TEXT | confirmed / inferred / uncertain               |

## relationships
Stated connections between two tags (electrical circuits, piping runs,
structural load paths, etc).

| column        | type | notes                                          |
|---------------|------|-------------------------------------------------|
| id            | INTEGER PK | |
| from_tag      | TEXT | |
| to_tag        | TEXT | |
| relation_type | TEXT | e.g. "feeds", "supports", "connects_to"        |
| source_sheet  | TEXT | |
| reliability   | TEXT | confirmed / inferred / uncertain               |

## notes
Free-text observations that don't fit the structured tables.

| column        | type | notes                                          |
|---------------|------|-------------------------------------------------|
| id            | INTEGER PK | |
| tag           | TEXT | related component, nullable                     |
| note          | TEXT | |
| source_sheet  | TEXT | |
| reliability   | TEXT | confirmed / inferred / uncertain               |

## Query examples

```sql
-- How many F10 footings, and where?
SELECT tag, gridline_ref, sheet_no FROM instances WHERE tag = 'F10';

-- What feeds AHU-2?
SELECT from_tag FROM relationships WHERE to_tag = 'AHU-2' AND relation_type = 'feeds';

-- Any uncertain data worth double-checking?
SELECT * FROM instances WHERE reliability = 'uncertain';
```
