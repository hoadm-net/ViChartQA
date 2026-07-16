# NOTES — Ghi chú nhanh cho annotator

Bản rút gọn, dễ đọc hơn tài liệu đầy đủ ở [docs/](../docs/). Đọc file này trước khi soạn câu hỏi; khi cần chi tiết/lý do đằng sau 1 quy tắc, xem [docs/02](../docs/02-dataset-design.md) (thiết kế) hoặc [docs/03](../docs/03-annotation-guidelines.md) (hướng dẫn đầy đủ). Ví dụ thật, gán nhãn đủ 7 loại câu hỏi: [docs/05](../docs/05-annotation-examples.md).

## 1. 7 loại câu hỏi (`question_type`)

| Loại | Giải thích | Ví dụ |
|---|---|---|
| `data_retrieval` | Đọc trực tiếp 1 giá trị/nhãn có sẵn — không cần tính toán, không cần so màu/vị trí | "Tỷ lệ lạm phát năm 2024 là bao nhiêu?" |
| `visual` | Phải nhìn đặc điểm thị giác (màu, vị trí, kích thước) để xác định đối tượng, rồi mới đọc giá trị | "Cột màu xanh lam cao nhất nằm ở năm nào?" |
| `compositional` | Cần ≥2 phép toán số học/logic (cộng, trừ, so sánh, tính %...) trên các giá trị đã biết | "Chênh lệch tăng trưởng GDP giữa quý 1 và quý 3 là bao nhiêu điểm %?" |
| `visual_compositional` | Kết hợp cả `visual` lẫn `compositional` — xác định đối tượng bằng thị giác *trước*, rồi mới tính toán | "Trong các năm có cột màu xanh lá, năm nào chênh lệch với năm liền trước là lớn nhất?" |
| `multiple_choice` | Trắc nghiệm 4 lựa chọn (`choices`) — nhiễu nên dùng số liệu thật gần đúng trong document, không bịa số ngẫu nhiên | "Năm nào tăng trưởng GDP cao nhất? A. 2021 B. 2022 C. 2023 D. 2024" |
| `fact_check` | Kiểm tra đúng/sai 1 phát biểu — `answer_type: boolean`, đáp án ghi "Đúng"/"Sai" | "Đúng hay sai: doanh thu quý 4 luôn cao nhất năm?" |
| `unanswerable` | Document không đủ thông tin trả lời — `answer` ghi đúng chuỗi `"unanswerable"`, không để trống. Không quá 5-7% tổng số câu hỏi | "Nguyên nhân lạm phát tăng đột biến là gì?" (nếu document không giải thích) |

`derivation` (công thức số học thuần, vd `"8.4 - 2.5"`): bắt buộc khi `answer_type: numeric` và loại câu là `compositional`/`visual_compositional` có tính toán thật; loại khác để trống.

## 2. 4 loại hop (`hop_type`)

Tách theo đúng **1 tiêu chí**: cần đọc nguồn nào để trả lời — không liên quan tới câu hỏi tính toán hay đúng/sai (đó là việc của `question_type` ở trên).

| Loại | Giải thích | Ví dụ |
|---|---|---|
| `text` | Trả lời được chỉ từ `body_text`, không đụng chart nào | "Bài viết dự báo tăng trưởng GDP 2022 là bao nhiêu %, theo ADB?" |
| `chart` | Trả lời được chỉ từ 1 chart | "Vốn FDI năm 2020 là bao nhiêu?" |
| `text_and_chart` | Cần **cả hai** — 1 claim/số liệu chỉ có trong text, đối chiếu/tính với chart | "Bài viết nêu dự báo ADB cho 2022 — so với GDP 2021 trên Hình 1, mức tăng tuyệt đối dự kiến là bao nhiêu?" |
| `charts` | Cần **≥2 chart**, body_text (nếu có) chỉ đóng vai trò cầu nối, không mang số liệu quyết định | "Trong 2011–2021, chỉ tiêu nào tăng nhanh hơn: GDP (Hình 1) hay kim ngạch xuất nhập khẩu (Hình 3)?" |

