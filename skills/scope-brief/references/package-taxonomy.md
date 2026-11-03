# Package Taxonomy — Phân loại hạng mục vào gói CSA / MEP / EAC

Bảng tham chiếu để xếp mỗi bộ môn / hạng mục của dự án vào đúng một gói thầu. Đọc
file này ở Bước 3 trước khi phân loại. Nguyên tắc: **một hạng mục chỉ thuộc một gói**;
nếu ranh giới không rõ, xử lý theo mục "Trường hợp ranh giới" ở cuối.

## 1. CSA — Civil, Structural, Architectural

Kết cấu và bao che của công trình.

| Nhóm | Hạng mục điển hình | Mã bộ môn bản vẽ thường gặp |
|---|---|---|
| Civil / Hạ tầng | San nền, móng, đường nội bộ, thoát nước mưa ngoài nhà, hố ga | CV, C, ST |
| Structural / Kết cấu | Cột, dầm, sàn, kết cấu thép, mái, sàn nâng | ST, S |
| Architectural / Kiến trúc | Tường bao, vách ngăn, cửa, hoàn thiện, sơn, trần, sàn hoàn thiện | AR, A |

Ghi chú: sơn chống cháy kết cấu thép (fireproofing) thuộc CSA nếu là bảo vệ kết cấu;
nếu là một phần hệ PCCC chủ động thì để MEP — bám theo cách BOQ/hợp đồng phân loại.

## 2. MEP — Mechanical, Electrical, Plumbing

Hệ cơ – điện – nước cơ bản của công trình.

| Nhóm | Hạng mục điển hình | Mã bộ môn bản vẽ thường gặp |
|---|---|---|
| Plumbing / Cấp thoát nước | Cấp nước, thoát nước thải, thoát nước trong nhà, bể | PL, P, PP |
| Fire Fighting / PCCC | Sprinkler, hydrant, bơm chữa cháy, đường ống chữa cháy | FF, PP, FP |
| HVAC / Điều hòa – thông gió | Điều hòa, thông gió, hút khói, ống gió, chiller | MA, HV, HVAC |
| Mechanical / Cơ khí | Khí nén, khí công nghiệp, thiết bị cơ khí, băng tải | ME, M |
| Điện động lực cơ bản | Cấp nguồn, tủ điện phân phối, chiếu sáng (khi không tách EAC) | EE, E, EL |

## 3. EAC — Electrical, Automation & Control

Điện, điều khiển, tự động hóa và hệ thống dòng thấp. Tách riêng khi dự án quản lý
điện/điều khiển thành gói độc lập; nếu dự án gộp điện vào MEP thì ghi rõ "EAC gộp
trong MEP".

| Nhóm | Hạng mục điển hình | Mã bộ môn bản vẽ thường gặp |
|---|---|---|
| Electrical / Điện | Trạm biến áp, tủ MSB/DB, busway, cấp nguồn thiết bị, chiếu sáng | EE, E, EL |
| ELV / Dòng thấp | Mạng, điện thoại, CCTV, access control, âm thanh | ELV, EL |
| Fire Alarm / Báo cháy | Đầu báo, tủ trung tâm báo cháy, nút nhấn, chuông đèn | FA, FAS |
| Automation & Control | BMS, SCADA, PLC, instrumentation, van điều khiển | ICA, BMS, INST |

## Trường hợp ranh giới (borderline) — cách xử lý

- **Điện nằm ở MEP hay EAC?** Nếu hợp đồng/BOQ có gói điện–điều khiển riêng → EAC.
  Nếu điện chỉ là cấp nguồn cho hệ cơ và không tách gói → để ở MEP, và ghi EAC "gộp
  trong MEP". Chọn một cách, ghi rõ, giữ nhất quán toàn tài liệu.
- **PCCC (chữa cháy nước) vs Báo cháy:** phần đường ống/bơm/sprinkler → MEP (Fire
  Fighting); phần đầu báo/tủ báo cháy/điều khiển → EAC (Fire Alarm). Nêu rõ điểm giao.
- **Sơn/bọc chống cháy kết cấu:** theo cách BOQ phân loại (thường CSA). Nếu không rõ,
  nêu là ranh giới và hỏi người dùng.
- **Hạng mục do thầu phụ làm:** không đổi gói vì lý do ai làm; vẫn xếp theo bản chất
  kỹ thuật, chỉ thêm ghi chú "(thầu phụ: <tên>)".

## Căn cứ nhận diện gói có mặt trong dự án

Một gói "có scope" khi có ít nhất một trong: sheet BOQ tương ứng có giá trị > 0, có
bản vẽ mã bộ môn tương ứng, hoặc hợp đồng nêu rõ. Nếu cả ba đều không → gói đó "không
thuộc phạm vi". Hạng mục có đơn giá = 0 trong BOQ (cờ `∅` của boq-mirror) là ngoài scope,
không đưa vào thuyết minh.
