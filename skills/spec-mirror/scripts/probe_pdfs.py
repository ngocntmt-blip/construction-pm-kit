#!/usr/bin/env python3
"""
Khảo sát nhanh một thư mục specification trước khi đọc.

Với mỗi PDF, báo: số trang, số ký tự trích được, và verdict
vector_text / needs_vision. Mục đích là biết trước file nào đọc được
bằng text (chính xác 100%, rẻ) và file nào là bản scan (phải dùng
vision, chậm và dễ sai) — để không im lặng bịa số liệu từ một bản scan.

Cũng đoán loại tài liệu từ tên file và mã tài liệu, vì Design Description
là nguồn thông số thiết kế quan trọng nhất và nên được đọc kỹ nhất.

Dùng:
    python probe_pdfs.py <thư_mục_hoặc_file> [--json] [--dump <thư_mục_text>]

  --dump   ghi text từng file ra <thư_mục_text>/<tên file>.txt, có dấu
           "=== TRANG n ===" trước mỗi trang — để đọc bằng grep và ghi được
           số trang nguồn cho từng con số trong mirror. Không ghi vào thư mục
           chứa PDF gốc.

Ưu tiên poppler-utils (pdftotext, pdfinfo) — nhanh nhất. Máy không có
poppler (thường gặp trên Windows) thì tự chuyển sang PyMuPDF
(pip install pymupdf), cũng nhanh; pdfplumber chỉ là phương án cuối.
"""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path

HAVE_POPPLER = bool(shutil.which('pdftotext') and shutil.which('pdfinfo'))

MIN_CHARS_PER_PAGE = 120   # trang dưới mức này coi như không có lớp text dùng được
# Đánh giá TỪNG TRANG, không lấy trung bình cả file: trang bìa / trang trống ít
# chữ không được làm cả file bị coi là scan, và vài trang scan chèn giữa file
# text (bảng tính, bản vẽ đính kèm) không được bị che mất.


def doc_kind(name: str) -> str:
    n = name.upper()
    if re.search(r'\bDD\b|DESIGN[ _-]?DESCRIPTION|THUYET[ _-]?MINH', n):
        return 'design_description'
    if re.search(r'\bDS\b|DATASHEET|DATA[ _-]SHEET', n):
        return 'datasheet'
    if re.search(r'\bSP\b|SPECIFICATION|SPEC\b', n):
        return 'specification'
    return 'unknown'


def page_texts(pdf: Path) -> list[str]:
    """Text từng trang (giữ bố cục). Thứ tự: poppler → PyMuPDF → pdfplumber."""
    if HAVE_POPPLER:
        txt = subprocess.run(['pdftotext', '-layout', str(pdf), '-'],
                             capture_output=True, text=True, timeout=300).stdout
        pages = txt.split('\f')
        if pages and not pages[-1].strip():
            pages = pages[:-1]
        return pages
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            pymupdf = None
    if pymupdf:
        with pymupdf.open(str(pdf)) as doc:
            return [p.get_text('text', sort=True) for p in doc]
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError('cần poppler-utils, hoặc pip install pymupdf')
    with pdfplumber.open(pdf) as doc:   # chậm — chỉ dùng khi không còn cách nào
        return [p.extract_text(layout=True) or '' for p in doc.pages]