**Cách xác định không nhầm — "phép thử bỏ nguồn":**

1. Xoá hết chart khỏi đầu, chỉ còn text → câu hỏi vẫn trả lời đủ? Nếu có → `text`.
2. Xoá hết text, chỉ còn (các) chart → câu hỏi vẫn trả lời đủ? Nếu có và chỉ cần **1** chart → `chart`; nếu cần **≥2** chart → `charts`.
3. Cả 2 phép thử trên đều **không** trả lời đủ (thiếu 1 trong 2 là bí) → `text_and_chart`.

**Lưu ý hay gặp:**

- 1 số liệu xuất hiện ở **cả** text lẫn chart (rất phổ biến, không phải lỗi) — câu hỏi ghi "theo biểu đồ" thì gán `chart`, ghi "theo bài viết" thì gán `text`; nếu không ghi rõ, mặc định `chart` vì đây là dataset chart-QA.
- `text`/`charts` vẫn có thể là câu hỏi nhiều bước (multi-hop) miễn không đụng nguồn còn lại — vd 1 câu `compositional` dùng 2 số liệu khác nhau, cả 2 đều nằm trong text, vẫn là `text`, không phải `text_and_chart`.
- Không tự ý gắn `text_and_chart`/`charts` chỉ để đạt tỷ trọng multi-hop — nếu ghép 2 chart không liên quan chủ đề để "cho đủ", câu hỏi sẽ gượng ép và annotator khác đọc sẽ thấy ngay. Không phải document nào cũng cần đủ cả 4 loại hop.
- Mục tiêu tỷ trọng: ≥50% câu hỏi thuộc `text_and_chart`/`charts` (dataset test set); còn lại `chart`/`text`.

## 3. Cách xây `evidence` theo từng hop

`evidence` bắt buộc cho **mọi** câu hỏi, kể cả `text`/`chart` (đơn nguồn) — không có bước xác minh chéo bởi người thứ 2, nên đây là chốt kiểm chứng tự động duy nhất còn lại. Mỗi hop trong `evidence` có `source: "text"` hoặc `source: "chart"`.

- **Hop nguồn `text`** → field `quote`: dán **nguyên văn** 1 đoạn ngắn từ `body_text`. Công cụ tự kiểm tra khớp chuỗi con nguyên văn — sai 1 dấu câu/khoảng trắng cũng bị chặn lưu. Không diễn giải lại, không tóm tắt.
- **Hop nguồn `chart`** → field `description`: viết **các bước đọc** đánh số thứ tự (`1. ... 2. ... 3. ...`), đủ chi tiết để người khác đọc lại (không thấy câu hỏi/đáp án trước) mà vẫn tự tìm ra đúng điểm dữ liệu trên ảnh — không diễn giải lại đáp án. Mỗi bước là 1 thao tác đọc chart cụ thể: xác định chuỗi/cột (theo tên hoặc màu) → xác định trục/mốc cần nhìn → đọc/so sánh giá trị.
  - ✅ `"1. Tìm cột doanh thu (màu xanh). 2. Tìm đường tăng trưởng (màu cam) cùng trục x. 3. Đọc giá trị 2 chuỗi tại năm 2023, so sánh."`
  - ❌ `"xem doanh thu và tăng trưởng năm 2023"` — không tách bước, không nói rõ đang nhìn chuỗi/trục nào.
  - **Luôn đọc trực tiếp trên ảnh, không suy từ lời văn mô tả chart** — text và chart thỉnh thoảng lệch nhau (bài báo viết sai số của chính chart nó đính kèm), đọc ảnh mới là chuẩn.
