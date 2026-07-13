# 02 — Thiết kế bộ dữ liệu

## Phạm vi

- **Đơn vị dữ liệu:** document = `{title, body_text, charts: [1..3 ảnh]}`, lấy từ một bài viết/báo cáo thật.
- **Loại ảnh chart:** bar, line, pie, stacked/grouped bar, multi-line — không nhận infographic, dashboard, hay bảng số liệu thuần text. `body_text` (văn bản thường) là thành phần bắt buộc đi kèm.
- **Ngôn ngữ:** tiêu đề, body_text, nhãn/chú thích trên chart phải là tiếng Việt gốc (không dịch từ tiếng Anh).
- **Miền:** mở rộng theo nguồn cung thực tế, không ép cứng tỷ lệ.

## Miền dữ liệu

**Kinh tế là miền neo, nguồn dồi dào** — thể loại "title + phân tích + 1-3 chart" lặp lại định kỳ trên báo kinh tế tiếng Việt (CafeF; consosukien.vn — tạp chí chính thức Tổng cục Thống kê). Chủ đề: GDP/tăng trưởng, CPI/lạm phát, xuất nhập khẩu, thị trường lao động, ngân sách nhà nước, chứng khoán, FDI.

**Khoa học và miền khác (giáo dục, y tế, môi trường, năng lượng, xã hội) là miền mở rộng** — ưu tiên báo cáo thường niên chính phủ (Bộ KH&CN, NASATI, báo cáo môi trường quốc gia, EVN/Bộ Công thương, Bộ Y tế) hơn báo phổ biến khoa học (Tia Sáng nghiêng bài chính sách/bình luận, ít data-journalism). Tỷ trọng domain do nguồn cung quyết định.

