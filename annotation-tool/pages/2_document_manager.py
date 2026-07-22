"""Xem/sửa/xoá document đã nạp. Sửa cần role pm/data_intake; xoá chỉ role pm.

Xoá thì xoá luôn toàn bộ câu hỏi/evidence/lịch sử liên quan — xem
documents.delete_document() cho lý do vì sao xoá tường minh theo thứ tự thay vì
dựa vào cascade ORM một mình.
"""

import hashlib
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import select

from auth import current_user, require_login
from constants import DOMAINS, MAX_BODY_TEXT_WORDS, CHART_TYPES
from db import get_session
from dedup import find_duplicates
from documents import delete_document
from models import Document, User, Chart
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
            delete_document(session, doc_id, deleted_by=current_user().id)
        st.session_state.pop("selected_doc_id", None)
        st.session_state.pop("doc_manager_table", None)
        st.session_state.pop("pending_delete_doc_id", None)
        st.rerun()





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
            "questions": len([q for q in d.questions if q.status == "active"]),
            "created_by": users.get(d.created_by, ""),
            "created_at": d.created_at,
        }
        for d in docs
    ]

if not rows:
    st.info("Chưa có document nào — sang trang Nhập document trước.")
    st.stop()

col1, col2 = st.columns(2)
search_id = col1.text_input("🔍 Tìm theo ID", placeholder="Nhập ID (VD: 12)...")
search_title = col2.text_input("🔍 Tìm theo Title", placeholder="Nhập từ khóa...")

if search_id.strip():
    rows = [r for r in rows if str(r["id"]) == search_id.strip()]
if search_title.strip():
    search_term = search_title.strip().lower()
    rows = [r for r in rows if search_term in r["title"].lower()]

df = pd.DataFrame(rows)
if df.empty:
    st.warning("Không tìm thấy document nào khớp với tìm kiếm.")
    event = {}
