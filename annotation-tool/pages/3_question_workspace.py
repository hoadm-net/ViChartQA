"""Bước duy nhất sau intake: gợi ý câu hỏi bằng LLM (chỉ tham khảo, không tự lưu) +
soạn/sửa câu hỏi thủ công. Thay cho 3 trang cũ (data_table/seed/VLM) — xem docs/03.

Không có data_table backing cho evidence — description của evidence chart là các bước
truy hồi giá trị, tự do gõ tay (xem docs/02). Không có bước xác minh chéo/phân xử: mỗi
lần tạo/sửa/rút một câu hỏi được ghi lại ở question_versions (xem versioning.py).
"""

import base64
from pathlib import Path

import streamlit as st
from sqlalchemy import delete, select

from auth import current_user, require_login
from constants import VLM_MODELS
from db import get_session
from models import Document, Evidence, Question
from question_ui import render_question_form
from validation import word_count
from versioning import record_version
from vlm_client import VLMError, generate_candidates

ANNOTATION_ROOT = Path(__file__).resolve().parent.parent  # chart.image_path lưu tương đối gốc này (xem pages/1)

_MIME_BY_SUFFIX = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def _image_data_uri(path: Path) -> str | None:
    """Base64-encode 1 ảnh chart để gửi cho LLM multimodal — None nếu file không đọc được,
    khi đó gợi ý LLM cho chart này chỉ còn dựa vào chart_type (xem vlm_client.py)."""
    if not path.exists():
        return None
    mime = _MIME_BY_SUFFIX.get(path.suffix.lower(), "image/png")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

require_login()
st.title("✍️ Soạn câu hỏi")

with get_session() as session:
    docs = session.scalars(select(Document).order_by(Document.id)).all()
    doc_options = {f"#{d.id} — {d.title[:60]} ({len(d.questions)} câu hỏi)": d.id for d in docs}

if not doc_options:
    st.info("Chưa có document nào — sang trang Nhập document trước.")
    st.stop()

doc_keys = list(doc_options.keys())
default_index = 0
if "workspace_doc_id" in st.session_state:
    target_id = st.session_state["workspace_doc_id"]
    for i, d in enumerate(docs):
        if d.id == target_id:
            default_index = i
            break

selected_label = st.selectbox("Chọn document", doc_keys, index=default_index)
doc_id = doc_options[selected_label]

if st.session_state.get("workspace_doc_id") != doc_id:
    st.session_state["workspace_doc_id"] = doc_id
    st.session_state.pop("llm_suggestions", None)
    st.session_state.pop("workspace_form_initial", None)

with get_session() as session:
    doc = session.get(Document, doc_id)
    charts = sorted(doc.charts, key=lambda c: c.chart_id)
    existing_questions = sorted(doc.questions, key=lambda q: q.id)
    charts_by_id = {
        c.id: {
            "chart_id": c.chart_id,
            "image_path": str(ANNOTATION_ROOT / c.image_path) if (ANNOTATION_ROOT / c.image_path).exists() else None,
        }
        for c in charts
    }
    # materialize evidence/versions while the session is open — both are lazy
    # relationships and questions_display is read again after this block closes
    questions_display = [
        {
            "id": q.id,
            "question_text": q.question_text,
            "answer": q.answer,
            "equivalent_answers": q.equivalent_answers,
            "answer_type": q.answer_type,
            "question_type": q.question_type,
            "hop_type": q.hop_type,
            "derivation": q.derivation,
            "choices": q.choices,
            "status": q.status,
            "evidence": [
                {"hop": e.hop_order, "source": e.source, "chart_id": e.chart_id, "description": e.description, "quote": e.quote}
                for e in sorted(q.evidence, key=lambda e: e.hop_order)
            ],
            "versions": [
                {"version_number": v.version_number, "change_type": v.change_type, "edited_at": v.edited_at}
                for v in sorted(q.versions, key=lambda v: v.version_number)
            ],
        }
        for q in existing_questions
    ]

# ---- Document context ----
st.subheader(doc.title)
with st.expander(f"Xem toàn văn body_text ({word_count(doc.body_text)} từ)", expanded=False):
    st.write(doc.body_text)
if charts:
    for col, chart in zip(st.columns(len(charts)), charts):
        with col:
            st.markdown(f"**{chart.chart_id}** ({chart.chart_type})")
            image_path = ANNOTATION_ROOT / chart.image_path
            if image_path.exists():
                st.image(str(image_path), width="stretch")

# ---- LLM suggestions (tham khảo, không lưu) ----
st.divider()
st.subheader("🤖 Gợi ý câu hỏi bằng LLM")
st.caption(
    "Chỉ gợi ý câu hỏi + đáp án, không sinh evidence — annotator luôn tự đọc chart/text "
    'và điền evidence tay để giảm sai lệch. Bấm "Dùng làm mẫu" để nạp vào form soạn câu '
    "hỏi bên dưới rồi tự rà lại từng field, tự điền evidence, trước khi Lưu."
)
col1, col2 = st.columns([1, 3])
with col1:
    model = st.selectbox("Model", VLM_MODELS)
    n = st.number_input("Số câu", min_value=1, max_value=8, value=5)

