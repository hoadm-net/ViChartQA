import os

# pyarrow's bundled mimalloc allocator segfaults when it first allocates on a
# freshly spawned thread (Streamlit runs each script rerun on its own thread) —
# must be set before pyarrow's memory pool is touched anywhere in the process.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import streamlit as st

from auth import require_login, sidebar_user_info
from db import init_db

st.set_page_config(page_title="ViChartQA Annotation Tool", layout="wide")

init_db()  # no-op if tables already exist
require_login()
sidebar_user_info()

pages = [
    st.Page("pages/1_document_intake.py", title="Nhập document", icon="📥"),
    st.Page("pages/2_document_manager.py", title="Quản lý document", icon="🗂️"),
    st.Page("pages/3_question_workspace.py", title="Soạn câu hỏi", icon="✍️"),
    st.Page("pages/4_dashboard.py", title="Dashboard", icon="📈"),
    st.Page("pages/5_export.py", title="Export", icon="📤"),
]

nav = st.navigation(pages)
nav.run()
