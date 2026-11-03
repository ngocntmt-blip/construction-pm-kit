---
name: edit-output-in-place
description: "Sửa file Word/Excel/markdown đã có của người dùng an toàn: lấy bản mới nhất trên đĩa, kiểm file đang mở, backup trước khi ghi, sửa tại chỗ, tô vàng chỗ sửa, hướng dẫn Compare. Dùng khi nói \"sửa file này\", \"cập nhật bản đã gởi\", \"lên rev\", \"chỉnh lại văn bản đã làm\", hoặc khi sửa bất kỳ file nào đã tồn tại."
---

# Sửa file output — luôn lấy bản mới nhất trên đĩa

File trong folder dự án là **bản gốc duy nhất**. Bản trong context của Claude (upload, `/tmp`,
`content.json`, script sinh file) chỉ là snapshot lúc tạo — dùng nó là xoá mất sửa tay của
người dùng. Lỗi hay gặp: dựng lại một kế hoạch HSE từ bản upload cũ rồi chép đè; dựng lại
một biện pháp thi công từ `content.json` rồi ghi về máy không kiểm mốc thời gian.

## Bước 1 — Xác định bản gốc và kiểm file có đang mở không

```bash
ls -la --time-style=full-iso "$HOME/mnt/<folder>/<đường dẫn>"
```
(hoặc `device_list_dir` với đường dẫn tuyệt đối trên máy người dùng)

- So `mtime` với lần ghi cuối của Claude. mtime **mới hơn** → file chứa sửa tay của người
  dùng → **bắt buộc** lấy file đó làm gốc. Không chắc ai sửa lần cuối thì vẫn lấy file trên đĩa.
- **Kiểm file khoá**: Word/Excel tạo `~$<tên file>` khi đang mở.
  ```bash
  ls -a "<folder>" | grep '^~\$' || echo "khong co file dang mo"
  ```
  Có file khoá → **DỪNG, không ghi**. Báo người dùng đóng file rồi mới làm tiếp. Ghi khi họ đang
  mở sẽ dẫn tới việc họ bấm Save và đè ngược lên bản Claude vừa sửa.
- Nói rõ trong câu trả lời: đang sửa file nào, mtime bao nhiêu.
- Không thấy file / thấy nhiều bản → **hỏi**, không đoán.

## Bước 2 — Backup trước khi ghi (BẮT BUỘC)

Sửa tại chỗ không có undo: script làm vỡ bảng, mất ảnh hay crash giữa lúc save là mất bản gốc.
Word không khôi phục được file bị ghi đè từ bên ngoài.

```bash
D="<folder chứa file>"; F="<tên file>"
mkdir -p "$D/_bak"
cp "$D/$F" "$D/_bak/${F%.*}_$(date +%y%m%d-%H%M).${F##*.}"
find "$D/_bak" -type f -mtime +7 -print   # báo bản cũ hơn 7 ngày để người dùng tự xoá
```

Không tự xoá file trong `_bak` — chỉ liệt kê, để người dùng quyết.

## Bước 3 — Sửa tại chỗ trên máy người dùng (mặc định)

Dùng `device_bash`, thao tác thẳng trên file trong `$HOME/mnt/...`. Không stage, không commit,
không tạo bản thứ hai.

- Word → `python-docx`
- Excel → `openpyxl` (giữ nguyên checkbox/print settings — sửa XML trong zip nếu cần)
- Markdown / text → `sed -i` hoặc python read-modify-write

**Không bao giờ** gõ lại nội dung file từ output tool trước đó (có thể đã bị cắt) — luôn để
script tự đọc file rồi ghi lại.

**Chỉ sửa đúng phần được yêu cầu.** Thấy lỗi khác thì nêu ra để người dùng quyết, không tự sửa.

## Bước 4 — Highlight vàng mọi chỗ đã sửa hoặc thêm mới

(Trừ khi hồ sơ công ty đặt `conventions.highlight_edits: false`.)

