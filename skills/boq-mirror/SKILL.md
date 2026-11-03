---
name: "boq-mirror"
description: "Mirror BOQ Excel của dự án sang markdown + SQLite trong 00_AI-CONTEXT/boq/ — từng dòng giữ số hàng Excel gốc, khối lượng CĐT/nhà thầu, đơn giá, thành tiền, nhãn hiệu, cờ ngoài phạm vi (giá 0) và lệch khối lượng. Dùng khi nói \"đọc/mirror/index BOQ\", \"làm boq.md\", \"hạng mục X nằm dòng nào\", \"đơn giá/khối lượng/nhãn hiệu dòng Y\", \"hạng mục nào ngoài phạm vi\", hoặc BOQ ra revision mới. Không dùng cho spec (spec-mirror) hay bản vẽ (drawings-analyzer)."
---

# BOQ Mirror

## Bước 0 — Đọc hồ sơ (construction-pm-kit)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/kit-start/scripts/profile_status.py" "<gốc dự án>"
```

Dùng đúng thư mục AI-context script báo (không tạo thư mục thứ hai). Ngôn ngữ, định
dạng ngày theo hồ sơ công ty (mặc định tiếng Việt, DD/MM/YYYY, giờ Việt Nam). Chưa có
hồ sơ vẫn chạy được: ghi rõ "chưa có hồ sơ công ty/dự án" ở đầu output và đề nghị
`kit-start`. Đây là một skill của **Bước 5 (dựng context)** trong `kit-start` — chạy
xong thì đánh dấu trong `00_AI-CONTEXT/ONBOARDING.md` và thêm/sửa dòng tương ứng
trong bảng "Đọc gì trước?" của `CLAUDE.md`.

Biến file BOQ Excel thành bản mirror markdown + SQLite nằm trong `00_AI-CONTEXT/boq/`,
để mọi câu hỏi về khối lượng — "hạng mục này nằm dòng nào", "đơn giá bao nhiêu",
"nhãn hiệu gì", "cái này có trong hợp đồng không" — trả lời được mà không phải
mở lại Excel.

## Vì sao cần mirror riêng, không dùng skill khác

Phân tích chênh lệch BOQ với ngân sách là việc khác (cần thêm file ngân sách).
`spec-mirror` đọc specification, chỉ *đối chiếu* BOQ ở bước tìm mâu thuẫn. Hồ sơ
dự án (`kit-start`) chỉ ghi file BOQ nào là bản chính thức. Skill này làm đúng một việc:
mirror BOQ **đủ chi tiết đến từng dòng** để tra cứu.

## Ba nguyên tắc không được vi phạm

1. **Giữ số hàng Excel gốc.** Tư vấn/chủ đầu tư trích dẫn BOQ theo số dòng
   ("dòng 140, DN80"). Mirror mất số dòng là mirror vô dụng. Cột `excel_row`
   trong database và cột đầu tiên trong bảng markdown chính là số hàng Excel.
2. **Dòng giá = 0 hoặc trống → NGOÀI phạm vi hợp đồng.** Đánh dấu `∅`, không
   xoá (vì tư vấn vẫn hỏi tới), nhưng khi trả lời câu hỏi về scope thì phải
   loại ra và nói rõ là ngoài phạm vi.
3. **Không suy đoán sheet không đọc được.** Sheet nào script không nhận diện
   được header thì ghi cảnh báo trong file `.md`, để trống số liệu. Bịa một con
   số trong BOQ nguy hiểm hơn nhiều so với thừa nhận chưa đọc được.

## Bước 1 — Xác định file BOQ nào là bản dùng được

Đọc `00_AI-CONTEXT/project.json` / `contract.md` (dữ kiện B14 — file BOQ chính
thức) hoặc `CLAUDE.md` của dự án; không có thì hỏi. Nhiều dự án có 3–4 bản BOQ (có giá / không
giá / bản "clean" / bản CSV trích sẵn) và chỉ **một** bản được phép reference.
Chọn sai bản là sai toàn bộ số liệu về sau.

Chốt với người dùng trước khi chạy:

- Đường dẫn file BOQ chính thức và revision của nó
- Nếu dự án đã cấm dùng một số bản → ghi lại danh sách cấm vào `README.md` output
- Thư mục output: `<thư mục AI-context của dự án>/boq/` — dùng thư mục AI-context mà `profile_status.py` báo; chưa có thì tạo `00_AI-CONTEXT/`

Nếu đã có thư mục `boq/` từ trước: đọc `README.md` trong đó xem đang mirror
revision nào. BOQ ra revision mới → chạy lại toàn bộ (BOQ thay đổi thường kéo
theo dịch số dòng, mirror từng phần sẽ lệch).

## Bước 2 — Probe cấu trúc trước khi trích

BOQ xây dựng không có layout chuẩn. Cùng một workbook thường có 2–3 layout khác
nhau: sheet cơ điện kiểu `Area | Local | Description`, sheet đường ống kiểu
`CODE | CLASS | WORK ITEM | Size`, sheet chi phí gián tiếp kiểu `No. | Item |
Q'ty | Amount`. **Luôn probe trước, đừng đoán.**

