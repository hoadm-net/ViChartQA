# 04 — Chiến lược mô hình

## Nguyên tắc chính

Không huấn luyện mô hình từ đầu — fine-tune một backbone VLM có sẵn (LoRA/QLoRA), đầu tư thời gian vào chất lượng dữ liệu + đánh giá thay vì kiến trúc mới.

Input mô hình là title + body_text + 1-3 ảnh chart cùng lúc. Backbone phải hỗ trợ multi-image input — xác nhận sớm (Tuần 1-2, Pod D) khả năng multi-image của từng backbone, đặc biệt Vintern-3B (không giả định).

## Backbone đề xuất

| Backbone | Lý do chọn | Rủi ro |
|---|---|---|
| **Vintern-3B** (chính) | InternViT-300M + Qwen2, nền tảng tiếng Việt sẵn có, 3B tham số → LoRA rẻ | Cần kiểm tra dữ liệu chart hiện có (tránh trùng train/test); xác nhận riêng khả năng multi-image + văn bản dài |
| Qwen2.5-VL-7B-Instruct | Đa ngôn ngữ mạnh, cũng là baseline zero-shot, multi-image tốt | 7B nặng hơn, cần nhiều compute hơn |
| InternVL3-8B | SOTA mã nguồn mở, cùng họ vision-encoder với Vintern, multi-image tốt | Không có nền tảng tiếng Việt sẵn |

Chạy Vintern-3B làm chính (Tuần 5-7), Qwen2.5-VL-7B làm fine-tune phụ nếu compute cho phép.

## Baseline zero-shot cần đo

Tuần 3-4, song song annotation:

- GPT-4o
- Gemini 2.5 (Flash và Pro nếu ngân sách cho phép)
- Qwen2.5-VL (7B, 72B nếu đủ compute/API)
- InternVL3-8B
- Vintern-1B-v2 / Vintern-3B (chưa fine-tune — baseline quan trọng nhất)

## Fine-tuning

- LoRA/QLoRA trên train set — giữ nguyên vision encoder, fine-tune connector + LLM decoder (hoặc full LoRA tuỳ compute).
- Multi-task phụ trợ (tuỳ chọn): chart-to-table extraction như loss phụ, tận dụng `data_table` sẵn có.
- Ablation bắt buộc:
  - Có/không multi-task chart-to-table.
  - Theo domain thực tế đạt được.
  - Theo `question_type` (8 giá trị) — xác định nhóm khó nhất.
  - Theo `hop_type` — `single_chart` vs `text_to_chart`/`chart_to_chart`/`fact_check_dual`, bằng chứng số liệu cho claim "multi-hop khó hơn chart-only".
  - Theo độ phức tạp chart (`simple`/`complex`).

## Metric đánh giá

- Đáp án số: relaxed accuracy (5%).
- Đáp án không phải số: exact match sau chuẩn hoá.
- `unanswerable`: tính riêng, đo tỷ lệ mô hình nhận diện đúng.
- Trắc nghiệm: accuracy trên 4 lựa chọn.
- Bảng kết quả chính báo cáo tách theo hop-type: accuracy trên `single_chart` (so sánh trực tiếp ChartQA/ChartQAPro) và trên multi-hop gộp.
- Tuỳ chọn nếu còn thời gian: đánh giá `evidence` mô hình sinh ra theo kiểu supporting-fact F1 (HotpotQA/MultiHiertt).

## Hướng mở rộng nếu còn thời gian (Tuần 7 trở đi / sau dự án)

Gán chuỗi suy luận (rationale) cho tập con câu hỏi số học, thử SFT-then-RLVR/GRPO trên câu hỏi kiểm chứng được bằng heuristic — hướng Chart-R1/RVR/RL. Nếu không kịp, để lại future work.

## Compute cần chuẩn bị

- Fine-tune LoRA backbone 3B-8B: tối thiểu 1× GPU 80GB, liên tục ~3-4 tuần (Tuần 5-7).
- Baseline zero-shot qua API: ngân sách riêng, ước theo test set (không toàn bộ dataset).
- Baseline mã nguồn mở: chạy local nếu có GPU.

Checklist ngân sách ở [docs/05](05-timeline-and-roles.md).
