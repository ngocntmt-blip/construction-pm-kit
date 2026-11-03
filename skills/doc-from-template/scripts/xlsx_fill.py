#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xlsx_fill.py — điền template Excel / thêm dòng vào sổ register, giữ định dạng.

    python3 xlsx_fill.py fill   <template.xlsx> <values.json> <out.xlsx> [--no-highlight]
    python3 xlsx_fill.py append <register.xlsx> <rows.json> [--sheet TÊN] [--header-row N]
                                [--no-highlight] [--backup-dir DIR]

fill — values.json:
{
  "cells":   { "Sheet1!C5": "AB-P01-DN-012", "C6": "03/11/2026" },
  "replace": { "{{project}}": "Kho P01" },
  "rows":    { "sheet": "Sheet1", "start": "A12", "values": [["1", "Ống DN80", "m", 100]] }
}
  out.xlsx phải chưa tồn tại và khác template.

append — rows.json: [ { "<tên cột>": giá trị, ... }, ... ]
  Thêm dòng vào CUỐI vùng dữ liệu của sổ đang dùng (sửa tại chỗ — đây là việc
  duy nhất sửa file gốc, nên LUÔN backup trước vào <thư mục file>/_bak/ hoặc
  --backup-dir). Cột không có trong rows.json để trống. Định dạng dòng mới chép
  từ dòng dữ liệu cuối. Dừng nếu file đang mở (~$ lock) hoặc tên cột không khớp.

