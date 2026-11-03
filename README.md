# Construction PM Kit

**Tiếng Việt** · [English](#english)

Bộ skill cho Claude (Cowork / Claude Code) giúp quản lý dự án xây dựng — dùng được
cho **mọi công ty, mọi dự án**. Kit **không chứa dữ liệu của công ty nào**: trước
khi làm việc, Claude đọc template, quy trình và hồ sơ bạn upload để nhận diện công
ty, dự án, khách hàng, các bên, rồi phỏng vấn bạn những gì tài liệu không có.

## Cách bắt đầu — 6 bước

Gọi `kit-start` (ví dụ: *"bắt đầu dùng kit cho công ty ALPHA, dự án KHO-P01 ở D:\ALPHA"*).

| Bước | Ai làm | Việc |
|---|---|---|
| 1 | Claude | Tạo cấu trúc folder: khu `_COMPANY\` (template, quy trình, logo của công ty) + folder dự án. Mỗi folder có `_README.md` ghi rõ upload gì |
| 2 | Bạn | Upload tài liệu vào các folder 📥 |
| 3 | Claude | Đọc toàn bộ file vừa upload, dựng hồ sơ nhận diện (nháp), mọi giá trị có nguồn |
| 4 | Claude ↔ bạn | Interview: một lượt câu hỏi cho dữ kiện chỉ bạn biết (người ký, TO/CC, file BOQ chính thức…), chỉ rõ tài liệu còn thiếu cần upload vào đâu |
| 5 | Claude | **Bắt buộc** dựng context: `boq-mirror`, `spec-mirror`, `drawings-analyzer`, `scope-brief` cho những tài liệu đang có |
| 6 | Claude | Làm task: transmittal, RFI, MOS, trình duyệt vật tư, biên bản… bằng `doc-from-template` |

Skill làm task sẽ **dừng** nếu hồ sơ chưa xác nhận hoặc context chưa dựng / đã cũ
hơn tài liệu gốc.

## Các skill

| Skill | Làm gì |
|---|---|
| `kit-start` | 6 bước trên; kiểm tra và cập nhật hồ sơ |
| `doc-from-template` | Mọi văn bản theo template: cấp số từ register, người nhận/ký từ hồ sơ, điền giữ định dạng, tô vàng, kiểm theo quy trình, ghi register |
| `boq-mirror` | BOQ Excel → markdown + SQLite, giữ số dòng Excel, đối soát tổng tiền |
| `spec-mirror` | Spec / datasheet PDF → markdown có trang nguồn, soi mâu thuẫn |
| `drawings-analyzer` | Bộ bản vẽ PDF → database, ký hiệu, xung đột / RFI, tách sheet, diện tích |
| `scope-brief` | Thuyết minh phạm vi công việc theo gói thầu |
| `edit-output-in-place` | Sửa file đã có: backup, kiểm file đang mở, tô vàng, Compare |
| `context-file-audit` | Rà `CLAUDE.md` so với folder thật, cắt gọn |

## Cấu trúc folder

```
D:\ALPHA\                      ← workspace của MỘT công ty
├── _COMPANY\
│   ├── 01_TEMPLATES\          📥 form mẫu trắng
│   ├── 02_PROCEDURES\         📥 quy trình nội bộ
│   ├── 03_ISSUED-SAMPLES\     📥 văn bản đã phát hành + sổ register
│   ├── 04_BRANDING\           📥 logo, letterhead
│   ├── 05_COMPANY-INFO\       📥 ĐKKD, nhân sự chủ chốt, ai ký gì
│   └── _PROFILE\              🤖 hồ sơ công ty (Claude ghi)
└── KHO-P01\                   ← một dự án
    ├── CLAUDE.md · WORKLOG.md
    ├── 00_AI-CONTEXT\         🤖 hồ sơ dự án + mirror
    ├── 00_PROJECT-INPUT\      📥 quy trình & form khách hàng, đầu mối, kick-off
    ├── 01_CONTRACT-BOQ\       📥 hợp đồng, BOQ
    ├── 02_DRAWINGS\           📥 bản vẽ
    ├── 03_SPECIFICATION\      📥 spec
    ├── 04_EXECUTION … 14_PAYMENT   🗂 hồ sơ làm việc hằng ngày
    └── 90_CLAUDE-OUTPUT\      🤖 bản nháp chờ review
```
Công ty có cây folder chuẩn riêng → sửa `skills/kit-start/references/folder-tree.json`.

## Cài đặt

- Cài plugin vào Claude (Cowork / Claude Code).
- Thư viện Python: `pip install -r requirements.txt`.
- Tuỳ chọn: poppler-utils (`pdftotext`), LibreOffice (đếm trang Word).

## Góp ý

Dùng thử rồi mở **Issue** trên GitHub (có sẵn mẫu Góp ý và Báo lỗi) — xem `CONTRIBUTING.md`. Đừng dán dữ liệu thật của công ty hay đối tác.

## Nguyên tắc

- Không đoán dữ kiện: số hiệu, người ký, người nhận, ngày, giá — lấy từ hồ sơ hoặc hỏi.
- Không ghi đè, không xoá, không đổi tên file của bạn.
- Mỗi workspace một công ty — không trộn.
- Mọi chỗ Claude điền/sửa trong Word/Excel được tô vàng.
- Dữ liệu công ty (kể cả email đối tác) chỉ nằm trong `_PROFILE\` và `00_AI-CONTEXT\` trên máy bạn — **đừng commit hai folder này lên GitHub**.

---

## English

Claude skills for construction project management that work for **any company
and any project**. The kit ships **no company data**: before doing any work,
Claude reads the templates, procedures and project documents you upload to
identify your company, project, client and parties, then interviews you for
anything the documents don't say.

**Flow** (`kit-start`): 1) create the folder structure, 2) you upload documents,
3) Claude reads them and drafts the profiles, 4) interview to fill gaps and
confirm, 5) mandatory context build (`boq-mirror`, `spec-mirror`,
`drawings-analyzer`, `scope-brief`), 6) tasks (`doc-from-template` for
transmittals, RFIs, method statements, material submittals, minutes…).

Task skills refuse to issue documents until the profiles are confirmed and the
context is built and up to date. Skill bodies are written in Vietnamese; output
language follows the company profile.

Install the plugin, then `pip install -r requirements.txt`. MIT licensed.
Keep `_COMPANY/_PROFILE/` and `00_AI-CONTEXT/` out of any public repository —
they hold your company's and partners' data.
