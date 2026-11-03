#!/usr/bin/env python3
"""
Report text density per page/sheet of a drawing PDF, to decide the
vector/raster fork (learning #5): a page with a real vector text layer can
be extracted near-losslessly from text; a page with little/no extractable
text (a scan, or text that's actually outlined vector shapes) needs a
vision pass instead — and should be flagged as a placeholder, never
fabricated.

Usage:
    python process_drawing.py <path_to_pdf> [--json]

Prints one row per page: page number, character count, and a verdict
(vector_text / needs_vision), plus a short reason.
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("pdfplumber is required: pip install pdfplumber --break-system-packages",
          file=sys.stderr)
    sys.exit(1)

# Below this many characters on a page, treat it as "no usable text layer"
# even if a handful of stray characters were extracted (e.g. a title block).
MIN_CHARS_FOR_VECTOR = 40


def analyze_pdf(pdf_path: Path) -> list[dict]:
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            char_count = len(text.strip())
            verdict = "vector_text" if char_count >= MIN_CHARS_FOR_VECTOR else "needs_vision"
            reason = (
                f"{char_count} chars extracted"
                if verdict == "vector_text"
                else f"only {char_count} chars extracted — likely a scan or outlined text"
            )
            results.append({
                "page": i,
                "char_count": char_count,
                "verdict": verdict,
                "reason": reason,
            })
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("--json", action="store_true", help="output JSON instead of a table")
    args = parser.parse_args()

    if not args.pdf_path.exists():
        print(f"File not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    results = analyze_pdf(args.pdf_path)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print(f"{'page':<6}{'chars':<8}{'verdict':<14}reason")
    for r in results:
        print(f"{r['page']:<6}{r['char_count']:<8}{r['verdict']:<14}{r['reason']}")

    needs_vision = [r["page"] for r in results if r["verdict"] == "needs_vision"]
    if needs_vision:
        print(f"\n{len(needs_vision)} page(s) need a vision pass: {needs_vision}")
        print("Flag these as placeholders in the database — do not fabricate values for them.")


if __name__ == "__main__":
    main()
