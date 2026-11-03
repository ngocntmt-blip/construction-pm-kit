---
name: doc-from-template
description: "Lập mọi văn bản dự án từ template đã nhận diện trong hồ sơ công ty/dự án: transmittal, RFI, công văn, biên bản, MOS/BPTC, trình duyệt vật tư (RMA), đề nghị vật tư, NCR, kế hoạch tuần, báo cáo… — số hiệu cấp từ register theo quy trình, người nhận/CC/người ký lấy từ hồ sơ, điền giữ nguyên định dạng, tô vàng, kiểm theo quy trình, cập nhật register. Dùng khi nói \"làm transmittal\", \"làm RFI\", \"soạn công văn\", \"lập biên bản\", \"làm MOS\", \"trình duyệt vật tư\", \"đề nghị vật tư\", \"cấp số\", \"next số\", \"điền form\", \"làm theo template\"."
---

# Lập văn bản từ template

Một skill cho mọi loại văn bản, vì **mọi thứ khác nhau giữa các công ty đều nằm
trong hồ sơ**: template nào, ô nào điền, đánh số ra sao, gởi ai, ai ký. Skill này
chỉ làm phần chung: tìm đúng template → gom dữ kiện → cấp số → điền → kiểm → ghi sổ.

## Bước 0 — Cổng hồ sơ (bắt buộc)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kit-start/scripts/profile_status.py" "<gốc dự án>"
```

| VERDICT issue | Làm gì |
|---|---|
| `STOP` (thiếu hồ sơ, hoặc Bước 5 chưa dựng context) | Dừng. Nói thiếu gì, đề nghị chạy `kit-start` hoặc mirror còn thiếu. Không làm văn bản "tạm" |
| `DRAFT_ONLY` | Làm được, nhưng là **bản nháp**: mọi giá trị lấy từ hồ sơ nháp tô vàng, nói rõ hồ sơ chưa xác nhận, không cập nhật register |
| `OK` | Làm việc |
| có `CẢNH BÁO` nguồn đổi | Báo template/quy trình nào đã đổi trước khi dùng |

Đọc: `_COMPANY/_PROFILE/profile.json` + `templates.md` + `procedures.md`, và
`00_AI-CONTEXT/project.json` + `parties.md` + `doc-control.md`. **Dự án thắng công
ty** khi khác nhau (cú pháp số, form bắt buộc, luồng gởi).

## Bước 1 — Chọn template

1. Loại văn bản người dùng muốn → tìm trong `project.json → templates_override`
   trước, rồi `profile.json → templates`.
2. Một template khớp → dùng. Nhiều template khớp → hỏi người dùng (liệt kê mã T-xx + tên file).
3. **Không có template** → nói rõ. Đề xuất một trong hai, để người dùng chọn:
   (a) dùng văn bản đã phát hành gần nhất cùng loại làm khuôn (đổi phần biến);
   (b) dựng mới trên letterhead công ty bằng skill `docx`. Không tự chọn.
4. Template đã bị sửa từ lần nhận diện (`profile_status` báo STALE) → mở lại, so
   các ô cần điền với `templates.md`; khác → báo, cập nhật `templates.md` sau khi người dùng đồng ý.

## Bước 2 — Gom dữ kiện

Mỗi ô cần điền (theo `templates.md → Ô phải điền`) lấy theo thứ tự:

| Nguồn | Ví dụ |
|---|---|
| Hồ sơ dự án | tên/mã dự án, bên nhận, Attn, CC theo loại văn bản (`parties.md`), mã Issue for, thời hạn phản hồi (`doc-control.md`) |
| Hồ sơ công ty | tên pháp lý, địa chỉ, người ký mặc định theo vai trò, định dạng ngày |
| Mirror context | dòng BOQ (sheet + **số dòng Excel**), thông số spec (kèm trang), số bản vẽ |
| Người dùng | nội dung riêng của lần này: tiêu đề, danh mục hồ sơ, lý do, câu hỏi RFI, ngày gởi nếu khác hôm nay |

Thiếu dữ kiện chỉ người dùng biết → **gom thành một lượt hỏi** trước khi điền.
Người dùng không có mặt / không trả lời → điền `[chưa có]`, tô vàng, liệt kê ở cuối.
**Không suy**: số hiệu, người ký, người nhận, ngày, số lượng, giá.

Thời hạn phản hồi → tính bằng code, theo ngày làm việc (bỏ T7, CN; ngày lễ chỉ bỏ
khi hồ sơ có danh sách), ghi cả số ngày lẫn ngày cụ thể.

## Bước 3 — Cấp số hiệu

Lấy mẫu từ `doc_control.naming_patterns` (dự án) hoặc `doc_numbering` (công ty),
thay các biến (mã công ty, mã dự án, bộ môn, loại) bằng giá trị trong hồ sơ, chỉ
để lại `{seq:N}`:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/doc-from-template/scripts/next_number.py" "AB-P01-T-{seq:04}" --register "<register.xlsx>" --column "<cột số hiệu>" --folder "<folder đã phát hành>"
```

- Có **số nhảy / số trùng** → hỏi người dùng lấp chỗ trống hay lấy số kế tiếp.
- Register và folder lệch nhau (folder có số register chưa ghi) → báo, hỏi.
- Không có register, không có văn bản cũ → hỏi người dùng số bắt đầu.
- Người dùng tự đưa số → dùng số đó, vẫn chạy script để cảnh báo nếu trùng.

## Bước 4 — Điền