Chạy script có sẵn trong skill (`scripts/boq_extract.py`, cần `openpyxl`):

```bash
python3 scripts/boq_extract.py probe "<đường dẫn>/BOQ.xlsx"
```

Nếu probe báo **"ô công thức CHƯA có giá trị lưu sẵn"** → dừng, nhờ người dùng
mở file bằng Excel và bấm Save rồi probe lại. File xuất từ phần mềm dự toán hay
do script sinh ra thường bị vậy, và build lúc đó sẽ ra thành tiền rỗng.

Đọc output và kiểm ba thứ:

- Hàng header có đúng không (script in số hàng + tên cột nhận diện được)
- Cột nào **không** map được — nếu thiếu `total` hay `description` thì mirror sẽ
  vô nghĩa, phải sửa `COLMAP` trong script trước khi build
- **3 dòng dữ liệu mẫu** script in ra: nhìn bằng mắt xem giá trị có rơi đúng
  cột không. Đây là bước bắt lỗi rẻ nhất — map sai một cột thì cả nghìn dòng sai.

Lỗi map cột hay gặp: từ khoá ngắn dính vào từ dài (`dn` dính `brandname`,
`code` dính `barcode`), và cột `Amount (VND)` bị cột `Month amount by contract`
cướp mất. Script đã xử lý bằng khớp nguyên từ cho từ khoá < 5 ký tự và tie-break
ưu tiên header ngắn hơn — nhưng vẫn phải nhìn dòng mẫu để chắc.

## Bước 3 — Build

```bash
python3 scripts/boq_extract.py build "<đường dẫn>/BOQ.xlsx" /tmp/boqbuild
```

Sinh ra `boq.db`, `boq_lines.csv`, `sheets/*.md`.

> ⚠️ Nếu thư mục dự án là ổ đĩa mount (Cowork), SQLite **không ghi trực tiếp
> được** (`disk I/O error`). Script đã tự dựng DB ở thư mục tạm rồi copy sang — nhưng
> `rm -rf` trên thư mục mount cũng có thể bị chặn, nên build ở `/tmp` rồi copy
> cả thư mục sang là an toàn nhất.

## Bước 4 — Đối soát (bắt buộc, đừng bỏ)

Đây là bước phân biệt mirror dùng được với mirror trông có vẻ đúng.

**Tổng tiền phải khớp với chính workbook.** BOQ luôn có dòng `GRAND TOTAL` hoặc
sheet `PRICE SUMMARY` ghi tổng. Chạy:

```bash
python3 scripts/boq_extract.py check /tmp/boqbuild
```

Lệnh này cộng các dòng `row_kind='item'` của từng sheet, so với dòng TỔNG lớn
nhất trong chính sheet đó, và báo KHỚP / LỆCH / "không thấy dòng TỔNG" (sheet
đó phải so tay với Excel hoặc với sheet `PRICE SUMMARY`). Nó cũng báo các dòng
có khối lượng mà thành tiền rỗng.

Lệch ≠ 0 nghĩa là một trong ba chuyện: map sai cột `total`, dòng cộng bị đếm
thành dòng item, hoặc sót dòng. **Sửa cho khớp tuyệt đối rồi mới đi tiếp** —
đừng ghi chú "lệch nhỏ, chấp nhận được".

**Kiểm chéo vài dòng bằng mắt.** Chọn 2–3 dòng ở giữa file, mở Excel so trực
tiếp: số hàng, mô tả, size, khối lượng, đơn giá, nhãn hiệu. Ưu tiên chọn dòng
đã từng dùng để trả lời tư vấn — nếu khớp thì mirror đáng tin.

**Kiểm tra bảng markdown không bị vỡ.** Ô `brand`/`remark` trong BOQ hay chứa
xuống dòng (`Hãng A / Xuất xứ B\n06.06`) làm vỡ bảng markdown. Script đã dọn,
nhưng verify lại:

```bash
python3 -c "
import glob
for f in glob.glob('<out>/sheets/*.md'):
    for i,l in enumerate(open(f,encoding='utf-8'),1):
        if l.startswith('|') and 3 < l.count('|') < 13 and '---' not in l:
            print('VỠ:',f,i,l[:80])
"
```

## Bước 5 — Viết `README.md` và `boq-index.md`

Script chỉ làm phần cơ học. Hai file này do bạn viết, vì cần nhận định.

**`README.md`** — cửa vào của folder:

- Câu đầu tiên: *"ĐỌC FOLDER NÀY THAY VÌ MỞ LẠI EXCEL"*
- Bảng "cần gì → mở file nào"
- **File BOQ nguồn nào được dùng, revision, ngày** — và **những bản BỊ CẤM dùng**
- Ý nghĩa cờ `§` `∅` `≠`
- Vài câu SQL mẫu
- Giới hạn: sheet nào chưa đọc được và vì sao
- Cách chạy lại khi có revision mới