**Tuần 1 (Pod A):** lấy mẫu ~30-50 document/domain, đếm tỷ lệ đạt tiêu chí (≥1 đoạn văn bình luận trực tiếp vào số liệu chart) trước khi chốt tỷ trọng domain — xem [docs/05 Tuần 1](05-timeline-and-roles.md#tuần-1-1420-07--setup--pilot).

## Nguồn dữ liệu

| Miền | Nguồn đề xuất | Lưu ý pháp lý |
|---|---|---|
| Kinh tế | Tổng cục Thống kê (gso.gov.vn, consosukien.vn), Ngân hàng Nhà nước, Bộ Tài chính, ấn bản tiếng Việt World Bank/IMF | Dữ liệu/ấn phẩm nhà nước — rủi ro bản quyền thấp, cần trích dẫn nguồn đầy đủ |
| Kinh tế | VnEconomy, CafeF, Vietnam Report, báo cáo thường niên doanh nghiệp niêm yết | Cần rà soát điều khoản sử dụng cả text lẫn hình ảnh; cân nhắc tự vẽ lại chart từ số liệu công bố nếu ảnh gốc có bản quyền |
| Khoa học/khác | Báo cáo thường niên Bộ KH&CN, NASATI, báo cáo môi trường quốc gia, EVN/Bộ Công thương, Bộ Y tế | Ấn phẩm công, thường cho phép phi thương mại — vẫn nên xin phép bằng văn bản |
| Khoa học/khác (dự phòng) | Tia Sáng, Khoa học & Phát triển | Cần liên hệ toà soạn xin phép trước khi crawl số lượng lớn; xác nhận số lượng bài đủ multi-chart trước khi coi là nguồn chính |

**Data Statement:** mỗi nguồn ghi rõ điều khoản sử dụng, ngày truy cập, phạm vi cho phép — cho cả text lẫn ảnh. Chuẩn bị từ Tuần 1.

**Tránh:** SGK/tài liệu giáo dục có bản quyền NXB Giáo dục rõ ràng.

## Taxonomy câu hỏi

Hai chiều độc lập, mỗi câu hỏi gán nhãn cả hai.

### Chiều 1 — loại suy luận

`question_type`, enum 8 giá trị lá:

| Nhóm | `question_type` | Mô tả | Ví dụ | Tỷ trọng mục tiêu |
|---|---|---|---|---|
| Truy vấn dữ liệu | `data_retrieval` | Đọc trực tiếp một giá trị/nhãn | "Tỷ lệ lạm phát năm 2024 là bao nhiêu?" | ~15% |
| Thị giác | `visual` | Tham chiếu màu sắc, vị trí, kích thước | "Cột màu xanh lam cao nhất nằm ở năm nào?" | ~15% |
| Suy luận kết hợp | `compositional` | ≥2 phép toán số học/logic | "Chênh lệch tăng trưởng GDP giữa quý 1 và quý 3 là bao nhiêu điểm %?" | ~30% |
| Thị giác + suy luận | `visual_compositional` | Kết hợp cả hai | "Trong các năm có cột màu xanh lá, năm nào chênh lệch với năm liền trước là lớn nhất?" | ~20% |
| Mở rộng | `multiple_choice` | Trắc nghiệm 4 đáp án (`choices`) | "Năm nào tăng trưởng GDP cao nhất? A. 2021 B. 2022 C. 2023 D. 2024" | ~20% (gộp 4 loại) |
| Mở rộng | `hypothetical` | Giả định ngoài dữ liệu quan sát được | "Nếu xu hướng tiếp diễn, giá trị năm 2027 gần nhất là bao nhiêu?" | nt. |
| Mở rộng | `fact_check` | Kiểm tra đúng/sai một phát biểu | "Đúng hay sai: doanh thu quý 4 luôn cao nhất năm?" | nt. |
| Mở rộng | `unanswerable` | Không trả lời được từ document | "Nguyên nhân lạm phát tăng đột biến là gì?" | nt. |

Hội thoại nhiều lượt không phải một `question_type` — câu lượt 2 trở đi khai `question_type` theo bản chất suy luận + `follow_up_of` trỏ tới id câu hỏi lượt trước.

### Chiều 2 — phạm vi bằng chứng / hop-type (mới, claim chính của dự án)

| Hop-type | Mô tả | Ví dụ |
|---|---|---|
| `single_chart` | Trả lời được chỉ từ 1 chart | "Vốn FDI năm 2020 là bao nhiêu?" |
| `text_to_chart` | Hop 1 lấy claim/số liệu chỉ có trong body_text, hop 2 đối chiếu/tính toán với chart | "Bài viết nêu dự báo ADB cho 2022 — so với GDP 2021 trên Hình 1, mức tăng tuyệt đối dự kiến là bao nhiêu?" |
| `chart_to_chart` | ≥2 chart, body_text là cầu nối | "Trong 2011–2021, chỉ tiêu nào tăng nhanh hơn: GDP (Hình 1) hay kim ngạch xuất nhập khẩu (Hình 3)?" |
| `fact_check_dual` | Cần cả text lẫn chart để xác minh đúng/sai | "Đúng hay sai: vốn FDI tăng liên tục suốt 2011–2021?" |

Ngưỡng mục tiêu: ≥50% câu hỏi test set thuộc 3 loại multi-hop (neo theo mốc 48.74% của MultiHiertt — [docs/01](01-related-work.md#4b-dòng-multi-hop-qa-trên-dữ-liệu-có-cấu-trúc-text--tablechart)). Phần còn lại là `single_chart`, dùng để so sánh trực tiếp với ChartQA/ChartQAPro.

Ví dụ tốt/xấu chi tiết ở [docs/03](03-annotation-guidelines.md).

## Quy trình gán nhãn (tổng quan)

0. **Đọc document** — xác định số liệu/claim chỉ có trong text, không vẽ trên chart nào (nguyên liệu cho `text_to_chart`/`fact_check_dual`).
1. **Seed thủ công** — 2-3 câu hỏi mồi/document, tối thiểu 1 multi-hop + 1 `single_chart`.
2. **Mở rộng bằng VLM** — GPT-4o/Gemini/Qwen2.5-VL sinh 4-6 câu ứng viên/document từ seed + title + body_text + data_table, rải đều cả 2 chiều taxonomy.
3. **Lọc & xác minh chéo** — người thứ hai đọc cả document, trả lời độc lập không nhìn đáp án gốc; với multi-hop phải điền `evidence` độc lập, lệch → phân xử.
4. **Kiểm tra IAA trên mẫu** — 300-500 câu/đợt, tách riêng theo hop-type (multi-hop dự kiến IAA thấp hơn single_chart, theo dõi không để tụt quá xa mốc: ChartQA gốc 61%/78.55%, ChartQAPro 66.17%).

Quy trình đầy đủ, vai trò từng pod, biểu mẫu adjudication ở [docs/03](03-annotation-guidelines.md).

## Trích xuất bảng dữ liệu gốc

Mỗi chart cần số hoá `data_table` (giá trị theo trục x/nhãn, theo chuỗi/legend) — dùng để lọc câu hỏi sai tự động, hỗ trợ relaxed accuracy ([docs/04](04-model-strategy.md#metric-đánh-giá)), làm tài nguyên phụ trợ cho RLVR. Nhập tay bởi annotator khi viết seed.

## Quy mô mục tiêu

| | Document | Chart (ước tính, 1–3/document) | Câu hỏi |
|---|---|---|---|
| **MVP** | 1.200 | ~1.800–3.000 | 6.000 |
| **Mở rộng** | 2.000 | ~3.000–5.000 | 10.000–12.000 |

Nhóm so sánh (multi-hop text+structured-data):

| Dataset | Quy mô |
|---|---|
| TAT-QA | 2.757 context / 16.552 QA |
| MultiHiertt | 2.513 document / 10.440 QA |
| SlideVQA | 2.600 deck / 14.500 QA |

MVP 1.200 document/6.000 QA cùng bậc quy mô với nhóm này. ChartQAPro (1.341/1.948) và ViInfographicVQA (6.747/20.409) là mốc tham khảo phụ cho slice `single_chart`. Ưu tiên đạt MVP với chất lượng cao hơn cố quy mô mở rộng mà giảm chất lượng.

## Chia tập train/val/test

Tỷ lệ ~77%/10%/13% (như ChartQA gốc), chia theo document (không theo câu hỏi) để tránh leakage. Test set làm sạch thủ công hoàn toàn, không dùng heuristic tự động. Giữ tỷ lệ hop-type ≥50% multi-hop sau khi làm sạch.

## Schema dữ liệu đề xuất

Đơn vị lưu trữ là **document**: một title + body_text + 1–3 chart, mang nhiều câu hỏi (mảng `qa`). Mỗi câu hỏi tự khai báo `hop_type` và `evidence`.

```json
{
  "id": "vichartqa_econ_00123",
  "title": "Trend 10 năm với kinh tế Việt Nam: Nền kinh tế đã trưởng thành hơn ra sao?",
  "body_text": "Nhìn chung GDP trong 10 năm qua tăng dần theo thời gian... [đoạn văn liên quan đến các chart, không cần toàn bài]",
  "source": {
    "provider": "CafeF",
    "domain": "economics",
    "topic": "GDP, FDI, xuất nhập khẩu 2011-2021",
    "license": "cần-xác-nhận-toà-soạn",
    "url": "https://cafef.vn/...",
    "accessed_date": "2026-07-20"
  },
  "charts": [
    {
      "chart_id": "fig1",
      "image": "images/econ/cafef_trend10nam_00123_fig1.png",
      "chart_type": "line",
      "chart_complexity": "simple",
      "topic": "GDP 2011-2021",
      "data_table": {
        "x_axis": ["2011", "2012", "...", "2021"],
        "series": { "GDP (triệu tỷ đồng)": [2.5, "...", 8.4] }
      }
    },
    { "chart_id": "fig2", "image": "images/econ/cafef_trend10nam_00123_fig2.png", "chart_type": "line", "topic": "FDI 2011-2021", "data_table": { "...": "..." } },
    { "chart_id": "fig3", "image": "images/econ/cafef_trend10nam_00123_fig3.png", "chart_type": "line", "topic": "Xuất nhập khẩu 2011-2021", "data_table": { "...": "..." } }
  ],
  "qa": [
    {
      "id": "q1",
      "question": "Trong giai đoạn 2011–2021, chỉ tiêu nào tăng nhanh hơn: GDP hay kim ngạch xuất nhập khẩu?",
      "answer": "Kim ngạch xuất nhập khẩu",
      "answer_type": "text",
      "question_type": "compositional",
      "hop_type": "chart_to_chart",
      "requires_visual_reference": false,
      "derivation": "",
      "follow_up_of": null,
      "choices": null,
      "evidence": [
        { "hop": 1, "source": "chart", "chart_id": "fig1", "series": "GDP (triệu tỷ đồng)", "x": ["2011", "2021"] },
        { "hop": 2, "source": "chart", "chart_id": "fig3", "series": "Kim ngạch xuất nhập khẩu (tỷ USD)", "x": ["2011", "2021"] }
      ]
    },
    {
      "id": "q2",
      "question": "GDP năm 2021 tăng bao nhiêu triệu tỷ đồng so với năm 2011?",
      "answer": "5.9",
      "answer_type": "numeric",
      "question_type": "compositional",
      "hop_type": "single_chart",
      "requires_visual_reference": false,
      "derivation": "8.4 - 2.5",
      "follow_up_of": null,
      "choices": null,
      "evidence": [
        { "hop": 1, "source": "chart", "chart_id": "fig1", "series": "GDP (triệu tỷ đồng)", "x": ["2011", "2021"] }
      ]
    },
    {
      "id": "q3",
      "question": "Vậy tốc độ tăng đó tương đương bao nhiêu %?",
      "answer": "236%",
      "answer_type": "numeric",
      "question_type": "compositional",
      "hop_type": "single_chart",
      "requires_visual_reference": false,
      "derivation": "5.9 / 2.5 * 100",
      "follow_up_of": "q2",
      "choices": null,
      "evidence": [
        { "hop": 1, "source": "chart", "chart_id": "fig1", "series": "GDP (triệu tỷ đồng)", "x": ["2011", "2021"] }
      ]
    },
    {
      "id": "q4",
      "question": "Năm nào GDP tăng trưởng cao nhất trong giai đoạn 2011–2021?",
      "answer": "2021",
      "answer_type": "text",
      "question_type": "multiple_choice",
      "hop_type": "single_chart",
      "requires_visual_reference": false,
      "derivation": "",
      "follow_up_of": null,
      "choices": ["2015", "2018", "2019", "2021"],
      "evidence": [
        { "hop": 1, "source": "chart", "chart_id": "fig1", "series": "GDP (triệu tỷ đồng)", "x": ["2011", "2012", "...", "2021"] }
      ]
    }
  ],
  "annotation": {
    "generation_method": "vlm_assisted",
    "seed_by": "annotator_07",
    "verified_by": "annotator_12",
    "iaa_sample": true,
    "iaa_agreement": "exact_match"
  },
  "split": "train"
}
```

Trường `chart_complexity` (`simple`/`complex`): bảng dữ liệu 2 cột = simple, nhiều cột = complex. `evidence` bắt buộc khi `hop_type != single_chart`.

`derivation`: bắt buộc khi `answer_type: numeric` và `question_type` là `compositional`/`visual_compositional` có tính toán — công thức số học thuần dùng đúng số trong `data_table` (vd. `"8.4 - 2.5"`), trống `""` với loại còn lại. Dùng để Pod C auto-eval đối chiếu `answer`, và tái dùng cho RLVR ([docs/04](04-model-strategy.md#hướng-mở-rộng-nếu-còn-thời-gian-tuần-7-trở-đi--sau-dự-án)).

### Định dạng `evidence` — tham chiếu bằng label, không mô tả tự do

- `source: "chart"` → `{chart_id, series, x}`, `series`/`x` lấy đúng nguyên văn từ `data_table.series`/`data_table.x_axis`.
- `source: "text"` → `{quote}`, đoạn trích nguyên văn ngắn từ `body_text`.

`series`/`x` đều là giá trị đã tồn tại sẵn trong `data_table` — auto-check được bằng cách so khớp chuỗi trực tiếp.

## Việc cần chốt trước khi crawl (Tuần 1)

Xem checklist đầy đủ ở README và [docs/05](05-timeline-and-roles.md#tuần-1). Không crawl hàng loạt trước khi có xác nhận pháp lý cho từng nguồn.
