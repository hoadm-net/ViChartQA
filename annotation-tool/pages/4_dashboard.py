"""Dashboard tiến độ.

Số document/câu hỏi theo status, tỷ trọng taxonomy thực tế vs mục tiêu, năng suất
theo người dùng. Không còn số liệu xác minh chéo (đã bỏ cơ chế này — xem
question_versions cho lịch sử tạo/sửa từng câu hỏi thay thế).
"""

import pandas as pd
import streamlit as st
from sqlalchemy import select

from auth import require_login
from constants import HOP_TYPES, MULTI_HOP_TYPES, QUESTION_TYPE_TARGETS, QUESTION_TYPES
from db import get_session
from models import Document, Question, QuestionVersion, User
from validation import get_dataset_deficit_ranking

require_login()
st.title("📈 Dashboard")

with get_session() as session:
    documents = session.scalars(select(Document)).all()
    questions = session.scalars(select(Question)).all()
    users = {u.id: u for u in session.scalars(select(User)).all()}
    versions = session.scalars(select(QuestionVersion)).all()

with st.container(border=True):
    st.markdown("#### 📊 Tổng quan trạng thái")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Document theo status**")
        if documents:
            counts = pd.Series([d.status for d in documents]).value_counts()
            st.bar_chart(counts)
            st.caption(f"Tổng: {len(documents)} document")
        else:
            st.info("Chưa có document.")

    with col2:
        st.markdown("**Câu hỏi theo status**")
        if questions:
            counts = pd.Series([q.status for q in questions]).value_counts()
            st.bar_chart(counts)
            st.caption(f"Tổng: {len(questions)} câu hỏi")
        else:
            st.info("Chưa có câu hỏi.")

st.divider()

# --- Taxonomy distribution vs targets ---
active = [q for q in questions if q.status == "active"]
active_dict_list = [{"question_type": q.question_type, "hop_type": q.hop_type} for q in active]
top3_q_deficits, priority_hops, multihop_pct = get_dataset_deficit_ranking(active_dict_list)

with st.container(border=True):
    st.markdown(f"#### 🎯 Tỷ trọng Taxonomy (trên {len(active)} câu active)")
    
    col_def1, col_def2 = st.columns(2)
    with col_def1:
        st.markdown(r"**🚨 Top 3 Question Types Thiếu Nhất ($\Delta P$):**")
        for item in top3_q_deficits:
            st.write(f"- `{item['type']}`: Thực tế `{item['current_pct']}%` / Target `{item['target_pct']}%` (Thiếu `+{item['deficit']}%`)")
    with col_def2:
        st.markdown("**🎯 Hop Types Cần Ưu Tiên Bổ Sung:**")
        for h in priority_hops:
            st.write(f"- `{h}`")
    st.divider()

    c_qtype, c_hop = st.columns(2)
    
    with c_qtype:
        st.markdown("**question_type** so với mục tiêu")
        if active:
            qt_counts = pd.Series([q.question_type for q in active]).value_counts()
            rows = []
            for qt in QUESTION_TYPES:
                actual = qt_counts.get(qt, 0) / len(active)
                rows.append({"question_type": qt, "thực tế": round(actual, 3), "mục tiêu": QUESTION_TYPE_TARGETS[qt]})
            df = pd.DataFrame(rows).set_index("question_type")
            st.bar_chart(df)
        else:
            st.info("Chưa có dữ liệu.")
            
    with c_hop:
        st.markdown("**hop_type**")
        if active:
            hop_counts = pd.Series([q.hop_type for q in active]).value_counts()
            multi_hop_n = sum(hop_counts.get(h, 0) for h in MULTI_HOP_TYPES)
            multi_hop_pct = multi_hop_n / len(active)
            st.metric("Tỷ lệ multi-hop (mục tiêu ≥50%)", f"{multi_hop_pct:.0%}", delta=f"{multi_hop_pct - 0.5:+.0%}")
            df = pd.DataFrame({"hop_type": HOP_TYPES, "số câu": [hop_counts.get(h, 0) for h in HOP_TYPES]}).set_index(
                "hop_type"
            )
            st.bar_chart(df)
        else:
            st.info("Chưa có dữ liệu.")

st.divider()

# --- Productivity ---
with st.container(border=True):
    st.markdown("#### ⚡ Năng suất theo Annotator/Pod")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**Document nạp (Pod A)**")
        doc_creators = [d.created_by for d in documents if d.created_by]
        if doc_creators:
            counts = pd.Series([users[uid].name if uid in users else str(uid) for uid in doc_creators]).value_counts()
            st.dataframe(counts.rename("số document"), width='stretch')
        else:
            st.info("Chưa có dữ liệu.")

    with col_b:
        st.markdown("**Câu hỏi tạo (Pod B)**")
        creators = [q.created_by for q in questions if q.created_by]
        if creators:
            counts = pd.Series([users[uid].name if uid in users else str(uid) for uid in creators]).value_counts()
            st.dataframe(counts.rename("số câu hỏi"), width='stretch')
        else:
            st.info("Chưa có dữ liệu.")
            
    with col_c:
        st.markdown("**Lượt tạo/sửa câu (Lịch sử)**")
        editors = [v.edited_by for v in versions if v.edited_by]
        if editors:
            counts = pd.Series([users[uid].name if uid in users else str(uid) for uid in editors]).value_counts()
            st.dataframe(counts.rename("số lượt thao tác"), width='stretch')
        else:
            st.info("Chưa có dữ liệu.")