def probe(pdf: Path, dump_dir: Path | None = None) -> dict:
    try:
        pages_txt = page_texts(pdf)
    except subprocess.TimeoutExpired:
        return {'file': pdf.name, 'error': 'pdftotext timeout'}
    except Exception as e:
        return {'file': pdf.name, 'error': f'đọc PDF lỗi: {e}'}
    pages = len(pages_txt)
    txt = '\n'.join(pages_txt)

    if dump_dir:
        dump_dir.mkdir(parents=True, exist_ok=True)
        out = dump_dir / (pdf.stem + '.txt')
        out.write_text(''.join(f'\n=== TRANG {i} ===\n{p}'
                               for i, p in enumerate(pages_txt, 1)), encoding='utf-8')

    chars = len(txt.strip())
    per_page = chars / pages if pages else 0
    low = [i for i, p in enumerate(pages_txt, 1) if len(p.strip()) < MIN_CHARS_PER_PAGE]
    text_pages = pages - len(low)
    if pages == 0 or text_pages == 0:
        verdict = 'needs_vision'
    elif text_pages < pages / 2:
        verdict = 'mostly_scan'
    else:
        verdict = 'vector_text'

    # revision + ngày phát hành, nếu trang bìa có
    rev = re.search(r'REV\.?\s*(?:NO\.?|CODE)?\s*[:\s]\s*([A-Z0-9]{1,3})\b', txt[:4000], re.I)
    date = re.search(r'(\d{2}[/-]\d{2}[/-]\d{4})', txt[:4000])

    return {
        'file': pdf.name,
        'kind': doc_kind(pdf.name),
        'pages': pages,
        'chars': chars,
        'chars_per_page': round(per_page),
        'verdict': verdict,
        'low_text_pages': low,
        'revision': rev.group(1) if rev else None,
        'issue_date': date.group(1) if date else None,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('path', type=Path)
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--dump', type=Path, help='thư mục ghi text từng trang')
    a = ap.parse_args()

    if not a.path.exists():
        sys.exit(f'Không tìm thấy: {a.path}')
    pdfs = sorted(a.path.rglob('*.pdf')) if a.path.is_dir() else [a.path]
    if not pdfs:
        sys.exit('Không có PDF nào trong thư mục.')

    if a.dump:
        src = a.path.resolve() if a.path.is_dir() else a.path.resolve().parent
        d = a.dump.resolve()
        if d == src or src in d.parents:
            sys.exit('--dump phải nằm ngoài thư mục chứa PDF gốc.')
    rows = [probe(p, a.dump) for p in pdfs]

    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    order = {'design_description': 0, 'specification': 1, 'datasheet': 2, 'unknown': 3}
    rows.sort(key=lambda r: order.get(r.get('kind', 'unknown'), 9))

    print(f'{"FILE":<58} {"LOẠI":<19} {"TR.":>4} {"KÝ TỰ/TR":>9}  VERDICT')
    print('-' * 108)
    for r in rows:
        if 'error' in r:
            print(f'{r["file"][:57]:<58} {"":<19} {"":>4} {"":>9}  LỖI: {r["error"]}')
            continue
        print(f'{r["file"][:57]:<58} {r["kind"]:<19} {r["pages"]:>4} '
              f'{r["chars_per_page"]:>9}  {r["verdict"]}')

    need = [r for r in rows if r.get('verdict') in ('needs_vision', 'mostly_scan')]
    partial = [r for r in rows if r.get('verdict') == 'vector_text' and r.get('low_text_pages')]
    dd = [r for r in rows if r.get('kind') == 'design_description']
    print()
    print(f'Bộ đọc: {"pdftotext (poppler)" if HAVE_POPPLER else "PyMuPDF/pdfplumber (không có poppler)"}')
    if a.dump:
        print(f'Text từng trang đã ghi vào: {a.dump}  (tìm "=== TRANG n ===" để lấy số trang)')
    if dd:
        print(f'→ Đọc kỹ nhất: {", ".join(r["file"] for r in dd)} '
              f'(Design Description = nguồn thông số thiết kế)')
    if need:
        print(f'⚠️  {len(need)} file không có lớp text dùng được — cần đọc bằng vision, '
              f'và phải ghi rõ "nguồn scan" trong mirror:')
        for r in need:
            print(f'   - {r["file"]}')
    if partial:
        print('ℹ️  File có lớp text nhưng vài trang ít/không có chữ (bìa, trang trống, '
              'hoặc trang scan chèn giữa) — mở xem các trang này:')
        for r in partial:
            pg = r['low_text_pages']
            print(f'   - {r["file"]}: tr. {", ".join(map(str, pg[:15]))}'
                  f'{" …" if len(pg) > 15 else ""}')
    if not need and not partial:
        print('✅ Tất cả file đều có lớp text vector — trích xuất bằng text là chính xác.')


if __name__ == '__main__':
    main()
