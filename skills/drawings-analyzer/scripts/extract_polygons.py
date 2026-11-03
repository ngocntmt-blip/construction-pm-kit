#!/usr/bin/env python3
"""
Extract closed polygons from the VECTOR layer of one drawing sheet and
convert their area to real-world m² using the drawing scale — for answering
"diện tích khu vực / phòng / sàn X là bao nhiêu" questions.

This is an OPTIONAL helper (Step 6b in SKILL.md), not a quantity takeoff.
Results are always reliability = "inferred": they depend on how the
drafter drew the outline, and must be cross-checked against the dimension
strings on the drawing before being reported as a figure.

How it works
  * Reads rectangles and closed curves/polylines from the PDF vector layer
    (pdfplumber). A raster/scanned sheet has none — the script says so and
    stops; never estimate an area from a picture.
  * Area by the shoelace formula, in PDF points², then converted:
      paper mm = pt × 25.4 / 72 ;  real m² = (paper mm² × scale²) / 1e6
  * Removes near-duplicate polygons (same outline drawn twice / on two
    layers) to avoid double-counting, and reports how many were dropped.
  * --label "KHO" keeps only polygons that contain that text label;
    --bbox x0,y0,x1,y1 (fractions of the page, 0–1) limits to a region.

Usage:
    python extract_polygons.py <sheet.pdf> --scale 100 [--page 1]
           [--label TEXT] [--bbox 0,0,1,1] [--min-area 1.0]
           [--check-dim 12000] [--top 30] [--json]

  --scale       drawing scale denominator (1:100 → 100). REQUIRED — take it
                from the title block / scale bar; never assume it.
  --min-area    ignore polygons smaller than this many m² (default 1.0)
  --check-dim   a known dimension on the sheet in mm (e.g. a 12000 grid
                span); the script reports the longest polygon edge in mm at
                the given scale so you can confirm the scale is right.

Prints one row per polygon (largest first) and a total. Does not modify
the PDF.
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

PT_TO_MM = 25.4 / 72.0
CLOSE_TOL_PT = 1.0      # first/last point closer than this → treated as closed
DUP_TOL = 0.01          # polygons within 1% area + same centre → duplicates


def shoelace(pts):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def centroid(pts):
    xs, ys = zip(*pts)
    return sum(xs) / len(xs), sum(ys) / len(ys)


def point_in_poly(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def longest_edge(pts):
    return max(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
               for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))


def collect_polygons(page):
    polys = []
    for r in page.rects:
        polys.append(("rect", [(r["x0"], r["top"]), (r["x1"], r["top"]),
                               (r["x1"], r["bottom"]), (r["x0"], r["bottom"])]))
    for c in page.curves:
        pts = [(float(x), float(y)) for x, y in (c.get("pts") or [])]
        if len(pts) < 3:
            continue
        (fx, fy), (lx, ly) = pts[0], pts[-1]
        closed = ((fx - lx) ** 2 + (fy - ly) ** 2) ** 0.5 <= CLOSE_TOL_PT or c.get("fill")
        if not closed:
            continue
        if ((fx - lx) ** 2 + (fy - ly) ** 2) ** 0.5 <= CLOSE_TOL_PT:
            pts = pts[:-1]
        if len(pts) >= 3:
            polys.append(("polyline", pts))
    return polys


def dedupe(items):
    kept, dropped = [], 0
    for it in items:
        dup = False
        for k in kept:
            if abs(it["area_pt2"] - k["area_pt2"]) <= DUP_TOL * max(k["area_pt2"], 1e-9):
                dx = it["cx"] - k["cx"]
                dy = it["cy"] - k["cy"]
                if (dx * dx + dy * dy) ** 0.5 <= 2.0:
                    dup = True
                    break
        if dup:
            dropped += 1
        else:
            kept.append(it)
    return kept, dropped


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("pdf_path", type=Path)
    p.add_argument("--scale", type=float, required=True, help="scale denominator, e.g. 100 for 1:100")
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--label", help="keep only polygons containing this text label")
    p.add_argument("--bbox", help="x0,y0,x1,y1 as page fractions 0–1")
    p.add_argument("--min-area", type=float, default=1.0, help="minimum area in m² (default 1.0)")
    p.add_argument("--check-dim", type=float, help="known dimension in mm to confirm the scale")
    p.add_argument("--top", type=int, default=30, help="rows to print (default 30)")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    if not a.pdf_path.exists():
        print(f"File not found: {a.pdf_path}", file=sys.stderr)
        sys.exit(1)
    if a.scale <= 0:
        print("--scale must be > 0", file=sys.stderr)
        sys.exit(1)

    pt2_to_m2 = (PT_TO_MM * a.scale) ** 2 / 1e6
    pt_to_real_mm = PT_TO_MM * a.scale

    with pdfplumber.open(a.pdf_path) as pdf:
        if not 1 <= a.page <= len(pdf.pages):
            print(f"Page {a.page} out of range (1–{len(pdf.pages)})", file=sys.stderr)
            sys.exit(1)
        page = pdf.pages[a.page - 1]
        W, H = page.width, page.height
        raw = collect_polygons(page)
        if not raw:
            print("No vector polygons on this page — likely a scanned/raster sheet or the "
                  "outline is drawn as separate lines. Do not estimate area from the image; "
                  "flag as a placeholder and use dimension strings or the CAD/BIM file.")
            sys.exit(2)

        label_pts = []
        if a.label:
            words = page.extract_words() or []
            label_pts = [((w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2)
                         for w in words if a.label.lower() in w["text"].lower()]
            if not label_pts:
                print(f"Label '{a.label}' not found in the text layer of page {a.page}.")
                sys.exit(2)

    box = None
    if a.bbox:
        x0, y0, x1, y1 = [float(v) for v in a.bbox.split(",")]
        box = (x0 * W, y0 * H, x1 * W, y1 * H)

    items = []
    for kind, pts in raw:
        area_pt2 = shoelace(pts)
        area_m2 = area_pt2 * pt2_to_m2
        if area_m2 < a.min_area:
            continue
        if area_pt2 >= 0.95 * W * H:      # sheet border / frame
            continue
        cx, cy = centroid(pts)
        if box and not (box[0] <= cx <= box[2] and box[1] <= cy <= box[3]):
            continue
        if label_pts and not any(point_in_poly(x, y, pts) for x, y in label_pts):
            continue
        items.append({
            "kind": kind, "vertices": len(pts), "area_pt2": area_pt2,
            "area_m2": round(area_m2, 2), "cx": cx, "cy": cy,
            "longest_edge_mm": round(longest_edge(pts) * pt_to_real_mm),
            "centre_page_frac": [round(cx / W, 3), round(cy / H, 3)],
        })

    items.sort(key=lambda d: d["area_pt2"], reverse=True)
    kept, dropped = dedupe(items)

    # With --label, the smallest enclosing polygon is the room/zone itself;
    # larger ones are the building outline etc.
    if a.label and kept:
        kept = sorted(kept, key=lambda d: d["area_pt2"])

    result = {
        "sheet": a.pdf_path.name, "page": a.page, "scale": f"1:{int(a.scale)}",
        "label": a.label, "polygons": len(kept), "duplicates_removed": dropped,
        "reliability": "inferred",
        "what_to_verify": "Cross-check against dimension strings on the sheet before reporting.",
        "items": [{k: v for k, v in d.items() if k not in ("area_pt2", "cx", "cy")} for d in kept],
    }
    if a.check_dim and kept:
        longest = max(d["longest_edge_mm"] for d in kept)
        result["scale_check"] = {"known_dim_mm": a.check_dim, "longest_edge_mm": longest}

    if a.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print(f"{result['sheet']} p.{a.page}  scale {result['scale']}"
          + (f"  label '{a.label}'" if a.label else ""))
    print(f"{'#':<4}{'area m²':>12}  {'kind':<9}{'verts':>6}{'longest edge mm':>18}  centre(page %)")
    for i, d in enumerate(result["items"][:a.top], start=1):
        cx, cy = d["centre_page_frac"]
        print(f"{i:<4}{d['area_m2']:>12,.2f}  {d['kind']:<9}{d['vertices']:>6}"
              f"{d['longest_edge_mm']:>18,}  {cx*100:.0f}%, {cy*100:.0f}%")
    if len(result["items"]) > a.top:
        print(f"... {len(result['items']) - a.top} more (use --top or --json)")
    print(f"\n{len(kept)} polygon(s); {dropped} near-duplicate(s) removed.")
    if not a.label:
        print("Polygons can nest (building outline contains rooms) — do NOT sum them blindly.")
    if "scale_check" in result:
        sc = result["scale_check"]
        print(f"Scale check: known {sc['known_dim_mm']:,.0f} mm vs longest edge "
              f"{sc['longest_edge_mm']:,} mm — if far apart, the scale is wrong.")
    print("Reliability: inferred — cross-check with dimension strings before reporting.")


if __name__ == "__main__":
    main()
