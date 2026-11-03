# Danh mục dữ kiện — Bước 3 (đọc) và Bước 4 (interview)

Mỗi dữ kiện: lấy từ tài liệu trước; tài liệu không có thì hỏi người dùng; người
dùng chưa có thì ghi `[chưa có]`. **Bắt buộc** = phải có trước khi
`doc-from-template` được phát hành văn bản ra ngoài (không phải bản nháp).

Cột "Nếu thiếu": **Hỏi** = dữ kiện chỉ người dùng biết, hỏi thẳng · **Upload** =
nên có tài liệu, chỉ người dùng upload file gì vào folder nào · **Hỏi/Upload** =
hỏi được nhưng tài liệu thì tốt hơn (có nguồn để dẫn).

## A. Công ty — `_COMPANY/_PROFILE/`

| # | Dữ kiện | Thường thấy ở | Bắt buộc | Nếu thiếu |
|---|---|---|---|---|
| A1 | Tên pháp lý tiếng Việt + tiếng Anh | letterhead (header/footer) template, `05_COMPANY-INFO` | ✔ | Hỏi/Upload giấy ĐKKD |
| A2 | Tên viết tắt / mã công ty dùng trong số hiệu | số hiệu trong `03_ISSUED-SAMPLES`, quy trình kiểm soát tài liệu | ✔ | Hỏi |
| A3 | Địa chỉ, MST, điện thoại, website, tên miền email | letterhead, chữ ký email | ✔ (địa chỉ, MST) | Hỏi/Upload |
| A4 | Logo, letterhead | `04_BRANDING`, ảnh trong header template | | Upload |
| A5 | Ngôn ngữ văn bản (Việt / Anh / song ngữ) cho từng loại | template, văn bản mẫu | ✔ | Hỏi |
| A6 | Định dạng ngày, số, tiền tệ | văn bản mẫu (scan đếm kiểu ngày) | | tự suy từ mẫu → xác nhận |
| A7 | Danh mục template: mỗi loại văn bản dùng form nào | `01_TEMPLATES` | ✔ | Upload |
| A8 | Phần cố định của từng template (không được sửa) và các ô phải điền | template + văn bản đã điền | ✔ | tự suy → xác nhận |
| A9 | Quy tắc đặt tên file / đánh số / revision của công ty | `02_PROCEDURES`, số hiệu mẫu | ✔ | Upload quy trình, hoặc Hỏi |
| A10 | Sổ theo dõi (register) đang dùng cho từng loại số | `03_ISSUED-SAMPLES` (Excel) | ✔ nếu có đánh số | Upload/Hỏi |
| A11 | Người ký mặc định theo loại văn bản (tên + chức danh) | khối chữ ký văn bản mẫu, `05_COMPANY-INFO` | ✔ | **Hỏi** — không suy từ một văn bản mẫu |
| A12 | Luồng duyệt nội bộ trước khi gởi (ai soát, ai ký) | quy trình | | Hỏi |
| A13 | Có tô vàng chỗ Claude sửa không (mặc định có) | — | | Hỏi nếu muốn khác |
| A14 | Cây folder chuẩn riêng của công ty (nếu có) | quy trình, folder hiện có | | Hỏi |

## B. Dự án — `<dự án>/00_AI-CONTEXT/`

