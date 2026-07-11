# 04 — Chiến lược mô hình

## Nguyên tắc chính

**Không huấn luyện mô hình từ đầu.** Mọi mô hình chart-VLM gần đây (ChartLlama, ChartGemma, TinyChart, ChartMoE) đều fine-tune trên một backbone VLM có sẵn — quyết định đúng đắn duy nhất trong timeline 6–7 tuần là làm giống vậy: chọn backbone tốt, fine-tune hiệu quả (LoRA/QLoRA), và đầu tư thời gian vào chất lượng dữ liệu + đánh giá thay vì kiến trúc mới.

**Ràng buộc mới sau pivot (xem [docs/02](02-dataset-design.md)):** input mô hình giờ là title + body_text + **1–3 ảnh chart cùng lúc**, không phải 1 ảnh đơn như bản đầu. Backbone phải hỗ trợ multi-image input trong cùng một context — cần xác nhận sớm (Tuần 1–2, Pod D) khả năng multi-image của từng backbone dưới đây trước khi cam kết, đặc biệt Vintern-3B (họ InternVL nhìn chung hỗ trợ multi-image, nhưng bản 3B/tiếng Việt cần tự kiểm tra, không giả định).

## Backbone đề xuất

| Backbone | Lý do chọn | Rủi ro |
|---|---|---|
| **Vintern-3B** (khuyến nghị chính) | InternViT-300M + Qwen2, đã có nền tảng tiếng Việt + Chart-VQA sơ khởi trong tập huấn luyện (3M+ cặp ảnh-hỏi-đáp), cộng đồng 5CD-AI hỗ trợ, chi phí fine-tune LoRA thấp (3B tham số) | Cần kiểm tra dữ liệu chart hiện có của Vintern để tránh trùng lặp train/test; có thể đã "quen" một số dạng chart nhất định khiến baseline zero-shot bị đánh giá cao ảo; **cần xác nhận riêng khả năng multi-image + văn bản dài trong 1 context** (chưa verify, xem ràng buộc mới ở trên) |
| Qwen2.5-VL-7B-Instruct | Đa ngôn ngữ mạnh, hệ sinh thái lớn, dễ so sánh baseline zero-shot cùng họ (Qwen2.5-VL cũng nằm trong nhóm baseline cần đo), hỗ trợ multi-image tốt | 7B nặng hơn Vintern-3B, cần nhiều compute hơn cho fine-tune |
| InternVL3-8B | SOTA mã nguồn mở, cùng họ vision-encoder với Vintern (InternViT) — dễ kế thừa kỹ thuật giữa hai backbone, hỗ trợ multi-image tốt | Không có nền tảng tiếng Việt sẵn, có thể cần nhiều epoch fine-tune hơn để thích nghi ngôn ngữ |

**Khuyến nghị:** bắt đầu với Vintern-3B làm mô hình chính (Tuần 5–7), chạy Qwen2.5-VL-7B như một fine-tune phụ nếu compute cho phép — hai kết quả fine-tune giúp bài báo có luận điểm mạnh hơn ("cải thiện nhất quán trên nhiều backbone" thay vì chỉ một điểm dữ liệu).

## Baseline zero-shot cần đo

Đo trước khi fine-tune (Tuần 3–4, chạy song song với annotation, không chờ dataset freeze):

- GPT-4o
- Gemini 2.5 (Flash và Pro nếu ngân sách cho phép)
- Qwen2.5-VL (7B, và 72B nếu đủ compute/API)
- InternVL3-8B
- Vintern-1B-v2 / Vintern-3B (**chưa fine-tune** — đây là con số baseline quan trọng nhất vì cùng backbone với mô hình đề xuất)

Đây chính là bằng chứng cho luận điểm "mô hình tổng quát mạnh nhưng vẫn có khoảng trống ở miền hẹp tiếng Việt", theo đúng cách VMMU và ChartQAPro trình bày kết quả (xem [docs/01](01-related-work.md)).

## Fine-tuning

