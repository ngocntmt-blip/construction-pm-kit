---
name: drawings-analyzer
description: Turn a construction drawing set (structural, MEP, architectural — PDF or folder of PDFs) into a queryable structured database plus per-sheet markdown summaries, a symbol/legend library, a cross-reference graph, and a list of coordination issues/RFIs. Every extracted fact is tagged with a reliability score and traceable back to its source sheet. Use this skill whenever the user shares construction drawings and asks to "phân tích/review bản vẽ", "đọc bộ bản vẽ này", "build a database from these drawings", "extract the symbols/legend", "tìm xung đột / coordination issues", "có bao nhiêu X", "X nằm ở đâu", "cái gì chạy suốt tòa nhà", or generally wants to understand, query, or cross-check a drawing set (kết cấu, cơ điện MEP, kiến trúc). Not for full quantity takeoffs and not for one-off "what does this single sheet show" questions that don't need a persistent database.
---

# Drawings Analyzer

Turns a construction drawing set into durable, structured artifacts that any
follow-up question can be answered from cheaply — without re-reading every
PDF each time. Produces two complementary layers, then answers precise
questions by querying them.

## The eight learnings this skill is built on (evidence, not assertion)

Measured across structural + plumbing + electrical sets, 80+ blind-judged
questions:

1. **Structure beats images.** Never make the model count symbols or trace
   connections off a render — extract to structure, query that. (Vision is
   ~40–55% on symbol counting; the vector text layer is ~100% on text.)
2. **Hybrid > either alone.** Keep prose (contextual, self-correcting) AND
   the database (exact, queryable).
3. **Validate provenance at build time.** The DB's one failure mode is
   *silent extraction errors* — a value attributed to the wrong sheet.
   `validate_provenance.py` relocates mis-sourced rows. Took a test DB
   96.4%→100%, 0 hallucinations. Always run it.
4. **Entity-completeness.** Every component gets an entity/instance row even
   with null attributes; aggregate counts over the entity table, never the
   relationship table — and store `count` as an explicit integer, never
   inline notation like "F10 x2" (ambiguity caused a real miscount).
5. **The vector/raster fork decides feasibility.** A vector PDF with a real
   text layer → near-lossless structured extraction, no ML. A scanned OR
   outlined-text sheet (no text layer) → extraction gets nothing; it needs
   vision. `process_drawing.py` reports text density per sheet; **for sheets
   with no text layer, flag a placeholder — never fabricate.**
6. **Schedule = catalogue; tags = instances. Capture BOTH.** A schedule
   gives one row per TYPE; every tag on a plan carries an (x,y) in the text
   layer, so also extract one row per physical INSTANCE with coordinates.
   This is the IFC model and it answers counts/locations. Validated:
   coordinate-filtered instance counts matched a verified takeoff 14/14
   marks.
7. **Build a concept wiki for the notes/requirements (not just per-sheet).**
   The database holds the physical things; the concept wiki holds the
   rules/specs about them, regrouped BY CONCEPT across all sheets
   (`[[wikilinks]]` + source citations + a conflict/lint register) —
   Karpathy's LLM-wiki pattern. Reconcile-once at ingest beats
   gather-and-reconcile-under-pressure at query: blind A/B (same source,
   by-sheet vs by-concept) — concept wiki scored completeness 6/6 vs 5/6,
   correctness 6/6 vs 4.5/6, caught conflicts the per-sheet pass garbled,
   ~40% cheaper. See `references/concept_wiki.md`.