if st.button("Sinh gợi ý"):
    charts_payload = [
        {
            "chart_id": c.chart_id,
            "chart_type": c.chart_type,
            "image_data_uri": _image_data_uri(ANNOTATION_ROOT / c.image_path),
        }
        for c in charts
    ]
    seed_questions = [q["question_text"] for q in questions_display]
    try:
        with st.spinner(f"Đang gọi {model}..."):
            raw = generate_candidates(model, doc.title, doc.body_text, charts_payload, seed_questions, n=int(n))
        st.session_state["llm_suggestions"] = raw
    except VLMError as exc:
        st.error(str(exc))
    except Exception as exc:  # noqa: BLE001 — surface any provider SDK/auth error to the annotator
        st.error(f"Lỗi gọi {model}: {exc}")

suggestions = st.session_state.get("llm_suggestions") or []
for i, sug in enumerate(suggestions):
    title = f"Gợi ý #{i + 1} [{sug.get('question_type')}/{sug.get('hop_type')}] {str(sug.get('question', ''))[:70]}"
    with st.expander(title):
        st.write(f"**Câu hỏi:** {sug.get('question', '')}")
        st.write(f"**Đáp án đề xuất:** {sug.get('answer', '')}")
        if st.button("Dùng làm mẫu", key=f"use_sug_{i}"):
            st.session_state["workspace_form_initial"] = {
                "question_text": sug.get("question", ""),
                "answer": str(sug.get("answer", "")),
                "answer_type": sug.get("answer_type"),
                "question_type": sug.get("question_type"),
                "hop_type": sug.get("hop_type"),
                "derivation": sug.get("derivation"),
                "choices": sug.get("choices"),
            }
            st.session_state["workspace_form_gen"] = st.session_state.get("workspace_form_gen", 0) + 1
            st.rerun()

# ---- Câu hỏi đã có ----
st.divider()
st.subheader("Câu hỏi đã có")
show_rejected = st.checkbox("Hiện cả câu đã rút (rejected)", value=False)
visible_questions = [q for q in questions_display if q["status"] == "active" or (show_rejected and q["status"] == "rejected")]
for q in visible_questions:
    last_version = q["versions"][-1] if q["versions"] else None
    version_note = f"v{last_version['version_number']}" if last_version else "v?"
    st.markdown(f"**#{q['id']}** [{q['question_type']}/{q['hop_type']}] {q['question_text']} → *{q['answer']}* — `{q['status']}` ({version_note})")
    c1, c2, c3 = st.columns([1, 1, 4])
    with c1:
        if q["status"] == "active" and st.button("Sửa", key=f"edit_q_{q['id']}"):
            st.session_state["workspace_form_initial"] = dict(q)
            st.session_state["workspace_form_gen"] = st.session_state.get("workspace_form_gen", 0) + 1
            st.rerun()
    with c2:
        if q["status"] == "active" and st.button("Bỏ", key=f"reject_q_{q['id']}"):
            with get_session() as write_session:
                db_q = write_session.get(Question, q["id"])
                db_q.status = "rejected"
                write_session.flush()
                record_version(write_session, db_q, current_user().id, "rejected")
                write_session.commit()
            st.rerun()
    with c3:
        with st.expander(f"Xem lịch sử ({len(q['versions'])})"):
            for v in q["versions"]:
                st.caption(f"v{v['version_number']} · {v['change_type']} · {v['edited_at']:%Y-%m-%d %H:%M}")

# ---- Thêm/sửa câu hỏi ----
st.divider()
st.subheader("Thêm/sửa câu hỏi")
form_initial = st.session_state.get("workspace_form_initial")
if form_initial:
    st.caption("Đang nạp nội dung tham khảo — rà lại từng field trước khi Lưu.")
    if st.button("Bỏ nội dung đang nạp, soạn từ đầu"):
        st.session_state.pop("workspace_form_initial", None)
        st.session_state["workspace_form_gen"] = st.session_state.get("workspace_form_gen", 0) + 1
        st.rerun()

result = render_question_form("workspace", doc, charts_by_id, existing_questions, initial=form_initial)
if result:
    with get_session() as write_session:
        if result["id"]:
            db_q = write_session.get(Question, result["id"])
            db_q.question_text = result["question_text"]
            db_q.answer = result["answer"]
            db_q.equivalent_answers = result["equivalent_answers"]
            db_q.answer_type = result["answer_type"]
            db_q.question_type = result["question_type"]
            db_q.hop_type = result["hop_type"]
            db_q.derivation = result["derivation"]
            db_q.choices = result["choices"]
            write_session.execute(delete(Evidence).where(Evidence.question_id == db_q.id))
            change_type = "edited"
        else:
            db_q = Question(
                document_id=doc.id,
                question_text=result["question_text"],
                answer=result["answer"],
                equivalent_answers=result["equivalent_answers"],
                answer_type=result["answer_type"],
                question_type=result["question_type"],
                hop_type=result["hop_type"],
                derivation=result["derivation"],
                choices=result["choices"],
                status="active",
                created_by=current_user().id,
            )
            write_session.add(db_q)
            change_type = "created"
        write_session.flush()
        for item in result["evidence"]:
            write_session.add(
                Evidence(
                    question_id=db_q.id,
                    hop_order=item["hop"],
                    source=item["source"],
                    chart_id=item.get("chart_id"),
                    description=item.get("description"),
                    quote=item.get("quote"),
                )
            )
        write_session.flush()
        record_version(write_session, db_q, current_user().id, change_type)
        db_doc = write_session.get(Document, doc.id)
        if db_doc.status == "intake":
            db_doc.status = "in_progress"
        write_session.commit()
        saved_id = db_q.id
    st.success(f"Đã lưu câu hỏi #{saved_id}.")
    st.session_state.pop("workspace_form_initial", None)
    st.session_state["workspace_form_gen"] = st.session_state.get("workspace_form_gen", 0) + 1
    st.rerun()
