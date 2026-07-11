# 03 — Hướng dẫn gán nhãn

Tài liệu này dành cho annotator (chủ yếu Pod B, Pod C — xem [docs/05](05-timeline-and-roles.md)). Đọc kỹ trước buổi pilot Tuần 1; guideline sẽ được cập nhật thành v2 sau pilot dựa trên các trường hợp gây bất đồng thực tế.

## Nguyên tắc chung

1. **Câu hỏi phải trả lời được chỉ từ document (title + body_text + chart đi kèm)** — không cần kiến thức nền bên ngoài (trừ nhóm câu hỏi "giả định" được thiết kế có chủ đích, xem bên dưới). Khác bản đầu: giờ "được phép" cần đọc body_text, nhưng **không được phép** cần kiến thức ngoài document.
2. **Đáp án phải duy nhất và khách quan** — tránh câu hỏi có thể có nhiều cách hiểu dẫn đến nhiều đáp án đều "đúng".
3. **Ưu tiên câu hỏi tự nhiên** — hình dung một người thật đang đọc báo cáo này sẽ hỏi gì, không viết câu hỏi máy móc kiểu "giá trị tại điểm dữ liệu thứ 3 là bao nhiêu".
4. **Giữ nguyên thuật ngữ miền** — không đơn giản hoá thuật ngữ kinh tế/khoa học trong câu hỏi; đây là một phần độ khó có chủ đích của bộ dữ liệu.
5. **Không tự ý gắn nhãn multi-hop** — một câu hỏi chỉ được gán `hop_type != single_chart` nếu khớp đúng định nghĩa ở [Hop-type](#hop-type-phạm-vi-bằng-chứng-mới) bên dưới; nếu bỏ phần body_text đi mà câu hỏi vẫn trả lời được chỉ từ 1 chart, đó là `single_chart`, không phải multi-hop dù văn bản có "liên quan chủ đề".

## Định nghĩa từng loại câu hỏi

### 1. Truy vấn dữ liệu (data retrieval)

Đọc trực tiếp một giá trị hoặc nhãn, không cần suy luận thêm.

- ✅ "Tỷ lệ thất nghiệp thanh niên năm 2023 là bao nhiêu?"
- ❌ "Số liệu năm 2023 là gì?" — mơ hồ, không rõ chuỗi/đại lượng nào nếu chart có nhiều chuỗi.

### 2. Thị giác (visual)

Câu hỏi bắt buộc phải tham chiếu một thuộc tính thị giác (màu sắc, vị trí, kích thước, độ cao) để xác định đối tượng cần đọc — nếu bỏ tham chiếu thị giác đi mà câu hỏi vẫn trả lời được, đây không phải câu hỏi thị giác.

- ✅ "Cột màu cam cao nhất nằm ở năm nào?"
- ✅ "Đường màu xanh lá nằm phía trên hay dưới đường màu xám vào năm 2022?"
- ❌ "Giá trị cao nhất là bao nhiêu?" — không cần tham chiếu thị giác, đây là truy vấn dữ liệu (loại 1) hoặc suy luận kết hợp (loại 3, nếu cần so sánh nhiều giá trị).

### 3. Suy luận kết hợp (compositional)

Yêu cầu ít nhất **hai** phép toán số học/logic: cộng, trừ, nhân, chia, phần trăm, trung bình, so sánh, đếm điều kiện.

- ✅ "Tổng kim ngạch xuất khẩu của ba năm gần nhất là bao nhiêu?" (cộng 3 giá trị)
- ✅ "Lạm phát năm nào cao hơn mức trung bình giai đoạn 2019–2023?" (tính trung bình rồi so sánh)
- ❌ "Lạm phát năm 2023 cao hơn năm 2022 bao nhiêu?" — chỉ một phép trừ, **vẫn tính là compositional** vì ChartQA gốc coi hiệu số là phép toán hợp lệ tối thiểu cho loại này; nhưng ưu tiên viết thêm biến thể có ≥2 bước tính khi có thể để tăng độ khó trung bình của tập.

### 4. Thị giác + suy luận

Kết hợp cả hai: trước tiên phải xác định đối tượng bằng đặc điểm thị giác, sau đó thực hiện phép toán.

- ✅ "Trong các năm có cột màu xanh lá, năm nào có chênh lệch lớn nhất so với năm liền trước?"
- ✅ "Đường nào (theo màu) có độ dốc tăng mạnh nhất giữa hai mốc đầu và cuối?"

### 5. Mở rộng (kiểu ChartQAPro)

| Loại | Định nghĩa | Ví dụ |
|---|---|---|
| Trắc nghiệm | Câu hỏi kèm 4 lựa chọn, chỉ 1 đúng; các lựa chọn sai phải "gần đúng" (số liệu lân cận, dễ nhầm) để có ý nghĩa kiểm tra | "Năm nào có tăng trưởng GDP cao nhất? A. 2021 B. 2022 C. 2023 D. 2024" |
| Giả định | Đặt một điều kiện/xu hướng ngoài dữ liệu quan sát được, yêu cầu ước lượng có căn cứ | "Nếu xu hướng 2020–2024 tiếp diễn, giá trị năm 2027 gần nhất là bao nhiêu?" |
| Fact-checking | Đưa ra một phát biểu, yêu cầu xác nhận đúng/sai dựa trên chart | "Đúng hay sai: chi tiêu R&D luôn tăng liên tục trong giai đoạn quan sát?" |
| Hội thoại nhiều lượt | 2–3 câu hỏi nối tiếp, câu sau phụ thuộc ngữ cảnh câu trước | Lượt 1: "Năm nào GDP tăng cao nhất?" → Lượt 2: "Vậy năm đó cao hơn năm liền trước bao nhiêu?" |
| Không trả lời được | Câu hỏi liên quan chủ đề chart nhưng **không thể** trả lời chỉ từ ảnh — dùng để kiểm tra mô hình có "bịa" đáp án hay không | "Nguyên nhân khiến lạm phát tăng đột biến năm 2023 là gì?" (chart không có thông tin nguyên nhân) |

**Lưu ý riêng cho loại "không trả lời được":** đáp án chuẩn ghi là `"unanswerable"`, không được để trống. Không lạm dụng loại này quá 5–7% tổng số câu hỏi — mục đích là kiểm tra, không phải làm khó annotator vòng xác minh.

## Hop-type (phạm vi bằng chứng, mới)

Đây là **chiều nhãn thứ hai**, độc lập với 5 loại suy luận ở trên — mọi câu hỏi phải có cả `question_type` (1 trong 5 loại trên) lẫn `hop_type` (1 trong 4 loại dưới đây). Đây là phần quan trọng nhất để claim "multi-hop" của dự án đứng vững trước reviewer, nên annotator cần đọc kỹ và tự kiểm tra bằng **phép thử bỏ text**: xoá body_text đi, nếu câu hỏi vẫn trả lời được đầy đủ từ (các) chart, đó là `single_chart`, dù nội dung có "liên quan" tới văn bản.

### 1. `single_chart`

Trả lời được chỉ từ 1 chart, không cần đọc body_text.

- ✅ "Vốn FDI năm 2020 là bao nhiêu?" (đọc thẳng 1 chart)
- ❌ Gắn nhãn `text_to_chart` cho câu này chỉ vì body_text "cũng có nhắc năm 2020" — nếu số liệu đã có sẵn trên chart, không tính là hop qua text.

### 2. `text_to_chart`

Hop 1 lấy một claim/số liệu **chỉ tồn tại trong body_text**, không xuất hiện trên bất kỳ chart nào; hop 2 đối chiếu hoặc tính toán với chart.

- ✅ "Bài viết nêu dự báo tăng trưởng theo ADB cho năm 2022 — so với giá trị GDP năm 2021 trên Hình 1, mức tăng tuyệt đối dự kiến là bao nhiêu?" (dự báo ADB chỉ có trong text)
- ❌ "GDP năm 2021 là bao nhiêu, theo đoạn văn mở đầu?" — nếu số liệu này cũng vẽ sẵn trên chart, đây thực chất là `single_chart` được diễn đạt lại qua text, không phải hop thật.

### 3. `chart_to_chart`

Cần ≥2 chart trong cùng document; body_text đóng vai trò cầu nối cho biết chart nào liên quan đến chart nào (ví dụ nêu rõ hai chỉ tiêu cùng so sánh, hoặc cùng giai đoạn thời gian).

- ✅ "Trong giai đoạn 2011–2021, chỉ tiêu nào tăng nhanh hơn: GDP (Hình 1) hay kim ngạch xuất nhập khẩu (Hình 3)?"
- ❌ Hai chart hoàn toàn không liên quan chủ đề, ghép câu hỏi gượng ép chỉ để đạt tỷ trọng multi-hop — loại bỏ ở bước xác minh chéo nếu annotator viết seed cố tình làm vậy.

### 4. `fact_check_dual`

Một phát biểu trong document, cần đọc **cả text lẫn chart** để xác minh đúng/sai — nếu chỉ cần chart (hoặc chỉ cần text) là đủ xác minh, không tính loại này.

- ✅ "Đúng hay sai: vốn FDI tăng liên tục suốt 2011–2021?" — text mở đầu chỉ nói chung chung "biến động", phải nhìn chart mới thấy có giảm ở 2012 và 2020.
- ❌ "Đúng hay sai: bài viết nói GDP tăng gấp 3 lần?" — nếu chỉ cần đọc câu trong text, không cần nhìn chart để xác minh, đây là câu hỏi đọc hiểu văn bản thuần, không thuộc phạm vi dataset này.

**Trường `evidence` bắt buộc với mọi câu `hop_type != single_chart`** (xem schema ở [docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất)) — annotator ghi rõ từng hop lấy từ đâu (câu nào trong text, chart nào, điểm dữ liệu nào). Thiếu evidence = câu hỏi bị trả về sửa ở bước xác minh chéo, không được tính hoàn thành.

## Quy tắc viết đáp án

- **Đáp án số:** giữ nguyên đơn vị và định dạng xuất hiện trên chart (ví dụ `6.2%` chứ không viết lại thành `0.062`), trừ khi câu hỏi yêu cầu đơn vị khác một cách tường minh.
- **Dung sai khi đánh giá tự động:** áp dụng "relaxed accuracy" như ChartQA gốc — đáp án số được coi là đúng nếu nằm trong 5% giá trị đúng, để chấp nhận sai số nhỏ trong OCR/trích xuất. Annotator vẫn phải ghi đáp án chính xác tuyệt đối, dung sai chỉ áp dụng ở bước đánh giá mô hình (xem [docs/04](04-model-strategy.md)).
- **Đáp án không phải số:** cần khớp chính xác (exact match) sau khi chuẩn hoá chính tả/khoảng trắng.

## Quy trình 5 bước (chi tiết)

### Bước 0 — Đọc document

Mỗi annotator nhận một batch document (title + body_text + 1–3 chart). Với mỗi document:

1. Đọc title + body_text trước khi nhìn kỹ chart — gạch chân/ghi chú những số liệu hoặc claim **chỉ xuất hiện trong text**, không vẽ trên chart nào. Đây là nguyên liệu bắt buộc cho câu hỏi `text_to_chart`/`fact_check_dual` ở bước sau.
2. Với từng chart: xác định loại (bar/line/pie), độ phức tạp (simple/complex), nhập bảng dữ liệu gốc vào công cụ annotation (xem schema ở [docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất)).

### Bước 1 — Seed thủ công

Viết 2–3 câu hỏi seed theo cả 2 chiều taxonomy, đảm bảo tối thiểu:

- 1 câu `single_chart` (compositional hoặc thị giác+suy luận — phần khó của chiều 1).
- 1 câu multi-hop (`text_to_chart`, `chart_to_chart`, hoặc `fact_check_dual`) dùng đúng nguyên liệu đã ghi chú ở Bước 0, kèm `evidence` đầy đủ.

VLM ở bước 2 sẽ mở rộng thêm các tổ hợp taxonomy còn thiếu.

### Bước 2 — Mở rộng bằng VLM

Vận hành bởi Pod B: đưa seed question + title + body_text + bảng dữ liệu của từng chart vào prompt cho GPT-4o/Gemini/Qwen2.5-VL, yêu cầu sinh 4–6 câu hỏi ứng viên **rải đều theo cả 2 chiều taxonomy còn thiếu** cho document đó (đặc biệt các hop-type multi-hop và nhóm mở rộng — trắc nghiệm, giả định, fact-check). Yêu cầu mô hình tự đề xuất `evidence` cho câu multi-hop — annotator ở bước 3 sẽ kiểm tra lại, không tin tưởng tuyệt đối.

### Bước 3 — Lọc & xác minh chéo

Một annotator **khác** người viết seed (không nhìn đáp án gốc) đọc lại toàn bộ document rồi trả lời toàn bộ câu hỏi ứng viên từ bước 2 cộng seed từ bước 1:

- Nếu đáp án khớp (exact match hoặc trong dung sai 5% với số) **và** evidence tự viết trùng khớp với evidence gốc (với câu multi-hop) → giữ, đánh dấu `verified`.
- Nếu không khớp → đối chiếu thủ công: lỗi ở người viết seed, lỗi ở người xác minh, hay câu hỏi bản chất mơ hồ? Sửa hoặc loại theo kết quả đối chiếu.
- Loại bỏ câu hỏi không thể trả lời từ document (trừ nhóm "không trả lời được" cố ý), và loại/hạ cấp về `single_chart` bất kỳ câu nào gắn nhãn multi-hop nhưng qua được phép thử bỏ text ở [Hop-type](#hop-type-phạm-vi-bằng-chứng-mới).

### Bước 4 — Kiểm tra IAA trên mẫu

Pod C rút mẫu ngẫu nhiên 300–500 câu mỗi đợt (khoảng 1 tuần annotation), tính tỷ lệ đồng thuận theo 2 cách, **tách riêng theo hop-type**:

- **Exact match nghiêm ngặt** — mốc tham chiếu: ChartQA gốc đạt 61.04% (đo trên câu single-chart, chỉ dùng làm tham chiếu gần đúng cho slice `single_chart`).
- **Có tính đến biến thể chính tả/lexical** (vd `"6,2%"` vs `"6.2 phần trăm"`) — mốc tham chiếu: ChartQA gốc đạt 78.55% khi tính theo cách này.
- **Với multi-hop:** ngoài đáp án, đo thêm tỷ lệ evidence trùng khớp giữa 2 annotator — dự kiến thấp hơn slice `single_chart`, đây là hiện tượng bình thường (đúng như MultiHiertt/HotpotQA cũng gặp), không phải dấu hiệu guideline sai, nhưng cần Pod C theo dõi xu hướng qua từng đợt để phát hiện sớm nếu tụt dốc bất thường.

Nếu tỷ lệ đồng thuận thấp hơn đáng kể so với các mốc trên, dừng annotation hàng loạt, họp Pod B+C rà lại các trường hợp bất đồng, cập nhật guideline (ghi rõ thay đổi trong changelog cuối file này) trước khi tiếp tục.

## Cơ chế phân xử (adjudication)

Khi Bước 3 phát hiện bất đồng không tự giải quyết được bằng đối chiếu 2 người:

1. Đưa case lên leader Pod C.
2. Leader quyết định theo thứ tự ưu tiên: (a) đối chiếu lại với bảng dữ liệu gốc, (b) nếu chart mơ hồ thật sự → loại câu hỏi, (c) nếu do lỗi diễn đạt câu hỏi → sửa câu hỏi, giữ đáp án.
3. Ghi lại case + quyết định vào log adjudication dùng chung — dùng để cập nhật guideline định kỳ, tránh lặp lại cùng một loại lỗi.

## Checklist nhanh trước khi nộp một batch

- [ ] Mỗi document có đủ tỷ trọng taxonomy theo mục tiêu ở [docs/02](02-dataset-design.md#taxonomy-câu-hỏi) — cả chiều loại suy luận lẫn chiều hop-type (≥1 câu multi-hop/document)
- [ ] Mọi câu `hop_type != single_chart` đã qua phép thử bỏ text và có `evidence` đầy đủ
- [ ] Không có câu hỏi trùng lặp ý nghĩa trong cùng một document
- [ ] Đáp án số giữ đúng định dạng/đơn vị xuất hiện trên chart
- [ ] Câu hỏi "không trả lời được" có đáp án `"unanswerable"`, không để trống
- [ ] Bảng dữ liệu gốc đã nhập đầy đủ cho mọi chart trong batch

---

**Changelog guideline**

- v1 — Tuần 1 (bản khởi tạo, dùng cho pilot 50 chart)
- v2 — *(cập nhật sau pilot, điền khi có)*