8. **Reliability score + qualitative context notes — add both.** Tag every
   fact HIGH (text) / MEDIUM (vision) / LOW (scaled) so the model hedges
   scaled values instead of stating them as fact; attach free-text
   `context_notes` from a vision gestalt pass ("the warehouse slab is the
   main concrete footprint, spanning ~the full grid"; "the west-wall waste
   main runs ~the full building length"). Use vision for gestalt, never for
   counts; pair each note with `what_to_verify`.

## Why both layers (prose + database)

Keep BOTH — do not drop either one to save time. They were A/B-validated
against each other and against raw images:

- Structure (the database) beats raw images on cost (~20×) and
  hallucination resistance.
- The prose layer is self-correcting and has caught database extraction
  errors that would otherwise go unnoticed.
- The database answers counts/locations/relationships that prose alone
  can't answer reliably.
- Reliability scores + context notes together lifted answer accuracy from
  9.5 to 14/16 and calibration from 9 to 15/16, with zero added
  hallucination.

## Before starting

0. **Read the profile first** (construction-pm-kit):
   `python3 "${CLAUDE_PLUGIN_ROOT}/skills/kit-start/scripts/profile_status.py" "<project root>"`
   — use the AI-context folder it reports; output language and date format follow
   the company profile (default Vietnamese, DD/MM/YYYY). No profile yet → still run,
   state "no company/project profile" at the top of `drawings.md`, suggest `kit-start`.
   This is a **Step 5 (context)** skill of `kit-start`: when done, tick it in
   `00_AI-CONTEXT/ONBOARDING.md` and add/update its row in the "Đọc gì trước?" table of `CLAUDE.md`.
1. **Confirm which project** this drawing set belongs to — keep artifacts
   for different projects in separate folders, never mixed.
2. **Confirm scope**: which discipline(s) are in the set — kết cấu
   (structural), cơ điện (MEP), kiến trúc (architectural), or a mix.
3. **Respond in Vietnamese by default**, matching the user's normal working
   language, unless the user is explicitly practicing English or asks for
   English output.

## Workflow

### Step 1 — Inventory the sheet set and build the index
List every PDF/sheet, its sheet number, title, discipline, and revision (from
the title block). Use the `pdf-reading` skill to inspect each file — prefer
extracting the **vector text layer** (the selectable text embedded under the
drawing, not an OCR/image guess) wherever the PDF has one; this is the most
reliable way to get 100%-accurate counts of tags/symbols. Fall back to
reading the rendered image only for scanned/raster sheets with no vector
layer. Flag any sheet with an unreadable or missing title block.

**If the set arrives as one merged PDF** (many sheets in a single file),
split it first: `scripts/split_drawings.py <merged.pdf> <out_dir> --png`.
It writes one PDF per sheet (named from the sheet number in the title
block when detectable, else `page_NNN.pdf`) plus an optional PNG preview,
into a folder separate from the original — never next to it, and the
source PDF is never modified. The detected sheet number is a best guess:
still read each title block and record the real number in `drawings.md`.
PNG previews are for looking, never for counting or measuring.

Write the inventory to `drawings.md` — a single top-level index of the whole
set (sheet no. → title → discipline → drawing type → revision → one-line
summary). This is the first thing to open in any later session or query, and
the map that Step 2's per-sheet files hang off of.

For each sheet, use `scripts/process_drawing.py <pdf_path>` to report text
density per page and decide the vector/raster fork: pages with a real text
layer extract near-losslessly from text; pages with little/no extractable
text (a scan, or outlined-text) need a vision pass instead — flag those as
placeholders (`references/placeholders` table), never fabricate a value for
them.

For each sheet, also classify its **drawing type** — see
`references/drawing_types.md` for the fixed taxonomy
(`general_arrangement`, `section_view`, `elevation`, `detail`,
`schedule_sheet`, or `other`). This is a judgement call based on reading the
rendered sheet, not pattern-matching the sheet number — drawing conventions
vary too much across offices/countries/disciplines for regex to be
reliable. The drawing type determines which prompt/approach to use when
extracting data from that sheet in Step 2 (e.g. a schedule sheet is read as
a table; a detail sheet is read for callouts and specs, not gridlines).

### Step 2 — Build the prose layer (per-sheet)
For each sheet, write a short markdown summary (`references/sheets/<sheet_no>.md`):
- What the sheet shows (plan/section/detail/schedule)
- Key components and their approximate locations/gridlines
- Notes, specs, and callouts worth remembering
- Any legend/symbol entries introduced on this sheet

Aggregate all symbols/legend entries across sheets into one
`references/symbol_library.md` (symbol → meaning → first-seen sheet).

Build a `references/cross_reference.md` mapping component tags/callouts to
every sheet that mentions them (detail bubbles, section cuts, schedule refs).

### Step 3 — Build the structured layer (SQLite database)
Run `scripts/init_db.py <project_folder>` to create `drawings.db` with the
generic schema in `references/schema.md` (schedules/instances/
relationships/notes) as the baseline.

For discipline-specific work (structural, plumbing, electrical, HVAC), use
the richer per-discipline tables in `references/schema_guidance.md` instead
— e.g. `footing_schedule` + `members` for structural, `fixtures` +
`connections` + `waste_routing` for plumbing, `boards` + `circuits` +
`luminaires` for electrical, `equipment` + `connections` for HVAC — plus the
universal `sheets`, `notes`, `relationships`, and `placeholders` tables.
Keep every listed item even if some attributes are null
(entity-completeness) — a missing footing is worse than a footing with
blank fields. Stage each instance using the template in
`references/instance_model_template.md` before committing it to the
database — it keeps extraction consistent across sheets and sessions.

Every row in every table carries:
- `source_sheet` (traceability)
- `reliability`/`confidence` — `confirmed` (explicit label, or read from a
  schedule/table on the drawing — schedules and counted tabular data are
  inherently higher-confidence than a manual read), `inferred` (reasoned
  from context, e.g. counted off a plan by eye), or `uncertain`
  (ambiguous/illegible)

When a schedule sheet or table is extractable as clean tabular data (e.g. via
the vector text layer), use the `data-analysis`/Python approach (pandas or
plain csv) to parse and count rather than reading it by eye — this is more
accurate for anything resembling a quantity takeoff of listed items (e.g.
"how many F10 footings are scheduled"). This skill still isn't for full
quantity takeoffs (see Notes below) — it's for counting/locating named
components the drawings already tag, not measuring/computing quantities not
given.

### Step 4 — Validate and flag issues
Run `scripts/validate_provenance.py <project_folder>` first — this catches
the database's main failure mode, silent extraction errors (a value
attributed to the wrong sheet, or an ambiguous inline count like "F10 x2"
that should be a clean tag + separate integer). Always run it before
trusting the database. Fix anything it flags, then:

