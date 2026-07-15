"""Xem/sửa/xoá document đã nạp. Sửa cần role pm/data_intake; xoá chỉ role pm.

Xoá thì xoá luôn toàn bộ câu hỏi/evidence/lịch sử liên quan — xem
documents.delete_document() cho lý do vì sao xoá tường minh theo thứ tự thay vì
dựa vào cascade ORM một mình.
"""

from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import select

from auth import current_user, require_login
from constants import DOMAINS, MAX_BODY_TEXT_WORDS
from db import get_session
from documents import delete_document
from models import Document, User
from validation import check_chart_placeholders, word_count

ANNOTATION_ROOT = Path(__file__).resolve().parent.parent

require_login()
st.title("🗂️ Quản lý document")

user = current_user()
can_edit = user.role in ("pm", "data_intake")
can_delete = user.role == "pm"


@st.dialog("Xoá document?")
def confirm_delete(doc_id: int, title: str, n_questions: int) -> None:
    st.warning(
        f'Xoá vĩnh viễn document #{doc_id} — "{title}" cùng **{n_questions} câu hỏi** '
        "liên quan (evidence + lịch sử chỉnh sửa). Không thể hoàn tác."
    )
    if st.button("Xoá vĩnh viễn", type="primary", key=f"confirm_delete_{doc_id}"):
        with get_session() as session:
            delete_document(session, doc_id)
        st.session_state.pop("selected_doc_id", None)
        st.session_state.pop("doc_manager_table", None)
        st.session_state.pop("pending_delete_doc_id", None)
        st.rerun()


def handle_row_delete_click() -> None:
    click = st.session_state.get("doc_row_action")
    if click:
        st.session_state["pending_delete_doc_id"] = doc_ids[click["row"]]


with get_session() as session:
    docs = session.scalars(select(Document).order_by(Document.id.desc())).all()
    users = {u.id: u.name for u in session.scalars(select(User)).all()}
    doc_ids = [d.id for d in docs]
    rows = [
        {
            "id": d.id,
            "title": d.title[:70],
            "domain": d.source_domain,
            "provider": d.source_provider,
            "status": d.status,
            "split": d.split or "",
            "charts": len(d.charts),
            "questions": len(d.questions),
            "created_by": users.get(d.created_by, ""),
            "created_at": d.created_at,
            "actions": [":material/delete: Xoá"] if can_delete else [],
        }
        for d in docs
    ]

if not rows:
    st.info("Chưa có document nào — sang trang Nhập document trước.")
    st.stop()

df = pd.DataFrame(rows)
event = st.dataframe(
    df,
    on_select="rerun",
    selection_mode="single-row",
    hide_index=True,
    key="doc_manager_table",
    column_config={
        "actions": st.column_config.ButtonColumn(
            "", on_click=handle_row_delete_click, key="doc_row_action", width="small"
        ),
    },
)

pending_delete_id = st.session_state.get("pending_delete_doc_id")
if pending_delete_id and can_delete:
    with get_session() as session:
        pending_doc = session.get(Document, pending_delete_id)
        if pending_doc is not None:
            pending_title = pending_doc.title
            pending_n_questions = len(pending_doc.questions)
    if pending_doc is not None:
        confirm_delete(pending_delete_id, pending_title, pending_n_questions)
    else:
        st.session_state.pop("pending_delete_doc_id", None)

if event.selection.rows:
    st.session_state["selected_doc_id"] = int(df.iloc[event.selection.rows[0]]["id"])
doc_id = st.session_state.get("selected_doc_id")

if not doc_id:
    st.caption("Chọn 1 dòng trong bảng để xem chi tiết.")
    st.stop()

with get_session() as session:
    doc = session.get(Document, doc_id)
    if doc is None:
        st.session_state.pop("selected_doc_id", None)
        st.rerun()
    charts = sorted(doc.charts, key=lambda c: c.chart_id)
    n_questions = len(doc.questions)
    doc_data = {
        "id": doc.id,
        "title": doc.title,
        "body_text": doc.body_text,
        "source_provider": doc.source_provider,
        "source_domain": doc.source_domain,
        "source_url": doc.source_url,
        "status": doc.status,
        "split": doc.split,
    }
    charts_data = [{"chart_id": c.chart_id, "chart_type": c.chart_type, "image_path": c.image_path} for c in charts]

st.divider()
st.subheader(f"#{doc_data['id']} — {doc_data['title']}")

col_a, col_b, col_c = st.columns(3)
col_a.metric("Status", doc_data["status"])
col_b.metric("Split", doc_data["split"] or "(chưa gán)")
col_c.metric("Câu hỏi", n_questions)

with st.expander("Xem toàn văn body_text", expanded=False):
    st.write(doc_data["body_text"])

if charts_data:
    for col, chart in zip(st.columns(len(charts_data)), charts_data):
        with col:
            st.markdown(f"**{chart['chart_id']}** ({chart['chart_type']})")
            image_path = ANNOTATION_ROOT / chart["image_path"]
            if image_path.exists():
                st.image(str(image_path), width="stretch")

if not can_edit and not can_delete:
    st.caption("Chỉ `pm`/`data_intake` được sửa, chỉ `pm` được xoá document.")

if can_edit:
    st.divider()
    st.subheader("Sửa document")
    gen = st.session_state.setdefault("docmgr_form_gen", 0)
    k = lambda name: f"docmgr_{name}_{doc_id}_{gen}"  # noqa: E731 — reset widget keys after mỗi lần lưu

    new_title = st.text_input("Title", value=doc_data["title"], key=k("title"))
    new_body_text = st.text_area("Body text", value=doc_data["body_text"], height=260, key=k("body_text"))
    if new_body_text.strip():
        n_words = word_count(new_body_text)
        st.caption(f"{n_words} từ" + (" ⚠️ vượt 2000 từ, cân nhắc rút gọn" if n_words > MAX_BODY_TEXT_WORDS else ""))

    col1, col2 = st.columns(2)
    with col1:
        new_provider = st.text_input("Provider", value=doc_data["source_provider"], key=k("provider"))
        domain_default = doc_data["source_domain"] if doc_data["source_domain"] in DOMAINS else DOMAINS[0]
        new_domain = st.selectbox("Domain", DOMAINS, index=DOMAINS.index(domain_default), key=k("domain"))
    with col2:
        new_url = st.text_input("URL", value=doc_data["source_url"] or "", key=k("url"))

    if st.button("Lưu thay đổi", type="primary", key=k("submit")):
        errors = []
        if not new_title.strip() or not new_body_text.strip():
            errors.append("Cần nhập title và body_text.")
        ok, msg = check_chart_placeholders(new_body_text, len(charts_data))
        if not ok:
            errors.append(msg)

        if errors:
            for e in errors:
                st.error(e)
        else:
            with get_session() as write_session:
                db_doc = write_session.get(Document, doc_id)
                db_doc.title = new_title.strip()
                db_doc.body_text = new_body_text.strip()
                db_doc.source_provider = new_provider.strip()
                db_doc.source_domain = new_domain
                db_doc.source_url = new_url.strip() or None
                write_session.commit()
            st.success("Đã lưu.")
            st.session_state["docmgr_form_gen"] += 1
            st.rerun()
