#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docx_fill.py — điền template Word mà KHÔNG phá định dạng.

    python3 docx_fill.py list  <template.docx>
    python3 docx_fill.py fill  <template.docx> <values.json> <out.docx> [--no-highlight]
    python3 docx_fill.py check <file.docx> [--name-regex REGEX]

values.json:
{
  "replace": { "{{transmittal_no}}": "AB-P01-T-0021", "[Tên người nhận]": "Ông A" },
  "labels":  { "Người ký": "Nguyễn Văn B", "Date": "03/11/2026" },
  "tables":  [ { "match_header": ["No.", "Document No."],
                 "rows": [["1", "AB-P01-RMA-003", "Sprinkler", "0", "A"]] } ]
}
  replace — thay đúng chuỗi, kể cả khi Word cắt chuỗi đó ra nhiều run.
  labels  — ô kiểu biểu mẫu: "Nhãn: ......" → thay dãy chấm/gạch đầu tiên sau nhãn;
            "Nhãn:" trống → thêm giá trị sau dấu ":"; nhãn nằm một mình trong ô bảng
            và ô bên phải trống → điền ô bên phải.
  tables  — bảng có dòng đầu chứa các tiêu đề match_header: điền vào các dòng trống
            sẵn có, thiếu thì thêm dòng (sao chép định dạng dòng cuối).