- **Câu `hop_type: text_and_chart`** → `evidence` có 2 hop: 1 hop `source: text` (quote) + 1 hop `source: chart` (description) — thiếu 1 trong 2 là sai.
- **Câu `hop_type: charts`** → `evidence` có ≥2 hop, tất cả `source: chart`, mỗi hop 1 `chart_id` khác nhau (fig1, fig2...).
- **Câu `hop_type: chart`/`text`** → `evidence` chỉ cần đúng 1 hop, nguồn tương ứng.

`equivalent_answers` (tuỳ chọn): các cách viết khác cũng được chấp nhận cho cùng 1 đáp án (đơn vị/cách viết số khác nhau) — chỉ điền khi thực sự có biến thể đáng kể.

## 4. Quy ước chọn & thu thập bài báo

**Chọn nguồn:**

- **Ưu tiên** trang chính thống của cơ quan/tổ chức nhà nước, uy tín (Tổng cục Thống kê, Ngân hàng Nhà nước, Bộ ngành, báo lớn có ban biên tập rõ ràng...) hơn blog/trang không rõ nguồn gốc — vừa đảm bảo số liệu đáng tin, vừa giảm rủi ro bản quyền. Xem bảng nguồn đề xuất theo domain ở [docs/02 §Nguồn dữ liệu](../docs/02-dataset-design.md#nguồn-dữ-liệu).
- **Chart phải đọc được số** — phóng to ảnh lên vẫn phải thấy rõ giá trị/nhãn/chú thích bên trong (trục, legend, số ghi trên cột/điểm...). Ảnh mờ, quá nhỏ, hoặc chụp màn hình chart bị cắt góc thì bỏ qua, không thu thập.

**Thu thập những gì (đúng thứ tự khi nhập vào công cụ):**

- **Title**: lấy nguyên văn tiêu đề bài.
- **Nội dung bài (`body_text`)**: lấy toàn văn phần nội dung chính — **không lấy đoạn mô tả/sa-pô mở đầu** (dòng tóm tắt in đậm/nghiêng ngay dưới tiêu đề, trước đoạn văn đầu tiên) và **không gồm** ảnh/video/embed khác không phải chart (ảnh minh hoạ, ảnh sự kiện, box liên quan...). Chỉ lấy phần văn xuôi.
- **Ảnh biểu đồ**: chỉ lấy ảnh chart thật (tối đa 3/document) — không lấy infographic, dashboard, hay ảnh chụp bảng số liệu thuần text (xem [docs/02 §Phạm vi](../docs/02-dataset-design.md#phạm-vi)).

**Chèn placeholder:**

- Vị trí chart xuất hiện trong bài chỉ đánh dấu bằng `[CHART 1]`, `[CHART 2]`... chèn đúng vị trí ảnh xuất hiện trong mạch bài, theo đúng thứ tự.
- **Bỏ qua alt text và caption của ảnh** (nếu bài gốc có chú thích riêng dưới ảnh) — không copy các đoạn đó vào `body_text`. `body_text` chỉ gồm placeholder + văn xuôi thật của bài, không lẫn text mô tả ảnh.

Xem ví dụ `body_text` đã chèn placeholder đúng chuẩn (2 document thật, đầy đủ) ở [docs/05](../docs/05-annotation-examples.md).

## Trước khi bấm Lưu — checklist nhanh

- [ ] `question_type` và `hop_type` đã áp dụng đúng "phép thử bỏ nguồn" ở mục 2, không đoán bừa.
- [ ] `evidence` đủ cho mọi hop — quote khớp nguyên văn (`text`) hoặc description đánh số bước đọc trực tiếp từ ảnh (`chart`).
- [ ] Không gắn `text_and_chart`/`charts` gượng ép chỉ để "cho đủ" multi-hop.
- [ ] `derivation` đã điền (và bấm "Kiểm tra derivation") nếu là `compositional`/`visual_compositional` dạng số.
- [ ] Document có tối thiểu 1 câu `hop_type: chart` + 1 câu multi-hop (`text_and_chart`/`charts`).
