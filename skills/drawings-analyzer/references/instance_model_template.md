# Instance Model Template

A standard Markdown-KV template for recording one component instance before
it goes into the database (Step 3). Using the same template for every
instance keeps extraction consistent across sheets, disciplines, and
sessions, and gives you a plain-text staging area you can review before
committing to SQLite.

## Generic template

```markdown
tag: <component tag as labeled on the sheet, e.g. "F10", "AHU-2">
discipline: <structural | plumbing | electrical | hvac | architectural>
entity_table: <target table, e.g. "members", "fixtures", "boards">
schedule_ref: <matching row in the type schedule, or "none found">
sheet_no: <sheet where this instance appears>
gridline_ref: <gridline/coordinate, e.g. "C-3", "col 5/B">
source_sheet: <same as sheet_no unless the spec came from a different sheet>
reliability: <confirmed | inferred | uncertain>

## Attributes
<discipline-specific fields — see schema_guidance.md for the field list per
entity table, e.g. members: category, section, span_or_location>

## Notes
<any qualitative context — condition, ambiguity, why reliability is what it
is, cross-references to other sheets>
```

## Discipline-specific attribute blocks

Fill the `## Attributes` section using the field names from
`schema_guidance.md` for the matching entity table, so the instance maps
directly onto a database row:

- **Structural** (`members`): `category`, `section`, `span_or_location`
- **Plumbing** (`fixtures` + `connections`): `fixture_class`, `manufacturer`,
  `model`, `schedule_name`; then per connection: `service`, `size`, `qty`
- **Electrical** (`circuits` + `luminaires`): `board_tag`, `circuit_no`,
  `load_desc`, `breaker`, `cable`; or `type`, `wattage`, `ip_rating`,
  `mounting`
- **HVAC** (`equipment` + `connections`): `type`, `capacity`; then per
  connection: `service`, `size`

## Entity-completeness rule

Create an instance entry for every occurrence you can see, even if some
attributes are unknown — use `null`/blank rather than skipping the entry
entirely. A missing row is worse than a row with gaps: it silently
undercounts, while a row with gaps is visibly incomplete and prompts a
follow-up check.

## Worked example

```markdown
tag: F10
discipline: structural
entity_table: members
schedule_ref: footing_schedule row "F10 — 1200x1200x400, 4 no. legs"
sheet_no: S-201
gridline_ref: C-3
source_sheet: S-201
reliability: confirmed

## Attributes
category: footing
section: 1200x1200x400
span_or_location: gridline C-3, ground floor

## Notes
Matches footing schedule on S-005 exactly. No conflicting reference found on
other sheets.
```
