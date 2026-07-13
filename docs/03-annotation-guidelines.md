# 03 — Hướng dẫn gán nhãn

Dành cho annotator (Pod B, Pod C — xem [docs/05](05-timeline-and-roles.md)). Đọc trước pilot Tuần 1; cập nhật thành v2 sau pilot.

## Nguyên tắc chung

1. Câu hỏi phải trả lời được chỉ từ document (title + body_text + chart đi kèm) — không cần kiến thức nền bên ngoài (trừ nhóm "giả định").
2. Đáp án phải duy nhất và khách quan.
3. Ưu tiên câu hỏi tự nhiên — hình dung người thật đọc báo cáo sẽ hỏi gì.
4. Giữ nguyên thuật ngữ miền — không đơn giản hoá thuật ngữ kinh tế/khoa học.
5. Không tự ý gắn nhãn multi-hop — chỉ gán `hop_type != single_chart` nếu khớp đúng định nghĩa ở [Hop-type](#hop-type-phạm-vi-bằng-chứng-mới); nếu bỏ body_text mà câu hỏi vẫn trả lời được từ 1 chart, đó là `single_chart`.

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
| `hypothetical` | Giả định ngoài dữ liệu quan sát được | "Nếu xu hướng 2020–2024 tiếp diễn, giá trị năm 2027 gần nhất là bao nhiêu?" |
| `fact_check` | Xác nhận đúng/sai một phát biểu | "Đúng hay sai: chi tiêu R&D luôn tăng liên tục trong giai đoạn quan sát?" |
| `unanswerable` | Không trả lời được từ document | "Nguyên nhân khiến lạm phát tăng đột biến năm 2023 là gì?" |

Hội thoại nhiều lượt: câu sau set `follow_up_of` trỏ tới id câu trước, `question_type` khai theo bản chất suy luận của câu đó. Ví dụ: Lượt 1 (`id: q1`, `data_retrieval`) "Năm nào GDP tăng cao nhất?" → Lượt 2 (`follow_up_of: q1`, `compositional`) "Vậy năm đó cao hơn năm liền trước bao nhiêu?".

`unanswerable`: đáp án ghi `"unanswerable"`, không để trống. Không quá 5–7% tổng số câu hỏi.

## Hop-type (phạm vi bằng chứng, mới)

Chiều nhãn thứ hai, độc lập với `question_type` — mọi câu hỏi có cả hai. Kiểm tra bằng phép thử bỏ text: xoá body_text, nếu câu hỏi vẫn trả lời được đầy đủ từ chart, đó là `single_chart`.

### 1. `single_chart`

- ✅ "Vốn FDI năm 2020 là bao nhiêu?"
- ❌ Gắn `text_to_chart` chỉ vì body_text "cũng nhắc năm 2020" khi số liệu đã có sẵn trên chart.

### 2. `text_to_chart`

Hop 1 lấy claim/số liệu chỉ tồn tại trong body_text; hop 2 đối chiếu/tính toán với chart.

- ✅ "Bài viết nêu dự báo tăng trưởng theo ADB cho năm 2022 — so với GDP năm 2021 trên Hình 1, mức tăng tuyệt đối dự kiến là bao nhiêu?"
- ❌ "GDP năm 2021 là bao nhiêu, theo đoạn văn mở đầu?" — nếu số liệu cũng có trên chart, đây là `single_chart`.

### 3. `chart_to_chart`

≥2 chart trong cùng document; body_text là cầu nối.

- ✅ "Trong giai đoạn 2011–2021, chỉ tiêu nào tăng nhanh hơn: GDP (Hình 1) hay kim ngạch xuất nhập khẩu (Hình 3)?"
- ❌ Hai chart không liên quan chủ đề, ghép câu hỏi gượng ép chỉ để đạt tỷ trọng multi-hop.

### 4. `fact_check_dual`

Cần đọc cả text lẫn chart để xác minh đúng/sai.

- ✅ "Đúng hay sai: vốn FDI tăng liên tục suốt 2011–2021?" — text chỉ nói "biến động", chart mới cho thấy giảm ở 2012, 2020.
- ❌ "Đúng hay sai: bài viết nói GDP tăng gấp 3 lần?" — chỉ cần đọc text, không thuộc phạm vi dataset.

`evidence` bắt buộc với mọi câu `hop_type != single_chart`, trỏ vào dữ liệu đã có sẵn:

- Hop từ chart: `series` + `x` lấy nguyên văn từ `data_table` đã nhập ở Bước 0.
- Hop từ text: `quote` là đoạn trích nguyên văn ngắn từ body_text.

Thiếu evidence hoặc evidence không khớp `data_table`/`body_text` = trả về sửa ở bước xác minh chéo.

## Quy tắc viết đáp án

- Đáp án số: giữ nguyên đơn vị/định dạng trên chart (vd `6.2%`, không viết `0.062`).
- Dung sai đánh giá tự động: relaxed accuracy trong 5%. Annotator vẫn ghi đáp án chính xác tuyệt đối.
- Đáp án không phải số: exact match sau chuẩn hoá.
- `derivation` (bắt buộc có điều kiện): với `answer_type: numeric` và `question_type` là `compositional`/`visual_compositional` có tính toán — công thức số học thuần dùng đúng số trong `data_table`/evidence (vd. `"8.4 - 2.5"`, `"(14740 + 1910)/2"`). Các loại khác để trống. Xem ví dụ ở [docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất).

## Quy trình 5 bước

### Bước 0 — Đọc document

1. Đọc title + body_text trước, ghi chú số liệu/claim chỉ xuất hiện trong text (nguyên liệu cho `text_to_chart`/`fact_check_dual`).
2. Với từng chart: xác định loại (bar/line/pie), độ phức tạp (simple/complex), nhập `data_table` vào công cụ ([docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất)).

### Bước 1 — Seed thủ công

2-3 câu hỏi seed theo cả 2 chiều taxonomy, tối thiểu:

- 1 câu `single_chart` (compositional hoặc visual_compositional).
- 1 câu multi-hop (`text_to_chart`/`chart_to_chart`/`fact_check_dual`) dùng nguyên liệu từ Bước 0, kèm `evidence` đầy đủ.

### Bước 2 — Mở rộng bằng VLM

Đưa seed + title + body_text + data_table vào prompt cho GPT-4o/Gemini/Qwen2.5-VL, sinh 4-6 câu ứng viên rải đều theo cả 2 chiều còn thiếu. Yêu cầu mô hình tự đề xuất `evidence` — annotator ở Bước 3 kiểm tra lại, không tin tưởng tuyệt đối.

### Bước 3 — Lọc & xác minh chéo

Người khác (không nhìn đáp án gốc) đọc cả document, trả lời toàn bộ câu hỏi:

- Khớp (exact match hoặc dung sai 5%; evidence trùng khớp với multi-hop) → `verified`.
- Không khớp → đối chiếu thủ công, sửa hoặc loại.
- Loại câu hỏi không trả lời được từ document (trừ `unanswerable` cố ý); hạ cấp về `single_chart` câu nào không qua được phép thử bỏ text.

### Bước 4 — Kiểm tra IAA trên mẫu

300-500 câu/đợt, tách riêng theo hop-type:

- Exact match nghiêm ngặt — mốc tham chiếu: ChartQA gốc 61.04%.
- Có dung sai lexical (vd `"6,2%"` vs `"6.2 phần trăm"`) — mốc: ChartQA gốc 78.55%.
- Multi-hop: đo thêm tỷ lệ evidence trùng khớp giữa 2 annotator (dự kiến thấp hơn single_chart, theo dõi xu hướng qua từng đợt).

Nếu đồng thuận thấp hơn đáng kể, dừng annotation hàng loạt, họp Pod B+C rà lại, cập nhật guideline.

## Cơ chế phân xử (adjudication)

1. Đưa case lên leader Pod C.
2. Quyết định theo thứ tự: (a) đối chiếu bảng dữ liệu gốc, (b) chart mơ hồ thật → loại câu hỏi, (c) lỗi diễn đạt → sửa câu hỏi, giữ đáp án.
3. Ghi log adjudication dùng chung để cập nhật guideline.

## Checklist nhanh trước khi nộp một batch

- [ ] Mỗi document đủ tỷ trọng taxonomy (cả 2 chiều, ≥1 câu multi-hop/document)
- [ ] Mọi câu `hop_type != single_chart` qua phép thử bỏ text và có `evidence` đầy đủ
- [ ] Mọi câu `answer_type: numeric` thuộc compositional/visual_compositional có `derivation`, khớp `data_table`
- [ ] Không có câu hỏi trùng lặp ý nghĩa trong cùng document
- [ ] Đáp án số giữ đúng định dạng/đơn vị trên chart
- [ ] Câu "không trả lời được" có đáp án `"unanswerable"`
- [ ] `data_table` đã nhập đầy đủ cho mọi chart trong batch

---

**Changelog guideline:** v1 — Tuần 1 (bản khởi tạo). v2 — cập nhật sau pilot.
