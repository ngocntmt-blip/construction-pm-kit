---
name: spec-mirror
description: "Mirror Specification, Technical Datasheet, Design Description (PDF) của dự án sang markdown có cấu trúc trong 00_AI-CONTEXT/ — tiêu chuẩn áp dụng, thông số thiết kế từng hệ, vật liệu, thử nghiệm/nghiệm thu, datasheet, vendor list, mâu thuẫn cần RFI — mỗi con số ghi trang nguồn. Dùng khi nói \"đọc/mirror spec\", \"làm specs.md\", \"tóm tắt hồ sơ kỹ thuật\", \"tiêu chuẩn áp dụng\", \"thông số thiết kế hệ PCCC/HVAC/điện\", hoặc spec ra revision mới. Không dùng cho bản vẽ (drawings-analyzer) hay khối lượng/chi phí (boq-mirror)."
---

# Spec Mirror

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

Bộ specification của một dự án thường 50–150 trang PDF chia làm nhiều file. Mỗi lần cần tra "cường độ phun sprinkler bao nhiêu" mà phải mở lại PDF thì vừa chậm vừa tốn token, và câu trả lời không ổn định giữa các lần hỏi.

Skill này đọc một lần, viết ra bản markdown có cấu trúc, rồi mọi câu hỏi sau đó trả lời từ file markdown đó. Bộ spec 89 trang của một dự án PCCC nén còn khoảng 14 KB markdown — rẻ hơn hai bậc độ lớn.

Điều quan trọng nhất cần hiểu: **đây không phải việc chuyển định dạng.** Chép nguyên văn PDF sang markdown thì vô dụng — vẫn dài như cũ, vẫn phải đọc hết. Giá trị nằm ở chỗ chắt lọc ra những con số và yêu cầu mà PM thực sự phải tra trong lúc làm việc, rồi xếp chúng vào chỗ dễ tìm.

## Trước khi bắt đầu

Xác định 2 việc, chưa rõ thì hỏi người dùng:

1. **Có những bộ môn nào** — PCCC, HVAC, điện, cấp thoát nước, kết cấu… Số bộ môn quyết định cấu trúc output.
2. **Có file BOQ không** — nếu có thì đối chiếu để tìm mâu thuẫn (Bước 5). Không có thì bỏ qua bước đó, đừng bịa.

Trả lời bằng tiếng Việt, trừ khi người dùng yêu cầu khác.

## Nếu mirror đã tồn tại

Kiểm tra `specs*.md` trong thư mục AI-context của dự án trước khi làm bất cứ gì. Nếu đã có mirror:

- **Câu hỏi tra cứu** ("cường độ phun bao nhiêu", "áp thử mấy bar") → trả lời thẳng từ mirror, rồi **spot-verify vài con số then chốt** với PDF gốc bằng `pdftotext`. Đừng dựng lại mirror — đó là lãng phí và là lý do mirror tồn tại.
- **Spec có revision mới** → surgical edit, chỉ sửa phần đổi.
- **Người dùng yêu cầu làm lại từ đầu** → mới dựng lại toàn bộ.

Spot-verify quan trọng vì mirror có thể đã cũ hoặc thiếu. Nếu phát hiện mirror thiếu con số mà người dùng cần, bổ sung luôn vào mirror rồi mới trả lời — lần sau đỡ phải mở PDF.

## Bước 1 — Khảo sát và phân loại tài liệu

Liệt kê mọi PDF trong thư mục spec. Với mỗi file ghi lại: tên file, mã tài liệu, số trang, revision, ngày phát hành, người duyệt (đọc từ trang bìa).

Phân loại theo vai trò, vì mỗi loại cho ra thông tin khác nhau:

| Loại | Nhận biết | Cho ra cái gì |
|------|-----------|---------------|
| **Design Description** (DD) | Ngắn, 10–20 trang, có công thức và bảng tính | **Thông số thiết kế** — quý nhất, đọc kỹ nhất |
| **Specification** (SP) | Dài nhất, 40–100 trang, chia mục theo vật liệu / lắp đặt / thử nghiệm | Yêu cầu vật liệu, thi công, thử nghiệm, hồ sơ phải nộp |
| **Technical Datasheet** (DS) | Bảng thông số theo từng thiết bị | Danh mục thiết bị + yêu cầu kỹ thuật từng loại |

Nếu thư mục lẫn cả bản vẽ, catalogue nhà sản xuất hay biên bản họp — bỏ qua, chỉ lấy 3 loại trên, và nói cho người dùng biết đã bỏ qua gì.

