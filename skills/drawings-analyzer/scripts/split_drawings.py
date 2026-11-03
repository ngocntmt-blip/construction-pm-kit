#!/usr/bin/env python3
"""
Split a merged drawing-set PDF (one file, many sheets) into one PDF per
sheet, so each sheet can be inventoried, summarised and cited on its own.

Each output file is named from the sheet number found in the page's text
layer when one can be detected (e.g. "M-101.pdf"); otherwise it falls back
to "page_003.pdf". Sheet-number detection is a best guess — Step 1 still
reads the title block and records the real sheet number in drawings.md.

Optionally renders a PNG preview per sheet (--png) for quick visual checks
of raster/scanned sheets. PNGs are previews only: never count symbols or
measure off them (learning #1).

The source PDF is never modified.

Usage:
    python split_drawings.py <merged.pdf> <out_dir> [--png] [--dpi 110]
                             [--pattern REGEX] [--json]

Prints one row per page: page, output file, detected sheet no., chars.
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pdfplumber
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("pdfplumber and pypdf are required: "
          "pip install pdfplumber pypdf --break-system-packages", file=sys.stderr)
    sys.exit(1)

# Typical sheet numbers: M-101, FP-201, E-001A, S101, A-3.01, HVAC-01
DEFAULT_PATTERN = r"\b([A-Z]{1,4}[-_. ]?\d{1,3}(?:[.\-]\d{1,3})?[A-Z]?)\b"
# Sheet numbers usually sit in the title block (bottom-right corner).
TITLE_BLOCK_X = 0.60
TITLE_BLOCK_Y = 0.70
SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def detect_sheet_no(page, pattern: re.Pattern):
    """Return the most likely sheet number from the title-block area, or None."""
    w, h = page.width, page.height
    # Filter words by where they START (not crop): crop clips text that runs
    # past the page edge, which often happens in title blocks.
    try:
        words = page.extract_words() or []
    except Exception:
        words = []
    text = " ".join(wd["text"] for wd in words
                    if wd["x0"] >= w * TITLE_BLOCK_X and wd["top"] >= h * TITLE_BLOCK_Y)
    candidates = pattern.findall(text)
    if not candidates:
        return None
    # The last candidate in reading order is usually the sheet number box.
    return candidates[-1].replace(" ", "-")


def unique_name(base: str, used: set) -> str:
    name, n = base, 2
    while name.lower() in used:
        name = f"{base}_{n}"
        n += 1
    used.add(name.lower())
    return name


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--png", action="store_true", help="also render a PNG preview per sheet")
    parser.add_argument("--dpi", type=int, default=110, help="PNG preview resolution (default 110)")
    parser.add_argument("--pattern", default=DEFAULT_PATTERN,
                        help="regex for sheet numbers (first group is used)")
    parser.add_argument("--json", action="store_true", help="output JSON instead of a table")
    args = parser.parse_args()

    if not args.pdf_path.exists():
        print(f"File not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)
    if args.out_dir.resolve() == args.pdf_path.parent.resolve():
        print("out_dir must differ from the source folder (never write next to originals).",
              file=sys.stderr)
        sys.exit(1)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(args.pattern)
    reader = PdfReader(str(args.pdf_path))
    used, rows = set(), []

    with pdfplumber.open(args.pdf_path) as pdf:
        for i, (page, rpage) in enumerate(zip(pdf.pages, reader.pages), start=1):
            text = page.extract_text() or ""
            sheet_no = detect_sheet_no(page, pattern)
            base = SAFE_NAME.sub("_", sheet_no) if sheet_no else f"page_{i:03d}"
            name = unique_name(base, used)

            writer = PdfWriter()
            writer.add_page(rpage)
            out_pdf = args.out_dir / f"{name}.pdf"
            with open(out_pdf, "wb") as f:
                writer.write(f)

            png = None
            if args.png:
                png = args.out_dir / f"{name}.png"
                page.to_image(resolution=args.dpi).save(str(png))

            rows.append({
                "page": i,
                "file": out_pdf.name,
                "png": png.name if png else None,
                "detected_sheet_no": sheet_no,
                "char_count": len(text.strip()),
            })

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    print(f"{'page':<6}{'file':<28}{'sheet_no?':<14}chars")
    for r in rows:
        print(f"{r['page']:<6}{r['file']:<28}{(r['detected_sheet_no'] or '-'):<14}{r['char_count']}")
    undetected = [r["page"] for r in rows if not r["detected_sheet_no"]]
    print(f"\n{len(rows)} sheet(s) written to {args.out_dir}")
    if undetected:
        print(f"No sheet number detected on page(s) {undetected} — read the title block "
              "in Step 1 and record the real number in drawings.md.")


if __name__ == "__main__":
    main()
