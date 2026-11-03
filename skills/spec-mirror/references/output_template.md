# Mẫu output specs.md

Đây là hình dung cụ thể về mức chi tiết cần đạt. Không phải khuôn cứng — dự án
khác bộ môn thì mục 3 sẽ khác hẳn. Điều cần giữ là **mức chi tiết**, không phải
danh sách mục.

---

# [Tên dự án] — Specifications & Design Basis (mirror)

> Mirror từ `[đường dẫn thư mục spec]`:
> - `[file].pdf` ([N] tr.)
> - `[file].pdf` ([N] tr.)
>
> Tất cả Rev.[X], phát hành [ngày]. Author [tên] · Approver [tên] ([đơn vị TV]).
> Cập nhật lần cuối: [ngày]

---

## 1. Tiêu chuẩn thiết kế áp dụng

### 1.1 Quy chuẩn / tiêu chuẩn Việt Nam (bắt buộc)

| Mã | Nội dung |
|----|----------|
| **QCVN 06:2022/BXD** + SĐ 01:2023 | An toàn cháy cho nhà và công trình |
| **QCVN 02:2020/BCA** | Trạm bơm nước chữa cháy — bắt buộc cho cụm bơm chính |

Ghi vai trò cụ thể trong dự án, không chỉ chép tên tiêu chuẩn.

### 1.2 Tiêu chuẩn nước ngoài tham chiếu

| Mã | Vai trò trong dự án |
|----|---------------------|
| **SP 241.1311500.2015** (Nga) | Cơ sở tính sprinkler cho kho rack ≤12,5 m |
| ASME B16.5 | Áp lực thiết kế đường ống (max 16 bar @ 90 °C) |

---

## 2. Dữ liệu thiết kế công trình

| Thông số | Giá trị | Nguồn |
|----------|---------|-------|
| Nhóm công trình | F5 | DD tr. 3 |
| Bậc chịu lửa | Nhà kho IV, nhà sản xuất II | DD tr. 3 |
| Hạng nguy hiểm cháy | C | DD tr. 3 |
| Khối tích khoang cháy | 50.000 – 200.000 m³ | DD tr. 4 |

---

## 3. Thông số thiết kế từng hệ

Mục dài nhất và chi tiết nhất. Mỗi hệ một mục con, mỗi mục nêu đủ tham số
**và cơ sở tiêu chuẩn của nó**.

### 3.1 [Tên hệ] — [khu vực nếu có nhiều cơ sở tính]

- Cơ sở: [Bảng/điều nào, tiêu chuẩn nào]
- [Tham số]: **[giá trị + đơn vị]**
- [Tham số]: **[giá trị + đơn vị]**

Khi hai khu vực dùng hai cơ sở tính khác nhau, tách hẳn hai mục con và ghi rõ,
kèm cảnh báo không được lấy tiêu chuẩn này thay tiêu chuẩn kia.

Khi có công thức, ghi cả công thức lẫn kết quả:

> ∑V = Vfh + Vfhc + Vspr = 30×3,6×3 + 5×3,6×1 + 87,66×3,6×1 = **658 m³**

---

## 4. Yêu cầu vật liệu

| Hạng mục | Yêu cầu | Nguồn |
|----------|---------|-------|
| Vật liệu ống | Ống thép đen (carbon steel) | SP tr. 12 |
| Bề dày tối thiểu | 1/2"–2": Medium, BS 1387, SMLS, PE<br>8"–10": Schedule 20, ASTM A53 Gr.B | SP tr. 12 |
| Mặt bích | A-105N mạ kẽm, ASME Class 150#, forged slip-on | SP tr. 13 |

Giữ nguyên số hiệu tiêu chuẩn — đó là thứ dùng để so vật tư khi trình duyệt.

---

## 5. Thử nghiệm & nghiệm thu

| Hạng mục | Yêu cầu | Nguồn |
|----------|---------|-------|
| Thử thủy tĩnh chung | ≥ 1,5 × áp làm việc tối đa | SP tr. 31 |
| Thử thủy tĩnh toàn hệ | **12 bar trong 2 giờ** | SP tr. 31 |
| Mối hàn rò rỉ | Cắt bỏ và hàn lại — không vá | SP tr. 32 |
| Nghiệm thu cuối | Cảnh sát PCCC | SP tr. 34 |

---

## 6. Hồ sơ nhà thầu phải nộp

Liệt kê ngắn gọn, kèm số mục trong spec để tra lại khi cần.

---

## 7. Thiết bị được chấp thuận (vendor list)

| Hạng mục | Được duyệt | Nhà thầu đề xuất |
|----------|------------|------------------|
| Fire pump | Hãng A / Hãng B / Hãng C | **Hãng A** — phải comply QCVN 02:2020 |

---

## 8. Danh mục datasheet chi tiết

| # | Thiết bị | Mã datasheet |
|---|----------|--------------|
| 1 | Addressable Fire Alarm Panel | `-001.1` |

---

## 9. Điểm cần lưu ý cho PM

Đánh số, mỗi điểm nêu rủi ro và việc phải làm. Ví dụ mức cụ thể cần đạt:

1. **Bể 158 m³ nằm ngoài scope** (BOQ ghi "Excluded follow TCQ-05") nhưng hệ thống
   phụ thuộc bể này để đạt 658 m³ → theo dõi bên thi công và tiến độ, nếu chậm sẽ
   không đủ nước khi nghiệm thu.
2. **Vendor list ghi ASD = Hochiki, BOQ báo giá Securiton ASD 535** → làm rõ với
   tư vấn trước khi nộp Material Approval, tránh bị trả hồ sơ.
3. **Kho dùng SP 241 (tiêu chuẩn Nga), không phải NFPA 13** → khi so vật tư tương
   đương phải bám K=16,8 / 74 °C / 8,4 m² / 12 đầu.

Không tìm thấy mâu thuẫn nào thì ghi thẳng "không phát hiện mâu thuẫn giữa spec
và BOQ", đừng nặn cho đủ mục.
