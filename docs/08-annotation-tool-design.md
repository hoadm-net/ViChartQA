# 08 — Thiết kế công cụ gán nhãn

Dựa trên schema/quy trình ở [docs/02](02-dataset-design.md) và [docs/03](03-annotation-guidelines.md) (đơn vị = document: title + body_text + 1-3 chart, taxonomy 2 chiều, evidence chart tự do do annotator gõ tay, evidence text trỏ vào `body_text`).

Đã chốt: tự host trên server/VPS sẵn có, Streamlit + SQLite; taxonomy "Mở rộng" tách enum riêng; quản lý dự án trực tiếp build.

## 1. Yêu cầu chức năng

Label Studio/Argilla/doccano/Prodigy giả định 1 task = 1 input, gán vài nhãn/span. Thiết kế này khác ở 3 điểm: (1) 1 document nhiều câu hỏi, mỗi câu có trường điều kiện (`derivation`, `evidence` tuỳ `hop_type`/`answer_type`); (2) evidence không có bảng dữ liệu gốc để tra cứu — `series`/`x` là annotator tự gõ mô tả những gì họ nhìn thấy trên chart; (3) không có bước xác minh chéo độc lập — mỗi lần tạo/sửa/rút một câu hỏi ghi thành 1 bản snapshot (`question_versions`) làm audit trail thay thế.

