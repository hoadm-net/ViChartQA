# 05 — Lịch trình & phân công nhân sự

10 sinh viên, 5 pod, 7 tuần (14/07 – 31/08/2026). Nếu nhóm chỉ có 6 tuần, gộp Tuần 6 và 7 (fine-tune và viết bài chạy song song thay vì nối tiếp) — không cắt bớt Tuần 1 (pilot/guideline) hay Tuần 5 (data freeze), đây là hai tuần quyết định chất lượng cuối cùng.

## Phân công theo pod

| Pod | Số người | Vai trò chính |
|---|---|---|
| **A — Nguồn dữ liệu & pháp lý** | 2 | Thu thập **document nguyên bài** (title + content + 1–3 chart) từ nguồn đã duyệt, kiểm tra giấy phép cho **cả text lẫn ảnh**, chuẩn hoá metadata (nguồn, ngày, loại chart, miền), thực hiện mẫu kiểm tra nguồn cung theo domain (xem Tuần 1) |
| **B — Câu hỏi & annotation pipeline** | 3 | Đọc document, viết seed question theo cả 2 chiều taxonomy (loại suy luận + hop-type), vận hành pipeline VLM-assisted expansion, duy trì guideline |
| **C — Kiểm soát chất lượng & IAA** | 2 | Xác minh chéo câu trả lời, đo độ đồng thuận trên mẫu, phân xử bất đồng, dọn tập test cuối |
| **D — Modeling & đánh giá** | 2 | Xây eval harness từ Tuần 1–2, chạy baseline zero-shot, fine-tune backbone, ablation, error analysis |
| **E — Hạ tầng, viết bài & PM** | 1 | Công cụ annotation, theo dõi tiến độ liên pod, dataset card, chuẩn bị bản thảo & gói công bố |

Các pod có gối đầu để tránh nghẽn: thành viên Pod A/C có thể chuyển sang hỗ trợ Pod D ở Tuần 6 khi khối lượng annotation giảm dần. Pod E hoạt động xuyên suốt (điều phối) nhưng chỉ trở thành trọng tâm ở Tuần 7 (viết bài).

## Lịch trình theo tuần

### Tuần 1 (14–20/07) — Setup & pilot

