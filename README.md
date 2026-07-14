# ViChartQA

Bộ dữ liệu và mô hình Hỏi–Đáp biểu đồ (Chart Question Answering) tiếng Việt, cốt lõi là **multi-hop reasoning trên text + chart** trong các bài viết thật (không phải chart rời lẻ), hướng tới công bố tại hội nghị NLP hạng A* (ACL hoặc EMNLP — xem [docs/06](docs/06-publication-strategy.md)).

> Trạng thái: **giai đoạn lập kế hoạch** — chưa có dữ liệu/code. Tài liệu trong repo này là kế hoạch làm việc nội bộ cho nhóm 10 sinh viên, chưa phải công bố chính thức.

## Vấn đề & động lực

Chart QA tiếng Anh đã gần bão hoà ở benchmark gốc ChartQA (VLM hàng đầu đạt &gt;90%), tiếng Việt chưa có benchmark chuyên biệt cho biểu đồ. Phần lớn chart tiếng Việt chất lượng tốt nằm trong bài báo (title + nội dung phân tích + 1-3 chart minh hoạ), không phải chart rời trong thư viện — ViChartQA khai thác đặc điểm này: **multi-hop reasoning kết hợp đọc hiểu văn bản và đọc chart**, gần với dòng HybridQA/TAT-QA/MultiHiertt/SlideVQA hơn dòng ChartQA/CharXiv (chart-only). So sánh đầy đủ ở [docs/01](docs/01-related-work.md).

ViInfographicVQA và VMMU là căn cứ động lực bổ sung — chi tiết ở docs/01.

ViChartQA nhắm lấp khoảng trống: **văn bản + chart cùng lúc** × **tiếng Việt** × **multi-hop reasoning thật sự** (verify bằng evidence chain, không chỉ gắn nhãn).

## Mục tiêu dự án

1. **Bộ dữ liệu** — bài viết thật nguồn Việt Nam (title + content + 1-3 chart), câu hỏi multi-hop kết hợp đọc văn bản và đọc chart. Miền dữ liệu mở rộng theo nguồn cung thực tế (xem [docs/02](docs/02-dataset-design.md#miền-dữ-liệu)), ưu tiên kinh tế, mở sang khoa học/giáo dục/y tế/môi trường/năng lượng nếu có nguồn cùng dạng.
2. **Mô hình** — fine-tune một VLM backbone (Vintern hoặc Qwen2.5-VL), cạnh tranh với các VLM tổng quát (GPT-4o, Gemini) trong miền hẹp tiếng Việt.
3. **Công bố** — dataset + model paper tại hội nghị A*, qua ACL Rolling Review.

## Cấu trúc repo

```
.
├── README.md                       # tài liệu này
├── docs/
│   ├── 01-related-work.md          # bối cảnh & rà soát công trình liên quan
│   ├── 02-dataset-design.md        # thiết kế dataset: nguồn, taxonomy câu hỏi, schema
│   ├── 03-annotation-guidelines.md # hướng dẫn gán nhãn chi tiết cho annotator
│   ├── 04-model-strategy.md        # chiến lược mô hình, backbone, đánh giá
│   ├── 05-timeline-and-roles.md    # lịch trình 7 tuần & phân công nhân sự
│   ├── 06-publication-strategy.md  # chiến lược công bố & thời hạn
│   ├── 07-risks.md                 # rủi ro & giảm thiểu
│   └── 08-annotation-tool-design.md # thiết kế công cụ gán nhãn
└── annotation-tool/                # công cụ gán nhãn (Streamlit + SQLite) — xem annotation-tool/README.md
```

*(các thư mục `data/`, `models/`, `scripts/` cho phần dataset/model sẽ được tạo khi cần, từ Tuần 2 trở đi)*

## Tóm tắt kế hoạch

| | |
|---|---|
| **Nhân lực** | 10 sinh viên, chia 5 pod (xem [docs/05](docs/05-timeline-and-roles.md)) |
| **Thời lượng lõi** | 6–7 tuần (14/07 – 31/08/2026) |
| **Đơn vị dữ liệu** | Document: title + body_text + 1–3 chart (không phải chart rời) |
| **Miền dữ liệu** | Kinh tế (neo) · Khoa học/giáo dục/y tế/môi trường/năng lượng (mở rộng theo nguồn cung) |
| **Taxonomy câu hỏi** | 2 chiều: loại suy luận (8 giá trị: data_retrieval/visual/compositional/visual_compositional/multiple_choice/hypothetical/fact_check/unanswerable) × phạm vi bằng chứng (single_chart/text_to_chart/chart_to_chart/fact_check_dual) |
| **Quy mô mục tiêu** | MVP: 1.200 document / 6.000 QA · Mở rộng: 2.000 document / ~15.000 QA |
| **Backbone mô hình** | Vintern-3B (chính), Qwen2.5-VL-7B, InternVL3-8B |
| **Venue mục tiêu** | ACL hoặc EMNLP (2 hội nghị CORE A* trong dòng *ACL; NAACL/EACL chỉ hạng A) qua ARR — xem [docs/06](docs/06-publication-strategy.md) |

Chi tiết đầy đủ từng phần nằm trong `docs/`. Bản kế hoạch trực quan (bảng so sánh, Gantt, checklist) xem tại artifact đã chia sẻ với nhóm.

## Nguyên tắc làm việc

- **Chất lượng &gt; số lượng thô.** ChartQAPro (1.341 chart / 1.948 câu hỏi) vẫn đủ mạnh để công bố nhờ độ khó và thiết kế tốt — nếu phải đánh đổi, ưu tiên độ khó và độ sạch của nhãn.
- **Không huấn luyện mô hình từ đầu.** Fine-tune backbone có sẵn (ChartGemma, TinyChart, ChartMoE đều làm vậy).
- **Ưu tiên nguồn dữ liệu mở/chính phủ.** Xem [docs/02](docs/02-dataset-design.md#nguồn-dữ-liệu).

## Đóng góp

Dự án đang ở giai đoạn nội bộ, chưa mở đóng góp bên ngoài. Phân công cụ thể tại [docs/05](docs/05-timeline-and-roles.md).

## Giấy phép

Chưa xác định — chốt cùng rà soát pháp lý nguồn dữ liệu ở Tuần 1 (xem [docs/02](docs/02-dataset-design.md#nguồn-dữ-liệu)).
