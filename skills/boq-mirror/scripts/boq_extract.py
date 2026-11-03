#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
boq_extract.py — trích BOQ xây dựng (Excel) sang SQLite + CSV + markdown mirror.

    python3 boq_extract.py probe  <file.xlsx>
    python3 boq_extract.py build  <file.xlsx> <out_dir>
    python3 boq_extract.py check  <out_dir>

Không sửa file Excel gốc. Số hàng Excel gốc giữ trong cột `excel_row`.
`check` đối soát tổng tiền dòng item với các dòng TỔNG/GRAND TOTAL trong
chính workbook (Bước 4 của SKILL.md).
"""
import sys, os, re, json, sqlite3, csv, unicodedata, tempfile, shutil

try:
    import openpyxl
except ImportError:
    sys.exit("Cần: pip install openpyxl --break-system-packages")

COLMAP = [
    ("area",        ["area", "khu vuc", "code"]),
    ("system",      ["local", "class", "he thong"]),
    ("item_code",   ["code", "no."]),
    ("description", ["description", "work item", "item", "mo ta", "hang muc", "noi dung"]),
    ("size",        ["size", "kich thuoc", "duong kinh"]),
    ("unit",        ["unit", "don vi", "dvt"]),
    ("qty_client",  ["by client", "by owner", "by consultant", "kl moi thau", "q'ty", "qty", "so luong"]),
    ("qty_bidder",  ["by bidder", "by contractor", "q'ty by contract", "qty by contract",
                     "kl nha thau"]),
    ("unit_price",  ["unit price", "unit rate", "don gia"]),
    ("mat_unit",    ["material unit", "unit cost material", "material price", "don gia vt"]),
    ("mat_total",   ["total material", "thanh tien vt"]),
    ("lab_unit",    ["labour unit", "labor unit", "labour price", "labor price", "don gia nc"]),
    ("lab_total",   ["total labour", "total labor", "total installation", "thanh tien nc"]),
    ("total",       ["total cost", "amount", "thanh tien", "tong cong"]),
    ("brand",       ["brand", "nhan hieu"]),
    ("remark",      ["remark", "ghi chu"]),
]


def norm(s):
    if s is None:
        return ""
    s = str(s).replace("\n", " ")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    # NFD không tách được "đ/Đ" -> phải đổi tay, nếu không "Đơn giá", "ĐVT"
    # sẽ không khớp từ khoá "don gia", "dvt".
    s = s.replace("đ", "d").replace("Đ", "D")
    return re.sub(r"\s+", " ", s).strip().lower()


def num(v):
    """float nếu là số thật, None nếu rỗng/text. Không ép chuỗi thành 0."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "").replace("\u00a0", "")
    if not s or s in ("-", "—", "N/A"):
        return None
    # Số dạng text: "1,234,567.5" (Anh) hoặc "1.234.567,5" (Việt).
    # Chỉ nhận khi định dạng rõ ràng; mơ hồ thì trả None, không đoán.
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", s):
        s = s.replace(",", "")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?", s):
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d+,\d+", s):
        return None   # "1,5" hay "1,500"? mơ hồ -> không đoán
    try:
        return float(s)
    except ValueError:
        return None


def hit(kw, h):
    """Từ khoá ngắn (<5 ký tự) phải khớp nguyên từ — tránh 'dn' dính 'brandname'."""
    if len(kw) < 5:
        return re.search(r"(?<![a-z])" + re.escape(kw) + r"(?![a-z])", h) is not None
    return kw in h


def find_header(ws, limit=25):
    best, best_score = None, 0
    for r in range(1, min(limit, ws.max_row) + 1):
        vals = [norm(c.value) for c in ws[r]]
        score = sum(1 for v in vals if v and any(
            hit(kw, v) for _, kws in COLMAP for kw in kws))
        if score > best_score:
            best, best_score = r, score
    return (best, best_score) if best_score >= 4 else (None, best_score)


