---
name: scope-brief
description: >-
  Đọc toàn bộ file .md và folder của một dự án xây dựng rồi xuất ra BẢN THUYẾT
  MINH PHẠM VI CÔNG VIỆC (scope of works) có cấu trúc theo gói thầu CSA / MEP /
  EAC — nêu rõ scope tổng của nhà thầu và scope từng gói. Xuất cả .md (lưu vào
  00_AI-CONTEXT/) và .docx. Dùng skill này BẤT CỨ KHI NÀO người dùng nói "thuyết
  minh scope", "thuyết minh phạm vi công việc", "scope của nhà thầu là gì",
  "chia/structure công việc theo gói thầu", "scope gói CSA/MEP/EAC", "tóm tắt
  công việc dự án theo gói", "làm bản mô tả phạm vi", hoặc muốn hiểu/trình bày
  một dự án được chia thành những gói thầu nào và mỗi gói làm gì.
  Không dùng cho báo cáo ngày, BOQ chi tiết, hay trình duyệt
  vật tư.
---

# Scope Brief — Thuyết minh phạm vi công việc theo gói thầu

## Bước 0 — Đọc hồ sơ (construction-pm-kit)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kit-start/scripts/profile_status.py" "<gốc dự án>"
```

Dùng đúng thư mục AI-context script báo (không tạo thư mục thứ hai). Ngôn ngữ, định
dạng ngày theo hồ sơ công ty (mặc định tiếng Việt, DD/MM/YYYY, giờ Việt Nam). Chưa có
hồ sơ vẫn chạy được: ghi rõ "chưa có hồ sơ công ty/dự án" ở đầu output và đề nghị
`kit-start`. Đây là skill cuối của **Bước 5 (dựng context)** trong `kit-start` — chạy
xong thì đánh dấu trong `00_AI-CONTEXT/ONBOARDING.md` và thêm/sửa dòng tương ứng
trong bảng "Đọc gì trước?" của `CLAUDE.md`.

Skill này biến bộ tài liệu dự án (các file `.md` trong `00_AI-CONTEXT/`, `CLAUDE.md`,
BOQ, danh mục bản vẽ...) thành **một bản thuyết minh phạm vi công việc** trình bày
mạch lạc theo ba gói thầu chuẩn: **CSA / MEP / EAC** — hoặc theo cách chia gói của chính hợp đồng/hồ sơ dự án nếu có. Mục tiêu là để một người đọc
(chủ đầu tư, tư vấn, nội bộ) nắm ngay: nhà thầu làm gì tổng thể, và từng gói bao gồm
những hạng mục nào.

Đây là tài liệu **mô tả (descriptive)**, không phải bảng khối lượng. Không copy
nguyên văn BOQ; hãy diễn giải thành câu văn scope rõ ràng, kèm số liệu chốt khi có.

## Nguyên tắc cốt lõi — đọc trước khi làm

1. **Chỉ dùng dữ liệu, thuật ngữ, template và vendor của công ty sở hữu workspace** (theo hồ sơ công ty).
> Mọi đường dẫn `00_AI-CONTEXT/...` dưới đây hiểu là thư mục AI-context mà
> `profile_status.py` báo cho dự án đó.

2. **Ưu tiên đọc mirror trong thư mục AI-context trước.** Các file `project.md`,
   `contract.md`, `drawings.md` (và `specs.md`, `boq.md` nếu có) là nguồn tĩnh đã
   được tóm tắt sẵn — đọc chúng trước, rẻ và nhanh hơn mở file gốc PDF/Excel. Chỉ mở
   file gốc (LOI, BOQ, bản vẽ) khi mirror thiếu chi tiết cần cho scope.
3. **Không bịa scope.** Nếu một gói không có trong dự án, ghi rõ *"Không thuộc phạm
   vi hợp đồng của nhà thầu trong dự án này"* thay vì tự nghĩ ra hạng mục. Nếu một
   phần scope do thầu phụ đảm nhận, nêu rõ ai làm.
4. **Bám số liệu chốt.** Giá trị hợp đồng, mốc thời gian, cơ sở pháp lý (LOI/HĐ),
   tiêu chuẩn áp dụng — trích đúng từ tài liệu, không làm tròn hay phỏng đoán.
5. **Phân biệt scope nhà thầu chính vs thầu phụ.** Nhiều dự án nhà thầu chính đứng
   tên toàn bộ nhưng giao một gói (thường CSA) cho thầu phụ. Thuyết minh phải phản
   ánh đúng: gói nào tự làm, gói nào giao thầu phụ (nêu tên thầu phụ nếu có).

## Quy trình

### Bước 1 — Khảo sát dự án

Liệt kê cấu trúc thư mục dự án. Đọc `CLAUDE.md` (nếu có) và `00_AI-CONTEXT/project.md`
để nắm: tên dự án, mã dự án, chủ đầu tư, địa điểm, loại công trình, cơ sở pháp lý
(LOI/hợp đồng), giá trị, tiến độ. Thiếu thông tin nào thì **hỏi người dùng trước
khi tiếp tục**, đừng bịa.

### Bước 2 — Thu thập dữ liệu scope

Đọc theo thứ tự ưu tiên (dừng khi đã đủ thông tin để mô tả scope từng gói):

1. `00_AI-CONTEXT/project.md` — bối cảnh & scope tổng.
2. `00_AI-CONTEXT/contract.md` — phạm vi công việc chính, giá trị, thầu phụ, tiêu chuẩn.
3. `00_AI-CONTEXT/drawings.md` — các hệ thống & bộ môn có bản vẽ (suy ra gói thầu nào có mặt).
4. `00_AI-CONTEXT/specs.md` / `boq.md` (nếu có) — tiêu chuẩn áp dụng theo hệ.
5. File gốc BOQ / danh mục bản vẽ — CHỈ khi cần phân loại hạng mục vào gói mà mirror chưa đủ.

Đối chiếu chéo: tên sheet BOQ và mã bộ môn của bản vẽ (VD: `CV`=Civil, `PP`=Piping,
`MA`=HVAC, `EE`=Electrical) là căn cứ đáng tin để biết gói nào thực sự có scope.

### Bước 3 — Phân loại hạng mục vào 3 gói CSA / MEP / EAC

Dùng bảng mapping trong `references/package-taxonomy.md` để xếp từng bộ môn/hạng mục
vào đúng gói. Đọc file đó trước khi phân loại — nó xử lý cả các trường hợp ranh giới
(VD: điện có thể nằm ở MEP hay tách ra EAC tùy dự án).

Tóm tắt nhanh:
- **CSA** — Civil, Structural, Architectural: nền móng, kết cấu, hoàn thiện kiến trúc,
  hạ tầng, nhà xưởng/kho, tường bao, sàn, mái.
- **MEP** — Mechanical, Electrical, Plumbing: cấp thoát nước, PCCC (chữa cháy), HVAC
  (điều hòa – thông gió), cơ khí, khí nén, điện động lực cơ bản.
- **EAC** — Electrical, Automation & Control: điện, tự động hóa & điều khiển, ELV,
  hệ báo cháy, BMS, instrumentation, SCADA, hệ thống nhẹ. (Khi dự án gộp điện vào MEP,
  ghi rõ EAC đã gộp vào MEP thay vì để trống mập mờ.)

### Bước 4 — Viết bản thuyết minh (.md)

Bám đúng cấu trúc trong `references/output-template.md`. Cốt lõi gồm:
1. **Thông tin chung** — dự án, công ty/nhà thầu, chủ đầu tư, cơ sở pháp lý, giá trị,
   tiến độ, tiêu chuẩn khung.
2. **Scope tổng của nhà thầu** — 1 đoạn văn nói nhà thầu chịu trách nhiệm gì tổng thể,
   loại hợp đồng (lump sum/đơn giá), ranh giới cấp (supply/install/T&C), phần nào
   giao thầu phụ.
3. **Thuyết minh từng gói CSA / MEP / EAC** — mỗi gói: mô tả phạm vi bằng văn xuôi +
   một bảng liệt kê hạng mục chính (hệ thống · nội dung công việc · tiêu chuẩn áp dụng
   · ghi chú tự làm/thầu phụ).
4. **Ranh giới & loại trừ (interfaces & exclusions)** — điểm giao giữa các gói, hạng
   mục ngoài scope, điều kiện tiên quyết.

Lưu file `.md` vào `<thư mục AI-context của dự án>/scope-brief.md` — dò tên đang có
(theo `profile_status.py`); không có thư mục nào thì lưu ở gốc
dự án. Ghi dòng nguồn + ngày ở đầu file.

### Bước 5 — Xuất bản .docx

Sau khi bản `.md` đã đủ và đúng, đọc skill `docx` (`.../skills/docx/SKILL.md`) rồi tạo
bản Word trình bày được từ chính nội dung `.md` — tiêu đề, bảng, đánh số mục. Đặt tên
theo quy tắc đặt tên trong hồ sơ công ty/dự án. Nếu hồ sơ có template văn bản/letterhead
trong `TEMPLATE/`, dùng nó.

> Thứ tự bắt buộc: **nội dung đúng trước → định dạng sau.** Không mở skill `docx` khi
> chưa chốt xong nội dung scope.

### Bước 6 — Báo cáo & lưu vị trí

Nói ngắn gọn: đã tạo file nào (đường dẫn `.md` + `.docx`), gói nào có scope / gói nào
không thuộc phạm vi, và những chỗ còn thiếu dữ liệu cần người dùng bổ sung. Present
file `.docx` cho người dùng.

## Trường hợp đặc biệt

- **Dự án chỉ có 2 gói (CSA + MEP):** vẫn giữ đủ 3 mục; mục EAC ghi rõ đã gộp vào MEP
  hoặc ngoài phạm vi. Không xoá mục để giữ tính nhất quán giữa các dự án.
- **Thiếu `00_AI-CONTEXT/`:** đề xuất chạy `kit-start` trước để dựng hồ sơ dự án,
  hoặc đọc trực tiếp file gốc (chậm hơn) nếu người dùng muốn làm ngay.
- **Cập nhật lại (re-brief):** nếu `scope-brief.md` đã tồn tại và chỉ đổi một phần
  (VD giá trị hợp đồng, thêm hạng mục), edit tại chỗ đúng phần đó — không viết lại cả
  file.