Mọi chỗ điền được tô vàng (trừ --no-highlight). Không bao giờ ghi đè: out.docx
phải chưa tồn tại và khác template. Chạy khắp thân văn bản, bảng, header,
footer, text box. In báo cáo: điền được gì, còn sót gì.
"""
import copy
import json
import os
import re
import sys
import unicodedata
import zipfile

try:
    from lxml import etree
except ImportError:
    sys.exit("Cần lxml (cài kèm python-docx): pip install python-docx --break-system-packages")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{%s}" % W_NS
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
PARTS = re.compile(r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$")
PH_RES = [
    ("curly", re.compile(r"\{\{\s*[^{}]{1,60}?\s*\}\}")),
    ("guillemet", re.compile(r"«[^«»]{1,60}»")),
    ("angle2", re.compile(r"<<[^<>]{1,60}>>")),
    ("bracket", re.compile(r"\[(?=[^\]]*[A-Za-zÀ-ỹ])[^\[\]\n]{2,60}\]")),
    ("xxxx", re.compile(r"(?<![A-Za-z])[xX]{3,}(?![A-Za-z])")),
    ("date_mask", re.compile(r"\b(?:dd|DD)[/\-.](?:mm|MM|mmm|MMM)[/\-.](?:yyyy|YYYY|yy|YY)\b")),
    ("dots", re.compile(r"\.{5,}|…{2,}")),
    ("underscores", re.compile(r"_{4,}")),
]
BLANK_RE = re.compile(r"\.{3,}|…+|_{3,}")


def nrm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.replace("đ", "d").replace("Đ", "D")).strip().lower()


# ---------- run helpers ----------
def runs_of(p):
    return p.xpath("./w:r | ./w:hyperlink/w:r | ./w:ins/w:r | ./w:smartTag/w:r",
                   namespaces={"w": W_NS})


def run_text(r):
    return "".join((t.text or "") for t in r.findall(W + "t"))


def set_run_text(r, text):
    ts = r.findall(W + "t")
    if not ts:
        t = etree.SubElement(r, W + "t")
        ts = [t]
    ts[0].text = text
    ts[0].set(XML_SPACE, "preserve")
    for t in ts[1:]:
        r.remove(t)


def highlight(r):
    rpr = r.find(W + "rPr")
    if rpr is None:
        rpr = etree.Element(W + "rPr")
        r.insert(0, rpr)
    h = rpr.find(W + "highlight")
    if h is None:
        h = etree.SubElement(rpr, W + "highlight")
    h.set(W + "val", "yellow")


def clone_run(r, text):
    n = copy.deepcopy(r)
    for child in list(n):
        if child.tag != W + "rPr":
            n.remove(child)
    t = etree.SubElement(n, W + "t")
    t.text = text
    t.set(XML_SPACE, "preserve")
    return n


def para_text(p):
    return "".join(run_text(r) for r in runs_of(p))


def replace_span(p, s, e, value, hl):
    """Thay ký tự [s, e) của paragraph bằng value. Giữ định dạng run chứa ký tự s."""
    runs = runs_of(p)
    pos, spans = 0, []
    for r in runs:
        t = run_text(r)
        spans.append((r, pos, pos + len(t), t))
        pos += len(t)
    first = next(x for x in spans if x[1] <= s < x[2])
    last = next(x for x in spans if x[1] < e <= x[2])
    r0, a0, _, t0 = first
    r1, a1, _, t1 = last
    before, after = t0[: s - a0], t1[e - a1:]
    new = clone_run(r0, value)
    if hl:
        highlight(new)
    r0.addnext(new)
    if r0 is r1:
        if after:
            new.addnext(clone_run(r0, after))
    else:
        started = False
        for r, _, _, _ in spans:
            if r is r0:
                started = True
                continue
            if r is r1:
                break
            if started:
                r.getparent().remove(r)
        set_run_text(r1, after)
        if not after:
            r1.getparent().remove(r1)
    if before:
        set_run_text(r0, before)
    else:
        r0.getparent().remove(r0)


def all_paragraphs(root):
    return root.iter(W + "p")


# ---------- operations ----------
def do_replace(root, mapping, hl, done):
    for key in sorted(mapping, key=len, reverse=True):
        val = str(mapping[key])
        for p in list(all_paragraphs(root)):
            cursor = 0
            while True:
                txt = para_text(p)
                i = txt.find(key, cursor)
                if i < 0:
                    break
                replace_span(p, i, i + len(key), val, hl)
                done["replace"][key] = done["replace"].get(key, 0) + 1
                cursor = i + len(val)


def cell_of(p):
    anc = p.getparent()
    while anc is not None and anc.tag != W + "tc":
        anc = anc.getparent()
    return anc


def do_labels(root, labels, hl, done):
    for label, val in labels.items():
        nl = nrm(label)
        hit = False
        for p in list(all_paragraphs(root)):
            txt = para_text(p)
            nt = nrm(txt)
            if not nt.startswith(nl) and (nl + ":") not in nt and (nl + " :") not in nt:
                continue
            # vị trí sau nhãn trong text gốc (so khớp không dấu theo độ dài tương ứng)
            idx = None
            for k in range(len(txt)):
                if nrm(txt[: k + 1]).endswith(nl):
                    idx = k + 1
                    break
            if idx is None:
                continue
            rest = txt[idx:]
            m = BLANK_RE.search(rest)
            colon = re.match(r"\s*[:：]?\s*", rest)
            if m and not rest[: m.start()].strip(" :：\t"):
                replace_span(p, idx + m.start(), idx + m.end(), str(val), hl)
                hit = True
            elif not rest.strip(" :：\t"):
                tc = cell_of(p)
                nxt = tc.getnext() if tc is not None else None
                if tc is not None and nxt is not None and nxt.tag == W + "tc" and \
                        not "".join(nxt.itertext()).strip():
                    tp = nxt.find(W + "p")
                    rr = runs_of(p)
                    newr = clone_run(rr[-1], str(val)) if rr else etree.Element(W + "r")
                    if not rr:
                        t = etree.SubElement(newr, W + "t")
                        t.text = str(val)
                    if hl:
                        highlight(newr)
                    tp.append(newr)
                else:
                    rr = runs_of(p)
                    if not rr:
                        continue
                    sep = "" if rest.endswith(" ") or not rest else " "
                    if not rest.strip():
                        sep = ": " if ":" not in rest else " "
                    newr = clone_run(rr[-1], sep + str(val))
                    if hl:
                        highlight(newr)
                    rr[-1].addnext(newr)
                hit = True
            if hit:
                done["labels"][label] = 1
                break


def cell_set(tc, text, hl):
    ps = tc.findall(W + "p")
    p = ps[0]
    rr = runs_of(p)
    for extra in ps[1:]:
        tc.remove(extra)
    if rr:
        tmpl = rr[0]
        for r in rr:
            r.getparent().remove(r)
        newr = clone_run(tmpl, str(text))
    else:
        newr = etree.Element(W + "r")
        t = etree.SubElement(newr, W + "t")
        t.text = str(text)
        t.set(XML_SPACE, "preserve")
    if hl:
        highlight(newr)
    p.append(newr)


def do_tables(root, specs, hl, done):
    for spec in specs:
        want = [nrm(h) for h in spec["match_header"]]
        for tbl in root.iter(W + "tbl"):
            trs = tbl.findall(W + "tr")
            if not trs:
                continue
            head = [nrm("".join(tc.itertext())) for tc in trs[0].findall(W + "tc")]
            if not all(any(w == h or w in h for h in head) for w in want):
                continue
            rows = spec["rows"]
            body = trs[1:]
            empty = [tr for tr in body if not "".join(tr.itertext()).strip()]
            slots = list(empty)
            tmpl = (empty[-1] if empty else (body[-1] if body else trs[0]))
            while len(slots) < len(rows):
                n = copy.deepcopy(tmpl)
                for t in n.iter(W + "t"):
                    t.text = ""
                (slots[-1] if slots else trs[-1]).addnext(n)
                slots.append(n)
            for tr, vals in zip(slots, rows):
                tcs = tr.findall(W + "tc")
                for tc, v in zip(tcs, vals):
                    if v is not None and str(v) != "":
                        cell_set(tc, v, hl)
            done["tables"].append({"header": spec["match_header"], "rows": len(rows),
                                   "added_rows": max(0, len(rows) - len(empty))})
            break
        else:
            done["tables"].append({"header": spec["match_header"], "rows": 0, "error": "không thấy bảng"})


# ---------- list / check ----------
def scan_placeholders(path):
    found = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if not PARTS.match(n):
                continue
            root = etree.fromstring(z.read(n))
            for p in all_paragraphs(root):
                t = para_text(p)
                for kind, rx in PH_RES:
                    for m in rx.finditer(t):
                        found.append({"part": n.split("/")[1], "kind": kind, "text": m.group(0),
                                      "context": re.sub(r"\s+", " ", t[max(0, m.start() - 35): m.end() + 15])})
    return found


def count_highlight(path):
    n = 0
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if PARTS.match(name):
                n += len(re.findall(rb'w:highlight w:val="yellow"', z.read(name)))
    return n


def cmd_list(path):
    ph = scan_placeholders(path)
    if not ph:
        print("Không thấy placeholder dạng {{…}} [..] «…» …… ____ xxxx. Form điền theo nhãn/bảng → dùng 'labels'/'tables'.")
        return 0
    print("| Phần | Loại | Chuỗi | Ngữ cảnh |\n|---|---|---|---|")
    for x in ph:
        print("| %s | %s | `%s` | %s |" % (x["part"], x["kind"], x["text"], x["context"].replace("|", "/")))
    return 0


def cmd_fill(tpl, values_path, out, hl):
    if os.path.abspath(tpl) == os.path.abspath(out):
        sys.exit("Không ghi đè template. Chọn tên file output khác.")
    if os.path.exists(out):
        sys.exit("File output đã tồn tại: %s — không ghi đè. Đổi tên hoặc hỏi người dùng." % out)
    with open(values_path, encoding="utf-8") as f:
        vals = json.load(f)
    done = {"replace": {}, "labels": {}, "tables": []}
    with zipfile.ZipFile(tpl) as zin:
        items = [(i, zin.read(i.filename)) for i in zin.infolist()]
    out_items = []
    for info, data in items:
        if PARTS.match(info.filename):
            root = etree.fromstring(data)
            do_replace(root, vals.get("replace", {}), hl, done)
            do_labels(root, {k: v for k, v in vals.get("labels", {}).items() if k not in done["labels"]},
                      hl, done)
            if info.filename == "word/document.xml":
                do_tables(root, vals.get("tables", []), hl, done)
            data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        out_items.append((info, data))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, data in out_items:
            zout.writestr(info, data)

    miss_r = [k for k in vals.get("replace", {}) if k not in done["replace"]]
    miss_l = [k for k in vals.get("labels", {}) if k not in done["labels"]]
    print("Đã ghi: %s" % out)
    print("- replace: %d/%d khóa (%d chỗ)" % (len(done["replace"]), len(vals.get("replace", {})),
                                           sum(done["replace"].values())))
    print("- labels : %d/%d" % (len(done["labels"]), len(vals.get("labels", {}))))
    for t in done["tables"]:
        print("- bảng %s: %s" % (t["header"], t.get("error") or "%d dòng (thêm %d)" % (t["rows"], t["added_rows"])))
    if miss_r or miss_l:
        print("KHÔNG TÌM THẤY: " + "; ".join(miss_r + miss_l))
    left = scan_placeholders(out)
    if left:
        print("Còn %d placeholder chưa điền:" % len(left))
        for x in left[:20]:
            print("  - %s `%s` … %s" % (x["kind"], x["text"], x["context"]))
    return 0 if not (miss_r or miss_l) else 3


def cmd_check(path, name_regex):
    ok = True
    left = scan_placeholders(path)
    print("Placeholder còn lại: %d" % len(left))
    for x in left[:30]:
        print("  - %s `%s` … %s" % (x["kind"], x["text"], x["context"]))
    print("Chỗ tô vàng (Claude điền/sửa): %d" % count_highlight(path))
    if name_regex:
        nm = os.path.basename(path)
        hit = re.search(name_regex, nm) is not None
        ok &= hit
        print("Tên file %s mẫu quy trình (%s): %s" % ("ĐÚNG" if hit else "SAI", name_regex, nm))
    ok &= not left
    return 0 if ok else 3


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 1
    if a[0] == "list" and len(a) == 2:
        return cmd_list(a[1])
    if a[0] == "fill" and len(a) >= 4:
        return cmd_fill(a[1], a[2], a[3], "--no-highlight" not in a)
    if a[0] == "check" and len(a) >= 2:
        rx = a[a.index("--name-regex") + 1] if "--name-regex" in a else None
        return cmd_check(a[1], rx)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
