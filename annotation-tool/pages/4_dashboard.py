"""Dashboard tiến độ.

Số document/câu hỏi theo status, tỷ trọng taxonomy thực tế vs mục tiêu, năng suất
theo người dùng. Không còn số liệu xác minh chéo (đã bỏ cơ chế này — xem
question_versions cho lịch sử tạo/sửa từng câu hỏi thay thế).
"""

import pandas as pd
import streamlit as st
from sqlalchemy import func, select

from auth import require_login
from constants import HOP_TYPES, MULTI_HOP_TYPES, QUESTION_TYPE_TARGETS, QUESTION_TYPES
from db import get_session
from models import Document, Question, QuestionVersion, User
from validation import get_dataset_deficit_ranking

require_login()
st.title("📈 Dashboard")

with get_session() as session:
    doc_status_counts = dict(
        session.execute(select(Document.status, func.count(Document.id)).group_by(Document.status)).all()
    )
    total_docs = sum(doc_status_counts.values())
    q_status_counts = dict(
        session.execute(select(Question.status, func.count(Question.id)).group_by(Question.status)).all()
    )
    total_questions = sum(q_status_counts.values())
    users = {u.id: u.name for u in session.scalars(select(User)).all()}
    active_q_rows = session.execute(
        select(Question.question_type, Question.hop_type).where(Question.status == "active")
    ).all()
    doc_creators_counts = session.execute(
        select(Document.created_by, func.count(Document.id))
        .where(Document.created_by.isnot(None))
        .group_by(Document.created_by)
    ).all()
    q_creators_counts = session.execute(
        select(Question.created_by, func.count(Question.id))
        .where(Question.created_by.isnot(None))
        .group_by(Question.created_by)
    ).all()
    v_editors_counts = session.execute(
        select(QuestionVersion.edited_by, func.count(QuestionVersion.id))
        .where(QuestionVersion.edited_by.isnot(None))
        .group_by(QuestionVersion.edited_by)
    ).all()

with st.container(border=True):
    st.markdown("#### 📊 Tổng quan trạng thái")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Document theo status**")
        if doc_status_counts:
            st.bar_chart(pd.Series(doc_status_counts))
            st.caption(f"Tổng: {total_docs} document")
        else:
            st.info("Chưa có document.")

    with col2:
        st.markdown("**Câu hỏi theo status**")
        if q_status_counts:
            st.bar_chart(pd.Series(q_status_counts))
            st.caption(f"Tổng: {total_questions} câu hỏi")
        else:
            st.info("Chưa có câu hỏi.")

st.divider()

# --- Taxonomy distribution vs targets ---
active_dict_list = [{"question_type": qt, "hop_type": ht} for qt, ht in active_q_rows]
top3_q_deficits, priority_hops, multihop_pct = get_dataset_deficit_ranking(active_dict_list)

with st.container(border=True):
    st.markdown(f"#### 🎯 Tỷ trọng Taxonomy (trên {len(active_dict_list)} câu active)")
    
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
        if active_dict_list:
            qt_counts = pd.Series([q["question_type"] for q in active_dict_list]).value_counts()
            rows = []
            for qt in QUESTION_TYPES:
                actual = qt_counts.get(qt, 0) / len(active_dict_list)
                rows.append({"question_type": qt, "thực tế": round(actual, 3), "mục tiêu": QUESTION_TYPE_TARGETS[qt]})
            df = pd.DataFrame(rows).set_index("question_type")
            st.bar_chart(df)
        else:
            st.info("Chưa có dữ liệu.")
            
    with c_hop:
        st.markdown("**hop_type**")
        if active_dict_list:
            hop_counts = pd.Series([q["hop_type"] for q in active_dict_list]).value_counts()
            multi_hop_n = sum(hop_counts.get(h, 0) for h in MULTI_HOP_TYPES)
            multi_hop_pct = multi_hop_n / len(active_dict_list)
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
        if doc_creators_counts:
            doc_user_series = pd.Series({users.get(uid, str(uid)): cnt for uid, cnt in doc_creators_counts})
            st.dataframe(doc_user_series.rename("số document"), width="stretch")
        else:
            st.info("Chưa có dữ liệu.")

    with col_b:
        st.markdown("**Câu hỏi tạo (Pod B)**")
        if q_creators_counts:
            q_user_series = pd.Series({users.get(uid, str(uid)): cnt for uid, cnt in q_creators_counts})
            st.dataframe(q_user_series.rename("số câu hỏi"), width="stretch")
        else:
            st.info("Chưa có dữ liệu.")
            
    with col_c:
        st.markdown("**Lượt tạo/sửa câu (Lịch sử)**")
        if v_editors_counts:
            v_user_series = pd.Series({users.get(uid, str(uid)): cnt for uid, cnt in v_editors_counts})
            st.dataframe(v_user_series.rename("số lượt thao tác"), width="stretch")
        else:
            st.info("Chưa có dữ liệu.")