else:
    event = st.dataframe(
        df,
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
        key="doc_manager_table",
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

if isinstance(event, dict):
    selected_rows = event.get("selection", {}).get("rows", [])
else:
    selected_rows = event.selection.rows if getattr(event, "selection", None) else []

if selected_rows:
    st.session_state["selected_doc_id"] = int(df.iloc[selected_rows[0]]["id"])
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

with st.expander(f"Xem toàn văn body_text ({word_count(doc_data['body_text'])} từ)", expanded=False):
    st.markdown(f"<div style='white-space: pre-wrap;'>{doc_data['body_text']}</div>", unsafe_allow_html=True)

if charts_data:
    for col, chart in zip(st.columns(len(charts_data)), charts_data):
        with col:
            st.markdown(f"**{chart['chart_id']}** ({chart['chart_type']})")
            image_path = ANNOTATION_ROOT / chart["image_path"]
            if image_path.exists():
                st.image(str(image_path), width="stretch")

if not can_edit and not can_delete:
    st.caption("Chỉ `pm`/`data_intake` được sửa, chỉ `pm` được xoá document.")

if can_delete:
    if st.button("Xoá document này", type="primary", key="btn_delete_doc_outside"):
        st.session_state["pending_delete_doc_id"] = doc_id
        st.rerun()

if can_edit:
    st.divider()
    st.subheader("Sửa document")
    gen = st.session_state.setdefault("docmgr_form_gen", 0)
    k = lambda name: f"docmgr_{name}_{doc_id}_{gen}"  # noqa: E731 — reset widget keys after mỗi lần lưu

    # Cảnh báo (không chặn lưu) ngay tại field title/URL nếu nghi trùng document khác
    # — dừng sớm thay vì phát hiện sau khi đã sửa xong cả body_text (xem dedup.py).
    with get_session() as session:
        existing_docs = [
            {"id": d.id, "title": d.title, "source_url": d.source_url} for d in session.scalars(select(Document)).all()
        ]

    with st.container(border=True):
        st.markdown("#### 📄 Thông tin văn bản")
        new_title = st.text_input("Title", value=doc_data["title"], key=k("title"))
        if new_title.strip():
            for m in find_duplicates(new_title, None, existing_docs, exclude_id=doc_id)[:5]:
                if m.reason == "title_exact":
                    st.warning(f"⚠️ Title trùng hệt document #{m.document_id} — \"{m.title[:70]}\"")
                else:
                    st.warning(f"⚠️ Title khá giống document #{m.document_id} ({m.score:.0%} tương đồng) — \"{m.title[:70]}\"")

        new_body_text = st.text_area("Body text", value=doc_data["body_text"], height=260, key=k("body_text"))
        if new_body_text.strip():
            n_words = word_count(new_body_text)
            st.caption(f"{n_words} từ" + (" ⚠️ vượt 2000 từ, cân nhắc rút gọn" if n_words > MAX_BODY_TEXT_WORDS else ""))

    with st.container(border=True):
        st.markdown("#### 🌐 Nguồn trích dẫn")
        col1, col2 = st.columns(2)
        with col1:
            new_provider = st.text_input("Provider", value=doc_data["source_provider"], key=k("provider"))
            domain_default = doc_data["source_domain"] if doc_data["source_domain"] in DOMAINS else DOMAINS[0]
            new_domain = st.selectbox("Domain", DOMAINS, index=DOMAINS.index(domain_default), key=k("domain"))
        with col2:
            new_url = st.text_input("URL", value=doc_data["source_url"] or "", key=k("url"))
            if new_url.strip():
                url_matches = [
                    m for m in find_duplicates(new_title, new_url, existing_docs, exclude_id=doc_id) if m.reason == "url_exact"
                ]
                for m in url_matches[:5]:
                    st.error(f"⚠️ URL trùng với document #{m.document_id} — \"{m.title[:70]}\"")

    with st.container(border=True):
        st.markdown("#### 🖼️ Ảnh chart")
        if n_questions > 0:
            st.info("Document đã có câu hỏi, không thể tải lên lại ảnh chart để tránh hỏng dữ liệu evidence đã gán. Bạn chỉ có thể cập nhật loại chart cho các ảnh hiện tại.")
            edited_chart_types = {}
            for chart in charts_data:
                edited_chart_types[chart["chart_id"]] = st.selectbox(
                    f"Loại chart {chart['chart_id']}", 
                    CHART_TYPES, 
                    index=CHART_TYPES.index(chart["chart_type"]) if chart["chart_type"] in CHART_TYPES else 0, 
                    key=k(f"type_{chart['chart_id']}")
                )
            new_chart_meta = None
            uploaded_files = None
        else:
            st.info("Để trống nếu muốn giữ nguyên các chart hiện tại. Nếu tải lên ảnh mới, toàn bộ chart cũ sẽ bị xoá và ghi đè (tối đa 3 ảnh).")
            uploaded_files = st.file_uploader(
                "Chọn ảnh mới (tối đa 3)",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key=k("files"),
            )
            new_chart_meta = []
            if uploaded_files:
                for i, f in enumerate(uploaded_files[:3]):
                    with st.container(border=True):
                        st.markdown(f"**[CHART {i + 1}]** — {f.name}")
                        c_img, c_type = st.columns([1, 1])
                        with c_img:
                            st.image(f, width=180)
                        with c_type:
                            default_idx = 0
                            if i < len(charts_data) and charts_data[i]["chart_type"] in CHART_TYPES:
                                default_idx = CHART_TYPES.index(charts_data[i]["chart_type"])
                            chart_type = st.selectbox(f"Loại chart #{i + 1}", CHART_TYPES, index=default_idx, key=k(f"new_type_{i}"))
                        new_chart_meta.append({"file": f, "chart_id": f"fig{i + 1}", "chart_type": chart_type})
            else:
                edited_chart_types = {}
                for chart in charts_data:
                    edited_chart_types[chart["chart_id"]] = st.selectbox(
                        f"Loại chart {chart['chart_id']}", 
                        CHART_TYPES, 
                        index=CHART_TYPES.index(chart["chart_type"]) if chart["chart_type"] in CHART_TYPES else 0, 
                        key=k(f"type_{chart['chart_id']}")
                    )

    if st.button("💾 Lưu thay đổi", type="primary", key=k("submit")):
        errors = []
        if not new_title.strip() or not new_body_text.strip():
            errors.append("Cần nhập title và body_text.")
        
        num_charts = len(new_chart_meta) if uploaded_files else len(charts_data)
        ok, msg = check_chart_placeholders(new_body_text, num_charts)
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

                if uploaded_files:
                    IMAGES_DIR = ANNOTATION_ROOT / "data" / "images"
                    db_charts = sorted(db_doc.charts, key=lambda c: c.chart_id)
                    
                    for i, meta in enumerate(new_chart_meta):
                        content = meta["file"].getvalue()
                        ext = Path(meta["file"].name).suffix.lower() or ".png"
                        file_hash = hashlib.sha256(content).hexdigest()[:16]
                        image_path = IMAGES_DIR / f"{file_hash}{ext}"
                        if not image_path.exists():
                            image_path.write_bytes(content)
                            
                        rel_path = str(image_path.relative_to(ANNOTATION_ROOT))
                        
                        if i < len(db_charts):
                            db_charts[i].image_path = rel_path
                            db_charts[i].chart_type = meta["chart_type"]
                            db_charts[i].chart_id = meta["chart_id"]
                        else:
                            new_chart = Chart(
                                document_id=doc_id,
                                chart_id=meta["chart_id"],
                                image_path=rel_path,
                                chart_type=meta["chart_type"],
                            )
                            write_session.add(new_chart)
                    
                    if len(new_chart_meta) < len(db_charts):
                        for c in db_charts[len(new_chart_meta):]:
                            write_session.delete(c)
                else:
                    db_charts = sorted(db_doc.charts, key=lambda c: c.chart_id)
                    for c in db_charts:
                        if c.chart_id in edited_chart_types:
                            c.chart_type = edited_chart_types[c.chart_id]

                try:
                    write_session.commit()
                    st.success("Đã lưu.")
                    st.session_state["docmgr_form_gen"] += 1
                    st.rerun()
                except Exception as e:
                    write_session.rollback()
                    st.error(f"Lỗi khi lưu (có thể do xung đột dữ liệu): {e}")