def map_columns(ws, hrow):
    """Gán tham lam TOÀN CỤC. Tie-break bằng header ngắn hơn — để 'Amount (VND)'
    thắng 'Month amount by contract', 'Q'ty' thắng 'Q'ty by contract'."""
    hdr = {i: norm(c.value) for i, c in enumerate(ws[hrow], 1) if norm(c.value)}
    cand = []
    for field, kws in COLMAP:
        for i, h in hdr.items():
            best = max((len(kw) for kw in kws if hit(kw, h)), default=0)
            if best:
                cand.append((best, -len(h), field, i))
    cand.sort(reverse=True)
    out, used_f, used_c = {}, set(), set()
    for _, _, field, i in cand:
        if field in used_f or i in used_c:
            continue
        out[field] = i
        used_f.add(field); used_c.add(i)
    return out


def meta_of(ws, hrow):
    m = {}
    for r in range(1, hrow):
        cells = [c.value for c in ws[r]]
        for i, v in enumerate(cells):
            k = norm(v)
            if k in ("job no.", "job no", "project", "project no.:", "rev:", "rev",
                     "date:", "date", "package", "package:", "inquiry no.", "inquiry no",
                     "owner:", "plant location:"):
                for j in range(i + 1, min(i + 4, len(cells))):
                    val = cells[j]
                    if val not in (None, "", ":"):
                        m[k.rstrip(":.")] = str(val).strip()
                        break
    return m


def formulas_without_cache(path, limit=2000):
    """Đếm ô công thức không có giá trị lưu sẵn. File do phần mềm/script sinh ra
    mà chưa mở-lưu bằng Excel thì data_only=True đọc ra None -> tổng tiền rỗng."""
    wf = openpyxl.load_workbook(path, data_only=False, read_only=True)
    wv = openpyxl.load_workbook(path, data_only=True, read_only=True)
    out = {}
    for name in wf.sheetnames:
        n = seen = 0
        for rf, rv in zip(wf[name].iter_rows(), wv[name].iter_rows()):
            for cf, cv in zip(rf, rv):
                if isinstance(cf.value, str) and cf.value.startswith("="):
                    seen += 1
                    if cv.value is None:
                        n += 1
                    if seen >= limit:
                        break
            if seen >= limit:
                break
        if n:
            out[name] = n
    return out


