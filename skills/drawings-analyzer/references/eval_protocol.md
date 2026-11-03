# Eval Protocol — validating extraction quality

How to check that the database + prose layers actually answer questions
correctly before relying on them, and how the A/B numbers cited in
"Why both layers" (SKILL.md) were produced. Use this whenever you want to
sanity-check a freshly-built drawing database, or when the user asks "how
confident are you in this data?"

## Test question set

Draw ~15–20 questions from the actual drawing set, spanning:
- **counts** — "how many X are there" (answerable from `instances`/entity
  tables)
- **locations** — "where is X" (gridline/coordinate lookup)
- **relationships** — "what feeds/connects to X" (relationship lookup)
- **cross-checks** — "does the schedule match the plan" (should surface any
  real coordination issues, not invent new ones)
- **specs** — "what's the spec/size of X" (schedule or wiki lookup)

Mix easy (single schedule lookup) and hard (requires combining two tables,
or a contradiction the model has to notice) questions.

## Scoring two dimensions

1. **Accuracy** — is the answer factually correct against the source
   drawings? Score each question right/wrong (or partial), not a vague
   impression — tally out of the total question count (e.g. 14/16).
2. **Calibration** — when the model expresses confidence (via the
   `reliability` field or in its answer), does that confidence match
   reality? A model that says "uncertain" on things that turn out wrong, and
   "confirmed" on things that turn out right, is well-calibrated even if a
   few answers are wrong. Penalize confident-and-wrong more than
   honest-and-uncertain.

## Blind judging

Where possible, have a separate pass (a fresh read of the question + answer,
without seeing which extraction method produced it) grade the answer against
the source PDF directly — this avoids the grader being anchored by knowing
"this came from the database, it must be trustworthy."

## Comparing approaches

If evaluating whether to trust the structured layer vs. the prose layer vs.
raw image re-reading for a given question type, run the same question
through each and compare: which one got it right, and did adding reliability
scores + context notes change the outcome. This is how the structure vs.
image cost/accuracy tradeoff in "Why both layers" was established — don't
assume it holds for every drawing set without spot-checking on this one too,
especially if the set has unusually poor scan quality or an unfamiliar
drafting convention.

## What to do with results

- If accuracy is low on a specific question type (e.g. relationships), that
  usually means Step 3 needs another pass on that entity table, not that the
  whole database should be discarded.
- If calibration is poor (confident answers turning out wrong), tighten the
  reliability criteria in Step 3 rather than lowering trust in the whole
  system.
- Report the score to the user in plain terms — "14 of 16 test questions
  were correct, 2 flagged as uncertain and worth double-checking" — not just
  a percentage.
