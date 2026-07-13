# 08 — Thiết kế công cụ gán nhãn

Dựa trên schema/quy trình ở [docs/02](02-dataset-design.md) và [docs/03](03-annotation-guidelines.md) (đơn vị = document: title + body_text + 1-3 chart, taxonomy 2 chiều, evidence trỏ vào `data_table`/`body_text`).

Đã chốt: tự host trên server/VPS sẵn có, Streamlit + SQLite; taxonomy "Mở rộng" tách enum riêng + `follow_up_of`; quản lý dự án trực tiếp build.

## 1. Yêu cầu chức năng

Label Studio/Argilla/doccano/Prodigy giả định 1 task = 1 input, gán vài nhãn/span. Thiết kế này khác ở 3 điểm: (1) Bước 0 nhập `data_table` phải hoàn tất trước, các bước sau tham chiếu ngược lại (dropdown evidence chỉ hiện giá trị đã có trong `data_table`); (2) 1 document nhiều câu hỏi, mỗi câu có trường điều kiện (`derivation`, `evidence` tuỳ `hop_type`/`answer_type`); (3) xác minh chéo mù có auto-diff quyết định `verified`/`needs_adjudication`.

| # | Chức năng | Nguồn |
|---|---|---|
| 1 | Nạp document (title, body_text, ảnh 1-3 chart, metadata nguồn) | [docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất) |
| 2 | Bảng nhập `data_table`/chart (x_axis + series), kèm ảnh chart | Bước 0, [docs/03](03-annotation-guidelines.md#bước-0--đọc-document) |
| 3 | Form câu hỏi: `question_type` (8 giá trị) × `hop_type` (4 loại) | [docs/02](02-dataset-design.md#taxonomy-câu-hỏi) |
| 4 | Evidence builder: chart → `series`+`x` (dropdown từ `data_table`); text → dán `quote` | [docs/02](02-dataset-design.md#định-dạng-evidence--tham-chiếu-bằng-label-không-mô-tả-tự-do) |
| 5 | Auto-check evidence khớp `data_table`/`body_text`, chặn submit nếu không khớp | nt. |
| 6 | `derivation` hiện có điều kiện, auto-eval và so `answer` (dung sai 5%) | [docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất) |
| 7 | Nút "Sinh câu hỏi bằng VLM" (GPT-4o/Gemini/Qwen2.5-VL), annotator duyệt từng câu | Bước 2 |
| 8 | Xác minh chéo mù: verifier không thấy đáp án gốc, hệ thống tự so khớp → `verified`/`needs_adjudication` | Bước 3 |
| 9 | Phân xử: song song 2 bản, leader Pod C quyết định + ghi log | [docs/03](03-annotation-guidelines.md#cơ-chế-phân-xử-adjudication) |
| 10 | IAA + đồng thuận (exact/lexical), tách theo `hop_type` | Bước 4 |
| 11 | Dashboard: trạng thái, tỷ trọng taxonomy thực tế vs mục tiêu, năng suất annotator | [docs/02](02-dataset-design.md#chiều-2--phạm-vi-bằng-chứng--hop-type-mới-claim-chính-của-dự-án) |
| 12 | Chặn nộp batch nếu thiếu ≥1 `single_chart` + 1 multi-hop/document | [docs/03](03-annotation-guidelines.md#checklist-nhanh-trước-khi-nộp-một-batch) |
| 13 | Export JSON theo schema, chia theo document | [docs/02](02-dataset-design.md#chia-tập-trainvaltest) |

## 2. Platform

| Tiêu chí | Label Studio/Argilla | Streamlit | React + API riêng |
|---|---|---|---|
| Evidence dropdown động theo `data_table` | Cần Frontend plugin riêng | `st.selectbox` nạp trực tiếp | Cần tự viết component |
| Bảng nhập `data_table` | Không có primitive phù hợp | `st.data_editor` | Cần thư viện ngoài (AG Grid) |
| Form điều kiện | Labeling config tĩnh | Python `if` | Được, tốn công hơn |
| Xác minh mù + auto-diff | Tự viết | Tự viết, thuần Python | Tự viết |
| Tốc độ dựng bản dùng được | Chậm | 2-3 ngày | Chậm hơn Streamlit |
| Kỹ năng cần | Python + API/plugin LS | Chỉ Python | Cần JS/React |
| Multi-user, review workflow có sẵn | Có | Không, tự làm | Không |

**Streamlit + SQLite, không dùng Label Studio.** 10 người đã biết Python; `st.data_editor` giải quyết gọn nhập `data_table`; dựng được bản chạy trong 2-3 ngày, kịp pilot cuối Tuần 1.

## 3. Kiến trúc

```
Streamlit (multi-page app, st.navigation)
        │
        ├── page: Nhập document
        ├── page: Nhập data_table cho chart (Bước 0)
        ├── page: Viết seed + Evidence builder (Bước 1)
        ├── page: Sinh & duyệt ứng viên VLM (Bước 2)
        ├── page: Xác minh chéo mù (Bước 3)
        ├── page: Phân xử (Adjudication)
        ├── page: Dashboard IAA & tiến độ
        └── page: Export dataset
        │
   validation.py  (Python thuần, không import Streamlit)
        │
   SQLAlchemy models  ──►  SQLite (1 file .db, WAL mode — mục 3.2)
        │
   vlm_client.py (GPT-4o/Gemini/Qwen2.5-VL, key qua st.secrets)
```

Validation logic (evidence khớp `data_table`, auto-eval `derivation`, kiểm tra tối thiểu taxonomy/document) viết trong `validation.py`, tách khỏi Streamlit — tái dùng được cho script export/làm sạch dữ liệu ở Tuần 5.

### 3.1 Data model

| Bảng | Cột chính | Ghi chú |
|---|---|---|
| `documents` | id, title, body_text, source_* (provider/domain/topic/license/url/accessed_date), split, status | `status`: intake → data_table_done → seeded → vlm_expanded → verifying → qc_done → ready_for_split |
| `charts` | id, document_id (fk), chart_id, image_path, chart_type, chart_complexity, topic, data_table (JSON) | 1-3 dòng/document |
| `questions` | id, document_id (fk), question_text, answer, answer_type, question_type, hop_type, requires_visual_reference, derivation, follow_up_of (fk questions), choices (JSON), status, generation_method, seed_by (fk user), verified_by (fk user) | `status`: seed → vlm_candidate → pending_verification → verified/needs_adjudication → final/rejected. `question_type`: `data_retrieval`, `visual`, `compositional`, `visual_compositional`, `multiple_choice`, `hypothetical`, `fact_check`, `unanswerable` |
| `evidence` | id, question_id (fk), hop_order, source (chart/text), chart_id (fk), series, x (JSON array), quote | 0-N dòng/câu hỏi |
| `verification_attempts` | id, question_id (fk), verifier_id (fk), answer_given, evidence_given (JSON), match (bool) | Dùng tính IAA |
| `iaa_samples` | id, question_id (fk), round_label, agreement_exact, agreement_lexical, evidence_match | |
| `adjudications` | id, question_id (fk), issue_note, decision, decided_by (fk), decided_at | |
| `users` | id, name, pod (A-E), role, password_hash | |

`data_table` và `choices` dùng kiểu `sqlalchemy.JSON` (không cột TEXT tự parse) — code không phụ thuộc SQLite hay Postgres.

### 3.2 SQLite

```python
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
```

Chỉ 1 tiến trình Streamlit ghi vào file `.db`. Backup: cron hằng ngày `sqlite3 vichartqa.db ".backup vichartqa-$(date +%F).db"`, đẩy sang nơi khác server.

### 3.3 Vòng đời câu hỏi

```
seed ──(VLM sinh: vlm_candidate → annotator duyệt)──► pending_verification
                                                              │
                                                 verifier trả lời mù
                                                              │
                             ┌────────────────────────────────┴───────────────────────┐
                       answer+evidence khớp                                answer/evidence lệch
                             │                                                          │
                         verified                                            needs_adjudication
                             │                                                          │
                             └──────────────────► final ◄─────────── adjudicator quyết định ─┘
                                                                        (hoặc → rejected)
```

## 4. Màn hình theo vai trò

### 4.1 Nhập `data_table` (Bước 0 — Pod B)

- Trái: ảnh chart (`st.image`, zoom).
- Phải: `st.data_editor` — `x_axis` + N cột series (thêm/xoá cột = thêm/xoá series). Header cột là tên dùng nguyên văn trong `evidence.series` sau này.
- Nút lưu → khi đủ 1-3 chart, `documents.status → data_table_done`.

### 4.2 Viết seed + Evidence builder (Bước 1 — Pod B)

- Trái (cố định): title + body_text + thumbnail 1-3 chart (click phóng to).
- Phải: danh sách câu hỏi đã có + form thêm câu mới:
  - `question_text`, `answer`.
  - `answer_type` (numeric/text/unanswerable/boolean); trắc nghiệm suy ra tự động từ `question_type=multiple_choice`.
  - `question_type` (8 giá trị). Chọn `multiple_choice` → hiện 4 ô `choices`.
  - `follow_up_of` (không bắt buộc) — dropdown câu đã có trong document.
  - `hop_type` (4 loại) — khác `single_chart` → hiện evidence builder.
  - Evidence builder: `source` (chart/text); chart → `chart_id` + `series` (dropdown từ `data_table`) + multi-select `x`; text → dán `quote`.
  - `derivation`: hiện khi `answer_type=numeric` và `question_type` thuộc {compositional, visual_compositional}. Nút "Kiểm tra" eval công thức, so `answer`, báo ✅/⚠️ (không chặn submit).
  - Submit → `validation.py`: chặn cứng nếu evidence không khớp; cảnh báo mềm nếu derivation lệch hoặc trùng câu hỏi.
- Cảnh báo nếu document chưa đủ 1 `single_chart` + 1 multi-hop.

### 4.3 Sinh & duyệt ứng viên VLM (Bước 2 — Pod B)

- Nút "Sinh 4-6 câu ứng viên" — gọi `vlm_client.py` với title+body_text+data_table+seed, chọn model qua dropdown.
- Kết quả dạng thẻ: Sửa (mở form 4.2, điền sẵn) / Giữ / Bỏ. Evidence do VLM đề xuất phải xác nhận lại qua UI 4.2, không copy thẳng.

### 4.4 Xác minh chéo mù (Bước 3 — Pod C, người khác)

- Giao document + câu hỏi (không kèm đáp án/evidence gốc) cho verifier khác người viết seed.
- Verifier trả lời + điền evidence qua UI 4.2, không thấy đáp án gốc.
- Submit → so khớp answer + evidence → `verified`/`needs_adjudication`, hiển thị kết quả ngay (không sửa được).

### 4.5 Phân xử (Pod C leader)

- 2 cột song song (bản gốc vs verify), highlight khác biệt.
- 3 nút quyết định (giữ gốc/giữ verify/chỉnh sửa) + ô ghi lý do bắt buộc.

### 4.6 Dashboard (Pod C + Pod E)

- Document/câu hỏi theo `status`.
- Tỷ trọng `question_type`/`hop_type` thực tế vs mục tiêu.
- IAA theo đợt, tách theo `hop_type`.
- Năng suất theo annotator/pod.

### 4.7 Export

Script cuối Tuần 5: join `documents`+`charts`+`questions`+`evidence` thành JSON theo [docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất), chỉ lấy `status=final`, gán `split` theo document.

## 5. Hạ tầng

- SQLite: 1 file `.db` trên volume server, WAL + busy_timeout.
- Streamlit: `streamlit run` trên server (hoặc 1 container Docker), sau reverse proxy (Nginx/Caddy).
- Backup: cron `sqlite3 ... .backup` hằng ngày, đẩy sang nơi khác server.
- Ảnh chart: ổ đĩa/volume server, cùng lịch backup với SQLite.
- Auth: 10-15 tài khoản tạo tay, `streamlit-authenticator` hoặc session login tự viết.
- API key VLM: `st.secrets` (`secrets.toml` không commit git).

## 6. Khi nào migrate khỏi Streamlit

Chỉ cân nhắc nếu: (a) độ trễ rerun gây khó chịu rõ rệt với 5+ người dùng cùng lúc; (b) cần tương tác Streamlit không hỗ trợ tốt (vd vẽ bounding box lên ảnh — thiết kế hiện tại không cần, evidence là dropdown không phải toạ độ pixel); (c) mở annotation quy mô lớn ngoài nhóm sau dự án.

## 7. Trạng thái quyết định

1. Hạ tầng: tự host, SQLite — mục 3.2 và 5.
2. Taxonomy: `question_type` 8 giá trị lá + `follow_up_of` + `choices` — mục 3.1, 4.2, đồng bộ [docs/02](02-dataset-design.md#taxonomy-câu-hỏi) + [docs/03](03-annotation-guidelines.md#5-mở-rộng-kiểu-chartqapro).
3. Người build: quản lý dự án.

Có thể bắt đầu scaffold code: SQLAlchemy models (3.1), `validation.py`, khung Streamlit multi-page (3).
