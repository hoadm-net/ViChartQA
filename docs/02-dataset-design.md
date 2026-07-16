# 02 — Thiết kế bộ dữ liệu

## Phạm vi

- **Đơn vị dữ liệu:** document = `{title, body_text, charts: [1..3 ảnh]}`, lấy từ một bài viết/báo cáo thật, dưới 2.000 từ.
- **Loại ảnh chart (`chart_type`):** `bar`, `line`, `pie` (đơn — 1 loại mark, kể cả khi có stack/group nhiều chuỗi), `combo` (1 vùng vẽ trộn từ 2 loại mark trở lên, vd cột doanh thu + đường tăng trưởng, thực tế gặp rất nhiều), `subplot` (nhiều panel trong 1 ảnh) — không nhận infographic, dashboard, hay bảng số liệu thuần text.
- **Ảnh có subplot:** nếu 1 ảnh là hình ghép nhiều panel khác loại chart (vd pie cạnh bar), coi cả ảnh là **1 chart entry**, `chart_type: "subplot"` — không tách nhãn theo từng panel vì bản thân ảnh không có nhãn (a)/(b) để phân biệt, tách ra chỉ tạo id ảo mà việc đọc ảnh (kể cả model) không dùng được.
- **`body_text` là toàn văn bài báo** (không cắt đoạn) — vì có câu hỏi chỉ dựa vào thông tin trong text mà không chart nào vẽ ra (`hop_type: "text"`), cắt bớt sẽ mất nguyên liệu cho cả loại đó lẫn `text_and_chart`. Bỏ hẳn phần bài không liên quan tới chủ đề đang khai thác. Chèn placeholder `[CHART 1]`, `[CHART 2]`... vào đúng vị trí từng chart xuất hiện trong bài, theo đúng thứ tự — vừa neo chart vào đúng mạch bài (khỏi cần tách nhãn subplot), vừa là quy ước duy nhất nối `body_text` với `charts[]` theo thứ tự.
- **Ngôn ngữ:** tiêu đề, body_text, nhãn/chú thích trên chart phải là tiếng Việt gốc (không dịch từ tiếng Anh).
- **Miền:** mở rộng theo nguồn cung thực tế, không ép cứng tỷ lệ.

## Miền dữ liệu

**Kinh tế là miền neo, nguồn dồi dào** — thể loại "title + phân tích + 1-3 chart" lặp lại định kỳ trên báo kinh tế tiếng Việt (CafeF; consosukien.vn — tạp chí chính thức Tổng cục Thống kê). Chủ đề: GDP/tăng trưởng, CPI/lạm phát, xuất nhập khẩu, thị trường lao động, ngân sách nhà nước, chứng khoán, FDI.

**Khoa học và miền khác (giáo dục, y tế, môi trường, năng lượng, xã hội) là miền mở rộng** — ưu tiên báo cáo thường niên chính phủ (Bộ KH&CN, NASATI, báo cáo môi trường quốc gia, EVN/Bộ Công thương, Bộ Y tế) hơn báo phổ biến khoa học (Tia Sáng nghiêng bài chính sách/bình luận, ít data-journalism). Tỷ trọng domain do nguồn cung quyết định.

**Trước khi crawl diện rộng:** lấy mẫu ~30-50 document/domain, đếm tỷ lệ đạt tiêu chí (≥1 đoạn văn bình luận trực tiếp vào số liệu chart) trước khi chốt tỷ trọng domain.

## Nguồn dữ liệu

| Miền | Nguồn đề xuất | Lưu ý pháp lý |
|---|---|---|
| Kinh tế | Tổng cục Thống kê (gso.gov.vn, consosukien.vn), Ngân hàng Nhà nước, Bộ Tài chính, ấn bản tiếng Việt World Bank/IMF | Dữ liệu/ấn phẩm nhà nước — rủi ro bản quyền thấp, cần trích dẫn nguồn đầy đủ |
| Kinh tế | VnEconomy, CafeF, Vietnam Report, báo cáo thường niên doanh nghiệp niêm yết | Cần rà soát điều khoản sử dụng cả text lẫn hình ảnh; cân nhắc tự vẽ lại chart từ số liệu công bố nếu ảnh gốc có bản quyền |
| Khoa học/khác | Báo cáo thường niên Bộ KH&CN, NASATI, báo cáo môi trường quốc gia, EVN/Bộ Công thương, Bộ Y tế | Ấn phẩm công, thường cho phép phi thương mại — vẫn nên xin phép bằng văn bản |
| Khoa học/khác (dự phòng) | Tia Sáng, Khoa học & Phát triển | Cần liên hệ toà soạn xin phép trước khi crawl số lượng lớn; xác nhận số lượng bài đủ multi-chart trước khi coi là nguồn chính |