def probe(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    print("FILE: %s" % os.path.basename(path))
    print("SHEETS: %d\n" % len(wb.sheetnames))
    nocache = formulas_without_cache(path)
    if nocache:
        print("⚠️  Có ô công thức CHƯA có giá trị lưu sẵn: %s" % nocache)
        print("    -> Mở file bằng Excel, bấm Save (để Excel tính và lưu kết quả), rồi "
              "probe lại.\n    Không build khi còn cảnh báo này: thành tiền sẽ bị rỗng.\n")
    for name in wb.sheetnames:
        ws = wb[name]
        hrow, score = find_header(ws)
        print("=" * 78)
        print("sheet %r   %d hàng x %d cột" % (name, ws.max_row, ws.max_column))
        if not hrow:
            print("  KHÔNG tìm được hàng header (score=%d) -> sheet tổng hợp/phụ trợ "
                  "hoặc layout lạ. Xem thủ công." % score)
            continue
        cols = map_columns(ws, hrow)
        print("  header ở hàng %d (khớp %d cột)" % (hrow, score))
        print("  meta: %s" % meta_of(ws, hrow))
        print("  cột nhận diện được:")
        for f, i in sorted(cols.items(), key=lambda x: x[1]):
            print("    %-12s -> cột %s  [%r]" % (
                f, openpyxl.utils.get_column_letter(i), str(ws.cell(hrow, i).value)[:38]))
        missing = [f for f, _ in COLMAP if f not in cols]
        print("  KHÔNG có: %s" % (", ".join(missing) or "-"))
        print("  3 dòng dữ liệu đầu (kiểm mắt xem map có đúng không):")
        shown = 0
        for r in range(hrow + 1, min(hrow + 40, ws.max_row) + 1):
            vals = {f: ws.cell(r, i).value for f, i in cols.items()}
            if not any(v not in (None, "") for v in vals.values()):
                continue
            print("    hàng %d: " % r + " · ".join(
                "%s=%s" % (f, str(v)[:22]) for f, v in vals.items() if v not in (None, "")))
            shown += 1
            if shown >= 3:
                break


def build(path, out):
    os.makedirs(os.path.join(out, "sheets"), exist_ok=True)
    # Dựng DB ở thư mục tạm cục bộ (SQLite không ghi được lên ổ mount của Cowork)
    tmpdir = tempfile.mkdtemp(prefix="boq_")
    tmpdb = os.path.join(tmpdir, "boq_build.db")
    db = sqlite3.connect(tmpdb)
    db.executescript("""
    CREATE TABLE sheets (
      sheet TEXT PRIMARY KEY, header_row INT, rows_total INT, lines_extracted INT,
      lines_in_scope INT, lines_zero INT, layout TEXT, meta TEXT);
    CREATE TABLE lines (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sheet TEXT, excel_row INT,
      area TEXT, system TEXT, item_code TEXT, description TEXT, size TEXT, unit TEXT,
      qty_client REAL, qty_bidder REAL, unit_price REAL,
      mat_unit REAL, mat_total REAL, lab_unit REAL, lab_total REAL, total REAL,
      brand TEXT, remark TEXT,
      row_kind TEXT,      -- item | section | subtotal
      in_scope INT,       -- 1 nếu total > 0
      qty_mismatch INT);  -- 1 nếu qty_bidder khác qty_client
    CREATE TABLE summary (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sheet TEXT, excel_row INT, item TEXT, amount REAL);
    CREATE INDEX ix_desc ON lines(description);
    CREATE INDEX ix_area ON lines(area);
    """)

    wb = openpyxl.load_workbook(path, data_only=True)
    total_lines = 0
    for name in wb.sheetnames:
        ws = wb[name]
        hrow, score = find_header(ws)
        if not hrow:
            # Sheet tổng hợp giá: chỉ là cặp "hạng mục - số tiền".
            n = 0
            for r in range(1, ws.max_row + 1):
                cells = [c.value for c in ws[r]]
                texts = [(i, str(v).strip()) for i, v in enumerate(cells)
                         if isinstance(v, str) and len(v.strip()) > 3]
                nums = [(i, num(v)) for i, v in enumerate(cells)
                        if num(v) is not None and not isinstance(v, str)]
                if len(texts) == 1 and len(nums) >= 1:
                    db.execute("INSERT INTO summary (sheet,excel_row,item,amount) "
                               "VALUES (?,?,?,?)", (name, r, texts[0][1], nums[0][1]))
                    n += 1
            db.execute("INSERT INTO sheets VALUES (?,?,?,?,?,?,?,?)",
                       (name, None, ws.max_row, n, 0, 0,
                        "summary" if n else "unrecognised",
                        json.dumps(meta_of(ws, min(12, ws.max_row)), ensure_ascii=False)))
            continue

        cols = map_columns(ws, hrow)
        meta = meta_of(ws, hrow)
        layout = "size_class" if "size" in cols else "area_local"
        last_area = last_sys = None
        n = nscope = nzero = 0
        for r in range(hrow + 1, ws.max_row + 1):
            def g(f):
                return ws.cell(r, cols[f]).value if f in cols else None

            desc = g("description")
            desc = str(desc).strip() if desc not in (None, "") else None
            area = g("area"); area = str(area).strip() if area not in (None, "") else None
            syst = g("system"); syst = str(syst).strip() if syst not in (None, "") else None
            # ô merge để trống ở dòng tiếp theo -> forward-fill
            if area:
                last_area = area
            else:
                area = last_area
            if syst:
                last_sys = syst
            else:
                syst = last_sys

            unit = g("unit"); unit = str(unit).strip() if unit not in (None, "") else None
            qc, qb = num(g("qty_client")), num(g("qty_bidder"))
            up = num(g("unit_price"))
            tot = num(g("total"))
            mu, mt = num(g("mat_unit")), num(g("mat_total"))
            lu, lt = num(g("lab_unit")), num(g("lab_total"))

            if not desc and tot is None and qb is None:
                continue
            if not unit and qb is None and qc is None:
                kind = "section" if tot is None else "subtotal"
            else:
                kind = "item"

            in_scope = 1 if (tot or 0) > 0 else 0
            mism = 1 if (qc is not None and qb is not None and abs(qc - qb) > 1e-9) else 0

            db.execute("""INSERT INTO lines
              (sheet,excel_row,area,system,item_code,description,size,unit,
               qty_client,qty_bidder,unit_price,mat_unit,mat_total,lab_unit,lab_total,
               total,brand,remark,row_kind,in_scope,qty_mismatch)
              VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (name, r, area, syst,
               str(g("item_code")).strip() if g("item_code") not in (None, "") else None,
               desc,
               str(g("size")).strip() if g("size") not in (None, "") else None,
               unit, qc, qb, up, mu, mt, lu, lt, tot,
               str(g("brand")).strip() if g("brand") not in (None, "") else None,
               str(g("remark")).strip() if g("remark") not in (None, "") else None,
               kind, in_scope, mism))
            n += 1
            if kind == "item":
                nscope += in_scope
                nzero += (0 if in_scope else 1)
        total_lines += n
        db.execute("INSERT INTO sheets VALUES (?,?,?,?,?,?,?,?)",
                   (name, hrow, ws.max_row, n, nscope, nzero, layout,
                    json.dumps(meta, ensure_ascii=False)))
    db.commit()

    cur = db.execute("SELECT * FROM lines ORDER BY sheet, excel_row")
    hdr = [d[0] for d in cur.description]
    with open(os.path.join(out, "boq_lines.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(hdr); w.writerows(cur.fetchall())

    def md(x):
        """Ô markdown: bỏ xuống dòng (brand hay có '\\n' -> vỡ bảng) và pipe."""
        if x is None:
            return ""
        return re.sub(r"\s+", " ", str(x)).replace("|", "/").strip()

    for (sheet, hrow, rows_total, nlines, nscope, nzero, layout, metaj) in db.execute(
            "SELECT * FROM sheets ORDER BY sheet"):
        meta = json.loads(metaj)
        safe = re.sub(r"[^A-Za-z0-9._ -]", "_", sheet).strip()
        L = ["---", "sheet: %s" % sheet, "header_row: %s" % hrow, "layout: %s" % layout,
             "lines: %d" % nlines, "in_scope: %d" % nscope, "zero_price: %d" % nzero,
             "---", "", "# %s" % sheet, ""]
        if meta:
            L += ["| Trường | Giá trị |", "|---|---|"]
            L += ["| %s | %s |" % (k, md(v)) for k, v in meta.items()] + [""]
        if hrow is None:
            srows = db.execute("SELECT excel_row,item,amount FROM summary WHERE sheet=? "
                               "ORDER BY excel_row", (sheet,)).fetchall()
            if srows:
                L += ["> Sheet tổng hợp giá — trích dạng *hạng mục -> số tiền*, không phải "
                      "bảng khối lượng. **Trích tự động ở đây KHÔNG đầy đủ** (ô merge, tiêu "
                      "đề nhiều cấp). Sheet này thường nhỏ — mở Excel đọc thủ công và viết "
                      "lại cấu trúc giá vào `boq-index.md`.", "",
                      "| Dòng | Hạng mục | Số tiền (VNĐ) |", "|---:|---|---:|"]
                L += ["| %d | %s | %s |" % (r, md(i), format(a, ",.0f")) for r, i, a in srows]
                L += [""]
            else:
                L += ["> Không nhận diện được hàng header — sheet này CHƯA trích.",
                      "> Mở Excel xem thủ công, đừng suy đoán số liệu.", ""]
        else:
            rows = db.execute(
                "SELECT excel_row,area,system,item_code,description,size,unit,"
                "qty_client,qty_bidder,COALESCE(unit_price, "
                "COALESCE(mat_unit,0)+COALESCE(lab_unit,0)),total,brand,row_kind,"
                "in_scope,qty_mismatch "
                "FROM lines WHERE sheet=? ORDER BY excel_row", (sheet,)).fetchall()
            tot = db.execute("SELECT SUM(total) FROM lines WHERE sheet=? AND row_kind='item'",
                             (sheet,)).fetchone()[0] or 0
            L += ["**Tổng cộng dòng item: %s VNĐ** · %d dòng trong phạm vi · "
                  "%d dòng giá 0 (ngoài phạm vi)" % (format(tot, ",.0f"), nscope, nzero), "",
                  "| Dòng | Khu vực | Hệ/Class | Mã | Mô tả | Size | ĐVT | KL CĐT | KL NT "
                  "| Đơn giá | Thành tiền | Nhãn hiệu | ⚑ |",
                  "|---:|---|---|---|---|---|---|---:|---:|---:|---:|---|---|"]
            for (er, a, s, ic, d, sz, u, qc, qb, up, t, b, kind, insc, mism) in rows:
                flag = ("§" if kind != "item" else "") + \
                       ("∅" if kind == "item" and not insc else "") + ("≠" if mism else "")
                f_ = lambda x: "" if x is None else (
                    format(x, ",.0f") if abs(x) >= 1000 else ("%g" % x))
                L.append("| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                    er, md(a), md(s), md(ic), md(d), md(sz), md(u),
                    f_(qc), f_(qb), f_(up or None), f_(t), md(b), flag))
            L += ["", "> **⚑**: `§` dòng tiêu đề/cộng · `∅` giá = 0 -> **ngoài phạm vi hợp "
                  "đồng** · `≠` khối lượng nhà thầu khác khối lượng chủ đầu tư.", ""]
        open(os.path.join(out, "sheets", safe + ".md"), "w", encoding="utf-8").write("\n".join(L))

    db.commit(); db.close()
    shutil.copy(tmpdb, os.path.join(out, "boq.db"))
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("OK — %d dòng -> %s/boq.db · boq_lines.csv · sheets/*.md" % (total_lines, out))
    print("Bước tiếp theo BẮT BUỘC: python3 boq_extract.py check %s" % out)


TOTAL_WORDS = ("grand total", "tong cong", "tong gia tri", "total amount",
               "sub total", "subtotal", "sub-total", "cong", "total")


def check(out):
    """Đối soát: tổng dòng item mỗi sheet so với dòng TỔNG ghi sẵn trong workbook.
    Không tự sửa gì — chỉ báo khớp / lệch để người làm quyết."""
    dbp = os.path.join(out, "boq.db")
    if not os.path.exists(dbp):
        sys.exit("Không thấy %s — chạy build trước." % dbp)
    db = sqlite3.connect(dbp)
    bad = 0
    print("%-28s %18s %18s  %s" % ("SHEET", "TỔNG DÒNG ITEM", "DÒNG TỔNG LỚN NHẤT", "KẾT QUẢ"))
    for (sheet,) in db.execute("SELECT sheet FROM sheets WHERE header_row IS NOT NULL "
                               "ORDER BY sheet"):
        s = db.execute("SELECT COALESCE(SUM(total),0) FROM lines WHERE sheet=? AND "
                       "row_kind='item'", (sheet,)).fetchone()[0]
        cands = []
        for er, d, t in db.execute("SELECT excel_row, description, total FROM lines WHERE "
                                   "sheet=? AND row_kind!='item' AND total IS NOT NULL",
                                   (sheet,)):
            nd = norm(d)
            if any(hit(w, nd) for w in TOTAL_WORDS):
                cands.append((t, er, d))
        if not cands:
            print("%-28s %18s %18s  ? không thấy dòng TỔNG — so tay với Excel"
                  % (sheet[:28], format(s, ",.0f"), "-"))
            continue
        t, er, d = max(cands)
        ok = abs(s - t) <= max(1.0, abs(t) * 1e-9)
        bad += 0 if ok else 1
        print("%-28s %18s %18s  %s (dòng %d: %s)" % (
            sheet[:28], format(s, ",.0f"), format(t, ",.0f"),
            "KHỚP" if ok else "LỆCH %s" % format(s - t, ",.0f"), er, str(d)[:30]))
    zero_total = db.execute("SELECT COUNT(*) FROM lines WHERE row_kind='item' AND "
                            "total IS NULL AND (qty_bidder IS NOT NULL OR qty_client "
                            "IS NOT NULL)").fetchone()[0]
    if zero_total:
        print("\n⚠️  %d dòng item có khối lượng nhưng thành tiền rỗng — kiểm map cột "
              "`total` hoặc công thức chưa có giá trị lưu sẵn." % zero_total)
    print("\n" + ("✅ Mọi sheet có dòng TỔNG đều khớp." if not bad else
                  "❌ %d sheet lệch — sửa cho khớp tuyệt đối rồi mới đi tiếp." % bad))
    db.close()
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    if sys.argv[1] == "probe":
        probe(sys.argv[2])
    elif sys.argv[1] == "check":
        check(sys.argv[2])
    elif sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
