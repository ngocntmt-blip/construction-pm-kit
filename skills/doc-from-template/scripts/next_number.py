#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
next_number.py — cấp số hiệu kế tiếp theo mẫu của quy trình, từ sổ register
và/hoặc tên file/folder đã phát hành. Không ghi gì.

    python3 next_number.py "<mẫu>" [--register <file.xlsx> [--sheet S] [--column "Document No."]]
                                   [--folder <thư mục đã phát hành> ...]

<mẫu> lấy từ hồ sơ (doc_numbering / doc_control.naming_patterns), các biến khác
đã thay sẵn, chỉ còn {seq:N} (N chữ số, có số 0 đầu) hoặc {seq} (độ dài bất kỳ).
Ví dụ: "AB-P01-T-{seq:04}"   "PRJ-PP-RMA-{seq:03}"

In: số lớn nhất đang dùng, SỐ KẾ TIẾP, số bị nhảy (gap), số trùng, và mỗi số
thấy ở đâu. Có gap hoặc trùng → hỏi người dùng, không tự chọn.
"""
import argparse
import collections
import os
import re
import sys
import unicodedata


def nrm(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.replace("đ", "d").replace("Đ", "D")).strip().lower()


def build_regex(pattern):
    m = re.search(r"\{seq(?::0?(\d+))?\}", pattern)
    if not m:
        sys.exit("Mẫu phải có {seq:N} hoặc {seq}: %r" % pattern)
    width = int(m.group(1)) if m.group(1) else None
    left, right = pattern[: m.start()], pattern[m.end():]
    if re.search(r"\{[^}]+\}", left + right):
        sys.exit("Mẫu còn biến chưa thay: %r — thay bằng giá trị từ hồ sơ trước." % pattern)
    num = r"(\d{%d})" % width if width else r"(\d+)"
    rx = re.compile(r"(?<![A-Za-z0-9])" + re.escape(left) + num + re.escape(right) + r"(?!\d)", re.I)
    return rx, width, left, right


def from_register(path, sheet, column, rx):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    sheets = [wb[sheet]] if sheet else wb.worksheets
    hits = []
    for ws in sheets:
        col_idx = None
        for r_i, row in enumerate(ws.iter_rows(values_only=True), 1):
            if column and col_idx is None:
                for j, v in enumerate(row):
                    if v is not None and nrm(v) == nrm(column):
                        col_idx = j
                        break
                if col_idx is not None or r_i <= 30:
                    continue          # dòng tiêu đề, hoặc chưa tới dòng tiêu đề
                sys.exit("Không thấy cột %r trong 30 dòng đầu của sheet %s." % (column, ws.title))
            cells = [row[col_idx]] if (column and col_idx < len(row)) else (() if column else row)
            for v in cells:
                if isinstance(v, str):
                    for m in rx.finditer(v):
                        hits.append((int(m.group(1)), "%s!dòng %d" % (ws.title, r_i)))
    return hits


def from_folders(folders, rx):
    hits = []
    for f in folders:
        for dp, dns, fns in os.walk(f):
            dns[:] = [d for d in dns if d.lower() not in ("_bak", "superseded")]
            for name in dns + fns:
                for m in rx.finditer(name):
                    hits.append((int(m.group(1)), os.path.relpath(os.path.join(dp, name), f)))
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pattern")
    ap.add_argument("--register")
    ap.add_argument("--sheet")
    ap.add_argument("--column")
    ap.add_argument("--folder", action="append", default=[])
    a = ap.parse_args()
    if not a.register and not a.folder:
        sys.exit("Cần --register hoặc --folder.")
    rx, width, left, right = build_regex(a.pattern)
    hits = []
    if a.register:
        hits += from_register(a.register, a.sheet, a.column, rx)
    if a.folder:
        hits += from_folders(a.folder, rx)

    def fmt(n):
        return left + (str(n).zfill(width) if width else str(n)) + right

    if not hits:
        print("Chưa thấy số nào theo mẫu %s → số đầu tiên: %s" % (a.pattern, fmt(1)))
        print("Kiểm lại với người dùng: đúng là chưa phát hành số nào?")
        return 0
    where = collections.defaultdict(set)
    for n, w in hits:
        where[n].add(w)
    nums = sorted(where)
    mx = nums[-1]
    gaps = [n for n in range(1, mx) if n not in where]
    reg_dups = collections.Counter(n for n, w in hits if "!dòng" in w)
    dups = [n for n, c in reg_dups.items() if c > 1]
    print("Mẫu: %s · thấy %d số khác nhau · lớn nhất %s" % (a.pattern, len(nums), fmt(mx)))
    print("SỐ KẾ TIẾP: %s" % fmt(mx + 1))
    if gaps:
        print("Số bị nhảy (%d): %s%s" % (len(gaps), ", ".join(fmt(g) for g in gaps[:15]),
                                         " …" if len(gaps) > 15 else ""))
    if dups:
        print("Số TRÙNG trong register: %s" % ", ".join(fmt(d) for d in dups[:15]))
    for n in nums[-3:]:
        print("  %s ← %s" % (fmt(n), "; ".join(sorted(where[n]))[:150]))
    if gaps or dups:
        print("→ Có số nhảy/trùng: hỏi người dùng lấp chỗ trống hay lấy số kế tiếp.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
