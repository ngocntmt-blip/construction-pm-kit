# Hợp đồng hồ sơ nhận diện (profile contract)

Mọi skill trong kit đọc cùng một bộ hồ sơ, ở cùng vị trí, theo cùng cấu trúc.
Bộ kit **không chứa dữ liệu của công ty nào** — mọi tên, địa chỉ, người ký, mã
tài liệu, template đều nằm trong hồ sơ trên máy người dùng.

## 1. Hai tầng hồ sơ

| Tầng | Thư mục | Ai viết | Dùng chung cho |
|---|---|---|---|
| **Công ty** | `<workspace>/_COMPANY/_PROFILE/` — workspace là thư mục gốc của một công ty, ví dụ `D:\ALPHA\_COMPANY\_PROFILE\` | `kit-start` | mọi dự án của công ty đó |
| **Dự án** | `<gốc dự án>/00_AI-CONTEXT/` (hoặc thư mục AI-context đang có) | `kit-start` | một dự án |

Một người làm cho nhiều công ty → mỗi công ty một workspace riêng (`D:\ALPHA\`, `D:\BETA\`), mỗi workspace một `_COMPANY/_PROFILE/`.
Không bao giờ trộn hai công ty trong một hồ sơ.

### Tầng công ty — `_COMPANY/_PROFILE/`

| File | Nội dung |
|---|---|
| `company.md` | Tên pháp lý (Việt/Anh), tên viết tắt, mã công ty dùng trong số hiệu, địa chỉ, MST, website, tên miền email, logo, letterhead, vai trò & người ký mặc định, ngôn ngữ, định dạng ngày/số, thuật ngữ riêng |
| `templates.md` | Danh mục template: mã T-xx, loại văn bản, đường dẫn, các trường phải điền, phần cố định không được sửa, quy tắc đặt tên file, nơi lưu, người ký |
| `procedures.md` | Quy tắc rút từ quy trình nội bộ: đặt tên / đánh số / revision, mã mục đích phát hành, luồng duyệt, thời hạn, phân phối, hồ sơ kèm theo — mỗi quy tắc ghi **file nguồn + trang** |
| `profile.json` | Bản máy-đọc của 3 file trên (schema bên dưới) |
| `SOURCES.json` | Ghim sha256 của từng file đầu vào — để biết hồ sơ đã cũ khi template/quy trình đổi |

### Tầng dự án — `00_AI-CONTEXT/`

| File | Nội dung | Ai viết |
|---|---|---|
| `project.md` | Tên, mã, địa điểm, loại công trình, giai đoạn, vai trò của công ta, bảng folder STATIC/LIVE | `kit-start` |
| `parties.md` | Chủ đầu tư, tư vấn/PMC, tổng thầu, công ty ta, thầu phụ — đầu mối, chức danh, email, ai TO ai CC | `kit-start` |
| `doc-control.md` | Quy trình hồ sơ **của dự án/khách hàng**: cú pháp mã tài liệu, mã bộ môn/loại, luồng đệ trình, mã Issue for, thời hạn phản hồi, các sổ đăng ký (register) và vị trí | `kit-start` |
| `contract.md` | Cơ sở pháp lý, giá trị, hình thức, tiến độ, phạt, bảo lãnh, thanh toán, bảo hiểm | `kit-start` |
| `project.json` | Bản máy-đọc, có trường `company_profile` trỏ về tầng công ty | `kit-start` |
| `SOURCES.json` | Ghim nguồn của mọi mirror | `kit-start` + các skill mirror |
| `boq/`, `specs*.md`, `drawings/`, `scope-brief.md` | Mirror tài liệu | `boq-mirror`, `spec-mirror`, `drawings-analyzer`, `scope-brief` |

## 2. Thứ tự ưu tiên khi hai tầng khác nhau

**Dự án thắng công ty.** Ví dụ: công ty đánh số transmittal `ABC-T-0012`, nhưng
quy trình của khách hàng bắt `PRJ-ABC-CLI-T-0012` → dùng cú pháp dự án.
Template dự án (`project.json → templates_override`) thắng template công ty cùng loại.

## 3. Bước 0 — cổng hồ sơ (mọi skill chạy trước khi làm việc)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kit-start/scripts/profile_status.py" "<gốc dự án>"
```

Script tìm thư mục AI-context, đọc `project.json`, lần theo `company_profile`,
và báo: file nào có / thiếu, đã được người dùng xác nhận chưa, nguồn nào đã đổi
(STALE). Không có `project.json` thì tự tìm hồ sơ công ty ở `../_COMPANY/_PROFILE`.

| Kết quả | Skill đọc/mirror (boq, spec, drawings, scope, audit) | Skill tạo văn bản gởi ra ngoài (doc-from-template) |
|---|---|---|
| Đủ, đã xác nhận | Làm việc | Làm việc |
| Thiếu hồ sơ công ty | Làm được — dùng mặc định (tiếng Việt, DD/MM/YYYY, `00_AI-CONTEXT`), ghi rõ "chưa có hồ sơ công ty" | **Dừng.** Đề nghị chạy `kit-start` |
| Thiếu hồ sơ dự án | Làm được nếu biết gốc dự án; nhắc chạy `kit-start` | **Dừng.** Đề nghị chạy `kit-start` |
| Có nhưng `confirmed_by_user` trống (bản nháp) | Làm việc | Chỉ làm bản nháp; mọi trường lấy từ hồ sơ nháp tô vàng |
| Nguồn STALE | Báo người dùng, không tự dựng lại | Báo trước khi dùng template/quy trình đã đổi |
| Mirror bắt buộc (Bước 5) chưa chạy / cũ hơn nguồn | Skill mirror chạy bình thường (đây chính là việc của nó) | **Dừng.** Chạy mirror còn thiếu trước |

