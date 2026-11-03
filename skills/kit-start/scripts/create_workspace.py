#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_workspace.py — Bước 1 của kit-start: dựng cấu trúc folder công ty + dự án,
mỗi folder có _README.md nói rõ upload gì vào đó.

    python3 create_workspace.py <workspace> [--project TÊN] [--disciplines PCCC,HVAC]
            [--tree folder-tree.json] [--ps1 <file.ps1>] [--dry-run]

  <workspace>      thư mục gốc của MỘT công ty, ví dụ D:\\ALPHA
  --project        tên folder dự án (HOA, không dấu, không khoảng trắng). Bỏ trống
                   = chỉ dựng khu _COMPANY.
  --disciplines    bộ môn → folder con trong 03_SPECIFICATION. Không có thì để flat.
  --ps1            không tạo folder, chỉ xuất script PowerShell để người dùng tự chạy
                   (khi Claude không có shell trên máy người dùng).
  --dry-run        chỉ in danh sách sẽ tạo.

Không ghi đè file nào đã có, không xoá, không đổi tên. Folder đã có thì giữ
nguyên và chỉ bổ sung phần thiếu.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TREE = os.path.join(HERE, "..", "references", "folder-tree.json")
ROLE_BADGE = {
    "upload": "📥 UPLOAD — bỏ tài liệu của bạn vào folder này",
    "claude": "🤖 CLAUDE GHI — không upload tài liệu vào đây",
    "work": "🗂 LÀM VIỆC — lưu hồ sơ hằng ngày của dự án",
}
NAME_OK = re.compile(r"^[A-Z0-9][A-Z0-9_.\-]*$")


def today_vn():
    return (datetime.now(timezone.utc) + timedelta(hours=7)).strftime("%d/%m/%Y")


def walk(tree, base):
    """→ list (đường dẫn tương đối, role, note)."""
    out = []
    for name, node in tree.items():
        if name.startswith("_note"):
            continue
        rel = os.path.join(base, name) if base else name
        out.append((rel, node.get("role", "work"), node.get("note", "")))
        if node.get("children"):
            out.extend(walk(node["children"], rel))
    return out


def readme(rel, role, note):
    return "# %s\n\n**%s**\n\n%s\n" % (rel.replace("\\", "/"), ROLE_BADGE.get(role, role), note)


def claude_md(project):
    return f"""# CLAUDE.md — Dự án {project}

> ĐỌC FILE NÀY ĐẦU MỖI PHIÊN. Tài liệu nguồn nằm sẵn trong folder — không yêu cầu upload lại.
> Trạng thái onboarding: `00_AI-CONTEXT/ONBOARDING.md`. Chưa xong bước 5 (dựng context) thì chạy `kit-start` trước mọi task khác.

## Đọc gì trước?
| Cần biết | Đọc file |
|---|---|
| Dự án, vai trò, folder STATIC/LIVE | `00_AI-CONTEXT/project.md` |
| Các bên, đầu mối, ai TO ai CC | `00_AI-CONTEXT/parties.md` |
| Quy trình hồ sơ của dự án (mã, transmittal, thời hạn) | `00_AI-CONTEXT/doc-control.md` |
| Điều khoản hợp đồng | `00_AI-CONTEXT/contract.md` |
| Công ty: template, quy trình, người ký | `<_COMPANY/_PROFILE>` (đường dẫn trong `00_AI-CONTEXT/project.json`) |
| BOQ (tra dòng, đơn giá, phạm vi) | `00_AI-CONTEXT/boq/README.md` |
| Spec kỹ thuật | `00_AI-CONTEXT/specs.md` |
| Bản vẽ | `00_AI-CONTEXT/drawings/` |
| Phạm vi công việc theo gói | `00_AI-CONTEXT/scope-brief.md` |
| Đã làm gì các phiên trước | `WORKLOG.md` |

## Tóm tắt 10 giây
[chưa có — kit-start điền sau bước 4]

## Lưu file mới ở đâu
| Loại | Vị trí |
|---|---|
| Bản nháp Claude vừa dựng | `90_CLAUDE-OUTPUT/_INBOX/` |
| Transmittal gởi đi | `10_TRANSMITTAL/OUT/<số transmittal>_<tiêu đề>/` |
| Biện pháp thi công | `04_EXECUTION/MOS/` |
| Kế hoạch tuần | `04_EXECUTION/WEEKLY-PLAN/` |
| Báo cáo ngày/tuần | `08_SCHEDULE-REPORT/` |
| Trình duyệt vật tư | `07_MATERIAL/` |
| RFI / SI / VO | `09_RFI-SI-VO/` |

## Quy tắc
- Không ghi đè, không xoá file. Trùng tên → dừng, hỏi.
- Sửa tại chỗ; mọi chỗ Claude điền/sửa tô vàng.
- File trên đĩa là bản gốc duy nhất — không dựng lại từ bản trong phiên.
- Chỉ dùng hồ sơ, template, thuật ngữ của công ty sở hữu workspace này.

**Sau mỗi phiên:** thêm mục mới ở ĐẦU `WORKLOG.md`.
"""


def worklog_md(project):
    return f"""# WORKLOG — {project}

> Mục mới thêm ở ĐẦU. Mỗi phiên một mục.

## Nhật ký phiên

### {today_vn()} — Bước 1: tạo cấu trúc folder (kit-start)
- Dựng cây folder dự án + khu _COMPANY.
- Tiếp theo: upload tài liệu theo `_README.md` trong từng folder 📥, rồi gọi lại `kit-start`.
"""


