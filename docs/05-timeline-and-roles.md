# 05 — Lịch trình & phân công nhân sự

10 sinh viên, 5 pod, 7 tuần (14/07–31/08/2026). Nếu chỉ có 6 tuần, gộp Tuần 6 và 7 — không cắt Tuần 1 hay Tuần 5.

## Phân công theo pod

| Pod | Số người | Vai trò chính |
|---|---|---|
| **A — Nguồn dữ liệu & pháp lý** | 2 | Thu thập document (title + content + 1–3 chart), kiểm tra giấy phép text+ảnh, chuẩn hoá metadata, mẫu kiểm tra nguồn cung theo domain |
| **B — Câu hỏi & annotation pipeline** | 3 | Đọc document, viết seed (2 chiều taxonomy), vận hành VLM-assisted expansion, duy trì guideline |
| **C — Kiểm soát chất lượng** | 2 | Rà soát/sửa câu hỏi đã soạn (không phải bước xác minh chéo riêng — dùng chung trang Soạn câu hỏi), dọn test set, Data Statement |
| **D — Modeling & đánh giá** | 2 | Eval harness, baseline zero-shot, fine-tune backbone, ablation, error analysis |
| **E — Hạ tầng, viết bài & PM** | 1 | Công cụ annotation, theo dõi tiến độ, dataset card, bản thảo & gói công bố |

Pod A/C có thể chuyển hỗ trợ Pod D ở Tuần 6. Pod E trọng tâm ở Tuần 7 (viết bài).

## Lịch trình theo tuần

### Tuần 1 (14–20/07) — Setup & pilot

- **Pod A:** chốt nguồn ưu tiên, gửi xin phép nguồn cần xác nhận (Tia Sáng, KH&PT, báo kinh tế tư nhân — cả text lẫn ảnh), crawl thử nguồn rủi ro thấp (GSO/consosukien.vn). Lấy mẫu ~30–50 document/domain, đếm tỷ lệ đạt tiêu chí document-grounded ([docs/02](02-dataset-design.md#miền-dữ-liệu)) để chốt tỷ trọng domain cuối tuần.
- **Pod B:** hoàn thiện guideline v1 ([docs/03](03-annotation-guidelines.md)), viết seed cho pilot 50 document.
- **Pod C:** làm quen công cụ, thử rà/sửa câu hỏi qua trang Soạn câu hỏi ([docs/08](08-annotation-tool-design.md#42-soạn-câu-hỏi-pod-b--trang-duy-nhất-sau-intake)), kiểm tra `evidence` cho câu multi-hop.
- **Pod D:** dựng eval harness cho baseline VLM; xác nhận khả năng multi-image của Vintern-3B ([docs/04](04-model-strategy.md#backbone-đề-xuất)).
- **Pod E:** chọn & dựng công cụ annotation (hỗ trợ nhiều ảnh + văn bản dài + evidence), theo dõi tiến độ chung.
- **Cột mốc:** pilot 50 document / ~150–250 câu hỏi qua đủ quy trình soạn câu hỏi ([docs/03](03-annotation-guidelines.md#quy-trình)). Tính lại tốc độ annotation thực tế sau pilot (multi-hop tốn công hơn single-chart) — có thể ảnh hưởng mục tiêu MVP Tuần 4.

### Tuần 2 (21–27/07) — Hiệu chỉnh & crawl diện rộng

- **Pod A:** crawl chính, đạt ~60–70% mục tiêu document.
- **Pod B:** rà pilot, chốt guideline v2, bắt đầu annotation hàng loạt.
- **Pod C:** rà pilot cùng Pod B, tổng hợp lỗi phổ biến góp ý guideline v2.
- **Pod D:** chạy baseline zero-shot trên pilot set.
- **Cột mốc:** guideline v2 chốt, annotation hàng loạt bắt đầu.

### Tuần 3 (28/07–03/08) — Annotation sprint đợt 1

- **Pod A:** hoàn tất crawl, hỗ trợ Pod C đối chiếu nguồn.
- **Pod B:** annotation sprint chính, theo dõi tỷ trọng taxonomy.
- **Pod C:** QC vòng 1, log lỗi lặp lại.
- **Pod D:** baseline zero-shot đầy đủ (GPT-4o, Gemini, Qwen2.5-VL, InternVL3, Vintern chưa fine-tune) trên dữ liệu đã có.
- **Cột mốc:** QC vòng 1 hoàn tất, ~50% mục tiêu MVP.

### Tuần 4 (04–10/08) — Annotation sprint đợt 2

- **Pod B:** tiếp tục sprint, ưu tiên nhóm taxonomy còn thiếu.
- **Pod C:** QC vòng 2, hoàn thiện Data Statement.
- **Pod D:** tổng hợp baseline zero-shot, phân tích khoảng cách theo domain/loại câu hỏi.
- **Cột mốc:** MVP (1.200 document / 6.000 câu hỏi, ≥50% multi-hop — [docs/02](02-dataset-design.md#quy-mô-mục-tiêu)); nếu tốc độ thấp hơn ước tính, giữ ngưỡng multi-hop và chất lượng, hạ số document.

### Tuần 5 (11–17/08) — Data freeze

- **Pod A + C:** làm sạch thủ công test set, chia train/val/test ([docs/02](02-dataset-design.md#chia-tập-trainvaltest)).
- **Pod B:** hoàn thiện dataset card nội bộ.
- **Pod D:** bắt đầu fine-tune Vintern-3B vòng 1.
- **Cột mốc:** data freeze — không sửa nhãn train/val trừ lỗi nghiêm trọng.

### Tuần 6 (18–24/08) — Fine-tune & ablation

- **Pod D (+ người từ A/C):** fine-tune vòng 2, ablation ([docs/04](04-model-strategy.md#fine-tuning)).
- **Pod C:** hỗ trợ error analysis cùng Pod D.
- **Pod E:** khung bản thảo (Introduction, Related Work — [docs/01](01-related-work.md)).
- **Cột mốc:** model v1 — số liệu fine-tuned so với baseline.

### Tuần 7 (25–31/08) — Viết bài & chuẩn bị công bố

- **Toàn nhóm:** error analysis chi tiết, thí nghiệm bổ sung nếu cần.
- **Pod E (chính):** hoàn thiện bản thảo, Ethics/Data Statement, đóng gói dataset + model card (Hugging Face, GitHub).
- **Cột mốc:** draft bài hoàn chỉnh.

## Sau Tuần 7 — buffer đến hạn nộp

Thời điểm nộp phụ thuộc lựa chọn venue ([docs/06](06-publication-strategy.md#ba-phương-án)). Buffer sau Tuần 7 dùng để: bổ sung thí nghiệm, human evaluation (ChartQAPro baseline người ~85%), tinh chỉnh văn phong và rà soát số liệu.

## Ngân sách & tài nguyên cần chuẩn bị trước Tuần 1

- GPU fine-tune (Tuần 5–7): tối thiểu 1× GPU 80GB.
- Ngân sách API GPT-4o/Gemini cho annotation (Tuần 2–5) và baseline eval (Tuần 3–4).
- Công cụ annotation dựng xong trước ngày pilot.
- Trưởng nhóm cho từng pod.

Rủi ro chi tiết ở [docs/07-risks.md](07-risks.md).