**Data Statement:** mỗi nguồn ghi rõ điều khoản sử dụng, ngày truy cập, phạm vi cho phép — cho cả text lẫn ảnh. Chuẩn bị từ Tuần 1 (theo dõi ở tài liệu riêng, không phải field trong tool — công cụ không lưu license per-document).

**Tránh:** SGK/tài liệu giáo dục có bản quyền NXB Giáo dục rõ ràng.

## Taxonomy câu hỏi

Hai chiều độc lập, mỗi câu hỏi gán nhãn cả hai.

### Chiều 1 — loại suy luận

`question_type`, enum 7 giá trị lá:

| Nhóm | `question_type` | Mô tả | Ví dụ | Tỷ trọng mục tiêu |
|---|---|---|---|---|
| Truy vấn dữ liệu | `data_retrieval` | Đọc trực tiếp một giá trị/nhãn | "Tỷ lệ lạm phát năm 2024 là bao nhiêu?" | ~15% |
| Thị giác | `visual` | Tham chiếu màu sắc, vị trí, kích thước | "Cột màu xanh lam cao nhất nằm ở năm nào?" | ~15% |
| Suy luận kết hợp | `compositional` | ≥2 phép toán số học/logic | "Chênh lệch tăng trưởng GDP giữa quý 1 và quý 3 là bao nhiêu điểm %?" | ~30% |
| Thị giác + suy luận | `visual_compositional` | Kết hợp cả hai | "Trong các năm có cột màu xanh lá, năm nào chênh lệch với năm liền trước là lớn nhất?" | ~20% |
| Mở rộng | `multiple_choice` | Trắc nghiệm 4 đáp án (`choices`) | "Năm nào tăng trưởng GDP cao nhất? A. 2021 B. 2022 C. 2023 D. 2024" | ~20% (gộp 3 loại) |
| Mở rộng | `fact_check` | Kiểm tra đúng/sai một phát biểu | "Đúng hay sai: doanh thu quý 4 luôn cao nhất năm?" | nt. |
| Mở rộng | `unanswerable` | Không trả lời được từ document | "Nguyên nhân lạm phát tăng đột biến là gì?" | nt. |

### Chiều 2 — phạm vi bằng chứng / hop-type (mới, claim chính của dự án)

Tách theo đúng 1 tiêu chí duy nhất — cần đọc nguồn nào để trả lời — không trộn với dạng câu trả lời (đúng/sai hay tính toán, việc đó đã thuộc `question_type`):

| Hop-type | Mô tả | Ví dụ |
|---|---|---|
| `text` | Trả lời được chỉ từ body_text, không cần chart nào | "Bài viết dự báo tăng trưởng GDP 2022 là bao nhiêu %, theo ADB?" |
| `chart` | Trả lời được chỉ từ 1 chart | "Vốn FDI năm 2020 là bao nhiêu?" |
| `text_and_chart` | Cần cả body_text lẫn 1 chart kết hợp — vd 1 claim/số liệu chỉ có trong text, đối chiếu/tính toán với chart; hoặc xác minh 1 phát biểu đúng/sai cần cả 2 nguồn | "Bài viết nêu dự báo ADB cho 2022 — so với GDP 2021 trên Hình 1, mức tăng tuyệt đối dự kiến là bao nhiêu?" / "Đúng hay sai: vốn FDI tăng liên tục suốt 2011–2021?" |
| `charts` | ≥2 chart, body_text là cầu nối | "Trong 2011–2021, chỉ tiêu nào tăng nhanh hơn: GDP (Hình 1) hay kim ngạch xuất nhập khẩu (Hình 3)?" |