- **Pod A:** chốt danh sách nguồn ưu tiên, bắt đầu gửi yêu cầu xin phép cho nguồn cần xác nhận (Tia Sáng, KH&PT, báo kinh tế tư nhân — xin phép cho **cả text lẫn ảnh**), crawl thử nguồn rủi ro thấp (GSO/consosukien.vn). **Lấy mẫu ~30–50 document ứng viên mỗi domain đang cân nhắc**, đếm tỷ lệ đạt tiêu chí document-grounded (xem [docs/02](02-dataset-design.md#miền-dữ-liệu)) — kết quả dùng để chốt tỷ trọng domain cuối Tuần 1, không ép cứng 50/50 như bản kế hoạch đầu.
- **Pod B:** hoàn thiện guideline v1 ([docs/03](03-annotation-guidelines.md)), viết seed cho pilot 50 document (cả 2 chiều taxonomy).
- **Pod C:** thiết lập quy trình xác minh chéo + form log adjudication, gồm cả kiểm tra `evidence` cho câu multi-hop.
- **Pod D:** dựng eval harness (script chạy inference + tính relaxed accuracy) cho các baseline VLM; xác nhận khả năng multi-image input của Vintern-3B (xem [docs/04](04-model-strategy.md#backbone-đề-xuất)).
- **Pod E:** chọn & dựng công cụ annotation (Label Studio hoặc nội bộ, cần hỗ trợ nhập nhiều ảnh + văn bản dài + trường evidence cho 1 mẫu), theo dõi tiến độ chung.
- **Cột mốc cuối tuần:** pilot 50 document / ~150–250 câu hỏi hoàn chỉnh cả 5 bước quy trình (số câu hỏi/document là ước tính ban đầu — Pod B/E cần tính lại tốc độ thực tế sau pilot vì annotation multi-hop tốn công hơn single-chart, có thể ảnh hưởng mục tiêu MVP ở Tuần 4).

### Tuần 2 (21–27/07) — Hiệu chỉnh & bắt đầu crawl diện rộng

- **Pod A:** crawl chính, đạt ~60–70% mục tiêu số lượng document nguồn.
- **Pod B:** rà lại pilot, chốt guideline v2 dựa trên các bất đồng thực tế, bắt đầu annotation hàng loạt.
- **Pod C:** đo IAA trên pilot, đối chiếu với mốc tham chiếu (61%/78.55% theo ChartQA gốc — xem [docs/03](03-annotation-guidelines.md#bước-4--kiểm-tra-iaa-trên-mẫu)).
- **Pod D:** chạy baseline zero-shot trên pilot set (kiểm tra harness hoạt động đúng trước khi scale).
- **Cột mốc cuối tuần:** guideline v2 chốt, annotation hàng loạt chính thức bắt đầu.

### Tuần 3 (28/07–03/08) — Annotation sprint đợt 1

- **Pod A:** hoàn tất crawl, hỗ trợ Pod C nếu cần đối chiếu nguồn.
- **Pod B:** annotation sprint chính, theo dõi tỷ trọng taxonomy so với mục tiêu.
- **Pod C:** QC vòng 1 trên batch đã annotate, log các loại lỗi lặp lại.
- **Pod D:** chạy baseline zero-shot đầy đủ (GPT-4o, Gemini, Qwen2.5-VL, InternVL3, Vintern chưa fine-tune) trên phần dữ liệu đã có, không chờ dataset freeze.
- **Cột mốc cuối tuần:** QC vòng 1 hoàn tất, ~50% mục tiêu MVP.

### Tuần 4 (04–10/08) — Annotation sprint đợt 2

- **Pod B:** tiếp tục sprint, ưu tiên lấp các nhóm taxonomy còn thiếu tỷ trọng.
- **Pod C:** QC vòng 2 + đối chiếu IAA subset thứ hai, hoàn thiện Data Statement/tài liệu giấy phép cho toàn bộ nguồn đã dùng.
- **Pod D:** tổng hợp kết quả baseline zero-shot, viết phân tích sơ bộ khoảng cách theo domain/loại câu hỏi.
- **Cột mốc cuối tuần:** đạt mục tiêu MVP (1.200 document / 6.000 câu hỏi, ≥50% multi-hop — xem [docs/02](02-dataset-design.md#quy-mô-mục-tiêu)); nếu tốc độ thực tế sau pilot thấp hơn ước tính, ưu tiên giữ ngưỡng multi-hop và chất lượng, hạ số document thay vì hạ chất lượng.

### Tuần 5 (11–17/08) — Data freeze

- **Pod A + C:** làm sạch thủ công tập test (không dùng heuristic tự động cho test set — xem [docs/02](02-dataset-design.md#chia-tập-trainvaltest)), chia train/val/test.
- **Pod B:** hoàn thiện dataset card nội bộ (thống kê taxonomy, domain, chart type thực tế đạt được).
- **Pod D:** bắt đầu fine-tune backbone chính (Vintern-3B) vòng 1.
- **Cột mốc cuối tuần:** **data freeze** — không sửa nhãn train/val sau mốc này trừ lỗi nghiêm trọng.

### Tuần 6 (18–24/08) — Fine-tune & ablation

- **Pod D (mở rộng, nhận thêm người từ Pod A/C):** fine-tune vòng 2, chạy ablation (multi-task chart-to-table, theo domain, theo loại câu hỏi, theo độ phức tạp chart — xem [docs/04](04-model-strategy.md#fine-tuning)).
- **Pod C:** chuyển sang hỗ trợ error analysis cùng Pod D.
- **Pod E:** bắt đầu khung bản thảo bài báo (Introduction, Related Work dựa trên [docs/01](01-related-work.md)).
- **Cột mốc cuối tuần:** **model v1** — có số liệu fine-tuned so với baseline zero-shot.

### Tuần 7 (25–31/08) — Viết bài & chuẩn bị công bố

- **Toàn nhóm:** error analysis chi tiết, thí nghiệm bổ sung nếu số liệu model v1 có điểm bất thường cần giải thích.
- **Pod E (chủ lực):** hoàn thiện bản thảo, chuẩn bị Ethics Statement/Data Statement, đóng gói dataset + model card cho release (Hugging Face, GitHub).
- **Cột mốc cuối tuần:** **draft bài** hoàn chỉnh, sẵn sàng cho giai đoạn polishing.

## Sau Tuần 7 — buffer đến hạn nộp

Thời điểm nộp thực tế phụ thuộc lựa chọn venue ở [docs/06](06-publication-strategy.md#thay-đổi-khuyến-nghị-so-với-bản-trước) (chờ ACL 2027 A* hay nộp NAACL qua chu kỳ 10/2026). Dù chọn phương án nào, sẽ còn ít nhất vài tuần đến vài tháng đệm sau Tuần 7 để:

- Bổ sung thí nghiệm reviewer nội bộ/cố vấn yêu cầu.
- Human evaluation bổ sung nếu cần củng cố baseline người (ChartQAPro báo cáo baseline người ~85%).
- Tinh chỉnh văn phong, rà soát lại toàn bộ số liệu trước khi nộp.

## Ngân sách & tài nguyên cần chuẩn bị trước Tuần 1

- GPU cho fine-tune (Tuần 5–7): tối thiểu 1× GPU 80GB hoặc tương đương.
- Ngân sách API GPT-4o/Gemini cho VLM-assisted annotation (Tuần 2–5) và baseline eval (Tuần 3–4).
- Công cụ annotation đã dựng xong trước ngày pilot (cuối Tuần 1).
- Trưởng nhóm cho từng pod, chỉ định trước buổi kickoff.

Chi tiết rủi ro nếu các mốc trên bị trễ, xem [docs/07-risks.md](07-risks.md).
