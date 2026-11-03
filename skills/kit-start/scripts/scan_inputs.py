#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_inputs.py — Bước 3 của kit-start: đọc mọi file người dùng vừa upload và
tóm tắt những gì cần để nhận diện công ty / dự án / khách hàng / template /
quy trình. KHÔNG sửa, không di chuyển file nguồn.

    python3 scan_inputs.py <thư mục> [<thư mục 2> ...] --out <thư mục kết quả>
            [--max-files 400]

Ghi ra <thư mục kết quả>:
  scan.json   — đầy đủ, máy-đọc
  scan.md     — tóm tắt để Claude đọc: bảng file, ứng viên "công ty mình",
                tổ chức khác, email/tên miền, MST, mẫu số hiệu văn bản,
                ô cần điền của từng template.
Thư mục kết quả phải nằm NGOÀI các thư mục đầu vào.

Đọc được: .docx .docm .xlsx .xlsm .pptx .pdf .md .txt .csv, ảnh (chỉ tên/kích thước).
.doc .xls .ppt cũ: chỉ liệt kê, đề nghị người dùng lưu lại dạng mới.

Mọi "ứng viên" chỉ là gợi ý có kèm bằng chứng — Claude phải xác nhận với
người dùng trước khi ghi vào hồ sơ.
"""
import argparse
import collections
import hashlib
import json
import os
import re
import sys
import zipfile
from datetime import datetime

try:
    from lxml import etree
except ImportError:
    sys.exit("Cần lxml: pip install lxml --break-system-packages")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
SKIP_DIRS = {"_bak", "_BAK", "_PROFILE", "90_CLAUDE-OUTPUT", "__pycache__", ".git"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".emf", ".wmf", ".svg", ".tif", ".tiff"}
LEGACY = {".doc", ".xls", ".ppt"}
# File do kit tự tạo — không phải tài liệu của người dùng
KIT_FILES = {"_readme.md", "onboarding.md", "claude.md", "worklog.md"}

# ---------- nhận diện mẫu ----------
PLACEHOLDER_RES = [
    ("curly", re.compile(r"\{\{\s*[^{}]{1,60}?\s*\}\}")),
    ("guillemet", re.compile(r"«[^«»]{1,60}»")),
    ("angle2", re.compile(r"<<[^<>]{1,60}>>")),
    ("bracket", re.compile(r"\[(?=[^\]]*[A-Za-zÀ-ỹ])[^\[\]\n]{2,60}\]")),
    ("angle", re.compile(r"<(?=[^>]*[A-Za-zÀ-ỹ])[^<>\n/=\"]{2,40}>")),
    ("dots", re.compile(r"\.{5,}|…{2,}")),
    ("underscores", re.compile(r"_{4,}")),
    ("xxxx", re.compile(r"(?<![A-Za-z])[xX]{3,}(?![A-Za-z])")),
    ("date_mask", re.compile(r"\b(?:dd|DD)[/\-.](?:mm|MM|mmm|MMM)[/\-.](?:yyyy|YYYY|yy|YY)\b")),
]
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+84|\(\+84\)|\b0)[\s.\-]?\d{2,3}(?:[\s.\-]?\d{3,4}){2}\b")
TAX_RE = re.compile(r"(?:MST|M\.S\.T|Mã số thuế|Ma so thue|Tax\s*(?:code|ID|No\.?))\s*[:：]?\s*"
                    r"(\d{10}(?:-\d{3})?)", re.I)
COMPANY_VI = re.compile(r"(?:CÔNG TY|CONG TY|Công ty|Công Ty|TỔNG CÔNG TY|TẬP ĐOÀN)"
                        r"[ \t]+[^\n\r,;:()·|–—]{3,80}")
NAME_CUT = re.compile(r"\s(?:-|MST|M\.S\.T|Tax|Tel|ĐT|Địa chỉ|Address|Email)\b.*$", re.I)
COMPANY_EN = re.compile(r"\b[A-Z][A-Za-z0-9&'.\- ]{1,60}?\s(?:CO\.,?\s?LTD\.?|Co\.,?\s?Ltd\.?|"
                        r"JSC|J\.S\.C|CORPORATION|Corporation|CORP\.?|LIMITED|Limited|"
                        r"COMPANY LIMITED|Company Limited|INC\.?|GROUP)\b")
CODE_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,9}(?:[-_.][A-Z0-9]{1,8}){2,6}\b")
DATE_STYLES = [
    ("DD/MM/YYYY", re.compile(r"\b[0-3]\d/[01]\d/(?:19|20)\d\d\b")),
    ("DD-MM-YYYY", re.compile(r"\b[0-3]\d-[01]\d-(?:19|20)\d\d\b")),
    ("DD.MM.YYYY", re.compile(r"\b[0-3]\d\.[01]\d\.(?:19|20)\d\d\b")),
    ("YYYY-MM-DD", re.compile(r"\b(?:19|20)\d\d-[01]\d-[0-3]\d\b")),
    ("DD-Mmm-YYYY", re.compile(r"\b[0-3]?\d[- ](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
                               r"[a-z]*[- ,]+(?:19|20)\d\d\b")),
    ("ngày … tháng … năm", re.compile(r"ngày\s+\S{1,4}\s+tháng\s+\S{1,4}\s+năm", re.I)),
]
KIND_WORDS = {
    "procedure": ["procedure", "quy trinh", "quy trình", "quy dinh", "quy định", "huong dan",
                  "hướng dẫn", "instruction", "manual", "policy", "chinh sach", "sop", "plan"],
    "template": ["template", "form", "mau", "mẫu", "bieu mau", "biểu mẫu", "blank", "trong",
                 "annex", "attachment", "phu luc mau"],
    "register": ["register", "log", "tracker", "theo doi", "theo dõi", "so dang ky",
                 "sổ", "danh muc", "danh mục", "list", "mdl"],
    "contract": ["contract", "hop dong", "hợp đồng", "loi", "letter of intent", "po ",
                 "purchase order", "phu luc", "appendix", "addendum"],
    "contacts": ["contact", "danh ba", "danh bạ", "org chart", "so do to chuc",
                 "communication matrix", "ma tran"],
}


def norm(s):
    import unicodedata
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


def sha_short(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def clip(s, n):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def placeholders(lines, limit=60):
    """Ô cần điền, kèm nhãn đứng trước (để biết ô đó là gì)."""
    out, seen = [], set()
    for line in lines:
        for kind, rx in PLACEHOLDER_RES:
            for m in rx.finditer(line):
                label = clip(line[max(0, m.start() - 40): m.start()], 40)
                key = (kind, m.group(0) if kind not in ("dots", "underscores") else label)
                if key in seen:
                    continue
                seen.add(key)
                out.append({"kind": kind, "text": clip(m.group(0), 60), "label": label})
                if len(out) >= limit:
                    return out
        # nhãn kết thúc bằng ":" mà không có giá trị → ô trống kiểu biểu mẫu
        m = re.match(r"^\s*([^:：]{2,40})[:：]\s*$", line)
        if m and ("label", m.group(1)) not in seen:
            seen.add(("label", m.group(1)))
            out.append({"kind": "empty_label", "text": "", "label": clip(m.group(1), 40)})
    return out


# ---------- đọc từng loại file ----------
def xml_paragraphs(xml_bytes, ptag=W + "p", ttag=W + "t"):
    root = etree.fromstring(xml_bytes)
    paras = []
    for p in root.iter(ptag):
        t = "".join(x.text or "" for x in p.iter(ttag))
        if t.strip():
            paras.append(t)
    return root, paras


def read_docx(path):
    info = {"paragraphs": 0, "tables": 0, "images": 0, "header_footer": [], "highlighted": []}
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        root, paras = xml_paragraphs(z.read("word/document.xml"))
        info["paragraphs"] = len(paras)
        info["tables"] = len(root.findall(".//" + W + "tbl"))
        info["images"] = sum(1 for n in names if n.startswith("word/media/"))
        hl = []
        for r in root.iter(W + "r"):
            rpr = r.find(W + "rPr")
            if rpr is not None and (rpr.find(W + "highlight") is not None or
                                    rpr.find(W + "shd") is not None and
                                    (rpr.find(W + "shd").get(W + "fill") or "auto") not in ("auto", "FFFFFF")):
                t = "".join(x.text or "" for x in r.iter(W + "t")).strip()
                if t:
                    hl.append(t)
        info["highlighted"] = list(dict.fromkeys(clip(h, 50) for h in hl))[:30]
        hf = []
        for n in names:
            if re.match(r"word/(header|footer)\d*\.xml$", n):
                _, hp = xml_paragraphs(z.read(n))
                hf.extend(hp)
        info["header_footer"] = list(dict.fromkeys(clip(x, 120) for x in hf))[:20]
        # bảng đầu tiên: dòng tiêu đề, để biết form kiểu bảng
        tbls = root.findall(".//" + W + "tbl")
        heads = []
        for tbl in tbls[:6]:
            tr = tbl.find(W + "tr")
            if tr is not None:
                cells = ["".join(x.text or "" for x in tc.iter(W + "t")).strip()
                         for tc in tr.findall(W + "tc")]
                heads.append([clip(c, 30) for c in cells][:10])
        info["table_heads"] = heads
        props = doc_props(z)
    return paras, info, props, info["header_footer"]


def doc_props(z):
    out = {}
    for n, keys in (("docProps/core.xml", ("title", "creator", "lastModifiedBy", "subject")),
                    ("docProps/app.xml", ("Company", "Template", "Pages"))):
        if n in z.namelist():
            try:
                root = etree.fromstring(z.read(n))
                for el in root.iter():
                    tag = etree.QName(el).localname
                    if tag in keys and (el.text or "").strip():
                        out[tag] = el.text.strip()
            except etree.XMLSyntaxError:
                pass
    return out


def read_xlsx(path):
    import openpyxl
    info = {"sheets": []}
    lines = []
    big = os.path.getsize(path) > 15 * 1024 * 1024
    wb = openpyxl.load_workbook(path, data_only=True, read_only=big)
    for ws in wb.worksheets:
        sh = {"name": ws.title, "max_row": ws.max_row, "max_col": ws.max_column,
              "merged": 0 if big else len(ws.merged_cells.ranges), "header_guess": None,
              "first_rows": []}
        best, best_n = None, 0
        for i, row in enumerate(ws.iter_rows(min_row=1, max_row=min(ws.max_row or 1, 60),
                                             values_only=True), 1):
            vals = [v for v in row if v not in (None, "")]
            txt = [str(v) for v in vals if isinstance(v, str)]
            lines.extend(str(v) for v in vals if isinstance(v, str))
            if len(sh["first_rows"]) < 6 and vals:
                sh["first_rows"].append([clip(str(v), 25) for v in vals][:12])
            if len(txt) > best_n and len(txt) >= 3:
                best, best_n = (i, [clip(t, 25) for t in txt][:14]), len(txt)
        sh["header_guess"] = best
        info["sheets"].append(sh)
    props = {}
    try:
        with zipfile.ZipFile(path) as z:
            props = doc_props(z)
    except zipfile.BadZipFile:
        pass
    return lines, info, props, []


def read_pptx(path):
    info = {"slides": 0, "layouts": []}
    lines = []
    with zipfile.ZipFile(path) as z:
        slides = sorted((n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                        key=lambda n: int(re.findall(r"\d+", n)[-1]))
        info["slides"] = len(slides)
        for n in slides:
            _, paras = xml_paragraphs(z.read(n), A + "p", A + "t")
            lines.extend(paras)
        for n in z.namelist():
            if re.match(r"ppt/slideLayouts/slideLayout\d+\.xml$", n):
                root = etree.fromstring(z.read(n))
                cs = root.find(".//{http://schemas.openxmlformats.org/presentationml/2006/main}cSld")
                if cs is not None and cs.get("name"):
                    info["layouts"].append(cs.get("name"))
        props = doc_props(z)
    return lines, info, props, []


def read_pdf(path, max_pages=4):
    info = {"pages": None, "text_pages_checked": 0, "has_text": None, "page_size_mm": None}
    lines = []
    try:
        from pypdf import PdfReader
        r = PdfReader(path)
        info["pages"] = len(r.pages)
        box = r.pages[0].mediabox
        info["page_size_mm"] = [round(float(box.width) * 25.4 / 72), round(float(box.height) * 25.4 / 72)]
        chars = 0
        for p in r.pages[:max_pages]:
            t = p.extract_text() or ""
            chars += len(t.strip())
            lines.extend(l for l in t.splitlines() if l.strip())
        info["text_pages_checked"] = min(max_pages, len(r.pages))
        info["has_text"] = chars >= 80 * info["text_pages_checked"] * 0.5
        props = {k.strip("/"): str(v) for k, v in (r.metadata or {}).items()
                 if k in ("/Title", "/Author", "/Creator", "/Subject")}
    except Exception as e:
        info["error"] = clip(str(e), 80)
        props = {}
    return lines, info, props, []


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = [l.rstrip("\n") for l in f.readlines()[:400]]
    return lines, {"lines": len(lines)}, {}, []


def guess_kind(path, ext, lines, info, ph):
    n = norm(os.path.basename(path))
    head = norm(" ".join(lines[:15]))
    if ext in IMG_EXT:
        return "logo/asset" if any(w in n for w in ("logo", "letterhead", "stamp", "dau", "chu ky",
                                                      "signature")) else "image"
    if ext == ".pdf" and info.get("has_text") is False and info.get("page_size_mm"):
        w, h = info["page_size_mm"]
        if max(w, h) >= 400:
            return "drawing?"
    scores = collections.Counter()
    for kind, words in KIND_WORDS.items():
        for wd in words:
            w = norm(wd)
            if w in n:
                scores[kind] += 2
            if w in head:
                scores[kind] += 1
    real_ph = [p for p in ph if p["kind"] not in ("dots",)] if ph else []
    if len(ph) >= 3 or len(real_ph) >= 2:
        scores["template"] += 3
    if ext in (".xlsx", ".xlsm"):
        rows = max((s["max_row"] or 0) for s in info.get("sheets", [{"max_row": 0}]))
        if rows >= 15 and scores["register"]:
            scores["register"] += 2
    if not scores:
        stem = os.path.splitext(os.path.basename(path))[0].upper()
        if CODE_RE.search(stem) and re.search(r"\d", stem):
            return "issued_sample"
        return "document"
    kind, sc = scores.most_common(1)[0]
    if kind == "template" and not ph and ext in (".pdf",):
        return "document"
    return kind


# ---------- quét ----------
def scan(dirs, out_dir, max_files):
    files, skipped = [], []
    for d in dirs:
        for dp, dns, fns in os.walk(d):
            dns[:] = [x for x in dns if x not in SKIP_DIRS and not x.startswith(".")]
            for fn in fns:
                if fn.startswith("~$") or fn.startswith(".") or fn.lower().endswith(".lnk") \
                        or fn.lower() in KIT_FILES:
                    continue
                files.append((d, os.path.join(dp, fn)))
    if len(files) > max_files:
        skipped = files[max_files:]
        files = files[:max_files]

    records = []
    agg = {k: collections.Counter() for k in ("email_domain", "email", "tax", "company_vi",
                                              "company_en", "code_shape", "date_style", "phone")}
    where = collections.defaultdict(lambda: collections.Counter())   # entity -> nơi xuất hiện
    code_examples = collections.defaultdict(list)

    readers = {".docx": read_docx, ".docm": read_docx, ".xlsx": read_xlsx, ".xlsm": read_xlsx,
               ".pptx": read_pptx, ".pdf": read_pdf, ".md": read_text, ".txt": read_text,
               ".csv": read_text}
    for base, path in files:
        ext = os.path.splitext(path)[1].lower()
        rel = os.path.relpath(path, os.path.dirname(os.path.abspath(base)))
        rec = {"file": rel.replace("\\", "/"), "abs": os.path.abspath(path), "ext": ext,
               "size_kb": round(os.path.getsize(path) / 1024, 1),
               "mtime": datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M"),
               "sha256": sha_short(path)}
        lines, info, props, hf = [], {}, {}, []
        if ext in LEGACY:
            rec["kind"] = "legacy"
            rec["note"] = "định dạng cũ — mở bằng Office rồi Save As .docx/.xlsx/.pptx để đọc được"
            records.append(rec)
            continue
        if ext in readers:
            try:
                lines, info, props, hf = readers[ext](path)
            except Exception as e:
                rec["error"] = clip("%s: %s" % (type(e).__name__, e), 120)
        ph = placeholders(lines) if lines else []
        rec.update({"kind": guess_kind(path, ext, lines, info, ph), "props": props, "info": info,
                    "first_text": [clip(l, 100) for l in lines[:8]], "placeholders": ph})
        if ext in IMG_EXT:
            rec["kind"] = guess_kind(path, ext, [], {}, [])
        records.append(rec)

        # gom thực thể; trọng số cao hơn khi nằm ở header/footer/thuộc tính file
        text = "\n".join(lines)
        hf_text = "\n".join(hf) + "\n" + " ".join(props.get(k, "") for k in ("Company", "creator"))
        for src, blob, wgt in (("body", text, 1), ("letterhead", hf_text, 3)):
            for e in EMAIL_RE.findall(blob):
                e = e.lower().rstrip(".")
                agg["email"][e] += wgt
                agg["email_domain"][e.split("@")[1]] += wgt
                where[("email_domain", e.split("@")[1])][src] += 1
            for t in TAX_RE.findall(blob):
                agg["tax"][t] += wgt
                where[("tax", t)][src] += 1
            for rx, key in ((COMPANY_VI, "company_vi"), (COMPANY_EN, "company_en")):
                for c in rx.findall(blob):
                    c = clip(NAME_CUT.sub("", c).strip(" .-·"), 80)
                    if len(c) < 8:
                        continue
                    agg[key][c] += wgt
                    where[(key, c)][src] += 1
            for p in PHONE_RE.findall(blob):
                agg["phone"][re.sub(r"[\s.\-()]", "", p)] += wgt
        if props.get("Company"):
            agg["company_en"][clip(props["Company"], 80)] += 3
            where[("company_en", clip(props["Company"], 80))]["file_property"] += 1
        stem = os.path.splitext(os.path.basename(path))[0].upper()
        for c in set(CODE_RE.findall(text + "\n" + stem)):
            if not re.search(r"\d", c):
                continue
            shape = re.sub(r"\d", "#", c)
            agg["code_shape"][shape] += 1
            if len(code_examples[shape]) < 4:
                code_examples[shape].append(c)
        for name, rx in DATE_STYLES:
            n = len(rx.findall(text))
            if n:
                agg["date_style"][name] += n

    def top(counter, n=12, key=None):
        rows = []
        for k, v in counter.most_common(n):
            w = dict(where.get((key, k), {})) if key else {}
            rows.append({"value": k, "score": v, "where": w})
        return rows

    orgs = []
    for key in ("company_vi", "company_en"):
        for r in top(agg[key], 15, key):
            lh = r["where"].get("letterhead", 0) + r["where"].get("file_property", 0)
            orgs.append({**r, "type": key, "letterhead_hits": lh})
    orgs.sort(key=lambda r: (r["letterhead_hits"], r["score"]), reverse=True)
    own = [o for o in orgs if o["letterhead_hits"] > 0][:6]
    others = [o for o in orgs if o["letterhead_hits"] == 0][:15]

    result = {
        "scanned_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "inputs": [os.path.abspath(d) for d in dirs],
        "file_count": len(records), "skipped_over_limit": len(skipped),
        "by_kind": dict(collections.Counter(r["kind"] for r in records)),
        "own_company_candidates": own[:6],
        "organisations": others,
        "email_domains": top(agg["email_domain"], 12, "email_domain"),
        "tax_ids": top(agg["tax"], 6, "tax"),
        "phones": top(agg["phone"], 6),
        "doc_code_shapes": [{"shape": s, "count": c, "examples": code_examples[s]}
                            for s, c in agg["code_shape"].most_common(25)],
        "date_styles": dict(agg["date_style"]),
        "files": records,
    }
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "scan.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "scan.md"), "w", encoding="utf-8") as f:
        f.write(render_md(result))
    return result


def render_md(r):
    L = ["# Kết quả quét đầu vào — %s" % r["scanned_at"], "",
         "Nguồn: " + " · ".join("`%s`" % p for p in r["inputs"]),
         "Tổng %d file · theo loại: %s" % (r["file_count"], ", ".join(
             "%s %d" % (k, v) for k, v in sorted(r["by_kind"].items(), key=lambda x: -x[1]))), ""]
    if r["skipped_over_limit"]:
        L += ["> ⚠️ %d file bị bỏ qua vì vượt giới hạn --max-files." % r["skipped_over_limit"], ""]
    L += ["> Mọi ứng viên dưới đây là GỢI Ý kèm bằng chứng. Xác nhận với người dùng trước khi ghi hồ sơ.", "",
          "## Ứng viên \"công ty mình\" (xuất hiện ở letterhead / thuộc tính file nhiều nhất)", "",
          "| Tên | Điểm | Ở letterhead/thuộc tính | Nơi xuất hiện |", "|---|---:|---:|---|"]
    for o in r["own_company_candidates"]:
        L.append("| %s | %d | %d | %s |" % (o["value"], o["score"], o["letterhead_hits"],
                                            ", ".join("%s %d" % kv for kv in o["where"].items())))
    L += ["", "## Tổ chức khác (khách hàng, tư vấn, nhà cung cấp…)", "", "| Tên | Điểm |", "|---|---:|"]
    L += ["| %s | %d |" % (o["value"], o["score"]) for o in r["organisations"]]
    L += ["", "## Tên miền email", "", "| Tên miền | Điểm | Nơi |", "|---|---:|---|"]
    L += ["| %s | %d | %s |" % (e["value"], e["score"], ", ".join("%s %d" % kv for kv in e["where"].items()))
          for e in r["email_domains"]]
    if r["tax_ids"]:
        L += ["", "## Mã số thuế", ""] + ["- %s (điểm %d)" % (t["value"], t["score"]) for t in r["tax_ids"]]
    L += ["", "## Mẫu số hiệu văn bản (chữ số thay bằng #)", "", "| Mẫu | Số lần | Ví dụ |", "|---|---:|---|"]
    L += ["| `%s` | %d | %s |" % (c["shape"], c["count"], ", ".join(c["examples"]))
          for c in r["doc_code_shapes"]]
    if r["date_styles"]:
        L += ["", "## Kiểu ngày tháng đang dùng", ""] + \
             ["- %s: %d" % kv for kv in sorted(r["date_styles"].items(), key=lambda x: -x[1])]
    L += ["", "## Danh mục file", "", "| File | Loại (đoán) | KB | Ghi chú |", "|---|---|---:|---|"]
    for f in r["files"]:
        note = f.get("note") or f.get("error") or ""
        inf = f.get("info", {})
        if not note:
            if "pages" in inf:
                note = "%s tr.%s" % (inf.get("pages"), "" if inf.get("has_text") else " · KHÔNG có lớp text")
            elif "sheets" in inf:
                note = "%d sheet: %s" % (len(inf["sheets"]), ", ".join(s["name"] for s in inf["sheets"][:5]))
            elif "slides" in inf:
                note = "%d slide" % inf["slides"]
            elif "paragraphs" in inf:
                note = "%d đoạn · %d bảng · %d ảnh" % (inf["paragraphs"], inf["tables"], inf["images"])
            if f.get("placeholders"):
                note += " · %d ô cần điền" % len(f["placeholders"])
        L.append("| `%s` | %s | %s | %s |" % (f["file"], f.get("kind", "?"), f["size_kb"], note))
    tpl = [f for f in r["files"] if f.get("placeholders") or f.get("kind") == "template"]
    if tpl:
        L += ["", "## Ô cần điền theo từng file (template / form)", ""]
        for f in tpl:
            L += ["### `%s`" % f["file"]]
            inf = f.get("info", {})
            if inf.get("header_footer"):
                L.append("- Header/footer: " + " | ".join(inf["header_footer"][:4]))
            if inf.get("table_heads"):
                L.append("- Bảng (dòng đầu): " + " || ".join(" | ".join(h) for h in inf["table_heads"][:3]))
            if inf.get("highlighted"):
                L.append("- Đoạn đang tô màu (thường là chỗ cần thay): " + " · ".join(inf["highlighted"][:10]))
            for p in f.get("placeholders", [])[:25]:
                L.append("- %s `%s` ← nhãn: %s" % (p["kind"], p["text"], p["label"] or "—"))
            L.append("")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-files", type=int, default=400)
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    for d in a.dirs:
        if not os.path.isdir(d):
            sys.exit("Không thấy thư mục: %s" % d)
        d = os.path.abspath(d)
        if out == d or out.startswith(d + os.sep):
            sys.exit("--out phải nằm ngoài thư mục đầu vào (%s)." % d)
    r = scan(a.dirs, out, a.max_files)
    print("Đã quét %d file → %s/scan.md, scan.json" % (r["file_count"], out))
    print("Theo loại: %s" % r["by_kind"])
    if r["own_company_candidates"]:
        c = r["own_company_candidates"][0]
        print("Ứng viên công ty mình: %s (letterhead %d) — CẦN XÁC NHẬN" % (c["value"], c["letterhead_hits"]))


if __name__ == "__main__":
    main()
