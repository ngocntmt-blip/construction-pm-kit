---
name: context-file-audit
description: Audit a project context file (CLAUDE.md, instruction.md, AGENTS.md) against what the folder actually contains, and slim it down. Use when the user says "check CLAUDE.md", "CLAUDE.md is out of date / too long", "what's changed this week", "rà lại CLAUDE.md", "file này dài quá", or after a folder restructure. Not for writing a context file from scratch.
---

# Audit and slim a project context file

A context file is read at the start of every session, so every line costs tokens forever.
Stale lines cost more than missing ones: they get trusted instead of checked.

## The test

Keep a line only if **`ls` can't tell you** and it **won't be false next week**.

That splits the file in two:

- **Rules** — where a new file of type X goes, which of five similar files is authoritative,
  naming conventions, who the counterparty is. Not derivable. Stable for months. **Keep.**
- **State** — folder trees, file lists, revision numbers, counts, what's outstanding.
  Derivable in one command. Changes weekly. **Move out or delete.**

## 1. Measure (write code — do not eyeball)

```python
import os, re
P = 'CLAUDE.md'          # or instruction.md / AGENTS.md
t = open(P, encoding='utf-8').read(); mt = os.path.getmtime(P)

# a) dead paths the file still claims
for p in sorted(set(re.findall(r'`([^`\n]+[\\/][^`\n]+)`', t))):
    if not os.path.exists(p.rstrip('\\/').replace('\\', '/')):
        print('DEAD', p)

# b) what changed since the file was last written
for r, d, f in os.walk('.'):
    d[:] = [x for x in d if not x.startswith('.')]
    for n in f:
        q = os.path.join(r, n)
        if os.path.getmtime(q) > mt: print('NEW ', q)

# c) cost per section, to aim the cuts
for s in re.split(r'^## ', t, flags=re.M):
    if s.strip(): print(f'{len(s):>7}  {s.splitlines()[0][:50]}')
```

Also list the top-level folders and compare against the file's tree. New folders the file
never mentions are as important as dead paths.

## 2. Report in three buckets

1. **Now wrong** — dead paths, superseded revisions, claims contradicted by the folder.
   Lead with anything whose failure destroys work or sends a bad document out.
2. **Outgrown** — still true, no longer earns its place: resolved items, struck-through text,
   sections describing an earlier project phase.
3. **Repeated but unwritten** — rules you keep applying from memory or correction that the
   file never states. Check project memory and recent session history for these; they are
   the highest-value additions and the easiest to miss.

Report findings and **stop**. Do not rewrite a context file unasked.

## 3. Slimming, once approved

- **Delete struck-through text entirely.** It is history for a human reader; history lives in
  the worklog.
- **Replace the folder tree with a traps list.** Not "here is the structure" but *"here is where
  you'd guess wrong"* — the authoritative file among near-duplicates, folders whose name
  misleads, files that moved. Usually ~10 lines replacing ~150.
- **Move volatile state out** to the top of the worklog, newest first.
- **Cut rules that duplicate the project/global instructions.** Those load automatically.
  Keep only what is specific to *these files*.
- **Keep every save-location rule.** Where a new file goes is never derivable, and getting it
  wrong loses the file. This is the floor.
- **Keep exceptions attached to their rule.** A rule flattened to its general case is how
  in-scope items get dropped.

## Verify before handing back

Re-run step 1 against the rewritten file: zero dead paths, and every rule from the original
still present or deliberately relocated. State where each removed rule went.

## Keep it from re-bloating

> The context file changes when a **rule** changes, not when a **file** changes.

If it ever needs editing because something moved, that content belonged elsewhere.
