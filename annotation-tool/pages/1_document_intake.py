"""Bước intake: Pod A nạp document (title + toàn văn body_text + tối đa 3 ảnh chart).
Sau khi lưu, document ở status=intake, chờ Bước 0 (nhập data_table) — xem trang kế tiếp.

body_text là TOÀN VĂN bài báo (không cắt đoạn) với placeholder [CHART N] chèn đúng vị trí
chart xuất hiện trong bài — xem docs/02 §Phạm vi để biết lý do (có câu hỏi chỉ dựa vào text,
không liên quan chart nào; và [CHART N] giúp biết chart nằm ở đâu trong mạch bài mà không
cần tách nhãn subplot mà ảnh gốc không có).

Không dùng st.form vì cần rerun ngay khi upload ảnh để hiện dropdown loại chart/preview.
"""

import hashlib
from datetime import date
from pathlib import Path

import streamlit as st
from sqlalchemy import select

from auth import current_user, require_login
from constants import CHART_TYPES, DOMAINS, MAX_BODY_TEXT_WORDS
from db import get_session
from dedup import find_duplicates
from models import Chart, Document
from validation import check_chart_placeholders, word_count

IMAGES_DIR = Path(__file__).resolve().parent.parent / "data" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
MAX_CHARTS_PER_DOCUMENT = 3

require_login()
st.title("📥 Nhập document")
st.caption(
    "1 document = title + toàn văn bài báo (dưới 2000 từ) + tối đa 3 ảnh chart liên quan "
    "— xem docs/02 §Phạm vi."
)

gen = st.session_state.setdefault("intake_form_gen", 0)
k = lambda name: f"{name}_{gen}"  # noqa: E731 — reset widget keys after mỗi lần lưu

# Nhiều annotator cùng thu thập bài độc lập — cảnh báo (không chặn lưu, annotator tự
# quyết định) ngay tại field title/URL nếu nghi trùng, để dừng sớm thay vì phát hiện
# lúc đã soạn xong cả body_text/chart (xem dedup.py).
with get_session() as session:
    existing_docs = [
        {"id": d.id, "title": d.title, "source_url": d.source_url} for d in session.scalars(select(Document)).all()
    ]

title = st.text_input("Title", key=k("title"))
if title.strip():
    for m in find_duplicates(title, None, existing_docs)[:5]:
        if m.reason == "title_exact":
            st.warning(f"⚠️ Title trùng hệt document #{m.document_id} — \"{m.title[:70]}\"")
        else:
            st.warning(f"⚠️ Title khá giống document #{m.document_id} ({m.score:.0%} tương đồng) — \"{m.title[:70]}\"")

st.subheader("Ảnh chart")
uploaded_files = st.file_uploader(
    "Chọn ảnh (tối đa 3 — ảnh ghép nhiều subplot vẫn tính là 1 ảnh, chọn loại chart 'subplot' bên dưới)",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
    key=k("files"),
)

chart_meta = []
if uploaded_files:
    for i, f in enumerate(uploaded_files[:3]):
        st.markdown(f"**[CHART {i + 1}]** — {f.name}")
        c_img, c_type = st.columns([1, 1])
        with c_img:
            st.image(f, width=180)
        with c_type:
            chart_type = st.selectbox(f"Loại chart #{i + 1}", CHART_TYPES, key=k(f"type_{i}"))
        chart_meta.append({"file": f, "chart_id": f"fig{i + 1}", "chart_type": chart_type})

body_text = st.text_area(
    "Body text — TOÀN VĂN bài báo, chèn [CHART N] tại đúng vị trí chart N xuất hiện",
    height=260,
    key=k("body_text"),
    help=(
        "Lấy toàn bộ text bài báo (không chỉ đoạn liên quan chart) vì có câu hỏi chỉ dựa vào "
        "text mà không chart nào vẽ ra. Chèn [CHART 1], [CHART 2]... vào đúng chỗ ảnh xuất hiện "
        "trong bài. Bỏ hẳn phần bài không liên quan tới chủ đề đang khai thác. Ưu tiên bài dưới "
        f"{MAX_BODY_TEXT_WORDS} từ."
    ),
)

if body_text.strip():
    n_words = word_count(body_text)
    st.caption(f"{n_words} từ" + (" ⚠️ vượt 2000 từ, cân nhắc chọn bài ngắn hơn" if n_words > MAX_BODY_TEXT_WORDS else ""))

st.subheader("Nguồn")
col1, col2 = st.columns(2)
with col1:
    provider = st.text_input("Provider (vd. CafeF, GSO)", key=k("provider"))
    domain = st.selectbox("Domain", DOMAINS, key=k("domain"))
with col2:
    url = st.text_input("URL", key=k("url"))
    if url.strip():
        url_matches = [m for m in find_duplicates(title, url, existing_docs) if m.reason == "url_exact"]
        for m in url_matches[:5]:
            st.error(f"⚠️ URL trùng với document #{m.document_id} — \"{m.title[:70]}\"")
    st.caption(f"Ngày truy cập: tự động = hôm nay ({date.today()})")

if st.button("Lưu document", type="primary", key=k("submit")):
    errors = []
    if not title.strip() or not body_text.strip():
        errors.append("Cần nhập title và body_text.")
    if not uploaded_files:
        errors.append("Cần ít nhất 1 ảnh chart.")
    if len(chart_meta) > MAX_CHARTS_PER_DOCUMENT:
        errors.append(f"Tối đa {MAX_CHARTS_PER_DOCUMENT} chart/document — hiện có {len(chart_meta)}.")
    if chart_meta:
        ok, msg = check_chart_placeholders(body_text, len(chart_meta))
        if not ok:
            errors.append(msg)

    if errors:
        for e in errors:
            st.error(e)
    else:
        with get_session() as session:
            doc = Document(
                title=title.strip(),
                body_text=body_text.strip(),
                source_provider=provider.strip(),
                source_domain=domain,
                source_url=url.strip() or None,
                source_accessed_date=str(date.today()),
                status="intake",
                created_by=current_user().id,
            )
            session.add(doc)
            session.flush()  # get doc.id

            for meta in chart_meta:
                content = meta["file"].getvalue()
                ext = Path(meta["file"].name).suffix.lower() or ".png"
                file_hash = hashlib.sha256(content).hexdigest()[:16]
                image_path = IMAGES_DIR / f"{file_hash}{ext}"
                if not image_path.exists():
                    image_path.write_bytes(content)
                session.add(
                    Chart(
                        document_id=doc.id,
                        chart_id=meta["chart_id"],
                        image_path=str(image_path.relative_to(IMAGES_DIR.parent.parent)),
                        chart_type=meta["chart_type"],
                    )
                )
            session.commit()
        st.success(f"Đã lưu document #{doc.id} với {len(chart_meta)} chart. Sang trang 'Soạn câu hỏi' để tiếp tục.")
        st.session_state["intake_form_gen"] += 1
        st.rerun()
