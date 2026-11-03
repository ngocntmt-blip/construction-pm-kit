#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
profile_status.py — Bước 0 (cổng hồ sơ) của mọi skill trong construction-pm-kit.

    python3 profile_status.py <gốc dự án>                 # kiểm hồ sơ dự án + công ty
    python3 profile_status.py --company <…/_COMPANY/_PROFILE> # chỉ kiểm hồ sơ công ty
    thêm --json để lấy kết quả máy-đọc

Báo: thư mục AI-context nào, file hồ sơ nào có / thiếu, đã được người dùng xác
nhận chưa, nguồn nào đã đổi (STALE) so với lần ghim trong SOURCES.json, và
VERDICT cho hai nhóm skill:
  read  — skill đọc/mirror (boq, spec, drawings, scope, audit)
  issue — skill tạo văn bản gởi ra ngoài (doc-from-template)

Không sửa gì trên đĩa.
"""
import hashlib
import json
import os
import sys

AI_CANDIDATES = ["00_AI-CONTEXT", "0.ai-context", "00-AI-CONTEXT", "0_AI-CONTEXT",
                 "ai-context", "AI-CONTEXT"]
COMPANY_FILES = ["company.md", "templates.md", "procedures.md", "profile.json"]
PROJECT_FILES = ["project.md", "parties.md", "doc-control.md", "contract.md", "project.json"]
MIRRORS = {"boq": "boq-mirror", "specs.md": "spec-mirror", "drawings": "drawings-analyzer",
           "scope-brief.md": "scope-brief"}
# Bước 5 (bắt buộc): tài liệu nào có mặt thì mirror tương ứng phải có và không cũ hơn nguồn.
# (mirror, skill, folder nguồn, đuôi file, folder con bỏ qua)
CONTEXT_RULES = [
    ("boq", "boq-mirror", "01_CONTRACT-BOQ", {".xlsx", ".xlsm", ".xls"}, {"SUPERSEDED"}),
    ("specs.md", "spec-mirror", "03_SPECIFICATION", {".pdf"}, {"SUPERSEDED"}),
    ("drawings", "drawings-analyzer", "02_DRAWINGS", {".pdf"},
     {"SUPERSEDED", "SHOP-DRAWING", "AS-BUILT"}),
]
SKIP_FILES_PREFIX = ("~$", "_README")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, None
    except (ValueError, OSError) as e:
        return None, str(e)[:80]


def stale_sources(folder, root):
    """Trả về list (mirror, trạng thái, đường dẫn) cho nguồn đã đổi/mất."""
    data, err = load_json(os.path.join(folder, "SOURCES.json"))
    if err:
        return [("SOURCES.json", "LOI_DOC", err)]
    if not data:
        return [("SOURCES.json", "CHUA_GHIM", "chưa ghim nguồn — không biết hồ sơ đã cũ chưa")]
    out = []
    for name, info in data.get("mirrors", {}).items():
        for s in info.get("sources", []):
            p = s["path"]
            full = p if os.path.isabs(p) else os.path.join(root, p)
            if not os.path.exists(full):
                out.append((name, "MISSING_SOURCE", p))
            elif sha256(full) != s.get("sha256"):
                out.append((name, "STALE", p))
    return out


def find_ai(root):
    found = [d for d in AI_CANDIDATES if os.path.isdir(os.path.join(root, d))]
    # Windows không phân biệt hoa thường -> bỏ trùng
    seen, uniq = set(), []
    for d in found:
        k = os.path.realpath(os.path.join(root, d)).lower()
        if k not in seen:
            seen.add(k)
            uniq.append(d)
    return uniq


def source_files(folder, exts, skip):
    out = []
    for dp, dns, fns in os.walk(folder):
        dns[:] = [d for d in dns if d.upper() not in skip and not d.startswith(".")]
        for fn in fns:
            if fn.startswith(SKIP_FILES_PREFIX):
                continue
            if os.path.splitext(fn)[1].lower() in exts:
                out.append(os.path.join(dp, fn))
    return out


def mirror_path(aidir, name):
    """specs.md có thể là specs-<bộ môn>.md; drawings có thể là drawings.md trỏ vào drawings/."""
    p = os.path.join(aidir, name)
    if os.path.exists(p):
        return p
    if name == "specs.md":
        cands = [os.path.join(aidir, f) for f in os.listdir(aidir)
                 if f.startswith("specs") and f.endswith(".md")]
        return max(cands, key=os.path.getmtime) if cands else None
    return None


def newest_mtime(path):
    if os.path.isfile(path):
        return os.path.getmtime(path)
    ts = [os.path.getmtime(os.path.join(dp, f)) for dp, _, fs in os.walk(path) for f in fs]
    return max(ts) if ts else os.path.getmtime(path)


def check_context(root, aidir):
    """→ list dict: mirror, skill, trạng thái (OK / MISSING / OUTDATED / NO_SOURCE), số file nguồn."""
    rows = []
    for name, skill, folder, exts, skip in CONTEXT_RULES:
        src = source_files(os.path.join(root, folder), exts, skip) if os.path.isdir(
            os.path.join(root, folder)) else []
        mp = mirror_path(aidir, name) if aidir else None
        if not src:
            st = "NO_SOURCE"
        elif not mp:
            st = "MISSING"
        elif max(os.path.getmtime(s) for s in src) > newest_mtime(mp):
            st = "OUTDATED"
        else:
            st = "OK"
        rows.append({"mirror": name, "skill": skill, "status": st, "sources": len(src),
                     "folder": folder})
    return rows


def check_company(cdir):
    res = {"path": cdir, "exists": os.path.isdir(cdir), "files": {}, "confirmed": None,
           "open_questions": [], "stale": [], "errors": []}
    if not res["exists"]:
        return res
    for f in COMPANY_FILES:
        res["files"][f] = os.path.exists(os.path.join(cdir, f))
    prof, err = load_json(os.path.join(cdir, "profile.json"))
    if err:
        res["errors"].append("profile.json: " + err)
    if prof:
        st = prof.get("status", {})
        res["confirmed"] = st.get("confirmed_by_user")
        res["open_questions"] = st.get("open_questions", [])
        res["company"] = prof.get("company", {}).get("legal_name") or \
            prof.get("company", {}).get("short_code")
        res["templates"] = len(prof.get("templates", []))
        res["procedures"] = len(prof.get("procedures", []))
    # nguồn hồ sơ công ty ghim tương đối với _COMPANY (thư mục cha của _PROFILE)
    res["stale"] = stale_sources(cdir, os.path.dirname(cdir))
    return res


def check_project(root):
    res = {"root": root, "ai_context": None, "files": {}, "mirrors": {}, "confirmed": None,
           "open_questions": [], "stale": [], "errors": [], "company_profile": None}
    ai = find_ai(root)
    if len(ai) > 1:
        res["errors"].append("có %d thư mục AI-context: %s — hỏi người dùng giữ cái nào"
                             % (len(ai), ", ".join(ai)))
    if not ai:
        return res
    res["ai_context"] = ai[0]
    aidir = os.path.join(root, ai[0])
    for f in PROJECT_FILES:
        res["files"][f] = os.path.exists(os.path.join(aidir, f))
    for m, skill in MIRRORS.items():
        res["mirrors"][m] = (os.path.exists(os.path.join(aidir, m)), skill)
    proj, err = load_json(os.path.join(aidir, "project.json"))
    if err:
        res["errors"].append("project.json: " + err)
    if proj:
        st = proj.get("status", {})
        res["confirmed"] = st.get("confirmed_by_user")
        res["open_questions"] = st.get("open_questions", [])
        res["company_profile"] = proj.get("company_profile")
        res["project"] = proj.get("project", {}).get("name")
    res["stale"] = stale_sources(aidir, root)
    res["context"] = check_context(root, aidir)
    return res


def verdicts(comp, proj):
    """read: skill đọc/mirror · issue: skill tạo văn bản gởi ra ngoài."""
    c_ok = bool(comp and comp["exists"] and all(comp["files"].values()))
    p_ok = bool(proj and proj.get("ai_context") and all(proj["files"].values()))
    c_conf = bool(comp and comp.get("confirmed"))
    p_conf = bool(proj and proj.get("confirmed"))
    stale = (comp["stale"] if comp else []) + (proj["stale"] if proj else [])
    real_stale = [s for s in stale if s[1] in ("STALE", "MISSING_SOURCE")]

    if proj is not None and not proj.get("ai_context"):
        read = "OK_DEFAULTS — chưa có thư mục AI-context; skill mirror sẽ tạo 00_AI-CONTEXT"
    elif not c_ok:
        read = "OK_DEFAULTS — chưa có hồ sơ công ty; dùng mặc định và ghi rõ"
    else:
        read = "OK"
    if not c_ok:
        issue = "STOP — thiếu hồ sơ công ty → chạy kit-start (bước 3–4 phần công ty)"
    elif proj is not None and not p_ok:
        issue = "STOP — thiếu hồ sơ dự án → chạy kit-start (bước 3–4 phần dự án)"
    elif not c_conf or (proj is not None and not p_conf):
        issue = "DRAFT_ONLY — hồ sơ chưa được người dùng xác nhận; chỉ làm bản nháp, tô vàng"
    else:
        issue = "OK"
    if real_stale:
        issue += " · CẢNH BÁO: %d nguồn đã đổi/mất — báo người dùng trước" % len(real_stale)
        read += " · CẢNH BÁO: %d nguồn đã đổi/mất" % len(real_stale)
    todo = [c for c in (proj or {}).get("context", []) if c["status"] in ("MISSING", "OUTDATED")]
    if todo and not issue.startswith("STOP"):
        issue = "STOP — Bước 5 chưa xong: chạy %s trước" % ", ".join(
            "%s (%s)" % (c["skill"], "chưa có" if c["status"] == "MISSING" else "cũ hơn nguồn")
            for c in todo)
    return read, issue


def mark(b):
    return "có" if b else "THIẾU"


def main():
    a = sys.argv[1:]
    as_json = "--json" in a
    a = [x for x in a if x != "--json"]
    if not a:
        print(__doc__)
        return 1

    comp = proj = None
    if a[0] == "--company":
        if len(a) < 2:
            print(__doc__)
            return 1
        comp = check_company(os.path.abspath(a[1]))
    else:
        root = os.path.abspath(a[0])
        if not os.path.isdir(root):
            print("Không thấy thư mục dự án: %s" % root, file=sys.stderr)
            return 2
        proj = check_project(root)
        cp = proj.get("company_profile")
        if not cp:
            # mặc định của kit: <workspace>/_COMPANY/_PROFILE, workspace = thư mục cha của dự án
            guess = os.path.join(os.path.dirname(root), "_COMPANY", "_PROFILE")
            if os.path.isdir(guess):
                cp = guess
                proj["company_profile_guessed"] = True
        if cp:
            if not os.path.isabs(cp):
                cp = os.path.normpath(os.path.join(root, proj["ai_context"], cp))
            comp = check_company(cp)

    read, issue = verdicts(comp, proj)
    if as_json:
        print(json.dumps({"company": comp, "project": proj,
                          "verdict": {"read": read, "issue": issue}},
                         ensure_ascii=False, indent=2, default=list))
        return 0

    if proj is not None:
        print("## Hồ sơ dự án — %s" % proj["root"])
        if not proj.get("ai_context"):
            print("- Chưa có thư mục AI-context.")
        else:
            print("- Thư mục AI-context: `%s`" % proj["ai_context"])
            print("- Dự án: %s" % (proj.get("project") or "[chưa có]"))
            print("- File: " + " · ".join("%s %s" % (f, mark(v)) for f, v in proj["files"].items()))
            print("- Mirror: " + " · ".join("%s %s (%s)" % (m, mark(v[0]), v[1])
                                            for m, v in proj["mirrors"].items()))
            print("- Xác nhận: %s" % (proj.get("confirmed") or "CHƯA — bản nháp"))
            if proj["open_questions"]:
                print("- Câu hỏi còn mở: %d" % len(proj["open_questions"]))
            ctx = proj.get("context", [])
            if ctx:
                print("- Bước 5 (context bắt buộc): " + " · ".join(
                    "%s %s" % (c["skill"], {"OK": "OK", "MISSING": "CHƯA CHẠY (%d file nguồn)" % c["sources"],
                                           "OUTDATED": "CŨ HƠN NGUỒN — chạy lại",
                                           "NO_SOURCE": "chưa có tài liệu"}[c["status"]])
                    for c in ctx))
            if proj.get("company_profile_guessed"):
                print("- Hồ sơ công ty: dùng vị trí mặc định ../_COMPANY/_PROFILE (project.json chưa ghi).")
            elif not proj.get("company_profile"):
                print("- `project.json` chưa trỏ tới hồ sơ công ty (trường company_profile).")
        for e in proj["errors"]:
            print("- LỖI: %s" % e)
        for name, st, p in proj["stale"]:
            print("- %s: **%s** %s" % (name, st, p))
        print()

    if comp is not None:
        print("## Hồ sơ công ty — %s" % comp["path"])
        if not comp["exists"]:
            print("- Không thấy thư mục.")
        else:
            print("- Công ty: %s" % (comp.get("company") or "[chưa có]"))
            print("- File: " + " · ".join("%s %s" % (f, mark(v)) for f, v in comp["files"].items()))
            print("- Template: %s · Quy trình: %s" % (comp.get("templates", 0), comp.get("procedures", 0)))
            print("- Xác nhận: %s" % (comp.get("confirmed") or "CHƯA — bản nháp"))
            if comp["open_questions"]:
                print("- Câu hỏi còn mở: %d" % len(comp["open_questions"]))
        for e in comp["errors"]:
            print("- LỖI: %s" % e)
        for name, st, p in comp["stale"]:
            print("- %s: **%s** %s" % (name, st, p))
        print()
    elif proj is not None:
        print("## Hồ sơ công ty — chưa xác định (chưa có project.json hoặc thiếu company_profile)\n")

    print("VERDICT read : %s" % read)
    print("VERDICT issue: %s" % issue)
    return 0


if __name__ == "__main__":
    sys.exit(main())