Ô điền tô nền vàng (trừ --no-highlight). Công thức có sẵn giữ nguyên.
"""
import copy
import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timedelta, timezone

try:
    import openpyxl
    from openpyxl.styles import PatternFill
    from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
except ImportError:
    sys.exit("Cần openpyxl: pip install openpyxl --break-system-packages")

YELLOW = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")


def nrm(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.replace("đ", "d").replace("Đ", "D")).strip().lower()


def put(ws, coord, value, hl):
    c = ws[coord]
    if type(c).__name__ == "MergedCell":
        for rng in ws.merged_cells.ranges:
            if coord in rng:
                c = ws.cell(rng.min_row, rng.min_col)
                break
    c.value = value
    if hl:
        c.fill = YELLOW
    return c.coordinate


def cmd_fill(tpl, values_path, out, hl):
    if os.path.abspath(tpl) == os.path.abspath(out):
        sys.exit("Không ghi đè template.")
    if os.path.exists(out):
        sys.exit("File output đã tồn tại: %s — không ghi đè." % out)
    vals = json.load(open(values_path, encoding="utf-8"))
    keep_vba = tpl.lower().endswith(".xlsm")
    wb = openpyxl.load_workbook(tpl, keep_vba=keep_vba)
    n = 0
    for ref, v in vals.get("cells", {}).items():
        sh, coord = ref.split("!", 1) if "!" in ref else (wb.active.title, ref)
        put(wb[sh.strip("'")], coord, v, hl)
        n += 1
    rep, nrep = vals.get("replace", {}), 0
    if rep:
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for c in row:
                    if isinstance(c.value, str) and not c.value.startswith("="):
                        new = c.value
                        for k, v in rep.items():
                            new = new.replace(k, str(v))
                        if new != c.value:
                            c.value = new
                            nrep += 1
                            if hl:
                                c.fill = YELLOW
    rows = vals.get("rows")
    nrows = 0
    if rows:
        ws = wb[rows.get("sheet", wb.active.title)]
        col, r0 = coordinate_from_string(rows["start"])
        c0 = column_index_from_string(col)
        for i, line in enumerate(rows["values"]):
            for j, v in enumerate(line):
                if v is None:
                    continue
                cell = ws.cell(r0 + i, c0 + j)
                cell.value = v
                if hl:
                    cell.fill = YELLOW
            nrows += 1
    wb.save(out)
    print("Đã ghi %s — %d ô, %d ô thay chuỗi, %d dòng." % (out, n, nrep, nrows))
    left = []
    for ws in openpyxl.load_workbook(out).worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and re.search(r"\{\{[^}]+\}\}|«[^»]+»|<<[^>]+>>", c.value):
                    left.append("%s!%s %s" % (ws.title, c.coordinate, c.value[:40]))
    if left:
        print("Còn placeholder: " + "; ".join(left[:15]))
    return 0


def find_header(ws, want, limit=30):
    want_n = [nrm(w) for w in want]
    best = None
    for r in range(1, min(limit, ws.max_row) + 1):
        row = {nrm(ws.cell(r, c).value): c for c in range(1, ws.max_column + 1) if ws.cell(r, c).value}
        hits = sum(1 for w in want_n if w in row)
        if hits and (best is None or hits > best[1]):
            best = (r, hits, row)
    return best


def cmd_append(reg, rows_path, sheet, header_row, hl, backup_dir):
    d, fn = os.path.split(os.path.abspath(reg))
    if os.path.exists(os.path.join(d, "~$" + fn)):
        sys.exit("File đang mở trong Excel (%s). Nhờ người dùng đóng file rồi chạy lại." % ("~$" + fn))
    rows = json.load(open(rows_path, encoding="utf-8"))
    if isinstance(rows, dict):
        rows = [rows]
    keep_vba = reg.lower().endswith(".xlsm")
    wb = openpyxl.load_workbook(reg, keep_vba=keep_vba)
    ws = wb[sheet] if sheet else wb.active
    want = sorted({k for r in rows for k in r})
    if header_row:
        hdr = {nrm(ws.cell(header_row, c).value): c for c in range(1, ws.max_column + 1)
               if ws.cell(header_row, c).value}
        hr = header_row
    else:
        found = find_header(ws, want)
        if not found:
            sys.exit("Không tìm thấy dòng tiêu đề chứa các cột: %s" % want)
        hr, _, hdr = found
    missing = [k for k in want if nrm(k) not in hdr]
    if missing:
        sys.exit("Sổ không có cột: %s. Cột hiện có: %s" % (missing, list(hdr)))
    # dòng dữ liệu cuối = dòng cuối có giá trị ở bất kỳ cột tiêu đề nào
    cols = list(hdr.values())
    last = hr
    for r in range(hr + 1, ws.max_row + 1):
        if any(ws.cell(r, c).value not in (None, "") for c in cols):
            last = r

    bdir = backup_dir or os.path.join(d, "_bak")
    os.makedirs(bdir, exist_ok=True)
    vn = (datetime.now(timezone.utc) + timedelta(hours=7)).strftime("%y%m%d-%H%M%S")
    stem, ext = os.path.splitext(fn)
    bak = os.path.join(bdir, "%s_%s%s" % (stem, vn, ext))
    shutil.copy2(reg, bak)

    for i, rec in enumerate(rows, 1):
        r = last + i
        for c in range(1, ws.max_column + 1):
            src = ws.cell(last, c)
            dst = ws.cell(r, c)
            if src.has_style:
                dst._style = copy.copy(src._style)
            if isinstance(src.value, str) and src.value.startswith("=") and dst.value is None:
                # công thức theo dòng (vd =ROW()-1): dời số dòng tương đối
                dst.value = re.sub(r"(?<=[A-Z])%d\b" % last, str(r), src.value)
        for k, v in rec.items():
            cell = ws.cell(r, hdr[nrm(k)])
            cell.value = v
            if hl:
                cell.fill = YELLOW
    wb.save(reg)
    print("Đã thêm %d dòng vào %s!%s (dòng %d–%d). Backup: %s" % (
        len(rows), fn, ws.title, last + 1, last + len(rows), bak))
    return 0


def main():
    a = sys.argv[1:]
    hl = "--no-highlight" not in a
    a = [x for x in a if x != "--no-highlight"]

    def opt(name):
        if name in a:
            i = a.index(name)
            v = a[i + 1]
            del a[i:i + 2]
            return v
        return None
    sheet, hrow, bdir = opt("--sheet"), opt("--header-row"), opt("--backup-dir")
    if len(a) >= 4 and a[0] == "fill":
        return cmd_fill(a[1], a[2], a[3], hl)
    if len(a) >= 3 and a[0] == "append":
        return cmd_append(a[1], a[2], sheet, int(hrow) if hrow else None, hl, bdir)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
