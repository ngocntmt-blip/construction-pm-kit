#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_sources.py — giu cho ho so / mirror khong lech voi tai lieu nguon.

Dung chung trong construction-pm-kit: kit-start (ho so cong ty _COMPANY/_PROFILE va
ho so du an) va cac skill mirror (thu muc AI-context cua du an).

    check <goc-du-an> <thu-muc-ai-context>
        So sha256 hien tai cua tung file nguon voi ban da ghim trong SOURCES.json.
        In bang: OK / STALE / MISSING_SOURCE / NOT_BUILT / UNPINNED.

    pin <goc-du-an> <thu-muc-ai-context> <mirror.md> <nguon1> [nguon2 ...]
        Ghim (hoac ghim lai) danh sach file nguon cua mot mirror vua dung xong.

    scan <goc-du-an> <thu-muc-ai-context> <folder-static1> [folder-static2 ...]
        Liet ke file trong cac folder STATIC moi hon lan ghim gan nhat va chua
        duoc mirror nao tham chieu -> tai lieu moi con bo sot.

Duong dan nguon ghi trong SOURCES.json luon la duong dan TUONG DOI so voi goc du an.
"""

import hashlib
import json
import os
import sys
from datetime import datetime

SOURCES = "SOURCES.json"
# File do skill khac so huu - kit-start khong ghim, chi bao ai la chu.
OWNED_BY = {
    "boq": "boq-mirror",
    "drawings": "drawings-analyzer",
    "scope-brief.md": "scope-brief",
    "specs-scan": "spec-mirror",
}
# File bat dau bang tien to nay cung do skill khac so huu (specs.md, specs-pp.md, specs-ee.md...)
OWNED_PREFIX = {"specs": "spec-mirror"}
SKIP_NAMES = {SOURCES, "README.md"}
SKIP_EXT = {".db", ".db-journal", ".json", ".csv", ".py", ".txt"}

# scan: chi quan tam tai lieu doc duoc. .dwg/.zip/.png/.bak khong mirror duoc.
DOC_EXT = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}
SKIP_DIRS = {"OLD", "SUPERSEDED", "CAD", "_BAK", "90_CLAUDE-OUTPUT"}
MAX_ROWS = 40


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def mtime(path):
    return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")


def load(aidir):
    p = os.path.join(aidir, SOURCES)
    if not os.path.exists(p):
        return {"generated_at": None, "mirrors": {}}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(aidir, data):
    data["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(aidir, SOURCES), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def owner_of(name):
    own = OWNED_BY.get(name.split("/")[0], OWNED_BY.get(name))
    if own:
        return own
    stem = os.path.splitext(name)[0].split("-")[0]
    return OWNED_PREFIX.get(stem)


def check_boq(root, aidir):
    """Doi chieu BOQ da chot (boq/CANONICAL.json) voi file that va voi ban da mirror.
    Day la cho sai dat nhat: mirror BOQ lech ban => moi trich dan 'BOQ dong NN' sai theo."""
    bdir = os.path.join(aidir, "boq")
    can_p, src_p = os.path.join(bdir, "CANONICAL.json"), os.path.join(bdir, "SOURCE.txt")
    if not os.path.exists(can_p):
        return []
    try:
        can = json.load(open(can_p, encoding="utf-8"))
        src = json.load(open(src_p, encoding="utf-8")) if os.path.exists(src_p) else {}
    except (ValueError, OSError) as e:
        return [("boq/CANONICAL.json", "LOI_DOC", str(e)[:60])]

    can_sha, mirror_sha = can.get("sha256"), src.get("source_sha256")
    if mirror_sha and can_sha and mirror_sha != can_sha:
        return [("boq/", "LECH_BAN", "mirror dung ban khac ban da chot -> chay lai `boq-mirror`")]

    rel = src.get("source_path")
    if not rel:
        return [("boq/", "?", "co CANONICAL.json nhung SOURCE.txt thieu source_path")]
    full = os.path.join(root, rel)
    if not os.path.exists(full):
        return [("boq/", "MISSING_SOURCE", "%s (doi ten/dời folder?)" % rel)]
    if sha256(full) != can_sha:
        return [("boq/", "STALE", "%s da bi sua -> chay lai `boq-mirror`" % rel)]
    return [("boq/", "OK", "khop BOQ da chot %s" % (can.get("decided_on") or ""))]


def cmd_check(root, aidir):
    data = load(aidir)
    mirrors = data.get("mirrors", {})
    rows = []

    for name, info in sorted(mirrors.items()):
        built = os.path.exists(os.path.join(aidir, name))
        if not built:
            rows.append((name, "NOT_BUILT", "co ghim nhung chua co file mirror"))
            continue
        bad = []
        for s in info.get("sources", []):
            full = os.path.join(root, s["path"])
            if not os.path.exists(full):
                bad.append(("MISSING_SOURCE", s["path"]))
            elif sha256(full) != s.get("sha256"):
                bad.append(("STALE", s["path"]))
        if not bad:
            n = len(info.get("sources", []))
            rows.append((name, "OK", "%d nguon khong doi" % n))
        else:
            for st, p in bad:
                rows.append((name, st, p))

    # mirror co tren dia nhung chua ghim
    for entry in sorted(os.listdir(aidir)):
        if entry in SKIP_NAMES or entry in mirrors:
            continue
        ext = os.path.splitext(entry)[1]
        if os.path.isfile(os.path.join(aidir, entry)) and ext in SKIP_EXT:
            continue
        own = owner_of(entry)
        if own == "boq-mirror":
            continue  # da co dong rieng tu check_boq()
        if own:
            rows.append((entry, "—", "do `%s` quan ly va tu ghim" % own))
        elif entry.endswith(".md"):
            rows.append((entry, "UNPINNED", "chua ghim nguon — dung lai roi `pin`"))

    rows.extend(check_boq(root, aidir))

    print("| Mirror | Trang thai | Ghi chu |")
    print("|---|---|---|")
    for name, st, note in rows:
        print("| `%s` | **%s** | %s |" % (name, st, note))

    todo = [r for r in rows if r[1] in ("STALE", "NOT_BUILT", "UNPINNED", "MISSING_SOURCE",
                                        "LECH_BAN", "LOI_DOC", "?")]
    print()
    if not todo:
        print("=> Tat ca mirror con dung. KHONG can index lai.")
    else:
        print("=> Can xu ly %d muc: %s" % (len(todo), ", ".join(sorted({r[0] for r in todo}))))
    print("Lan ghim gan nhat: %s" % (data.get("generated_at") or "chua co SOURCES.json"))
    return 0


def cmd_pin(root, aidir, mirror, srcs):
    data = load(aidir)
    entries = []
    for s in srcs:
        s = s.replace("\\", "/").lstrip("./")
        full = os.path.join(root, s)
        if not os.path.exists(full):
            print("LOI: khong thay file nguon: %s" % full, file=sys.stderr)
            return 2
        entries.append({"path": s, "sha256": sha256(full),
                        "mtime": mtime(full), "size": os.path.getsize(full)})
    data.setdefault("mirrors", {})[mirror] = {
        "pinned_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sources": entries,
    }
    save(aidir, data)
    print("Da ghim `%s` voi %d file nguon:" % (mirror, len(entries)))
    for e in entries:
        print("  - %s  (%s, sha %s…)" % (e["path"], e["mtime"], e["sha256"][:12]))
    return 0


def cmd_scan(root, aidir, folders):
    data = load(aidir)
    pinned = {s["path"] for m in data.get("mirrors", {}).values() for s in m.get("sources", [])}
    since = data.get("generated_at")
    basis = "lan ghim gan nhat"
    if not since:
        # chua co SOURCES.json -> lay mirror .md moi nhat lam moc, dung liet ke ca folder
        mds = [os.path.join(aidir, f) for f in os.listdir(aidir) if f.endswith(".md")]
        if mds:
            since = mtime(max(mds, key=os.path.getmtime))
            basis = "mirror moi nhat (chua co SOURCES.json)"
    since_ts = datetime.strptime(since, "%Y-%m-%d %H:%M:%S").timestamp() if since else 0

    found = []
    for folder in folders:
        base = os.path.join(root, folder)
        if not os.path.isdir(base):
            print("Bo qua (khong phai folder): %s" % folder, file=sys.stderr)
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d.upper() not in SKIP_DIRS]
            for fn in filenames:
                if fn.startswith("~$") or os.path.splitext(fn)[1].lower() not in DOC_EXT:
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, root).replace("\\", "/")
                if rel in pinned:
                    continue
                if os.path.getmtime(full) > since_ts:
                    found.append((mtime(full), rel))

    if not found:
        print("Khong co tai lieu STATIC nao moi hon %s (%s)." % (basis, since or "—"))
        return 0
    print("Tai lieu moi hon %s (%s), chua mirror nao tham chieu:" % (basis, since or "—"))
    print()
    print("| Sua luc | File |")
    print("|---|---|")
    found.sort(reverse=True)
    for ts, rel in found[:MAX_ROWS]:
        print("| %s | `%s` |" % (ts, rel))
    if len(found) > MAX_ROWS:
        print()
        print("... con %d file nua. Thu hep lai bang cach chay scan tren tung folder con." % (len(found) - MAX_ROWS))
    return 0


def main():
    a = sys.argv[1:]
    if len(a) < 3:
        print(__doc__)
        return 1
    cmd, root, aidir = a[0], a[1], a[2]
    if not os.path.isdir(aidir):
        print("LOI: khong thay thu muc AI-context: %s" % aidir, file=sys.stderr)
        return 2
    if cmd == "check":
        return cmd_check(root, aidir)
    if cmd == "pin":
        if len(a) < 5:
            print("Dung: pin <goc> <aidir> <mirror.md> <nguon1> [nguon2 ...]", file=sys.stderr)
            return 1
        return cmd_pin(root, aidir, a[3], a[4:])
    if cmd == "scan":
        return cmd_scan(root, aidir, a[3:] or ["."])
    print("Lenh khong hop le: %s" % cmd, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
