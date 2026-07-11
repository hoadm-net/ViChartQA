# 02 — Thiết kế bộ dữ liệu

> **Pivot 11/07/2026:** đơn vị dữ liệu đổi từ "chart đơn lẻ" sang "document" (title + đoạn văn liên quan + 1–3 chart), claim chính là multi-hop reasoning qua text+chart. Xem lý do ở README và [docs/01 mục 4b](01-related-work.md#4b-dòng-multi-hop-qa-trên-dữ-liệu-có-cấu-trúc-text--tablechart). Các mục dưới đây đã cập nhật theo hướng này.

## Phạm vi

- **Đơn vị dữ liệu:** một **document** = `{title, body_text, charts: [1..3 ảnh]}`, lấy từ một bài viết/báo cáo thật (không cắt rời chart ra khỏi ngữ cảnh). Đây là thay đổi cốt lõi so với bản thiết kế đầu (chart đơn lẻ kiểu ChartQA).
- **Loại ảnh chart trong document:** bar, line, pie, stacked/grouped bar, multi-line — không nhận infographic, ảnh chụp màn hình dashboard phức tạp, hay bảng số liệu thuần text làm *chart*, nhưng **body_text** (văn bản thường, không phải bảng/infographic) là thành phần bắt buộc đi kèm.
- **Ngôn ngữ:** tiêu đề, body_text, và nhãn/chú thích trên chart phải là **tiếng Việt gốc** (không dịch từ nguồn tiếng Anh) — điều kiện bắt buộc để bài toán kiểm tra thật khả năng đọc-hiểu tiếng Việt (cả văn bản lẫn chart), không phải khả năng OCR rồi dịch.
- **Miền:** mở rộng theo nguồn cung thực tế, không ép cứng tỷ lệ — xem [Miền dữ liệu](#miền-dữ-liệu) bên dưới.

## Miền dữ liệu

Bản thiết kế đầu đặt mục tiêu 50/50 khoa học/kinh tế. Sau khi kiểm tra nhanh (11/07/2026): thể loại bài viết dạng "title + phân tích + 1-3 chart minh hoạ" là **thể loại lặp lại định kỳ** trong báo chí kinh tế tiếng Việt (vd. "Bức tranh kinh tế Việt Nam năm X và dự báo năm X+1" — xuất hiện hàng năm/hàng quý trên CafeF, và cả trên **consosukien.vn** — tạp chí chính thức của Tổng cục Thống kê, nguồn chính phủ rủi ro bản quyền thấp). Cùng một kiểm tra sơ bộ với báo khoa học (Tia Sáng) **không** cho tín hiệu tương tự — kết quả nghiêng về bài chính sách/bình luận (essay), ít bài dạng data-journalism nhiều chart.

**Hệ quả cho kế hoạch:**

- **Không ép tỷ lệ 50/50.** Domain split sẽ do nguồn cung quyết định, xác nhận cụ thể ở Tuần 1 (xem checklist bên dưới).
- **Kinh tế là miền neo (anchor), đã xác nhận khả thi.** Chủ đề: GDP/tăng trưởng, CPI/lạm phát, xuất nhập khẩu, thị trường lao động, ngân sách nhà nước, chứng khoán, FDI.
- **Khoa học vẫn giữ làm miền phụ nếu tìm được nguồn đúng dạng** — ưu tiên thử **báo cáo thường niên chính phủ** (Bộ KH&CN, NASATI, báo cáo môi trường quốc gia, EVN/Bộ Công thương cho năng lượng, Bộ Y tế cho y tế công cộng) thay vì báo phổ biến khoa học kiểu Tia Sáng — báo cáo thường niên nhiều khả năng có cấu trúc multi-chart + narrative giống thể loại kinh tế đã xác nhận hơn.
- **Mở thêm miền khác nếu tìm được nguồn cùng dạng** (giáo dục, y tế, môi trường, năng lượng, xã hội...) — không giới hạn cứng ở khoa học/kinh tế như bản đầu, miễn giữ được yêu cầu miền chuyên môn (không dùng ảnh tổng quát đời thường).

**Việc cần làm Tuần 1 (Pod A):** lấy mẫu ~30-50 document ứng viên mỗi domain đang cân nhắc, đếm tỷ lệ đạt tiêu chí (≥1 đoạn văn bình luận trực tiếp vào số liệu chart, không chỉ caption 1 câu) trước khi chốt tỷ trọng domain cuối cùng — xem thêm [docs/05 Tuần 1](05-timeline-and-roles.md#tuần-1-1420-07--setup--pilot).

## Nguồn dữ liệu

| Miền | Nguồn đề xuất | Lưu ý pháp lý |
|---|---|---|
| Kinh tế (neo, đã xác nhận) | Tổng cục Thống kê (gso.gov.vn, consosukien.vn), Ngân hàng Nhà nước, Bộ Tài chính, ấn bản tiếng Việt World Bank/IMF | Dữ liệu/ấn phẩm nhà nước — rủi ro bản quyền thấp, cần trích dẫn nguồn đầy đủ |
| Kinh tế (neo, đã xác nhận) | VnEconomy, CafeF (thể loại "bức tranh kinh tế" định kỳ), Vietnam Report, báo cáo thường niên doanh nghiệp niêm yết | Cần rà soát điều khoản sử dụng lại **cả text lẫn hình ảnh** cùng lúc (khác bản đầu chỉ tính riêng ảnh) — vì giờ lấy nguyên bài, không tách chart ra dùng riêng; cân nhắc tự vẽ lại chart từ số liệu công bố nếu ảnh gốc có bản quyền rõ ràng nhưng text vẫn trích dẫn có nguồn |
| Khoa học/khác (thử nghiệm, cần xác nhận Tuần 1) | Báo cáo thường niên Bộ KH&CN, NASATI, báo cáo môi trường quốc gia, EVN/Bộ Công thương (năng lượng), Bộ Y tế (y tế công cộng) | Ấn phẩm công phục vụ học thuật, thường cho phép phi thương mại — vẫn nên xin phép bằng văn bản, lưu lại làm bằng chứng |
| Khoa học/khác (dự phòng, rủi ro nguồn cung) | Tia Sáng, Khoa học & Phát triển và tạp chí phổ biến khoa học khác | Cần liên hệ toà soạn xin phép sử dụng cho nghiên cứu trước khi crawl số lượng lớn; **lưu ý:** kiểm tra sơ bộ 11/07 cho thấy nguồn này có thể ít bài đủ multi-chart hơn kỳ vọng — xác nhận số lượng thực tế trước khi coi là nguồn chính |

**Nguyên tắc** (theo đúng tiền lệ ChartQA gốc với Statista/Pew/OWID/OECD): mỗi nguồn phải có một dòng trong **Data Statement** ghi rõ điều khoản sử dụng, ngày truy cập, và phạm vi cho phép (học thuật/phi thương mại/công khai) — **cho cả text lẫn ảnh** của cùng một bài. Việc này nằm trong phần Ethics Considerations bắt buộc của bài báo ACL/EMNLP — chuẩn bị từ Tuần 1, không để đến lúc viết bài mới làm.

**Tránh:** SGK/tài liệu giáo dục có bản quyền NXB Giáo dục rõ ràng — rủi ro pháp lý cao so với lợi ích, không đáng đánh đổi.

## Taxonomy câu hỏi

Hai chiều **độc lập nhau**, mỗi câu hỏi được gán nhãn cả hai:

### Chiều 1 — loại suy luận (giữ nguyên từ bản đầu)

Kế thừa hai loại lõi của ChartQA gốc (*compositional*, *visual*) và mở rộng theo ChartQAPro để đảm bảo bài toán còn khó với VLM 2026 (xem lý do chi tiết ở [docs/01](01-related-work.md)).

| Nhóm | Mô tả | Ví dụ | Tỷ trọng mục tiêu |
|---|---|---|---|
| Truy vấn dữ liệu | Đọc trực tiếp một giá trị/nhãn, không cần tính toán | "Tỷ lệ lạm phát năm 2024 là bao nhiêu?" | ~15% |
| Thị giác | Tham chiếu màu sắc, vị trí, kích thước đối tượng trên chart | "Cột màu xanh lam cao nhất nằm ở năm nào?" | ~15% |
| Suy luận kết hợp (compositional) | ≥2 phép toán số học/logic: tổng, hiệu, %, trung bình, so sánh | "Chênh lệch tăng trưởng GDP giữa quý 1 và quý 3 là bao nhiêu điểm %?" | ~30% |
| Thị giác + suy luận | Kết hợp cả hai nhóm trên trong cùng một câu hỏi | "Trong các năm có cột màu xanh lá, năm nào chênh lệch với năm liền trước là lớn nhất?" | ~20% |
| Mở rộng (kiểu ChartQAPro) | Trắc nghiệm 4 đáp án, giả định ngoài dữ liệu quan sát được, kiểm tra đúng/sai một phát biểu (fact-check), hội thoại nhiều lượt, câu hỏi **không trả lời được** từ chart | "Nếu xu hướng tiếp diễn, giá trị năm 2027 gần nhất là bao nhiêu?" · "Đúng hay sai: doanh thu quý 4 luôn cao nhất năm?" | ~20% |

### Chiều 2 — phạm vi bằng chứng / hop-type (mới, claim chính của dự án)

Chỉ được gán `multi_hop = true` nếu câu hỏi khớp một trong ba dạng sau — không tự suy diễn, tránh gắn nhãn "multi-hop" cho câu thực chất chỉ cần 1 chart (xem hướng dẫn chi tiết + ví dụ tốt/xấu ở [docs/03](03-annotation-guidelines.md)):

| Hop-type | Mô tả | Ví dụ (dựa trên bài CafeF "Trend 10 năm với kinh tế Việt Nam") |
|---|---|---|
| `single_chart` | Trả lời được chỉ từ 1 chart, không cần body_text | "Vốn FDI năm 2020 là bao nhiêu?" (đọc thẳng Hình 2) |
| `text_to_chart` | Hop 1 lấy claim/số liệu **chỉ có trong body_text**, hop 2 đối chiếu/tính toán với chart | "Bài viết nêu dự báo ADB cho 2022 — so với giá trị GDP 2021 trên Hình 1, mức tăng tuyệt đối dự kiến là bao nhiêu?" |
| `chart_to_chart` | ≥2 chart trong cùng document, body_text là cầu nối cho biết chart nào liên quan chart nào | "Trong 2011–2021, chỉ tiêu nào tăng nhanh hơn: GDP (Hình 1) hay kim ngạch xuất nhập khẩu (Hình 3)?" |
| `fact_check_dual` | Một phát biểu trong bài, cần cả text lẫn chart để xác minh đúng/sai | "Đúng hay sai: vốn FDI tăng liên tục suốt 2011–2021?" (text mở đầu nói chung chung "biến động", chart mới cho thấy có giảm ở 2012, 2020) |

**Ngưỡng mục tiêu:** ≥50% câu hỏi ở test set thuộc 3 loại `text_to_chart`/`chart_to_chart`/`fact_check_dual` (neo theo mốc 48.74% của MultiHiertt — xem [docs/01](01-related-work.md#4b-dòng-multi-hop-qa-trên-dữ-liệu-có-cấu-trúc-text--tablechart)). Phần còn lại là `single_chart` phát sinh tự nhiên từ cùng document — không cần sourcing riêng, và đây chính là slice dùng để so sánh trực tiếp relaxed-accuracy với ChartQA/ChartQAPro.

Định nghĩa chi tiết từng loại (cả 2 chiều) + ví dụ tốt/xấu để annotator dùng khi gán nhãn nằm ở [docs/03-annotation-guidelines.md](03-annotation-guidelines.md).

## Quy trình gán nhãn (tổng quan)

Áp dụng mô hình đã kiểm chứng ở ChartQAPro (seed + VLM-assisted expansion, 9 người) và ViInfographicVQA (VLM hỗ trợ trích xuất + xác minh người), có thêm bước đọc document trước khi viết seed (khác bản đầu, vốn bắt đầu thẳng từ chart):

0. **Đọc document** — annotator đọc title + body_text trước, xác định những số liệu/claim nào chỉ có trong text (không vẽ trên chart nào) — đây là nguyên liệu bắt buộc cho câu hỏi `text_to_chart`/`fact_check_dual`.
1. **Seed thủ công** — annotator viết 2–3 câu hỏi mồi/document theo taxonomy, đảm bảo có ít nhất một câu multi-hop (`text_to_chart`, `chart_to_chart`, hoặc `fact_check_dual`) và một câu `single_chart`.
2. **Mở rộng bằng VLM** — dùng GPT-4o/Gemini/Qwen2.5-VL sinh thêm 4–6 câu hỏi ứng viên mỗi document, prompt kèm seed question + title + body_text + bảng dữ liệu gốc của từng chart làm ngữ cảnh, yêu cầu rải đều theo cả 2 chiều taxonomy.
3. **Lọc & xác minh chéo** — người thứ hai đọc **cả document** (không chỉ chart), trả lời độc lập không nhìn đáp án gốc; loại câu hỏi không thể trả lời từ document hoặc đáp án không khớp bảng dữ liệu/văn bản. Với câu multi-hop, người xác minh phải điền được `evidence` độc lập — nếu evidence không khớp giữa seed và verify, đây là dấu hiệu câu hỏi mơ hồ, đưa sang bước phân xử.
4. **Kiểm tra IAA trên mẫu** — đối chiếu độ đồng thuận trên tập con 300–500 câu mỗi đợt annotation, **tính riêng theo hop-type** (dự kiến IAA của multi-hop thấp hơn single_chart — đây là điều bình thường, không phải lỗi guideline, nhưng cần theo dõi để không tụt quá xa mốc tham chiếu: ChartQA gốc 61%/78.55%, ChartQAPro 66.17% vòng đầu — các mốc này đo trên câu hỏi single-chart nên chỉ dùng làm tham chiếu gần đúng cho slice `single_chart` của ViChartQA).

Quy trình đầy đủ, vai trò từng pod, và biểu mẫu adjudication nằm ở [docs/03-annotation-guidelines.md](03-annotation-guidelines.md).

## Trích xuất bảng dữ liệu gốc

Với mỗi chart trong document, ngoài câu hỏi–đáp án, annotator (hoặc pipeline bán tự động) cần số hoá **bảng dữ liệu gốc** (giá trị theo trục x/nhãn, theo từng chuỗi/legend). Lý do:

- Dùng làm căn cứ tự động lọc câu hỏi sai ở bước 3 trên.
- Hỗ trợ **relaxed accuracy** khi đánh giá (xem [docs/04](04-model-strategy.md#metric-đánh-giá)).
- Là tài nguyên phụ trợ cho hướng RLVR (câu trả lời số có thể so khớp tự động với dung sai) nếu nhóm mở rộng sang huấn luyện RL.

Nếu có thời gian, có thể thử áp dụng một pipeline trích xuất tự động kiểu ChartOCR (key-point detection + OCR + gán nhãn theo màu/vị trí) thay vì nhập tay hoàn toàn — nhưng với timeline 6–7 tuần, **nhập tay bởi annotator khi viết seed question là phương án mặc định an toàn hơn**.

## Quy mô mục tiêu

| | Document | Chart (ước tính, 1–3/document) | Câu hỏi |
|---|---|---|---|
| **MVP (tối thiểu)** | 1.200 | ~1.800–3.000 | 6.000 |
| **Mở rộng** | 2.000 | ~3.000–5.000 | 10.000–12.000 |

**Nhóm so sánh đổi** theo claim mới (multi-hop text+structured-data, không phải chart-only) — xem [docs/01 mục 4b](01-related-work.md#4b-dòng-multi-hop-qa-trên-dữ-liệu-có-cấu-trúc-text--tablechart):

| Dataset | Quy mô | So với MVP ViChartQA |
|---|---|---|
| TAT-QA | 2.757 context / 16.552 QA, từ 182 báo cáo | Lớn hơn, nhưng 1 context = 1 bảng+đoạn văn ngắn, không phải document nhiều chart |
| MultiHiertt | 2.513 document / 10.440 QA | Cùng cấp độ document count |
| SlideVQA | 2.600 deck / 14.500 QA | Cùng cấp độ, gần nhất về setup (nhiều ảnh/document) |

MVP 1.200 document/6.000 QA **cùng bậc quy mô** với nhóm này — không cần biện minh "nhỏ" như khi so với ChartQA gốc (20.9K chart). ChartQAPro (1.341 chart/1.948 QA) và ViInfographicVQA (6.747 ảnh/20.409 QA) vẫn là mốc tham khảo phụ cho slice `single_chart`. **Ưu tiên đạt MVP với chất lượng cao hơn là cố với quy mô mở rộng mà giảm chất lượng** — nguyên tắc này không đổi so với bản đầu.

## Chia tập train/val/test

Theo tỷ lệ tương tự ChartQA gốc (~77% / 10% / 13%), nhưng **chia theo document, không theo câu hỏi** — mọi câu hỏi (kể cả multi-hop) thuộc cùng một document phải nằm cùng một split, tránh leakage (câu hỏi ở test set vô tình dùng chart/text đã xuất hiện ở train). Tập test cần được **làm sạch thủ công hoàn toàn** (loại câu hỏi mơ hồ, sai đáp án, trùng lặp) — không dùng heuristic lọc tự động cho test set, vì đây là phần reviewer sẽ soi kỹ nhất. Riêng test set: đảm bảo tỷ lệ hop-type ≥50% multi-hop được giữ đúng sau khi làm sạch (xem [ngưỡng mục tiêu](#chiều-2--phạm-vi-bằng-chứng--hop-type-mới-claim-chính-của-dự-án)).

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
      "question": "Trong giai đoạn 2011–2021, chỉ tiêu nào tăng nhanh hơn: GDP hay kim ngạch xuất nhập khẩu?",
      "answer": "Kim ngạch xuất nhập khẩu",
      "answer_type": "text",
      "question_type": "compositional",
      "hop_type": "chart_to_chart",
      "requires_visual_reference": false,
      "evidence": [
        { "hop": 1, "source": "chart", "chart_id": "fig1", "data_point": "2011, 2021" },
        { "hop": 2, "source": "chart", "chart_id": "fig3", "data_point": "2011, 2021" }
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

Trường `chart_complexity` (`simple`/`complex`) theo đúng định nghĩa ChartQA gốc: bảng dữ liệu 2 cột = simple, nhiều cột (stacked/grouped/multi-series) = complex. Trường `evidence` bắt buộc với mọi câu hỏi có `hop_type != single_chart` (câu `single_chart` có thể để evidence rỗng hoặc 1 phần tử) — đây là phần dùng để chứng minh với reviewer rằng multi-hop là thiết kế thật, không phải nhãn dán (xem [docs/01 mục 4b](01-related-work.md#4b-dòng-multi-hop-qa-trên-dữ-liệu-có-cấu-trúc-text--tablechart)).

## Việc cần chốt trước khi crawl (Tuần 1)

Xem checklist đầy đủ ở README gốc và [docs/05](05-timeline-and-roles.md#tuần-1). Quan trọng nhất: **không crawl hàng loạt trước khi có xác nhận pháp lý cho từng nguồn** — bắt đầu từ nguồn chính phủ/mở rủi ro thấp trước, xử lý nguồn báo chí/tư nhân song song với việc xin phép.