## Bước 2 — Kiểm tra lớp text trước khi đọc

Chạy:

```bash
python3 scripts/probe_pdfs.py <thư_mục_spec> --dump <thư_mục_tạm>/spec_txt
```

Script báo từng file đọc được bằng text hay là bản scan, đánh giá **theo từng trang** (trang bìa ít chữ không làm cả file bị coi là scan; trang scan chèn giữa file text được liệt kê riêng). `--dump` ghi text từng file ra `.txt` có dấu `=== TRANG n ===`, để tìm bằng `grep` và lấy số trang nguồn. Thư mục dump phải nằm ngoài thư mục PDF gốc.

PDF có lớp text vector trích ra chính xác 100%. Trang scan thì text gần như rỗng — phải đọc bằng vision, chậm hơn và dễ sai. **File hay trang nào là scan thì ghi rõ trong mirror là "nguồn scan, độ tin cậy thấp hơn" thay vì im lặng.**

Script tự chọn bộ đọc: `pdftotext` (poppler) nếu máy có, không thì PyMuPDF (`pip install pymupdf`) — thường gặp khi chạy trên máy Windows. Chỉ dùng pdfplumber khi không còn cách nào: chậm hơn khoảng một bậc độ lớn và dễ timeout với file vài chục MB.

## Bước 3 — Trích thông số thiết kế (phần quan trọng nhất)

Đây là phần người dùng tra nhiều nhất nên làm kỹ nhất. Mục tiêu: **mọi con số cần cho tính toán, shop drawing hay RFI đều nằm trong mirror, không phải mở lại PDF.**

Design Description là nguồn chính. Lấy đủ:

- Dữ liệu đầu vào công trình: nhóm công trình, bậc chịu lửa, hạng nguy hiểm cháy, khối tích, loại hình
- Với **mỗi hệ thống**, lấy trọn bộ tham số thiết kế cùng **cơ sở tiêu chuẩn** của nó
- Kết luận lựa chọn thiết bị chính (công suất bơm, dung tích bể, cỡ máy…)
- Công thức tính nếu spec có nêu — ghi lại cả công thức, không chỉ kết quả

Ví dụ mức chi tiết đạt yêu cầu, hệ sprinkler kho rack:

> K = 16,8 · t = 74 °C · áp làm việc 3,24 bar · diện tích bảo vệ 1 đầu 8,4 m² (2,8 × 3,0) · 12 đầu hoạt động đồng thời · Q = 7,263 l/s/đầu → Q hệ = 87,12 l/s · không yêu cầu sprinkler trong rack · cơ sở: SP 241.1311500.2015 điều 5 · nguồn: DD tr. 7

Chỉ ghi "sprinkler theo SP 241" là hỏng — người đọc vẫn phải mở PDF, mirror mất hết giá trị.

**Mỗi con số hoặc nhóm số ghi kèm nguồn: loại tài liệu + số trang** (`DD tr. 7`, `SP tr. 23`, `DS-05 tr. 2`). Lấy số trang từ dấu `=== TRANG n ===` trong file dump. Có số trang thì lần spot-verify sau chỉ mở đúng một trang, và khi trả lời tư vấn trích dẫn được ngay. Trong bảng, thêm cột "Nguồn".

**Khi hai khu vực dùng hai cơ sở tính khác nhau, tách bạch rõ ràng.** Lỗi này hay gặp và hậu quả nặng: nếu khu kho tính theo tiêu chuẩn Nga còn khu sản xuất theo TCVN mà mirror gộp chung, người đọc sẽ lấy nhầm tiêu chuẩn khi xét vật tư tương đương.

## Bước 4 — Trích các phần còn lại

**Tiêu chuẩn áp dụng** — lập bảng, mỗi tiêu chuẩn kèm **vai trò cụ thể trong dự án này**, không chỉ liệt kê tên. "QCVN 02:2020/BCA — trạm bơm, bắt buộc cho cụm bơm chữa cháy chính" hữu ích hơn hẳn "QCVN 02:2020/BCA — trạm bơm chữa cháy". Tách quy chuẩn Việt Nam (bắt buộc) và tiêu chuẩn nước ngoài (tham chiếu).

