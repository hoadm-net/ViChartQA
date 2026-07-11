# ViChartQA

Bộ dữ liệu và mô hình Hỏi–Đáp biểu đồ (Chart Question Answering) tiếng Việt, cốt lõi là **multi-hop reasoning trên text + chart** trong các bài viết thật (không phải chart rời lẻ), hướng tới công bố tại hội nghị NLP hạng A* (ACL hoặc EMNLP — đã verify trực tiếp trên CORE portal, NAACL/EACL chỉ xếp hạng A, xem [docs/06](docs/06-publication-strategy.md)).

> Trạng thái: **giai đoạn lập kế hoạch** — chưa có dữ liệu/code. Tài liệu trong repo này là kế hoạch làm việc nội bộ cho nhóm 10 sinh viên, chưa phải công bố chính thức.
>
> **Pivot 11/07/2026:** đổi đơn vị dữ liệu từ "chart đơn lẻ" sang "document" (title + đoạn văn liên quan + 1–3 chart), với claim chính là multi-hop reasoning qua cả text lẫn chart — không chỉ chart-only QA kiểu ChartQA gốc. Lý do và toàn bộ quá trình cân nhắc xem ghi chú trong [docs/01](docs/01-related-work.md#4b-dòng-multi-hop-qa-trên-dữ-liệu-có-cấu-trúc-text--tablechart) và [docs/02](docs/02-dataset-design.md).

## Vấn đề & động lực

Chart QA tiếng Anh đã gần bão hoà ở benchmark gốc ChartQA (VLM hàng đầu đạt &gt;90%), trong khi tiếng Việt gần như chưa có benchmark chuyên biệt cho biểu đồ. Nhưng dịch nguyên taxonomy ChartQA (chart đơn lẻ, không context) sang tiếng Việt sẽ bị đánh giá là "chỉ là bản dịch" — đặc biệt khi tài nguyên chart tiếng Việt không dồi dào bằng kho Statista/Pew/OWID/OECD mà ChartQA gốc dùng được. Quan sát quan trọng: phần lớn chart tiếng Việt chất lượng tốt **nằm trong bài báo** (title + nội dung phân tích + 1-3 chart minh hoạ), không phải chart rời trong thư viện — đây vừa là ràng buộc thực tế vừa là cơ hội để claim một bài toán khác hẳn: **multi-hop reasoning kết hợp đọc hiểu văn bản và đọc chart**, gần với dòng HybridQA/TAT-QA/MultiHiertt/SlideVQA (multi-hop trên text + dữ liệu có cấu trúc) hơn là dòng ChartQA/CharXiv (chart-only). Xem so sánh đầy đủ ở [docs/01](docs/01-related-work.md).

ViInfographicVQA (gần nhất về miền dữ liệu tiếng Việt) và VMMU (khoảng cách OCR tốt vs suy luận đa phương thức yếu, ~66% ở mô hình mạnh nhất) vẫn là căn cứ động lực quan trọng — xem chi tiết ở docs/01.

ViChartQA nhắm lấp khoảng trống: **văn bản + chart cùng lúc** (không phải chart cô lập) × **tiếng Việt** × **multi-hop reasoning thật sự** (có thể verify bằng evidence chain, không chỉ gắn nhãn).

## Mục tiêu dự án

1. **Bộ dữ liệu** — bài viết thật nguồn Việt Nam (title + content + 1-3 chart), câu hỏi multi-hop yêu cầu kết hợp đọc văn bản và đọc chart, độ khó đủ để còn ý nghĩa với VLM hiện đại năm 2026. Miền dữ liệu **mở rộng theo nguồn cung thực tế** (không ép cứng 50/50 khoa học/kinh tế — xem [docs/02](docs/02-dataset-design.md#miền-dữ-liệu)), ưu tiên kinh tế (đã xác nhận có nguồn dồi dào, ví dụ thể loại "bức tranh kinh tế" định kỳ trên CafeF/consosukien.vn) và mở sang các miền khác (khoa học, giáo dục, y tế, môi trường, năng lượng...) nếu tìm được nguồn cùng dạng.
2. **Mô hình** — fine-tune một VLM backbone (Vintern hoặc Qwen2.5-VL) trên bộ dữ liệu, cạnh tranh với các VLM tổng quát (GPT-4o, Gemini) trong đúng miền hẹp tiếng Việt.
3. **Công bố** — dataset + model paper tại hội nghị A*, mục tiêu nộp chu kỳ ACL Rolling Review tháng 10/2026.

## Cấu trúc repo

```
.
├── README.md                       # tài liệu này
└── docs/
    ├── 01-related-work.md          # bối cảnh & rà soát công trình liên quan
    ├── 02-dataset-design.md        # thiết kế dataset: nguồn, taxonomy câu hỏi, schema
    ├── 03-annotation-guidelines.md # hướng dẫn gán nhãn chi tiết cho annotator
    ├── 04-model-strategy.md        # chiến lược mô hình, backbone, đánh giá
    ├── 05-timeline-and-roles.md    # lịch trình 7 tuần & phân công nhân sự
    ├── 06-publication-strategy.md  # chiến lược công bố & thời hạn
    └── 07-risks.md                 # rủi ro & giảm thiểu
```

*(các thư mục `data/`, `annotation-tool/`, `models/`, `scripts/` sẽ được tạo khi bước vào Tuần 1 — xem [docs/05-timeline-and-roles.md](docs/05-timeline-and-roles.md))*

## Tóm tắt kế hoạch

| | |
|---|---|
| **Nhân lực** | 10 sinh viên, chia 5 pod (xem [docs/05](docs/05-timeline-and-roles.md)) |
| **Thời lượng lõi** | 6–7 tuần (14/07 – 31/08/2026) |
| **Miền dữ liệu** | Khoa học (R&D, môi trường, y tế công cộng, năng lượng) · Kinh tế (GDP, CPI, xuất nhập khẩu, thị trường lao động) |
| **Loại câu hỏi** | Truy vấn dữ liệu, thị giác, suy luận kết hợp (compositional), thị giác+suy luận, và các dạng mở rộng (trắc nghiệm, giả định, fact-check, không trả lời được) |
| **Quy mô mục tiêu** | MVP: 1.200 chart / 6.000 QA · Mở rộng: 2.000 chart / 10.000–12.000 QA |
| **Backbone mô hình** | Vintern-3B (khuyến nghị chính), Qwen2.5-VL-7B, InternVL3-8B |
| **Venue mục tiêu** | ACL hoặc EMNLP (2 hội nghị duy nhất trong dòng *ACL đạt CORE A* — đã verify trực tiếp; NAACL/EACL chỉ hạng A) qua ARR — xem [docs/06](docs/06-publication-strategy.md) để biết chu kỳ nộp còn mở |

Chi tiết đầy đủ từng phần nằm trong `docs/`. Bản kế hoạch trực quan (bảng so sánh, Gantt, checklist) xem tại artifact đã chia sẻ với nhóm.

## Nguyên tắc làm việc

- **Chất lượng &gt; số lượng thô.** ChartQAPro (ACL 2025) cho thấy 1.341 chart / 1.948 câu hỏi vẫn đủ mạnh để công bố nhờ độ khó và thiết kế tốt — nếu phải đánh đổi trong 6–7 tuần, ưu tiên độ khó và độ sạch của nhãn.
- **Không huấn luyện mô hình từ đầu.** Mọi mô hình chart-VLM gần đây (ChartGemma, TinyChart, ChartMoE) đều fine-tune trên backbone có sẵn — ViChartQA đi theo hướng này.
- **Ưu tiên nguồn dữ liệu mở/chính phủ.** Xem [docs/02-dataset-design.md](docs/02-dataset-design.md#nguồn-dữ-liệu) để biết nguyên tắc chọn nguồn và rủi ro bản quyền cần rà soát trước khi crawl.

## Đóng góp

Dự án đang ở giai đoạn nội bộ, chưa mở đóng góp bên ngoài. Thành viên nhóm xem phân công cụ thể tại [docs/05-timeline-and-roles.md](docs/05-timeline-and-roles.md).

## Giấy phép

Chưa xác định — sẽ chốt cùng với rà soát pháp lý nguồn dữ liệu ở Tuần 1 (xem [docs/02-dataset-design.md](docs/02-dataset-design.md#nguồn-dữ-liệu)).
