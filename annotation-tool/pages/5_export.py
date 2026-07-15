"""Export dataset cuối kỳ (data freeze) — xem docs/02 §Schema.
Chỉ lấy câu hỏi status active, gán split theo document (không theo câu hỏi).
"""

import json

import streamlit as st
from sqlalchemy import select

from auth import require_login
from db import get_session
from export import EXPORT_ELIGIBLE_STATUSES, assign_splits, build_dataset
from models import Document, Question

require_login()
st.title("📤 Export dataset")

with get_session() as session:
    total_docs = len(session.scalars(select(Document)).all())
    unsplit_docs = len(session.scalars(select(Document).where(Document.split.is_(None))).all())
    eligible_questions = len(
        session.scalars(select(Question).where(Question.status.in_(EXPORT_ELIGIBLE_STATUSES))).all()
    )

col1, col2, col3 = st.columns(3)
col1.metric("Document", total_docs)
col2.metric("Document chưa gán split", unsplit_docs)
col3.metric("Câu hỏi đủ điều kiện export (active)", eligible_questions)

st.divider()

st.subheader("1. Gán split (chỉ chạy khi data freeze — Tuần 5)")
st.caption("Chia ~77/10/13 theo document, không theo câu hỏi, để tránh leakage. Idempotent — chạy lại không đụng document đã có split.")
if st.button("Gán split cho document chưa có"):
    with get_session() as write_session:
        n = assign_splits(write_session)
        write_session.commit()
    st.success(f"Đã gán split cho {n} document.")
    st.rerun()

st.divider()

st.subheader("2. Export JSON")
require_split = st.checkbox("Chỉ export document đã có split (khuyến nghị cho bản export chính thức)", value=True)

if st.button("Tạo file export"):
    with get_session() as session:
        dataset = build_dataset(session, require_split=require_split)
    st.session_state["export_preview"] = dataset

dataset = st.session_state.get("export_preview")
if dataset is not None:
    n_qa = sum(len(d["qa"]) for d in dataset)
    st.write(f"**{len(dataset)} document / {n_qa} câu hỏi** sẵn sàng export.")
    st.json(dataset[:1] if dataset else [], expanded=False)
    st.download_button(
        "Tải vichartqa.json",
        data=json.dumps(dataset, ensure_ascii=False, indent=2),
        file_name="vichartqa.json",
        mime="application/json",
    )