- **Phương pháp:** LoRA hoặc QLoRA trên train set ViChartQA — giữ nguyên vision encoder, fine-tune phần connector + một phần LLM decoder (hoặc full LoRA tuỳ ngân sách compute).
- **Multi-task phụ trợ (tuỳ chọn):** nếu có ngân sách, thêm tác vụ chart-to-table extraction (dự đoán lại bảng dữ liệu gốc từ ảnh) như một loss phụ — giúp mô hình học biểu diễn cấu trúc chart tốt hơn, đồng thời tận dụng trường `data_table` đã có sẵn trong schema (xem [docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất)).
- **Ablation tối thiểu cần chạy:**
  - Có/không multi-task chart-to-table.
  - Theo domain thực tế đạt được (không còn giả định 50/50 — xem [docs/02](02-dataset-design.md#miền-dữ-liệu)) — kiểm tra mô hình có lệch về một miền không.
  - Theo loại câu hỏi (5 nhóm taxonomy chiều 1) — xác định nhóm nào khó nhất, dùng cho phần phân tích lỗi của bài báo.
  - **Theo hop-type (chiều 2, mới — quan trọng nhất cho luận điểm chính của bài):** `single_chart` vs `text_to_chart` vs `chart_to_chart` vs `fact_check_dual`. Kỳ vọng khoảng cách rõ giữa `single_chart` và các loại multi-hop — đây chính là bằng chứng số liệu cho claim "multi-hop khó hơn chart-only", nên bắt buộc phải có, không phải ablation tuỳ chọn.
  - Theo độ phức tạp chart (`simple` vs `complex`, xem schema) — theo đúng cách ChartQA gốc phân tích.

## Metric đánh giá

- **Đáp án số:** relaxed accuracy — đúng nếu nằm trong 5% giá trị đúng (theo đúng ChartQA gốc, chấp nhận sai số nhỏ từ OCR/trích xuất).
- **Đáp án không phải số:** exact match sau chuẩn hoá.
- **Câu hỏi "không trả lời được":** tính riêng như một hạng mục — đo tỷ lệ mô hình nhận diện đúng là không trả lời được (tránh mô hình "bịa" đáp án), tương tự cách ChartQAPro báo cáo.
- **Trắc nghiệm:** accuracy thông thường trên 4 lựa chọn.
- **Bắt buộc báo cáo tách theo hop-type** — bảng kết quả chính của bài nên có ít nhất 2 cột: accuracy trên slice `single_chart` (so sánh trực tiếp được với ChartQA/ChartQAPro) và accuracy trên slice multi-hop gộp (`text_to_chart`+`chart_to_chart`+`fact_check_dual`). Đây là cách trình bày luận điểm mới của dự án, không phải chi tiết phụ.
- **Tuỳ chọn nếu còn thời gian:** đánh giá chất lượng `evidence` do mô hình sinh ra (nếu prompt yêu cầu model giải thích hop) theo kiểu supporting-fact F1 của HotpotQA/MultiHiertt — để lại như hướng mở rộng nếu Tuần 6–7 còn dư thời gian, không phải yêu cầu bắt buộc cho MVP.

## Hướng mở rộng nếu còn thời gian (Tuần 7 trở đi / sau dự án)

Gán nhãn chuỗi suy luận (rationale) cho một tập con câu hỏi số học, thử nghiệm SFT-then-RLVR/GRPO trên câu hỏi có đáp án kiểm chứng được bằng heuristic — bám xu hướng Chart-R1/Chart-RVR/Chart-RL 2025–2026 (xem [docs/01](01-related-work.md#2-dòng-chart-vlm-chuyên-biệt-mô-hình)). Nếu không kịp trong 7 tuần, để lại như hướng *future work* trong bài — vẫn có giá trị vì `data_table` đã hỗ trợ sẵn việc verify đáp án tự động.

## Compute cần chuẩn bị

- Fine-tune LoRA một backbone 3B–8B tham số: tối thiểu 1× GPU 80GB (hoặc tương đương nhiều GPU nhỏ hơn), khả dụng liên tục khoảng 3–4 tuần ở giai đoạn Tuần 5–7.
- Baseline zero-shot qua API (GPT-4o, Gemini) cần ngân sách riêng — ước lượng theo số câu hỏi trong test set (không phải toàn bộ dataset, chỉ chạy trên test set để so sánh công bằng).
- Baseline mã nguồn mở (Qwen2.5-VL, InternVL3) có thể chạy local nếu có GPU, giảm phụ thuộc ngân sách API.

Xem checklist ngân sách cụ thể ở [docs/05](05-timeline-and-roles.md) và README gốc.
