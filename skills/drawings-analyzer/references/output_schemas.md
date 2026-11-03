# Output Schemas — New Artefacts

The upgraded skill writes four new artefacts beyond the original three. This
file defines their schemas. Read it when generating each file.

All JSON is human-readable indented (`json.dump(..., indent=2)`). All
markdown uses Markdown-KV format for structured fields followed by prose
sections.

**Markdown-KV format**: a short block of `key: value` lines at the top of the
file (structured, machine-parseable), followed by a normal prose/markdown
body underneath. Example:

```markdown
tag: F10
discipline: structural
source_sheet: S-201
reliability: confirmed

## Notes
Isolated footing under column line C-3. Depth per soil report...
```

---

## 1. Concept Wiki (`references/concept_wiki/`)

**Not a single JSON file** — see `references/concept_wiki.md` for the full
design (Karpathy's LLM-wiki pattern: ingest/query/lint). One markdown page
per concept the drawing set warrants (e.g.
`references/concept_wiki/concrete-grades.md`), plus one
`references/concept_wiki/index.md` that lists all pages and carries the
standing conflict/lint register.

Each concept page uses Markdown-KV for its header, then prose with
`[[wikilinks]]` to related concept pages and inline source-sheet citations
on every fact:

```markdown
concept: concrete-grades
discipline: structural
reliability: confirmed
source_sheets: [S-002, S-201, S-305]

## Summary
Office slab specified at 32 MPa per [[reinforcement-and-mesh]] schedule
S-002. Plan callout on S-201 states 25 MPa for the same pour — see conflict
below.

## Conflicts
- 25 MPa (S-201 callout) vs 32 MPa (S-002 schedule) for the office slab.
  Unresolved — flagged in index.md and rfi_log.json.
```

`index.md` (one per project):

```markdown
project: <project name>
pages: [concrete-grades, reinforcement-and-mesh, cover-and-durability, slabs, footings, joints, subgrade-and-pavement, ...]
generated: 2026-07-11

## Conflicts / RFI register
- concrete-grades: office slab 25 MPa (S-201) vs 32 MPa (S-002) — unresolved
- reinforcement-and-mesh: slump-tolerance conflict between S-002 and S-210 — unresolved

## Stale / superseded notes
- (list anything a later revision replaced but an earlier sheet still shows)
```

## 2. RFI Log (`references/rfi_log.json`)

Structured, machine-queryable version of `coordination_issues.md` — same
findings, JSON form so they can be filtered/sorted or exported to an RFI
tracker.

```json
{
  "issues": [
    {
      "id": "RFI-001",
      "title": "Conflicting beam depth at gridline C-3",
      "tags_involved": ["B-2"],
      "sheets_involved": ["S-201", "S-305"],
      "description": "S-201 schedules B-2 at 500mm depth; S-305 detail shows 450mm.",
      "suggested_action": "Confirm actual depth with structural engineer before fabrication.",
      "status": "open",
      "reliability": "confirmed"
    }
  ]
}
```

## 3. Reliability Report (`references/reliability_report.md`)

A single rollup of how much of the extracted data is confirmed vs. inferred
vs. uncertain, so the user can see at a glance what needs manual
double-checking before relying on the database.

```markdown
total_facts: 342
confirmed: 298
inferred: 31
uncertain: 13
generated: 2026-07-11

## Items needing review
- instances.id=57 (tag "D-4", sheet M-110) — uncertain: gridline ref illegible on scan
- relationships.id=12 (DB-3 → AHU-2) — inferred: relation implied by proximity, not explicitly labeled
```

## 4. Manifest (`references/manifest.json`)

An index of every artefact produced for the project, so a future session (or
Claude in a new conversation) can see what already exists without re-scanning
the drawing set.

```json
{
  "project": "<project name>",
  "company": "<company short code>",
  "last_updated": "2026-07-11",
  "sheet_count": 48,
  "artefacts": {
    "database": "drawings.db",
    "per_sheet_markdown": "references/sheets/",
    "symbol_library": "references/symbol_library.md",
    "cross_reference": "references/cross_reference.md",
    "concept_wiki": "references/concept_wiki/",
    "rfi_log": "references/rfi_log.json",
    "reliability_report": "references/reliability_report.md"
  }
}
```