| # | Dữ kiện | Thường thấy ở | Bắt buộc | Nếu thiếu |
|---|---|---|---|---|
| B1 | Tên dự án đầy đủ, mã dự án, mã viết tắt trong số hiệu | hợp đồng/LOI, quy trình khách hàng | ✔ | Hỏi/Upload |
| B2 | Địa điểm, loại công trình | hợp đồng, kick-off | | Hỏi |
| B3 | Các bên: chủ đầu tư, tư vấn/PMC, tổng thầu, công ty ta, thầu phụ — tên pháp lý + viết tắt | hợp đồng, communication matrix | ✔ | Upload `01_CONTRACT-BOQ`, `03_CONTACTS` |
| B4 | Vai trò và gói thầu của công ty ta | hợp đồng, LOI | ✔ | Hỏi/Upload |
| B5 | Đầu mối từng bên: tên, chức danh, email; ai TO ai CC theo loại văn bản | `03_CONTACTS`, communication matrix | ✔ | Upload, rồi **Hỏi** xác nhận TO/CC |
| B6 | Người ký phía công ty ta cho dự án này (có thể khác mặc định công ty) | — | ✔ | **Hỏi** |
| B7 | Cơ sở pháp lý: số hợp đồng/LOI/PO, ngày ký, đã ký chính thức chưa | `01_CONTRACT-BOQ` | ✔ | Upload/Hỏi |
| B8 | Giá trị, hình thức HĐ, tiến độ, phạt, bảo lãnh, thanh toán | hợp đồng | | Upload |
| B9 | Quy trình hồ sơ của khách hàng: cú pháp mã, mã bộ môn, mã loại, mã Issue for, revision | `01_CLIENT-PROCEDURES` | ✔ nếu khách hàng có | Upload |
| B10 | Luồng đệ trình (ai gởi ai, qua ai) và thời hạn phản hồi | Document Handling Procedure, communication matrix | ✔ | Upload/Hỏi |
| B11 | Kênh gởi (email, cổng SharePoint/Aconex, bản cứng) | quy trình khách hàng | | Hỏi |
| B12 | Form bắt buộc của khách hàng (thắng form công ty) | `02_CLIENT-TEMPLATES` | ✔ nếu có | Upload |
| B13 | Sổ đăng ký của dự án (document register, transmittal log…) — file nào, sheet, cột số hiệu | `01_CLIENT-PROCEDURES`, folder dự án | ✔ nếu có đánh số | Hỏi/Upload |
| B14 | File BOQ CHÍNH THỨC được phép reference (và bản nào bị cấm) | `01_CONTRACT-BOQ` | ✔ trước khi chạy boq-mirror | **Hỏi** |
| B15 | Bộ môn của dự án | bản vẽ, spec, BOQ | | tự suy → xác nhận |
| B16 | Mốc chính: khởi công, hoàn thành, giai đoạn hiện tại | hợp đồng, tiến độ | | Hỏi |

## Cách hỏi ở Bước 4

1. **Trình trước những gì đã đọc được**, gọn: bảng dữ kiện → giá trị → nguồn
   (file + trang). Người dùng sửa chỗ sai nhanh hơn trả lời câu hỏi trống.
2. **Gom mọi câu hỏi vào một lượt.** Dùng AskUserQuestion khi câu hỏi có lựa chọn
   rõ (ứng viên công ty mình, template nào cho loại văn bản X); câu hỏi mở thì
   liệt kê đánh số để người dùng trả lời một tin nhắn.
3. **Chỉ hỏi dữ kiện chỉ người dùng biết** (cột Hỏi). Thứ tài liệu đã nói rõ thì
   không hỏi lại — chỉ trình để xác nhận.
4. **Tài liệu còn thiếu → chỉ cụ thể:** "Upload Document Handling Procedure của
   khách hàng vào `P01/00_PROJECT-INPUT/01_CLIENT-PROCEDURES/` — cần để biết cú
   pháp mã tài liệu và thời hạn phản hồi (B9, B10)." Không viết "vui lòng cung
   cấp thêm tài liệu".
5. **Mâu thuẫn giữa hai nguồn** (template ghi một địa chỉ, ĐKKD ghi địa chỉ khác;
   quy trình công ty đánh số 3 chữ số, văn bản mẫu dùng 4) → nêu cả hai kèm
   nguồn, hỏi cái nào đúng.
6. Người dùng trả lời xong → ghi vào hồ sơ, đặt `status.confirmed_by_user` = ngày
   hôm nay (giờ Việt Nam), dọn `open_questions`. Còn câu chưa trả lời → giữ trong
   `open_questions`, hồ sơ vẫn là bản nháp.
