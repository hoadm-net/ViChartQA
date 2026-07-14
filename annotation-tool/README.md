# ViChartQA Annotation Tool

Streamlit + SQLite, theo thiết kế ở [../docs/08-annotation-tool-design.md](../docs/08-annotation-tool-design.md). Không dùng Label Studio — lý do và kiến trúc đầy đủ nằm trong doc đó.

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

Mặc định chạy ở `localhost:8501`. Deploy thật (Tuần 1, xem [docs/05](../docs/05-timeline-and-roles.md)) chạy trên server/VPS sẵn có của nhóm, sau reverse proxy — chi tiết ở docs/08 §5.

## Cấu trúc

```
app.py              # entry point, đăng nhập + st.navigation
db.py                # engine SQLite (WAL + busy_timeout), init_db()
models.py             # SQLAlchemy ORM — 6 bảng, khớp docs/08 §3.1
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
  1_document_intake.py                 # nạp document (Pod A)
  2_question_workspace.py                # gợi ý LLM + soạn/sửa câu hỏi (Pod B)
  3_dashboard.py                           # tiến độ, taxonomy, năng suất
  4_export.py                                # export dataset cuối Tuần 5
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

Đã xong đủ 4 trang theo thiết kế (nhập document → soạn câu hỏi → dashboard → export), có test cho từng trang. Không còn bước xác minh chéo/phân xử — thay bằng version history (`question_versions`) ghi lại mỗi lần tạo/sửa/rút câu hỏi. Việc còn lại trước khi dùng cho pilot Tuần 1 thật:

- [ ] Điền danh sách 10 người thật vào `scripts/seed_users.py` (đang là placeholder `pod_a_1`, `pod_b_1`...)
- [ ] Điền API key thật vào `.streamlit/secrets.toml`, thử gọi thật cả 3 model VLM (chưa test được trong môi trường dev vì không có key)
- [ ] Deploy lên server/VPS thật + cấu hình backup cron (`sqlite3 ... .backup`) — xem docs/08 §5
- [ ] Chạy thử với 1-2 document thật (không phải dữ liệu test) để annotator góp ý UI trước khi bắt đầu pilot 50 document