**Yêu cầu vật liệu** — vật liệu, cấp áp lực, bề dày tối thiểu theo cỡ, tiêu chuẩn chế tạo, yêu cầu sơn/chống ăn mòn. Giữ nguyên số hiệu tiêu chuẩn (ASTM A53 Gr.B, BS 1387, ASME Class 150#) vì đó là thứ dùng để so vật tư khi trình duyệt.

**Thử nghiệm & nghiệm thu** — áp thử, thời gian giữ áp, cách xử lý khuyết tật, các bước kiểm tra tại nhà máy và tại công trường, đơn vị nghiệm thu cuối.

**Hồ sơ nhà thầu phải nộp** — liệt kê để PM biết trước phải chuẩn bị gì.

**Danh mục datasheet** — bảng thiết bị → mã datasheet, để tra nhanh khi làm material approval.

**Vendor list** — hãng được duyệt và hãng nhà thầu đề xuất, nếu spec hoặc BOQ có.

## Bước 4b — Soi mâu thuẫn ngay bên trong bộ hồ sơ

Trong lúc đọc, chú ý những chỗ chính bộ tài liệu tự đá nhau. Đây là loại phát hiện giá trị nhất mà skill này tạo ra, vì nó rẻ (đằng nào cũng đang đọc) nhưng hậu quả nếu bỏ sót thì thật — một con số sai trong Design Description sẽ chảy thẳng vào shop drawing rồi ra công trường.

Bốn chỗ hay sai, theo kinh nghiệm:

1. **Đơn vị không nhất quán** — cùng một hệ số K, trang này ghi `gpm/bar^½`, trang kia ghi `gpm/psi^½`. Chênh nhau gần 4 lần lưu lượng. Ghi rõ giá trị nào đúng và tại sao.
2. **Năm ban hành tiêu chuẩn lệch nhau** — mục này dẫn TCVN 7336:2021, mục kia ghi 7336:2023 (bản không tồn tại).
3. **Specification vs Datasheet** — SP yêu cầu thân van inox, DS ghi gang; SP bắt thử 12 bar, DS ghi van chịu 7 bar.
4. **Spec dẫn chiếu bảng/phụ lục không có trong file** — "theo Bảng 3" nhưng PDF chỉ có Bảng 1.

Cũng để ý **bộ môn bị thiếu spec hoàn toàn**. Nếu hợp đồng có hạng mục báo cháy vài tỷ mà thư mục spec chỉ có tài liệu chữa cháy, đó là khoảng trống lớn — nêu ra, vì lúc lập Compliance List sẽ không có gì để đối chiếu.

Đưa các phát hiện này vào mục "Điểm cần lưu ý cho PM".

## Bước 5 — Đối chiếu chéo và cảnh báo

Chỉ làm khi dự án có file BOQ hoặc vendor list. Đây là phần tạo giá trị cao nhất trên mỗi dòng chữ, vì nó bắt lỗi trước khi lỗi gây trả hồ sơ.

Loại mâu thuẫn đáng tìm:

- **Vendor list vs BOQ chi tiết** — vendor list ghi hãng A, BOQ báo giá hãng B. Gây trả hồ sơ material approval, mất 1–2 tuần.
- **Thông số vật tư BOQ thấp hơn spec** — datasheet yêu cầu tôn 1,6 mm, BOQ chào 1,0 mm. Đây là chỗ tư vấn bắt lỗi đầu tiên.
- **Yêu cầu spec vs phạm vi hợp đồng** — spec cần một hạng mục mà BOQ ghi 0 đ hoặc "excluded", nhưng hệ thống vẫn phụ thuộc nó để nghiệm thu.
- **Thiếu vật tư trong BOQ** — datasheet yêu cầu mỗi tủ có 2 van góc DN65, BOQ không có dòng nào cho chúng.

**Phân tầng mức độ** khi trình bày — người dùng cần biết cái nào xử lý được nội bộ, cái nào phải hỏi tư vấn:

| Mức | Nghĩa | Hành động |
|-----|-------|-----------|
| 🔴 Đỏ | BOQ/vật tư nhà thầu chào **thấp hơn** yêu cầu spec | Sửa nội bộ trước khi nộp, hoặc chấp nhận rủi ro bị trả |
| 🟡 Vàng | Spec và datasheet **tự mâu thuẫn** — nhà thầu không tự quyết được | Gộp thành RFI gửi tư vấn |
| ⚪ Xám | Spec **thiếu** hoặc dẫn chiếu tài liệu không có | Công văn xin bổ sung |

Viết mục cuối file: **"Điểm cần lưu ý cho PM"** — mỗi điểm nêu mức độ, rủi ro cụ thể và việc phải làm. Không tìm thấy mâu thuẫn nào thì nói thẳng là không tìm thấy, đừng nặn cho đủ mục.

## Cấu trúc file output

Quyết định theo số bộ môn:

- **1 bộ môn** → một file `specs.md`
- **Nhiều bộ môn** → `specs.md` làm mục lục ngắn (bảng: bộ môn → file → phạm vi), cộng `specs-pccc.md`, `specs-hvac.md`, `specs-dien.md`… Lý do tách: file 40 KB đọc một lần tốn gần bằng đọc lại PDF, mất ý nghĩa của việc mirror.

Lưu vào thư mục AI-context của dự án — dùng thư mục mà `profile_status.py` báo, không tạo thư mục thứ hai. Chưa có thư mục nào thì tạo `00_AI-CONTEXT/` và báo người dùng.

Mỗi file mở đầu bằng khối nguồn, để sau này biết mirror đã cũ chưa:

```markdown
> Mirror từ `02.Contract-BOQ-Spec/SPECIFICATION/`:
> - `PRJ-SP-FF-001-Rev.00-Specification.pdf` (55 tr.)
> - `PRJ-DD-FF-001-Rev.00-Design Description.pdf` (12 tr.)
> Tất cả Rev.00, phát hành DD/MM/YYYY. Author <tên> · Approver <tên> (<đơn vị tư vấn>).
> Cập nhật lần cuối: 08/08/2026
```

Bố cục thân file — thứ tự này đặt cái tra nhiều nhất lên trên:

```
1. Tiêu chuẩn thiết kế áp dụng      (bảng, có vai trò từng tiêu chuẩn)
2. Dữ liệu thiết kế công trình
3. Thông số thiết kế từng hệ         ← dài nhất, chi tiết nhất
4. Yêu cầu vật liệu
5. Thử nghiệm & nghiệm thu
6. Hồ sơ nhà thầu phải nộp
7. Thiết bị được chấp thuận (vendor list)
8. Danh mục datasheet chi tiết
9. Điểm cần lưu ý cho PM             ← mâu thuẫn & rủi ro
```

Dùng bảng cho mọi thứ có cặp tên–giá trị. Bảng vừa gọn hơn văn xuôi vừa dễ quét mắt khi đang vội.

Có mẫu đầy đủ trong `references/output_template.md` — đọc khi cần thấy hình dung cụ thể.

## Cập nhật khi có revision mới

Khi tư vấn phát hành spec revision mới, **chỉ sửa phần thay đổi** (surgical edit), giữ nguyên phần còn lại, rồi cập nhật dòng "Cập nhật lần cuối" và revision trong khối nguồn. Đừng viết lại cả file — người dùng có thể đã tự thêm ghi chú vào đó.

## Kiểm tra trước khi giao

Tự soát theo 6 câu hỏi này, vì đây là những chỗ mirror hay hỏng:

1. **Có con số nào bị bỏ sót không?** Mở lại phần thông số thiết kế trong Design Description, đối chiếu từng dòng. Thiếu một con số là lần sau vẫn phải mở PDF.
2. **Có chỗ nào chỉ ghi tên tiêu chuẩn mà không ghi giá trị không?** Có thì quay lại lấy giá trị.
3. **Số liệu có khớp giữa các mục không?** Ví dụ tổng dung tích bể ở mục thông số phải khớp với mục cảnh báo.
4. **Người đọc mirror này có làm được shop drawing và RFI mà không cần mở PDF không?** Chưa thì chưa xong.
5. **Có bộ môn nào trong hợp đồng mà mirror không nhắc tới không?** Nếu có, khả năng cao là thiếu spec — nêu ra thay vì im lặng.
6. **Con số nào chưa có trang nguồn không?** Bổ sung trước khi giao. Chọn ngẫu nhiên 3 con số, mở đúng trang ghi nguồn, xác nhận khớp.

## Nguyên tắc

**Chắt lọc, không chép.** Một đoạn trong mirror dài gần bằng đoạn gốc thì nó không đáng có mặt.

**Không suy diễn số liệu.** Spec không nêu thì ghi "spec không nêu", không tự điền theo tiêu chuẩn chung. Người dùng dựa vào mirror này để làm shop drawing và nghiệm thu — một con số bịa gây hậu quả thật.

**Mọi con số có trang nguồn.** Không có nguồn thì không kiểm lại được, và mirror mất uy tín ngay lần đầu tư vấn hỏi "lấy ở đâu".

**Giữ nguyên đơn vị và số hiệu tiêu chuẩn như bản gốc.** Đừng quy đổi bar sang MPa hay ngược lại trừ khi bản gốc ghi cả hai.

**Đánh dấu chỗ không chắc.** Nguồn scan, chữ mờ, bảng bị vỡ khi trích — ghi rõ, đừng đoán.