Word:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/doc-from-template/scripts/docx_fill.py" list "<template.docx>"
python3 "${CLAUDE_PLUGIN_ROOT}/skills/doc-from-template/scripts/docx_fill.py" fill "<template.docx>" values.json "<output.docx>"
```
Excel:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/doc-from-template/scripts/xlsx_fill.py" fill "<template.xlsx>" values.json "<output.xlsx>"
```
`values.json` gồm `replace` (placeholder), `labels` (ô kiểu "Nhãn: ……"), `tables`
(bảng danh mục) — xem đầu mỗi script. Template không có placeholder → dùng
`labels`/`tables`; vẫn không đủ → sửa đúng ô bằng python-docx/openpyxl, không dựng
lại tài liệu.

- **Output** → `90_CLAUDE-OUTPUT/_INBOX/` (bản nháp chờ review), tên file theo
  `templates.md → Đặt tên file`. Không bao giờ ghi vào folder template, không ghi đè.
- **Phần cố định** của template (letterhead, legend, điều khoản, khối chữ ký) giữ
  nguyên; chỉ đổi tên/chức danh người ký nếu template có chỗ đó.
- Văn bản nhiều trang nội dung (MOS, kế hoạch, báo cáo): **chốt nội dung trước**
  (dàn ý → người dùng duyệt nếu là văn bản dài), rồi mới điền vào template.
- PowerPoint (báo cáo dạng slide): sửa đúng text frame bằng python-pptx; đọc skill
  `pptx` trước nếu cần thêm slide/bảng.
- Hồ sơ gồm nhiều file (văn bản + phụ lục + catalogue) → làm từng file, rồi lập
  transmittal bọc ngoài bằng chính skill này.

## Bước 5 — Kiểm theo quy trình

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/doc-from-template/scripts/docx_fill.py" check "<output.docx>" --name-regex "<regex của mẫu tên file>"
```
Rồi tự đối chiếu, bằng code khi có thể:

1. Không còn placeholder; mọi ô "phải điền" có giá trị hoặc `[chưa có]` tô vàng.
2. Số hiệu và tên file khớp regex của quy trình.
3. Người nhận, Attn, CC đúng `parties.md` cho loại văn bản này và đúng **luồng đệ
   trình** (ví dụ gởi tư vấn chứ không gởi thẳng chủ đầu tư, nếu quy trình nói vậy).
4. Mã Issue for, revision, ngày đúng bảng mã và định dạng trong hồ sơ.
5. Số liệu trích dẫn (dòng BOQ, thông số spec, số bản vẽ) khớp mirror — mở lại
   mirror kiểm, không nhớ.
6. Hồ sơ kèm bắt buộc theo quy trình có đủ (catalogue, compliance sheet…).
7. Số trang (nếu form có ô số trang): đếm bằng code (convert PDF bằng LibreOffice rồi
   đọc số trang), không đoán.

Sai mục nào thì sửa trước khi giao; không sửa được (thiếu dữ kiện) thì liệt kê.

## Bước 6 — Giao và ghi sổ

- Giao file trong `_INBOX`, kèm danh sách ô đã điền / ô còn `[chưa có]`. Nhắc:
  review → sửa tay → save cùng tên → chuyển sang folder nghiệp vụ; bỏ highlight
  trước khi gởi ra ngoài.
- **Register**: chỉ thêm dòng khi người dùng xác nhận văn bản sẽ phát hành (số hiệu
  đã chốt). Thêm vào sổ đang dùng, có backup tự động:
  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/doc-from-template/scripts/xlsx_fill.py" append "<register.xlsx>" rows.json --sheet "<sheet>"
  ```
  Hồ sơ là `DRAFT_ONLY` → không ghi register.
- **Gởi ra ngoài** (email, cổng tài liệu): chỉ khi người dùng yêu cầu rõ trong phiên
  này; soạn sẵn email body theo `doc-control.md` (kênh gởi, CC), để người dùng gởi.
- Thêm một dòng vào `WORKLOG.md` của dự án: văn bản gì, số hiệu, trạng thái.

## Sửa văn bản đã có

Văn bản đã tạo và người dùng đã mở sửa tay → **không chạy lại fill**: sửa tại chỗ
theo skill `edit-output-in-place` (file trên đĩa là bản gốc duy nhất).

## Ghi chú theo loại văn bản (bổ sung cho hồ sơ, không thay hồ sơ)

| Loại | Điểm hay sai |
|---|---|
| Transmittal | Số transmittal ≠ số của tài liệu bên trong; danh mục ghi đúng rev và Issue for từng tài liệu |
| RFI | Một câu hỏi rõ, có tham chiếu (bản vẽ/spec/BOQ + trang/dòng), đề xuất của nhà thầu nếu có, ngày cần trả lời |
| Trình duyệt vật tư | Model/hãng khớp vendor list và spec (trang nguồn); dòng BOQ trích từ `boq.db` kèm số dòng Excel; dòng ngoài phạm vi (giá 0) không đưa vào |
| Đề nghị vật tư / mua hàng | Khối lượng tính bằng code từ BOQ/RMA đã duyệt, ghi nguồn; không lấy model chưa được duyệt |
| MOS / BPTC | Theo bố cục mục của template; mối nguy và biện pháp kiểm soát cụ thể cho công việc, không chung chung |
| Biên bản / công văn | Văn phong hành chính chuẩn của loại văn bản; không thêm điều khoản ngoài yêu cầu |