def onboarding_md(scope, name):
    return f"""# ONBOARDING — {scope}: {name}

> kit-start đọc file này để biết đang ở bước nào. Đánh [x] khi xong, ghi ngày (DD/MM/YYYY).

- [x] 1. Tạo cấu trúc folder — {today_vn()}
- [ ] 2. Người dùng upload tài liệu vào các folder 📥
- [ ] 3. Claude đọc tài liệu, dựng hồ sơ nháp
- [ ] 4. Interview: hỏi dữ kiện còn thiếu / chỉ tài liệu cần upload thêm — người dùng xác nhận hồ sơ
- [ ] 5. Dựng context BẮT BUỘC: boq-mirror (nếu có BOQ) · spec-mirror (nếu có spec) · drawings-analyzer (nếu có bản vẽ) · scope-brief
- [ ] 6. Sẵn sàng làm task (doc-from-template và các việc khác)

## Ghi chú
"""


def plan(ws, project, disciplines, tree):
    items = []  # (rel_path, kind, content)  kind: dir | file
    for rel, role, note in walk(tree["company"], ""):
        items.append((rel, "dir", None))
        items.append((os.path.join(rel, "_README.md"), "file", readme(rel, role, note)))
    items.append((os.path.join("_COMPANY", "_PROFILE", "ONBOARDING.md"), "file",
                  onboarding_md("Công ty", os.path.basename(os.path.abspath(ws)))))
    if project:
        for rel, role, note in walk(tree["project"], project):
            items.append((rel, "dir", None))
            items.append((os.path.join(rel, "_README.md"), "file", readme(rel, role, note)))
        for d in disciplines:
            rel = os.path.join(project, "03_SPECIFICATION", d)
            items.append((rel, "dir", None))
            items.append((os.path.join(rel, "_README.md"), "file",
                          readme(rel, "upload", "Spec / datasheet bộ môn %s." % d)))
        items.append((os.path.join(project, "CLAUDE.md"), "file", claude_md(project)))
        items.append((os.path.join(project, "WORKLOG.md"), "file", worklog_md(project)))
        items.append((os.path.join(project, "00_AI-CONTEXT", "ONBOARDING.md"), "file",
                      onboarding_md("Dự án", project)))
    return items


def to_ps1(ws, items):
    L = ["# Tạo cấu trúc folder — construction-pm-kit",
         "# Chạy: chuột phải → Run with PowerShell. Nếu bị chặn, mở PowerShell và chạy trước:",
         "#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass",
         "$ErrorActionPreference = 'Stop'",
         "$ws = '%s'" % ws.replace("'", "''"),
         "$utf8 = New-Object System.Text.UTF8Encoding($true)",
         "function W($rel, $text) { $p = Join-Path $ws $rel; if (-not (Test-Path $p)) "
         "{ [System.IO.File]::WriteAllText($p, $text, $utf8) } }", ""]
    for rel, kind, content in items:
        r = rel.replace("/", "\\").replace("'", "''")
        if kind == "dir":
            L.append("New-Item -ItemType Directory -Force -Path (Join-Path $ws '%s') | Out-Null" % r)
        else:
            body = content.replace("'", "''")
            L.append("W '%s' @'\n%s\n'@" % (r, body))
    L.append("Write-Host 'Xong. Mở folder và đọc _README.md trong từng folder 📥 để biết upload gì.'")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace")
    ap.add_argument("--project")
    ap.add_argument("--disciplines", default="")
    ap.add_argument("--tree", default=DEFAULT_TREE)
    ap.add_argument("--ps1")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.project and not NAME_OK.match(a.project):
        sys.exit("Tên folder dự án nên VIẾT HOA, không dấu, không khoảng trắng (vd KHO-P01): %r" % a.project)
    disc = [d.strip().upper() for d in a.disciplines.split(",") if d.strip()]
    bad = [d for d in disc if not NAME_OK.match(d)]
    if bad:
        sys.exit("Tên bộ môn nên VIẾT HOA, không dấu: %s" % bad)
    with open(a.tree, encoding="utf-8") as f:
        tree = json.load(f)
    items = plan(a.workspace, a.project, disc, tree)

    if a.ps1:
        with open(a.ps1, "w", encoding="utf-8-sig") as f:
            f.write(to_ps1(a.workspace, items))
        print("Đã xuất %s (%d folder, %d file)." % (a.ps1, sum(1 for i in items if i[1] == "dir"),
                                                    sum(1 for i in items if i[1] == "file")))
        return

    made_d = made_f = kept = 0
    for rel, kind, content in items:
        p = os.path.join(a.workspace, rel)
        if kind == "dir":
            if not os.path.isdir(p):
                made_d += 1
                if not a.dry_run:
                    os.makedirs(p, exist_ok=True)
        else:
            if os.path.exists(p):
                kept += 1
                continue
            made_f += 1
            if not a.dry_run:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(content)
    tag = "Sẽ tạo" if a.dry_run else "Đã tạo"
    print("%s %d folder, %d file trong %s · giữ nguyên %d file đã có." % (tag, made_d, made_f, a.workspace, kept))
    up = [rel for rel, role, _ in walk(tree["company"], "") + (walk(tree["project"], a.project) if a.project else [])
          if role == "upload"]
    print("\nFolder 📥 cần upload tài liệu:")
    for r in up:
        print("  - %s" % r.replace("\\", "/"))


if __name__ == "__main__":
    main()