Cross-check instances against schedules (does every instance have a matching
type?) and check for contradictions across sheets (same tag, different
spec/location). Write findings to `references/coordination_issues.md` —
each issue gets a short description, the conflicting sheets, and a suggested
RFI if the conflict can't be resolved from the drawings alone.

### Step 5 — Build the four extra artefacts
See `references/output_schemas.md` for exact schemas (JSON = `indent=2`,
markdown = Markdown-KV: key/value header block + prose body). Generate:

- `references/concept_wiki/` — a page per concept (`[[wikilinks]]` +
  source-sheet citations) plus one `index.md` carrying the standing
  conflict/lint register, NOT a single JSON file — see
  `references/concept_wiki.md` for the ingest/query/lint design and
  `references/output_schemas.md` for the exact page schema
- `references/rfi_log.json` — structured (JSON) version of
  `coordination_issues.md`, for filtering/exporting to an RFI tracker
- `references/reliability_report.md` — rollup counts of confirmed/inferred/
  uncertain facts, plus a list of items that need manual review
- `references/manifest.json` — index of every artefact produced, so a future
  session knows what already exists without re-scanning the drawings

### Step 6 — Answer questions
For follow-up questions ("có bao nhiêu móng F10", "X nằm ở đâu", "cái gì
chạy suốt trục A-A"), query `drawings.md` and the SQLite database first
(fast, structured). Only re-open the source PDF when the question needs
something not captured in the database (exact dimensions, areas, fine
print) — cite the sheet number when you do.

**Sanity-check every measurement or count against the whole.** Before
reporting a number, compare it to the overall scale of the project — e.g. if
a cable-tray run in one zone comes out longer than the building itself, or a
footing count exceeds the number of columns on the grid, that's a signal to
re-check rather than report. This catches extraction errors that a plausible
-looking single number wouldn't reveal on its own.

### Step 6b (optional) — Area of a zone/room/slab from the vector layer
Only when the user asks for an area ("diện tích kho / sàn / phòng X") and
the drawings give no area figure. Run on the single sheet that shows it:

`scripts/extract_polygons.py <sheet.pdf> --scale <N> [--label "TEXT"] [--check-dim <mm>]`

- `--scale` is the drawing scale denominator (1:100 → 100), read from the
  title block or scale bar — never assume it. If the sheet mixes scales,
  use the scale of the view the zone is in.
- `--label` keeps polygons that contain that text (room name/tag); the
  smallest one is usually the zone itself.
- `--check-dim` takes a known dimension in mm (e.g. a grid span) and
  reports the longest polygon edge at that scale — if they disagree, the
  scale is wrong; fix it before reporting anything.
- It removes near-duplicate outlines (same line drawn twice / on two
  layers) and says how many it dropped. Polygons nest (building outline
  contains rooms) — never sum them blindly.
- No polygons found = scanned sheet or an outline drawn as loose lines:
  say so, flag a placeholder, and point to the dimension strings or the
  CAD/BIM file. Never estimate area from the image.

Every area is **reliability = `inferred`** with `what_to_verify` = check
against the dimension strings. Report it as "≈ X m² (đo từ đường bao trên
bản vẽ <sheet>, tỷ lệ 1:N, cần đối chiếu kích thước ghi)". If stored, put
it in `notes` (or the discipline table) with `source_sheet` and
`reliability = inferred`. This is a check figure, not a contract quantity.

## Optional — validate extraction quality

If the user asks how confident to be in the extracted data, or after
finishing a large/complex set, run a spot-check using
`references/eval_protocol.md` — a small test-question set scored for
accuracy and calibration, ideally judged blind against the source PDFs.
Report results in plain terms (e.g. "14 of 16 correct, 2 flagged
uncertain"), not just a raw score.

## Notes

- **Ask object-first, not page-first.** Prefer "how many F10 footings are
  in the whole project, and where?" over "what's on sheet S-201?" — the
  whole point of the database is answering across the full set at once.
- This skill is for **understanding and querying** a drawing set, not for
  full quantity takeoffs (khối lượng) — those need a dedicated takeoff
  workflow.
- Keep reliability scores honest — mark anything read from a low-resolution
  scan or an ambiguous callout as `uncertain` rather than guessing.
- If the drawing set is revised, re-run Steps 1–4 for changed sheets only
  and note the revision date in each affected row.
- Simple text/lookup steps (reading a title block, listing sheets) don't
  need a lot of reasoning; save the deepest reasoning for genuinely hard
  visual interpretation — dense schedules, overlapping symbols, low-quality
  scans, or cross-sheet contradictions.
