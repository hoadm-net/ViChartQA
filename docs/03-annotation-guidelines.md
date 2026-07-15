# 03 — Hướng dẫn gán nhãn

Dành cho annotator. Đọc trước khi bắt đầu pilot; cập nhật thành v2 sau pilot. Xem [docs/05](05-annotation-examples.md) cho 2 document thật gán nhãn đầy đủ — ví dụ cụ thể áp dụng mọi quy tắc dưới đây.

## Nguyên tắc chung

1. Câu hỏi phải trả lời được chỉ từ document (title + body_text + chart đi kèm) — không cần kiến thức nền bên ngoài.
2. Đáp án phải duy nhất và khách quan.
3. Ưu tiên câu hỏi tự nhiên — hình dung người thật đọc báo cáo sẽ hỏi gì.
4. Giữ nguyên thuật ngữ miền — không đơn giản hoá thuật ngữ kinh tế/khoa học.
5. Không tự ý gắn nhãn multi-hop — chỉ gán `hop_type` là `text_and_chart`/`charts` nếu khớp đúng định nghĩa ở [Hop-type](#hop-type-phạm-vi-bằng-chứng-mới); nếu bỏ hết chart mà câu hỏi vẫn trả lời được từ text, đó là `text`; nếu bỏ body_text mà câu hỏi vẫn trả lời được từ 1 chart, đó là `chart`.

## Định nghĩa từng loại câu hỏi

### 1. Truy vấn dữ liệu (data_retrieval)

Đọc trực tiếp một giá trị hoặc nhãn.

- ✅ "Tỷ lệ thất nghiệp thanh niên năm 2023 là bao nhiêu?"
- ❌ "Số liệu năm 2023 là gì?" — mơ hồ nếu chart có nhiều chuỗi.

### 2. Thị giác (visual)

Bắt buộc tham chiếu thuộc tính thị giác (màu sắc, vị trí, kích thước, độ cao) để xác định đối tượng.

- ✅ "Cột màu cam cao nhất nằm ở năm nào?"
- ✅ "Đường màu xanh lá nằm phía trên hay dưới đường màu xám vào năm 2022?"
- ❌ "Giá trị cao nhất là bao nhiêu?" — không tham chiếu thị giác, thuộc loại 1 hoặc 3.

### 3. Suy luận kết hợp (compositional)

≥2 phép toán số học/logic: cộng, trừ, nhân, chia, phần trăm, trung bình, so sánh, đếm điều kiện.

- ✅ "Tổng kim ngạch xuất khẩu của ba năm gần nhất là bao nhiêu?"
- ✅ "Lạm phát năm nào cao hơn mức trung bình giai đoạn 2019–2023?"
- ❌ (vẫn hợp lệ) "Lạm phát năm 2023 cao hơn năm 2022 bao nhiêu?" — 1 phép trừ vẫn tính compositional; ưu tiên viết thêm biến thể ≥2 bước khi có thể.

### 4. Thị giác + suy luận (visual_compositional)

Xác định đối tượng bằng đặc điểm thị giác trước, rồi thực hiện phép toán.

- ✅ "Trong các năm có cột màu xanh lá, năm nào có chênh lệch lớn nhất so với năm liền trước?"
- ✅ "Đường nào (theo màu) có độ dốc tăng mạnh nhất giữa hai mốc đầu và cuối?"

### 5. Mở rộng (kiểu ChartQAPro)

| `question_type` | Định nghĩa | Ví dụ |
|---|---|---|
| `multiple_choice` | 4 lựa chọn (`choices`), 1 đúng; lựa chọn sai phải "gần đúng" | "Năm nào có tăng trưởng GDP cao nhất? A. 2021 B. 2022 C. 2023 D. 2024" |
| `fact_check` | Xác nhận đúng/sai một phát biểu | "Đúng hay sai: chi tiêu R&D luôn tăng liên tục trong giai đoạn quan sát?" |
| `unanswerable` | Không trả lời được từ document | "Nguyên nhân khiến lạm phát tăng đột biến năm 2023 là gì?" |

`unanswerable`: đáp án ghi `"unanswerable"`, không để trống. Không quá 5–7% tổng số câu hỏi.

## Hop-type (phạm vi bằng chứng, mới)

Chiều nhãn thứ hai, độc lập với `question_type` — mọi câu hỏi có cả hai. Tách theo đúng 1 tiêu chí: **cần đọc nguồn nào để trả lời** (không trộn với dạng câu trả lời — tính toán ra 1 giá trị hay xác minh đúng/sai, việc đó đã thuộc `question_type`). Kiểm tra bằng 2 phép thử:

- Bỏ hết chart, chỉ còn text — câu hỏi vẫn trả lời được đầy đủ? → `text`.
- Bỏ body_text, chỉ còn chart — câu hỏi vẫn trả lời được đầy đủ? → `chart`.
- Cả 2 phép thử đều KHÔNG trả lời được đầy đủ (thiếu 1 trong 2 là mất thông tin) → `text_and_chart` (hoặc `charts` nếu cần ≥2 chart, xem bên dưới).

### 1. `text`

Trả lời được chỉ từ body_text, không cần nhìn chart nào.

- ✅ "Theo bài viết, xu hướng chung của FDI và xuất nhập khẩu trong giai đoạn này là gì?" — nếu câu trả lời (vd "tích cực dù có biến động") chỉ được phát biểu trong text, không đọc được trực tiếp từ chart.
- ❌ Gắn `text` cho 1 số liệu vừa có trong text vừa có sẵn trên chart — ưu tiên `chart` (test bỏ text vẫn trả lời được).

### 2. `chart`

- ✅ "Vốn FDI năm 2020 là bao nhiêu?"
- ❌ Gắn `text_and_chart` chỉ vì body_text "cũng nhắc năm 2020" khi số liệu đã có sẵn trên chart.

### 3. `text_and_chart`

Cần cả 2 nguồn — thiếu 1 trong 2 thì không trả lời/xác minh đầy đủ được. Gồm 2 dạng thường gặp:

- **Lấy claim/số liệu chỉ có trong text, đối chiếu/tính toán với chart:**
  ✅ "Bài viết nêu dự báo tăng trưởng theo ADB cho năm 2022 — so với GDP năm 2021 trên Hình 1, mức tăng tuyệt đối dự kiến là bao nhiêu?"
  ❌ "GDP năm 2021 là bao nhiêu, theo đoạn văn mở đầu?" — nếu số liệu cũng có trên chart, đây là `chart`.
- **Xác minh 1 phát biểu đúng/sai cần cả 2 nguồn** (`question_type = fact_check`):
  ✅ "Đúng hay sai: vốn FDI tăng liên tục suốt 2011–2021?" — text chỉ nói "biến động", chart mới cho thấy giảm ở 2012, 2020.
  ❌ "Đúng hay sai: bài viết nói GDP tăng gấp 3 lần?" — chỉ cần đọc text, không thuộc phạm vi dataset (không phải `text_and_chart`, mà là `text`, và có thể không thuộc phạm vi nếu chỉ là trích dẫn nguyên văn không cần suy luận).

### 4. `charts`

≥2 chart trong cùng document; body_text là cầu nối.

- ✅ "Trong giai đoạn 2011–2021, chỉ tiêu nào tăng nhanh hơn: GDP (Hình 1) hay kim ngạch xuất nhập khẩu (Hình 3)?"
- ❌ Hai chart không liên quan chủ đề, ghép câu hỏi gượng ép chỉ để đạt tỷ trọng multi-hop.

`evidence` bắt buộc với **mọi** câu hỏi, kể cả hop_type đơn nguồn (`chart`/`text`) — không
còn bước xác minh chéo độc lập nên đây là chốt kiểm chứng duy nhất còn lại:

- Hop từ chart: `description` — đánh số từng bước truy hồi giá trị trên ảnh (xem quy ước ở [docs/02](02-dataset-design.md#định-dạng-evidence)), annotator gõ tay trực tiếp; không có bảng dữ liệu gốc để đối chiếu tự động, công cụ chỉ chặn lưu nếu để trống.
- Hop từ text: `quote` là đoạn trích nguyên văn ngắn từ body_text — công cụ auto-check khớp nguyên văn.

Thiếu evidence (rỗng) hoặc quote không khớp nguyên văn `body_text` = công cụ chặn lưu ngay lúc soạn (xem [annotation-tool/README.md](../annotation-tool/README.md#hướng-dẫn-sử-dụng)).

## Quy tắc viết đáp án

- Đáp án số: giữ nguyên đơn vị/định dạng trên chart (vd `6.2%`, không viết `0.062`).
- Dung sai đánh giá tự động: relaxed accuracy trong 5%. Annotator vẫn ghi đáp án chính xác tuyệt đối.
- Đáp án không phải số: exact match sau chuẩn hoá.
- `derivation` (bắt buộc có điều kiện): với `answer_type: numeric` và `question_type` là `compositional`/`visual_compositional` có tính toán — công thức số học thuần dùng đúng số annotator đọc được từ chart (vd. `"8.4 - 2.5"`, `"(14740 + 1910)/2"`). Các loại khác để trống. Xem ví dụ ở [docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất).
- `equivalent_answers` (tuỳ chọn): các cách diễn đạt khác cũng được chấp nhận cho cùng 1 đáp án (vd đơn vị/cách viết số khác nhau) — không bắt buộc, chỉ điền khi thực sự có biến thể đáng kể.

## Quy trình

### 1. Đọc document

Đọc title + body_text trước, ghi chú số liệu/claim chỉ xuất hiện trong text (nguyên liệu cho `text`/`text_and_chart`) và quan sát từng chart (loại: đơn/`combo`/`subplot`).

### 2. Soạn câu hỏi

Ở trang "Soạn câu hỏi" (xem [annotation-tool/README.md](../annotation-tool/README.md#hướng-dẫn-sử-dụng)): có thể bấm sinh gợi ý bằng LLM để tham khảo (không tự lưu vào dataset — chỉ dùng làm mẫu rồi tự viết/sửa lại), hoặc viết thẳng từ đầu. Mỗi document cần tối thiểu:

- 1 câu `chart` (compositional hoặc visual_compositional).
- 1 câu multi-hop (`text_and_chart`/`charts`).

Mọi câu đều cần `evidence` đầy đủ (xem [Hop-type](#hop-type-phạm-vi-bằng-chứng-mới)); công cụ chặn lưu nếu thiếu, hoặc nếu quote text không khớp nguyên văn `body_text`.

### 3. Sửa/rút câu hỏi

Không có bước xác minh chéo riêng — annotator (hoặc người khác xem lại sau) có thể bấm "Sửa" để chỉnh bất kỳ câu nào đã lưu, hoặc "Bỏ" để rút một câu không đạt. Mỗi lần tạo/sửa/rút đều ghi lại một bản snapshot (question_versions) — xem lịch sử ngay trên trang để biết ai sửa gì lúc nào.

## Checklist nhanh trước khi nộp một batch

- [ ] Mỗi document đủ tỷ trọng taxonomy (cả 2 chiều, ≥1 câu multi-hop/document)
- [ ] Mọi câu hỏi qua phép thử bỏ text/bỏ chart đúng hop_type và có `evidence` đầy đủ
- [ ] Mọi câu `answer_type: numeric` thuộc compositional/visual_compositional có `derivation`, khớp số liệu đọc từ chart
- [ ] Không có câu hỏi trùng lặp ý nghĩa trong cùng document
- [ ] Đáp án số giữ đúng định dạng/đơn vị trên chart
- [ ] Câu "không trả lời được" có đáp án `"unanswerable"`

---

**Changelog guideline:** v1 — Tuần 1 (bản khởi tạo). v2 — cập nhật sau pilot.
