import streamlit as st

from auth import require_login, sidebar_user_info
from db import init_db

st.set_page_config(page_title="ViChartQA Annotation Tool", layout="wide")

init_db()  # no-op if tables already exist
require_login()
sidebar_user_info()

pages = [
    st.Page("pages/1_document_intake.py", title="Nhập document", icon="📥"),
    st.Page("pages/2_question_workspace.py", title="Soạn câu hỏi", icon="✍️"),
    st.Page("pages/3_dashboard.py", title="Dashboard", icon="📈"),
    st.Page("pages/4_export.py", title="Export", icon="📤"),
]

nav = st.navigation(pages)
nav.run()