## 4. Quy tắc dùng hồ sơ

1. **Giá trị trong hồ sơ là dữ kiện người dùng đã xác nhận.** Không ghi đè bằng suy đoán. Thấy mâu thuẫn với tài liệu mới → báo, hỏi.
2. **Trường chưa có ghi `[chưa có]`, trường đoán chưa xác nhận ghi `[chưa xác nhận]`.** Không để trống im lặng, không bịa.
3. **Mỗi quy tắc/con số có nguồn** (file + trang/sheet). Không có nguồn = không đưa vào hồ sơ.
4. **Không chép tài liệu.** Hồ sơ là bản chắt lọc: `company.md` ≤ 120 dòng, `procedures.md` ≤ 200 dòng, `project.md` ≤ 130 dòng.
5. **Thông tin cá nhân của đối tác** (email, điện thoại) chỉ nằm trong `parties.md` / `project.json` trên máy người dùng — không chép vào skill, không đưa vào file chia sẻ công khai.
6. **Ngày tháng** theo `conventions.timezone` của hồ sơ; mặc định Asia/Ho_Chi_Minh.

## 5. Schema `profile.json` (tầng công ty)

```json
{
  "schema": "cpk-company/1",
  "company": {
    "short_code": "ABC",
    "legal_name": "CÔNG TY TNHH ABC",
    "legal_name_en": "ABC CO., LTD",
    "address": "...", "tax_id": "...", "phone": "...",
    "email_domain": "abc.com.vn", "website": "..."
  },
  "branding": { "logo_files": ["<đường dẫn>"], "letterhead_template": "T-01" },
  "conventions": {
    "language": "vi", "second_language": "en",
    "date_format": "DD/MM/YYYY", "timezone": "Asia/Ho_Chi_Minh",
    "number_format": "1.234.567,89", "currency": "VND",
    "highlight_edits": true, "ai_context_folder": "00_AI-CONTEXT",
    "folder_tree": "default | <đường dẫn file mô tả cây folder của công ty>"
  },
  "roles": [
    { "role": "Project Manager", "name": "[chưa có]", "signs": ["Transmittal", "MOS"] }
  ],
  "doc_numbering": [
    { "doc_type": "Transmittal", "pattern": "{company}-{project}-T-{seq:04}",
      "seq_scope": "per project", "source": "procedures.md §2 (QT-01 tr. 3)" }
  ],
  "templates": [
    { "id": "T-01", "doc_type": "Transmittal", "file": "<đường dẫn tuyệt đối>",
      "format": "docx", "fill_method": "placeholders | labels | table",
      "fields": ["transmittal_no", "date", "to", "cc", "subject", "items[]", "signatory"],
      "fixed": ["legend", "khối chữ ký"], "naming": "{number}-{short_title}.docx",
      "output_folder": "10_TRANSMITTAL/OUT", "signatory_role": "Project Manager",
      "samples": ["<file mẫu đã điền>"] }
  ],
  "procedures": [
    { "id": "P-01", "title": "Quy trình kiểm soát tài liệu", "file": "<đường dẫn>",
      "applies_to": ["Transmittal", "RFI"], "rules_section": "procedures.md §2" }
  ],
  "status": { "confirmed_by_user": "DD/MM/YYYY | null", "open_questions": [] }
}
```

## 6. Schema `project.json` (tầng dự án)

```json
{
  "schema": "cpk-project/1",
  "company_profile": "<đường dẫn tuyệt đối tới <workspace>/_COMPANY/_PROFILE>",
  "project": { "name": "...", "code": "...", "short_code": "...", "location": "...",
               "type": "...", "phase": "..." },
  "our_role": "Nhà thầu MEP | Tổng thầu EPC | ...",
  "parties": [
    { "role": "Client | Consultant | PMC | Main contractor | Us | Subcontractor",
      "name": "...", "short": "...",
      "contacts": [ { "name": "...", "title": "...", "email": "...",
                      "default": "to | cc | none" } ] }
  ],
  "contract": { "basis": "LOI/HĐ số ...", "value": null, "currency": "VND",
                "type": "lump sum | unit price", "start": null, "end": null },
  "doc_control": {
    "procedure_file": "<đường dẫn>",
    "naming_patterns": [ { "doc_type": "RMA", "pattern": "PRJ-{discipline}-RMA-{seq:03}-{title}",
                           "regex": "^PRJ-[A-Z]{2,3}-RMA-\\d{3}", "source": "..." } ],
    "codes": { "discipline": {"PP": "Piping"}, "doc_type": {"RMA": "Material Approval"},
               "issue_for": {"A": "Approval", "I": "Information"} },
    "submission_flow": ["Us", "Consultant", "Client"],
    "response_days": { "normal": 5, "urgent": 3, "unit": "working days" },
    "registers": [ { "name": "Document register", "file": "<đường dẫn>", "sheet": "Register",
                     "id_column": "Document No." } ]
  },
  "templates_override": [],
  "folders": { "ai_context": "00_AI-CONTEXT", "inbox": "90_CLAUDE-OUTPUT/_INBOX",
               "static": [], "live": [] },
  "status": { "confirmed_by_user": null, "open_questions": [] }
}
```

`{seq:04}` = số thứ tự 4 chữ số. Các biến khác trong `pattern` lấy từ
`company.short_code`, `project.short_code`, mã bộ môn / loại.