Word:
```python
from docx.enum.text import WD_COLOR_INDEX
for r in paragraph.runs:
    r.font.highlight_color = WD_COLOR_INDEX.YELLOW
```
Excel: `PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")`

Cách làm gọn: gom các chuỗi đặc trưng của phần mới vào một list `MARKERS`, duyệt toàn bộ
`doc.paragraphs` + paragraph trong mọi cell của mọi table, đoạn nào chứa marker thì tô cả run.
Nhớ duyệt cả bảng và sơ đồ khối — nội dung trong table không nằm ở `doc.paragraphs`.

**Giới hạn cần biết:** highlight chỉ cho thấy chỗ Claude *chủ động đánh dấu*. Nếu Claude lỡ sửa
chỗ khác mà không tô, người dùng không thấy — vì vậy bước 6 (Compare) là bắt buộc phải nhắc.

## Bước 5 — Chỉ khi buộc phải build trong container

Khi bước sửa cần thư viện/skill chỉ có ở container:

1. `device_stage_files` → **ghi lại `mtimeMs`** trả về.
2. Build.
3. `device_commit_files` **luôn kèm `expectedMtimeMs`** = mtime đã ghi. **Không dùng `force`.**

Bị từ chối vì lệch mtime = người dùng vừa sửa tay → stage lại, merge, không ép ghi.

## Bước 6 — File sinh ra từ script (doc-from-template, script dựng văn bản + content.json…)

Script chỉ dùng cho **lần tạo đầu tiên**. Một khi người dùng đã mở file sửa tay, chạy lại script
là **dựng lại toàn bộ nội dung và xoá sạch sửa tay**.

Từ lần sửa thứ hai trở đi: **file Word/Excel trên đĩa là bản gốc duy nhất**; `content.json` chỉ
coi là lịch sử nội dung ban đầu, **không dùng để dựng lại rev sau**. Nói rõ điều này với người
dùng ở lần sửa tay đầu tiên, và ghi vào project memory của tài liệu đó.

## Bước 7 — Báo lại cho người dùng

- Liệt kê đúng những chỗ đã sửa (mục nào, bảng nào, bước nào).
- **Nhắc cách xem toàn bộ thay đổi, không chỉ chỗ highlight**: Word → Review → Compare, chọn
  bản trong `_bak` làm Original và file hiện tại làm Revised. Cho ra danh sách **mọi** khác
  biệt, kể cả chỗ Claude không khai báo.
- Nhắc **đóng file trong Word/Excel rồi mở lại** — ứng dụng giữ bản đã nạp trong bộ nhớ nên
  không tự thấy thay đổi trên đĩa. Đây là lý do phổ biến nhất khiến người dùng "không thấy update".
- Nhắc bỏ highlight trước khi nộp ra ngoài (Word: Home → Text Highlight Color → No Color).
- Nói rõ bản backup nằm ở đâu.
- Sửa tại chỗ = **đã giao rồi**, không cần gởi lại file vào chat trừ khi người dùng yêu cầu.

## Verification trước khi trả lời

1. Xác nhận đã có bản backup trong `_bak` trước khi ghi.
2. `ls -la --time-style=full-iso` lại folder — mtime mới đúng là lần ghi vừa rồi, kích thước file
   thay đổi hợp lý (lệch quá lớn = script đã làm hỏng gì đó, phải kiểm lại).
3. Đếm số run đã highlight, in danh sách đoạn đã sửa để tự đối chiếu:
   ```bash
   python3 -c "import zipfile,re;x=zipfile.ZipFile('<file>.docx').read('word/document.xml').decode('utf8');print(len(re.findall(r'w:highlight w:val=\"yellow\"',x)))"
   ```
4. Đối chiếu từng gạch đầu dòng người dùng yêu cầu với chỗ đã sửa — thiếu chỗ nào thì làm nốt
   trước khi trả lời.