| # | Chức năng | Nguồn |
|---|---|---|
| 1 | Nạp document (title, body_text, ảnh 1-3 chart, metadata nguồn) | [docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất) |
| 2 | Form câu hỏi: `question_type` (8 giá trị) × `hop_type` (4 loại) + `equivalent_answers` tuỳ chọn | [docs/02](02-dataset-design.md#taxonomy-câu-hỏi) |
| 3 | Evidence builder: chart → chọn `chart_id` + gõ tay `series`+`x`; text → dán `quote` | [docs/02](02-dataset-design.md#định-dạng-evidence) |
| 4 | Auto-check evidence không rỗng + quote khớp `body_text`, chặn submit nếu không đạt — bắt buộc cho mọi câu hỏi | nt. |
| 5 | `derivation` hiện có điều kiện, auto-eval và so `answer` (dung sai 5%) | [docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất) |
| 6 | Nút "Sinh gợi ý bằng LLM" — chỉ hiển thị tham khảo, "Dùng làm mẫu" nạp vào form chứ không tự lưu | [docs/03](03-annotation-guidelines.md) |
| 7 | Sửa/rút câu hỏi bất kỳ lúc nào; mỗi lần tạo/sửa/rút ghi 1 `question_versions` snapshot | mục 3.3 |
| 8 | Dashboard: trạng thái, tỷ trọng taxonomy thực tế vs mục tiêu, năng suất annotator | [docs/02](02-dataset-design.md#chiều-2--phạm-vi-bằng-chứng--hop-type-mới-claim-chính-của-dự-án) |
| 9 | Chặn nộp batch nếu thiếu ≥1 `single_chart` + 1 multi-hop/document | [docs/03](03-annotation-guidelines.md#checklist-nhanh-trước-khi-nộp-một-batch) |
| 10 | Export JSON theo schema, chia theo document | [docs/02](02-dataset-design.md#chia-tập-trainvaltest) |

## 2. Platform

| Tiêu chí | Label Studio/Argilla | Streamlit | React + API riêng |
|---|---|---|---|
| Form điều kiện | Labeling config tĩnh | Python `if` | Được, tốn công hơn |
| Version history/edit log | Tự viết | Tự viết, thuần Python (`versioning.py`) | Tự viết |
| Tốc độ dựng bản dùng được | Chậm | 2-3 ngày | Chậm hơn Streamlit |
| Kỹ năng cần | Python + API/plugin LS | Chỉ Python | Cần JS/React |
| Multi-user, review workflow có sẵn | Có | Không, tự làm | Không |

**Streamlit + SQLite, không dùng Label Studio.** 10 người đã biết Python; dựng được bản chạy trong 2-3 ngày, kịp pilot cuối Tuần 1.

## 3. Kiến trúc

```
Streamlit (multi-page app, st.navigation)
        │
        ├── page: Nhập document
        ├── page: Soạn câu hỏi (gợi ý LLM + form + lịch sử)
        ├── page: Dashboard tiến độ
        └── page: Export dataset
        │
   validation.py  (Python thuần, không import Streamlit)
   versioning.py  (Python thuần — snapshot_question/record_version)
   question_ui.py (Streamlit — form/evidence-builder dùng chung)
        │
   SQLAlchemy models  ──►  SQLite (1 file .db, WAL mode — mục 3.2)
        │
   vlm_client.py (OpenRouter, key qua st.secrets — gợi ý tham khảo, không tự lưu)
```

Validation logic (evidence không rỗng + quote khớp `body_text`, auto-eval `derivation`, kiểm tra tối thiểu taxonomy/document) viết trong `validation.py`, tách khỏi Streamlit — tái dùng được cho script export/làm sạch dữ liệu ở Tuần 5.

### 3.1 Data model

| Bảng | Cột chính | Ghi chú |
|---|---|---|
| `documents` | id, title, body_text, source_* (provider/domain/url/accessed_date), split, status | `status`: intake → in_progress (thuần thông tin, không chặn thao tác nào) |
| `charts` | id, document_id (fk), chart_id, image_path, chart_type, chart_complexity | 1-3 dòng/document, không có bảng dữ liệu gốc |
| `questions` | id, document_id (fk), question_text, answer, equivalent_answers (JSON), answer_type, question_type, hop_type, derivation, choices (JSON), status, created_by (fk user) | `status`: active/rejected. `question_type`: `data_retrieval`, `visual`, `compositional`, `visual_compositional`, `multiple_choice`, `hypothetical`, `fact_check`, `unanswerable` |
| `evidence` | id, question_id (fk), hop_order, source (chart/text), chart_id (fk), series, x (JSON array), quote | 1-N dòng/câu hỏi — bắt buộc với mọi câu. `series`/`x` là text tự do annotator gõ tay khi source=chart |
| `question_versions` | id, question_id (fk), version_number, snapshot (JSON — toàn bộ question+evidence), change_type (created/edited/rejected), change_note, edited_by (fk user), edited_at | Ghi 1 dòng mỗi lần tạo/sửa/rút — thay cho verification_attempts/adjudications đã bỏ |
| `users` | id, name, pod (A-E), role, password_hash | `role`: annotator/pm/data_intake |

`choices`, `equivalent_answers`, `x`, `snapshot` dùng kiểu `sqlalchemy.JSON` (không cột TEXT tự parse) — code không phụ thuộc SQLite hay Postgres.

### 3.2 SQLite

```python
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
```

Chỉ 1 tiến trình Streamlit ghi vào file `.db`. Backup: cron hằng ngày `sqlite3 vichartqa.db ".backup vichartqa-$(date +%F).db"`, đẩy sang nơi khác server.

### 3.3 Vòng đời câu hỏi

```
(gợi ý LLM — tạm thời, chỉ trong session, không phải 1 status)
         │ "Dùng làm mẫu" nạp vào form, KHÔNG tự lưu
         ▼
     [form soạn câu hỏi] ──Lưu──► active ──Bỏ──► rejected
                                     │
                                     └──Sửa──► active (bản mới, version_number+1)
```

Mỗi lần vào ô "Lưu"/"Sửa"/"Bỏ" ghi 1 dòng `question_versions` (`change_type = created/edited/rejected`) — không sửa/xoá dòng cũ, nên lịch sử đầy đủ luôn xem lại được ngay trên trang.

## 4. Màn hình theo vai trò

### 4.1 Nhập document (Pod A)

- Title + toàn văn body_text (`[CHART N]` placeholder) + tối đa 3 ảnh chart, tự đặt tên theo hash + preview.
- Metadata nguồn (provider/domain/url), ngày truy cập tự động = hôm nay.

### 4.2 Soạn câu hỏi (Pod B) — trang duy nhất sau intake

- Trên: chọn document, xem lại title/body_text/ảnh chart.
- "Gợi ý câu hỏi bằng LLM": chọn model (qua `vlm_client.py`/OpenRouter) + số câu, bấm sinh. Kết quả chỉ hiển thị tham khảo (không lưu DB); nút "Dùng làm mẫu" nạp nội dung vào form soạn câu hỏi bên dưới, annotator vẫn phải tự rà và bấm Lưu.
- "Câu hỏi đã có": danh sách câu `active` (+ tuỳ chọn xem `rejected`), mỗi câu có nút Sửa (nạp lại vào form), Bỏ (rút, ghi version `rejected`), và xem lịch sử (`question_versions`).
- Form soạn câu hỏi (dùng chung cho thêm mới/sửa/nạp từ gợi ý):
  - `question_text`, `answer`, `equivalent_answers` (tuỳ chọn, nhiều dòng).
  - `answer_type` (numeric/text/unanswerable/boolean); trắc nghiệm suy ra tự động từ `question_type=multiple_choice`.
  - `question_type` (8 giá trị). Chọn `multiple_choice` → hiện 4 ô `choices`.
  - `hop_type` (4 loại).
  - Evidence builder (bắt buộc cho mọi hop_type): `source` (chart/text); chart → chọn `chart_id` (hiện preview ảnh chart đó ngay tại chỗ, không phải cuộn lên) + gõ tay `series`/`x` (không có bảng dữ liệu gốc để tra) — text → dán `quote`.
  - `derivation`: hiện khi `answer_type=numeric` và `question_type` thuộc {compositional, visual_compositional}. Nút "Kiểm tra" eval công thức, so `answer`, báo ✅/⚠️ (không chặn submit).
  - Submit → `validation.py`: chặn cứng nếu evidence thiếu hoặc quote không khớp `body_text`; cảnh báo mềm nếu derivation lệch hoặc trùng câu hỏi. Lưu thành công → `versioning.record_version()` ghi 1 snapshot.
- Cảnh báo nếu document chưa đủ 1 `single_chart` + 1 multi-hop.

### 4.3 Dashboard (PM)

- Document/câu hỏi theo `status`.
- Tỷ trọng `question_type`/`hop_type` thực tế (trên câu `active`) vs mục tiêu.
- Năng suất theo annotator/pod (document nạp, câu hỏi tạo, lượt tạo/sửa theo `question_versions`).

### 4.4 Export

Script cuối Tuần 5: join `documents`+`charts`+`questions`+`evidence` thành JSON theo [docs/02](02-dataset-design.md#schema-dữ-liệu-đề-xuất), chỉ lấy `status=active`, gán `split` theo document.

## 5. Hạ tầng

- SQLite: 1 file `.db` trên volume server, WAL + busy_timeout.
- Streamlit: `streamlit run` trên server (hoặc 1 container Docker), sau reverse proxy (Nginx/Caddy).
- Backup: cron `sqlite3 ... .backup` hằng ngày, đẩy sang nơi khác server.
- Ảnh chart: ổ đĩa/volume server, cùng lịch backup với SQLite.
- Auth: 10-15 tài khoản tạo tay, `streamlit-authenticator` hoặc session login tự viết.
- API key VLM: `st.secrets` (`secrets.toml` không commit git).

## 6. Khi nào migrate khỏi Streamlit

Chỉ cân nhắc nếu: (a) độ trễ rerun gây khó chịu rõ rệt với 5+ người dùng cùng lúc; (b) cần tương tác Streamlit không hỗ trợ tốt (vd vẽ bounding box lên ảnh — thiết kế hiện tại không cần, evidence là text tự do không phải toạ độ pixel); (c) mở annotation quy mô lớn ngoài nhóm sau dự án.

## 7. Trạng thái quyết định

1. Hạ tầng: tự host, SQLite — mục 3.2 và 5.
2. Taxonomy: `question_type` 8 giá trị lá + `choices` — mục 3.1, 4.2, đồng bộ [docs/02](02-dataset-design.md#taxonomy-câu-hỏi) + [docs/03](03-annotation-guidelines.md#5-mở-rộng-kiểu-chartqapro).
3. Người build: quản lý dự án.

Có thể bắt đầu scaffold code: SQLAlchemy models (3.1), `validation.py`, khung Streamlit multi-page (3).