Ngưỡng mục tiêu: ≥50% câu hỏi test set thuộc 2 loại multi-hop (`text_and_chart`/`charts`, neo theo mốc 48.74% của MultiHiertt — [docs/01](01-related-work.md#4b-dòng-multi-hop-qa-trên-dữ-liệu-có-cấu-trúc-text--tablechart)). Phần còn lại là `chart`/`text`, trong đó `chart` dùng để so sánh trực tiếp với ChartQA/ChartQAPro.

Ví dụ tốt/xấu chi tiết ở [docs/03](03-annotation-guidelines.md); 2 document thật gán nhãn đầy đủ (cả 7 `question_type`) ở [docs/05](05-annotation-examples.md).

## Quy trình gán nhãn (tổng quan)

1. **Đọc document** — xác định số liệu/claim chỉ có trong text, không vẽ trên chart nào (nguyên liệu cho `text`/`text_and_chart`).
2. **Soạn câu hỏi** — gợi ý bằng LLM (chỉ câu hỏi + đáp án, không sinh `evidence`, chỉ tham khảo, không tự lưu) + tự viết/sửa qua form, tối thiểu 1 multi-hop + 1 `chart`/document. `evidence` luôn do annotator tự đọc chart/text rồi điền tay — kể cả câu hỏi bắt nguồn từ gợi ý LLM — công cụ chặn lưu nếu thiếu/sai.
3. **Sửa/rút khi cần** — không có bước xác minh chéo độc lập; mỗi lần tạo/sửa/rút một câu hỏi được ghi lại thành một bản snapshot (version history) làm audit trail.

Quy trình đầy đủ ở [docs/03](03-annotation-guidelines.md).

## Quy mô mục tiêu

| | Document | Chart (ước tính, 1–3/document) | Câu hỏi |
|---|---|---|---|
| **MVP** | 1.200 | ~1.800–3.000 | 6.000 |
| **Mở rộng** | 2.000 | ~3.000 | ~15.000 |

Nhóm so sánh (multi-hop text+structured-data):

| Dataset | Quy mô |
|---|---|
| TAT-QA | 2.757 context / 16.552 QA |
| MultiHiertt | 2.513 document / 10.440 QA |
| SlideVQA | 2.600 deck / 14.500 QA |

MVP 1.200 document/6.000 QA cùng bậc quy mô với nhóm này. ChartQAPro (1.341/1.948) và ViInfographicVQA (6.747/20.409) là mốc tham khảo phụ cho slice `chart`. Ưu tiên đạt MVP với chất lượng cao hơn cố quy mô mở rộng mà giảm chất lượng.

## Chia tập train/val/test

Tỷ lệ ~77%/10%/13% (như ChartQA gốc), chia theo document (không theo câu hỏi) để tránh leakage. Test set làm sạch thủ công hoàn toàn, không dùng heuristic tự động. Giữ tỷ lệ hop-type ≥50% multi-hop sau khi làm sạch.

## Schema dữ liệu đề xuất

Đơn vị lưu trữ là **document**: một title + body_text (toàn văn, có placeholder `[CHART N]`) + 1–3 chart, mang nhiều câu hỏi (mảng `qa`). Mỗi câu hỏi tự khai báo `hop_type` và `evidence`.

```json
{
  "id": "vichartqa_econ_00123",
  "title": "Trend 10 năm với kinh tế Việt Nam: Nền kinh tế đã trưởng thành hơn ra sao?",
  "body_text": "Nhìn chung GDP trong 10 năm qua tăng dần theo thời gian. [CHART 1] Bên cạnh đó, dòng vốn FDI và kim ngạch xuất nhập khẩu cũng ghi nhận xu hướng tích cực dù có biến động ở một số năm. [CHART 2]",
  "source": {
    "provider": "CafeF",
    "domain": "economics",
    "url": "https://cafef.vn/...",
    "accessed_date": "2026-07-20"
  },
  "charts": [
    { "chart_id": "fig1", "image": "images/a3f5c1d8e2b04f91.png", "chart_type": "line" },
    { "chart_id": "fig2", "image": "images/9b1e7a04cc3d5f22.png", "chart_type": "subplot" }
  ],
  "qa": [
    {
      "id": "q1",
      "question": "Trong giai đoạn 2011–2021, chỉ tiêu nào tăng nhanh hơn: GDP hay kim ngạch xuất nhập khẩu?",
      "answer": "Kim ngạch xuất nhập khẩu",
      "equivalent_answers": [],
      "answer_type": "text",
      "question_type": "compositional",
      "hop_type": "charts",
      "derivation": "",
      "choices": null,
      "evidence": [
        { "hop": 1, "source": "chart", "chart_id": "fig1", "description": "1. Tìm đường \"GDP\". 2. Đọc giá trị trục y tại năm 2011 và 2021." },
        { "hop": 2, "source": "chart", "chart_id": "fig2", "description": "1. Tìm đường \"Xuất nhập khẩu\". 2. Đọc giá trị trục y tại năm 2011 và 2021." }
      ]
    },
    {
      "id": "q2",
      "question": "GDP năm 2021 tăng bao nhiêu triệu tỷ đồng so với năm 2011?",
      "answer": "5.9",
      "equivalent_answers": ["5,9"],
      "answer_type": "numeric",
      "question_type": "compositional",
      "hop_type": "chart",
      "derivation": "8.4 - 2.5",
      "choices": null,
      "evidence": [
        { "hop": 1, "source": "chart", "chart_id": "fig1", "description": "1. Tìm đường \"GDP\". 2. Đọc giá trị trục y tại năm 2011 và 2021." }
      ]
    },
    {
      "id": "q3",
      "question": "Năm nào GDP tăng trưởng cao nhất trong giai đoạn 2011–2021?",
      "answer": "2021",
      "equivalent_answers": [],
      "answer_type": "text",
      "question_type": "multiple_choice",
      "hop_type": "chart",
      "derivation": "",
      "choices": ["2015", "2018", "2019", "2021"],
      "evidence": [
        { "hop": 1, "source": "chart", "chart_id": "fig1", "description": "1. Tìm đường \"GDP\". 2. So sánh độ dốc giữa các năm liên tiếp từ 2011 đến 2021, xác định năm có mức tăng lớn nhất." }
      ]
    },
    {
      "id": "q4",
      "question": "Theo bài viết, xu hướng chung của dòng vốn FDI và kim ngạch xuất nhập khẩu trong giai đoạn này là gì?",
      "answer": "Tích cực dù có biến động ở một số năm",
      "equivalent_answers": [],
      "answer_type": "text",
      "question_type": "data_retrieval",
      "hop_type": "text",
      "derivation": "",
      "choices": null,
      "evidence": [
        { "hop": 1, "source": "text", "quote": "dòng vốn FDI và kim ngạch xuất nhập khẩu cũng ghi nhận xu hướng tích cực dù có biến động ở một số năm" }
      ]
    }
  ],
  "split": "train"
}
```

`evidence` bắt buộc với **mọi** câu hỏi (không riêng multi-hop) — không có bước xác minh chéo độc lập nên đây là chốt kiểm chứng còn lại. `equivalent_answers`: danh sách rỗng nếu không có biến thể nào khác được chấp nhận.

`derivation`: bắt buộc khi `answer_type: numeric` và `question_type` là `compositional`/`visual_compositional` có tính toán — công thức số học thuần dùng đúng số annotator đọc được từ chart (vd. `"8.4 - 2.5"`), trống `""` với loại còn lại. Dùng để đối chiếu tự động với `answer` lúc soạn.

### Định dạng `evidence`

- `source: "chart"` → `{chart_id, description}` — `description` là các bước truy hồi giá trị trên ảnh, annotator gõ tay trực tiếp (xem quy ước bên dưới). Không có bảng dữ liệu gốc để đối chiếu tự động — chỉ kiểm tra `chart_id` có tồn tại trong document và `description` không để trống.
- `source: "text"` → `{quote}`, đoạn trích nguyên văn ngắn từ `body_text` — vẫn auto-check được (phải khớp chuỗi con nguyên văn trong `body_text`).

**Quy ước viết `description`:** đánh số từng bước (`1. ... 2. ... 3. ...`), đủ chi tiết để người khác đọc lại (không nhìn câu hỏi/đáp án trước) mà vẫn tự tìm ra đúng điểm dữ liệu trên ảnh — không diễn giải lại đáp án. Mỗi bước nêu **một thao tác đọc chart cụ thể**: xác định chuỗi/cột theo tên hoặc màu → xác định trục/mốc cần nhìn → đọc hoặc so sánh giá trị. Chart càng phức tạp (combo, subplot, nhiều chuỗi chồng nhau) càng cần tách bước rõ ràng thay vì gộp chung 1 câu mơ hồ.

- ✅ `"1. Tìm cột doanh thu (màu xanh) trong biểu đồ combo. 2. Tìm đường tăng trưởng (màu cam) cùng trục x. 3. Đọc giá trị 2 chuỗi tại năm 2023, so sánh."`
- ❌ `"xem doanh thu và tăng trưởng năm 2023"` — không tách bước, không nói rõ đang nhìn chuỗi/trục nào, người đọc lại không tái lập được thao tác.

## Việc cần chốt trước khi crawl

Không crawl hàng loạt trước khi có xác nhận pháp lý cho từng nguồn.