**`boq-index.md`** — bức tranh tiền và phạm vi:

- Bảng: sheet → bộ môn → số dòng → số dòng trong phạm vi → tổng tiền
- **Cấu trúc giá hợp đồng**: direct cost / indirect cost / các khoản khác →
  tổng. Sheet tổng hợp giá thường có ô merge nhiều cấp nên trích tự động không
  đủ — mở Excel đọc thủ công phần này rồi gõ tay vào, nó chỉ vài chục dòng.
- **Danh mục dòng giá = 0** gom theo bộ môn — đây là ranh giới phạm vi hợp đồng,
  giá trị cao nhất của cả bản mirror. Người dùng sẽ cần nó mỗi lần tư vấn hỏi
  "sao không có hạng mục này".
- **Dòng lệch khối lượng** (`qty_mismatch=1`): nhà thầu chào khác khối lượng
  chủ đầu tư đưa. Nêu số lượng dòng, liệt kê những dòng lệch lớn.
- Ghi chú các quy ước riêng của dự án nếu có (mã CLASS, mã CODE hạng mục…)

## Bước 6 — Nối vào điều hướng

Mirror không ai biết là mirror vô dụng. Làm đủ ba việc:

1. Thêm dòng vào bảng "Đọc gì trước?" trong `CLAUDE.md` của dự án, trỏ tới
   `00_AI-CONTEXT/boq/README.md`, ghi rõ "mở thay vì mở lại Excel".
2. Thêm nhánh `boq\` vào sơ đồ cấu trúc folder trong `CLAUDE.md`.
3. Thêm mục vào `WORKLOG.md` (ở **đầu** phần nhật ký): mirror revision nào,
   tổng tiền đối soát khớp chưa, sheet nào chưa đọc được.

## Trả lời câu hỏi sau khi đã có mirror

Truy vấn `boq.db` trước, chỉ mở Excel khi cần thứ database không có (định dạng,
công thức, comment).

```sql
-- Hạng mục chứa từ khoá, kèm số dòng Excel để trích dẫn cho tư vấn
SELECT sheet, excel_row, description, size, unit, qty_bidder, total, brand
FROM lines WHERE description LIKE '%sprinkler%' AND row_kind='item';

-- Toàn bộ hạng mục của một khu vực
SELECT excel_row, description, size, qty_bidder, total FROM lines
WHERE area LIKE '%<tên khu vực>%' AND in_scope=1;

-- Ngoài phạm vi hợp đồng
SELECT sheet, excel_row, description FROM lines WHERE row_kind='item' AND in_scope=0;

-- Lệch khối lượng CĐT vs nhà thầu
SELECT sheet, excel_row, description, qty_client, qty_bidder FROM lines
WHERE qty_mismatch=1;
```

**Luôn trích dẫn kèm sheet + số dòng Excel** khi trả lời. Và luôn kiểm tra lại
tính hợp lý: một dòng ống đơn lẻ dài hơn cả nhà xưởng, hay số lượng đầu phun
nhiều hơn tổng diện tích cho phép, là dấu hiệu đọc sai chứ không phải phát hiện.

## Script

`scripts/boq_extract.py` — ba lệnh `probe` / `build` / `check`. Không sửa file
Excel gốc. Khi gặp layout cột lạ, sửa danh sách từ khoá `COLMAP` ở đầu script
(mỗi trường → các từ khoá header, không dấu, chữ thường) rồi probe lại.

Bảng `lines` trong `boq.db`: `sheet, excel_row, area, system, item_code,
description, size, unit, qty_client, qty_bidder, unit_price, mat_unit,
mat_total, lab_unit, lab_total, total, brand, remark, row_kind
(item/section/subtotal), in_scope, qty_mismatch`. Sheet tổng hợp giá không có
header chuẩn được lưu vào bảng `summary` (sheet, excel_row, item, amount).

Số dạng chữ trong ô Excel được đọc theo cả kiểu Anh (`1,234,567.5`) lẫn kiểu Việt
(`1.234.567,5`); dạng mơ hồ như `1,5` để trống chứ không đoán.

## Nhắc lại điều dễ sai

- **Chỉ mirror bản BOQ được phép reference.** Ghi rõ bản bị cấm vào `README.md`.
- Không xoá dòng giá 0 — đánh dấu `∅` và loại ra khi trả lời về phạm vi.
- Không bỏ qua bước đối soát tổng tiền. Lệch là sai, không phải sai số.
- Sheet tổng hợp giá đọc thủ công, đừng tin phần trích tự động.
- Chỉ dùng dữ liệu, thuật ngữ của công ty sở hữu workspace này (theo hồ sơ công ty).
- Xong thì ghim nguồn để biết khi BOQ đổi bản:
  `python3 "${CLAUDE_PLUGIN_ROOT}/skills/kit-start/scripts/check_sources.py" pin "<gốc dự án>" "<AI-context>" boq "<đường dẫn BOQ tương đối>"`

