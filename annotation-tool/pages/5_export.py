"""Export dataset cuối kỳ (data freeze) — xem docs/02 §Schema.
Chỉ lấy câu hỏi status active, gán split theo document (không theo câu hỏi).
"""

import json
from pathlib import Path
import tempfile

import streamlit as st
from sqlalchemy import select

from auth import require_login
from db import get_session
from export import (
    EXPORT_ELIGIBLE_STATUSES,
    assign_splits,
    build_dataset,
    export_to_directory,
    export_to_zip,
    format_size,
    get_export_manifest,
)
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
st.caption(
    "Chia ~77/10/13 theo document, không theo câu hỏi, để tránh leakage. "
    "Idempotent — chạy lại không đụng document đã có split."
)
if st.button("Gán split cho document chưa có"):
    with get_session() as write_session:
        n = assign_splits(write_session)
        write_session.commit()
    if n > 0:
        st.success(f"Đã gán split cho {n} document.")
    else:
        st.info("Tất cả document đã có split hoặc chưa có document nào.")
    st.rerun()

st.divider()

st.subheader("2. Export dataset package")
require_split = st.checkbox(
    "Chỉ export document đã có split (khuyến nghị cho bản export chính thức)", value=True
)

if st.button("Tạo file export", type="primary"):
    # Clean up previous temporary zip file if exists to prevent disk leak
    old_manifest = st.session_state.get("export_manifest")
    if old_manifest and old_manifest.get("zip_path"):
        try:
            Path(old_manifest["zip_path"]).unlink(missing_ok=True)
        except Exception:
            pass

    with get_session() as session:
        # Create disk-backed temporary zip file to avoid RAM / OOM issues
        tmp_zip = tempfile.NamedTemporaryFile(prefix="vichartqa_export_", suffix=".zip", delete=False)
        tmp_zip.close()
        manifest = export_to_zip(tmp_zip.name, session=session, require_split=require_split)

    st.session_state["export_preview"] = manifest["dataset"]
    st.session_state["export_manifest"] = manifest

manifest = st.session_state.get("export_manifest")
if manifest is not None:
    dataset = manifest["dataset"]
    st.markdown("### 📊 Thống kê gói export")
    if manifest["num_documents"] == 0:
        st.info("ℹ️ Không có tài liệu nào đủ điều kiện export. Hãy gán split (mục 1) và đảm bảo có câu hỏi với trạng thái active.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Eligible Documents", manifest["num_documents"])
    m2.metric("Số câu hỏi (active)", manifest["num_questions"])
    m3.metric("Ảnh chart đóng gói", manifest["unique_image_count"])
    m4.metric("Dung lượng ảnh", format_size(manifest["total_image_bytes"]))

    # Asset integrity feedback
    if manifest["missing_images"]:
        st.warning(
            f"⚠️ Cảnh báo toàn vẹn dữ liệu: Phát hiện {len(manifest['missing_images'])} ảnh "
            "trong DB không tìm thấy trên ổ đĩa. Gói export được tạo với các ảnh còn lại."
        )
        with st.expander("Chi tiết ảnh bị thiếu trên ổ đĩa"):
            for m in manifest["missing_images"]:
                st.caption(f"- `{m}`")
    else:
        st.success("✅ Toàn vẹn dữ liệu ảnh: 100% ảnh biểu đồ tham chiếu trong DB đã được tìm thấy.")

    st.markdown("#### 📦 Tải xuống hoặc xuất dữ liệu")

    # a) Download ZIP (deferred read via callable to prevent buffering in RAM during page render)
    zip_path = manifest.get("zip_path")
    if zip_path and Path(zip_path).exists():
        def _read_zip_file():
            with open(zip_path, "rb") as f:
                return f.read()

        st.download_button(
            label="📦 Tải trọn bộ dataset (ZIP)",
            data=_read_zip_file,
            file_name="vichartqa_export.zip",
            mime="application/zip",
            key="btn_download_zip",
            help="Bao gồm vichartqa.json và thư mục images/ chứa đầy đủ file ảnh chart",
        )

    # b) Option to export directly to a local directory
    st.markdown("---")
    st.markdown("#### 📁 Xuất trực tiếp ra thư mục máy tính (Local Directory)")
    default_export_dir = str(
        Path(__file__).resolve().parent.parent / "exports" / "vichartqa_export"
    )
    col_dir, col_btn = st.columns([3, 1])
    with col_dir:
        target_dir = st.text_input(
            "Đường dẫn thư mục",
            value=default_export_dir,
            help="Thư mục sẽ chứa file vichartqa.json và thư mục con images/",
            key="export_target_dir",
        )
    with col_btn:
        st.write("")
        st.write("")
        if st.button("Xuất ra thư mục", key="btn_export_dir"):
            target_cleaned = target_dir.strip()
            if not target_cleaned:
                st.error("Vui lòng nhập đường dẫn thư mục hợp lệ.")
            else:
                try:
                    res = export_to_directory(target_cleaned, dataset=dataset, manifest=manifest)
                    msg = (
                        f"Đã xuất thành công gói dataset ra `{res['output_dir']}` "
                        f"({res['unique_image_count']} ảnh, {res['num_documents']} tài liệu)."
                    )
                    if res.get("copy_errors"):
                        st.warning(f"{msg}\nCảnh báo: Có {len(res['copy_errors'])} ảnh không sao chép được.")
                    else:
                        st.success(msg)
                except Exception as e:
                    st.error(f"Lỗi khi xuất ra thư mục: {e}")

    # c) JSON-only download
    st.markdown("---")
    st.markdown("#### 📄 Tải riêng lẻ file JSON")
    st.download_button(
        "Tải vichartqa.json",
        data=json.dumps(dataset, ensure_ascii=False, indent=2),
        file_name="vichartqa.json",
        mime="application/json",
        key="btn_download_json",
    )

    with st.expander("Xem trước cấu trúc JSON (tài liệu đầu tiên)", expanded=False):
        st.json(dataset[:1] if dataset else [], expanded=True)
