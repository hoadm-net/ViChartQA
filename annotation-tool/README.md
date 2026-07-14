# ViChartQA Annotation Tool

Streamlit + SQLite — công cụ nội bộ để nạp document và soạn câu hỏi cho bộ dữ liệu ViChartQA.

## Cài đặt

```bash
cd annotation-tool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# điền OPENROUTER_API_KEY vào secrets.toml (không commit file này) — tất cả model
# (xem VLM_MODEL_SLUGS trong constants.py) gọi qua OpenRouter, chỉ cần 1 key: https://openrouter.ai/keys

python db.py                 # tạo data/vichartqa.db (WAL mode)
python scripts/seed_users.py # tạo tài khoản — SỬA DANH SÁCH USERS trong file này trước khi chạy thật
```

`scripts/seed_users.py` in ra mật khẩu **một lần duy nhất** — lưu lại ngay (password manager), gửi riêng cho từng người.

## Chạy

```bash
streamlit run app.py
```

Mặc định chạy ở `localhost:8501`. Deploy thật chạy trên server/VPS sẵn có của nhóm, sau reverse proxy (Nginx/Caddy) — SQLite chỉ chịu được 1 tiến trình Streamlit ghi cùng lúc, backup định kỳ bằng `sqlite3 data/vichartqa.db ".backup vichartqa-$(date +%F).db"`.

## Hướng dẫn sử dụng

### 1. Nhập document

Title + toàn văn body_text (chèn `[CHART N]` đúng vị trí từng chart xuất hiện trong bài) + tối đa 3 ảnh chart — ảnh tự đặt tên theo hash, preview ngay khi upload. Điền nguồn (provider/domain/url) — ngày truy cập tự động = hôm nay.

### 2. Soạn câu hỏi

Trang duy nhất sau khi nhập xong document:

- Chọn document, xem lại title/body_text/ảnh chart.
- **Gợi ý bằng LLM** (tuỳ chọn): chọn model + số câu, bấm sinh — kết quả chỉ hiển thị tham khảo, **không tự lưu**. Bấm "Dùng làm mẫu" để nạp vào form bên dưới; vẫn phải tự rà lại từng field và bấm Lưu mới thực sự tạo câu hỏi.
- **Form soạn câu hỏi**: câu hỏi, đáp án (+ đáp án tương đương tuỳ chọn), `question_type`/`hop_type`, evidence builder (nguồn chart → chọn ảnh + gõ tay `series`/`x`, có preview ảnh ngay tại chỗ; nguồn text → dán quote nguyên văn từ body_text), `derivation` (bắt buộc khi đáp án là số và thuộc `compositional`/`visual_compositional`). Evidence bắt buộc cho **mọi** câu hỏi — thiếu hoặc quote không khớp nguyên văn sẽ bị chặn lưu.
- **Câu hỏi đã có**: nút Sửa (nạp lại vào form, lưu thành version mới), Bỏ (rút, chuyển status `rejected`), xem lịch sử chỉnh sửa (`question_versions`).
- Cảnh báo nếu document chưa đủ tối thiểu 1 câu `single_chart` + 1 câu multi-hop.

### 3. Dashboard

Theo dõi tiến độ: document/câu hỏi theo status, tỷ trọng `question_type`/`hop_type` thực tế so với mục tiêu, năng suất theo người dùng.

### 4. Export

Gán split train/val/test theo document (không theo câu hỏi, tránh leakage), xuất file JSON theo schema ở [docs/02](../docs/02-dataset-design.md#schema-dữ-liệu-đề-xuất) — chỉ lấy câu hỏi `status=active`.

## Cấu trúc

```
app.py              # entry point, đăng nhập + st.navigation
db.py                # engine SQLite (WAL + busy_timeout), init_db()
models.py             # SQLAlchemy ORM — 6 bảng (documents, charts, questions, evidence,
                        # question_versions, users)
constants.py           # enum dùng chung (question_type, hop_type, status...)
validation.py            # logic thuần Python: evidence không rỗng + quote khớp body_text,
                            # eval derivation — KHÔNG import streamlit, test độc lập được
versioning.py              # logic thuần Python: snapshot_question/record_version (question_versions)
question_ui.py                # widget Streamlit dùng chung: evidence builder, form soạn câu hỏi
                                 # (pages/2 gọi lại, không định nghĩa lại)
vlm_client.py                    # gọi model qua OpenRouter, parse response thành gợi ý tham khảo
export.py                          # build JSON dataset cuối + gán train/val/test split
auth.py                              # session login (bcrypt), không dùng dịch vụ ngoài
pages/
  1_document_intake.py                 # nạp document
  2_question_workspace.py                # gợi ý LLM + soạn/sửa câu hỏi
  3_dashboard.py                           # tiến độ, taxonomy, năng suất
  4_export.py                                # export dataset
scripts/seed_users.py                          # tạo tài khoản (chạy 1 lần, sửa USERS trước)
tests/
  test_validation.py    # unit test cho validation.py
  test_vlm_client.py       # unit test cho phần parse response (không gọi API thật)
  test_export.py             # unit test cho export.py
  test_app_flow.py             # integration test — lái thật từng trang qua
                                  # streamlit.testing.v1.AppTest (không chỉ import-check)
```

## Chạy test

```bash
python tests/test_validation.py
python tests/test_vlm_client.py
python tests/test_export.py
python tests/test_app_flow.py   # dùng DB riêng (tests/_test.db), an toàn chạy lại nhiều lần
```

Không có `pytest` trong requirements — mỗi file test tự chạy được bằng `python <file>` (in PASS/FAIL từng test), giữ dependency tối thiểu.

## Trạng thái hiện tại

Đã xong đủ 4 trang (nhập document → soạn câu hỏi → dashboard → export), có test cho từng trang. Không có bước xác minh chéo/phân xử — thay bằng version history (`question_versions`) ghi lại mỗi lần tạo/sửa/rút câu hỏi. Việc còn lại trước khi dùng cho pilot thật:

- [ ] Điền danh sách người thật vào `scripts/seed_users.py` (đang là placeholder `pod_a_1`, `pod_b_1`...)
- [ ] Điền API key thật vào `.streamlit/secrets.toml`, thử gọi thật cả 3 model VLM (chưa test được trong môi trường dev vì không có key)
- [ ] Deploy lên server/VPS thật + cấu hình backup cron
- [ ] Chạy thử với 1-2 document thật (không phải dữ liệu test) để annotator góp ý UI trước khi bắt đầu pilot diện rộng
