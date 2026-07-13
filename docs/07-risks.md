# 07 — Rủi ro & giảm thiểu

| Rủi ro | Ảnh hưởng | Giảm thiểu | Chủ trì |
|---|---|---|---|
| Annotation multi-hop (đọc text + đối chiếu chart + điền evidence) tốn công hơn single-chart, 6-7 tuần có thể không đủ | Không đạt quy mô kỳ vọng, hoặc phải hạ ngưỡng ≥50% multi-hop | Ưu tiên chất lượng/độ khó hơn số lượng (ChartQAPro: 1.341 chart vẫn đủ mạnh); tính lại tốc độ thực tế sau pilot Tuần 1, giảm số document trước khi giảm ngưỡng multi-hop | Pod B, Pod E |
| Bản quyền cả text lẫn hình ảnh cùng một bài từ báo chí/kinh tế tư nhân | Rủi ro pháp lý khi công bố dataset | Ưu tiên nguồn chính phủ/mở (GSO, consosukien.vn); với báo chí, xin phép rõ cho cả bài hoặc chỉ giữ đoạn văn liên quan trực tiếp đến chart; Data Statement đầy đủ | Pod A |
| Miền khoa học (và ngoài kinh tế) có thể không đủ nguồn document-grounded cùng dạng "title+content+1-3 chart" | Không đạt tỷ trọng domain kỳ vọng, dataset lệch về kinh tế | Thử báo cáo thường niên chính phủ thay vì báo phổ biến khoa học; mẫu kiểm tra 30-50 document/domain ở Tuần 1; chấp nhận domain split lệch nếu nguồn cung không cho phép cân bằng | Pod A |
| IAA cho câu hỏi multi-hop thấp hơn `single_chart`, đặc biệt trường `evidence` | Chất lượng nhãn multi-hop bị nghi ngờ khi review | Định nghĩa hop-type chặt + phép thử bỏ text ([docs/03](03-annotation-guidelines.md#hop-type-phạm-vi-bằng-chứng-mới)); đo IAA tách theo hop-type; dừng sprint để rà guideline nếu tụt quá xa | Pod C |
| Bị coi là "chart hoá lại HybridQA/TAT-QA/MultiHiertt" hoặc trùng DCQA/DocHop-QA | Reviewer A* bác vì thiếu tính mới | Bảng so sánh + khoảng trống cụ thể ở [docs/01 mục 4b](01-related-work.md#4b-dòng-multi-hop-qa-trên-dữ-liệu-có-cấu-trúc-text--tablechart) — verify lại số liệu bảng này qua PDF gốc trước bản thảo cuối | Pod E |
| Mô hình fine-tune không đủ mạnh để thắng VLM hiện đại toàn diện | Yếu luận điểm đóng góp mô hình | Định vị cạnh tranh trong miền hẹp (tiếng Việt + khoa học/kinh tế), chi phí thấp hơn — mô-típ ChartGemma/TinyChart ([docs/04](04-model-strategy.md)) | Pod D |
| Ngân sách API (GPT-4o/Gemini) cho annotation & baseline eval vượt dự kiến | Thiếu ngân sách giữa chừng | Ưu tiên mô hình mã nguồn mở (Qwen2.5-VL) cho sinh câu hỏi hàng loạt; API trả phí chỉ cho baseline eval cuối (test set cố định) | Pod E |
| Nhắm nhầm chu kỳ ARR tháng 8 hoặc 10/2026 tưởng A* nhưng thực ra EACL/NAACL (hạng A) | Đạt venue không đúng mục tiêu ban đầu | Chu kỳ 8/2026 → EACL, chu kỳ 10/2026 nhiều khả năng → NAACL, cả hai hạng A. Quyết định sớm giữa 3 phương án ở [docs/06](06-publication-strategy.md#ba-phương-án) | Pod E |
| Trùng lặp dữ liệu/miền với ViInfographicVQA hoặc chart-VQA sẵn có trong tập huấn luyện Vintern | Reviewer nghi ngờ tính mới, hoặc leakage khiến baseline Vintern bị đánh giá cao ảo | Chọn nguồn ảnh khác infographics.vn ([docs/01](01-related-work.md#so-sánh-trực-tiếp-với-viinfographicvqa)); kiểm tra tập chart hiện có của Vintern trước khi dùng làm backbone ([docs/04](04-model-strategy.md#backbone-đề-xuất)) | Pod A, Pod D |
| Taxonomy câu hỏi bị "dễ" hoá dần trong sprint để chạy kịp tiến độ | Benchmark bị đánh giá là lặp lại ChartQA gốc đã bão hoà | Pod C kiểm tra tỷ trọng taxonomy mỗi đợt QC ([docs/03](03-annotation-guidelines.md#checklist-nhanh-trước-khi-nộp-một-batch)), không chỉ đúng/sai đáp án | Pod C |

## Cơ chế escalation

Rủi ro xảy ra thực tế → báo ngay Pod E trong buổi sync gần nhất, không chờ cột mốc cuối tuần.

## Rà soát định kỳ

Cập nhật bảng cuối mỗi tuần, đối chiếu cột mốc ở [docs/05](05-timeline-and-roles.md) — thêm rủi ro mới, đóng rủi ro đã qua giai đoạn liên quan.
