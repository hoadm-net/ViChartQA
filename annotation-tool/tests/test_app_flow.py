"""Drives the real Streamlit pages via AppTest (not just import-checks) to catch
wiring bugs (session_state keys, form reruns, DB writes) that static review misses.
Uses an isolated test DB via VICHARTQA_DB_PATH — safe to run repeatedly.
"""

import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TEST_DB = ROOT / "tests" / "_test.db"
for suffix in ("", "-wal", "-shm"):
    p = Path(str(TEST_DB) + suffix)
    if p.exists():
        p.unlink()
os.environ["VICHARTQA_DB_PATH"] = str(TEST_DB)

from PIL import Image  # noqa: E402
from sqlalchemy import select  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

from auth import hash_password  # noqa: E402
from db import get_session, init_db  # noqa: E402
from documents import delete_document  # noqa: E402
from models import Chart, Document, Evidence, Question, QuestionVersion, User  # noqa: E402
from versioning import record_version  # noqa: E402

init_db()


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (40, 30), color="red").save(buf, format="PNG")
    return buf.getvalue()


# Real composite chart (pie + grouped bar, 2 subplots) provided during dev to
# validate the subplot flow against an actual figure, not a synthetic placeholder.
_SAMPLE_SUBPLOT_IMAGE = ROOT / "tests" / "fixtures" / "sample_subplot_chart.png"


def _subplot_png_bytes() -> bytes:
    if _SAMPLE_SUBPLOT_IMAGE.exists():
        return _SAMPLE_SUBPLOT_IMAGE.read_bytes()
    return _png_bytes()


def seed_test_user() -> int:
    with get_session() as s:
        existing = s.scalar(select(User).where(User.name == "tester"))
        if existing:
            return existing.id
        u = User(name="tester", pod="B", role="annotator", password_hash=hash_password("x"))
        s.add(u)
        s.commit()
        return u.id


def seed_pm_user() -> int:
    with get_session() as s:
        existing = s.scalar(select(User).where(User.name == "pm_tester"))
        if existing:
            return existing.id
        u = User(name="pm_tester", pod="E", role="pm", password_hash=hash_password("x"))
        s.add(u)
        s.commit()
        return u.id


def seed_data_intake_user() -> int:
    with get_session() as s:
        existing = s.scalar(select(User).where(User.name == "data_intake_tester"))
        if existing:
            return existing.id
        u = User(name="data_intake_tester", pod="A", role="data_intake", password_hash=hash_password("x"))
        s.add(u)
        s.commit()
        return u.id


def _insert_active_question(doc_id: int, user_id: int, question_text: str, answer: str) -> int:
    """Direct DB insert (bypasses the UI) — used to set up fixtures for tests that
    drive a different part of the page than the authoring form itself."""
    with get_session() as s:
        q = Question(
            document_id=doc_id,
            question_text=question_text,
            answer=answer,
            answer_type="text",
            question_type="data_retrieval",
            hop_type="text",
            status="active",
            created_by=user_id,
        )
        s.add(q)
        s.flush()
        s.add(Evidence(question_id=q.id, hop_order=1, source="text", quote="GDP tăng dần theo thời gian."))
        s.flush()
        record_version(s, q, user_id, "created")
        s.commit()
        return q.id


def _select_document(at: AppTest, doc_id: int) -> None:
    doc_select = next(sb for sb in at.selectbox if sb.label == "Chọn document")
    match = next(opt for opt in doc_select.options if opt.startswith(f"#{doc_id} "))
    doc_select.set_value(match)


def _select_doc_manager_row(at: AppTest, doc_id: int) -> None:
    """st.dataframe(on_select=...) has no direct AppTest set_value() — inject the
    selection dict into the session_state key the widget reads on the next rerun
    (same workaround pattern already used for st.data_editor elsewhere in this file)."""
    with get_session() as s:
        ordered_ids = [d.id for d in s.scalars(select(Document).order_by(Document.id.desc())).all()]
    row_idx = ordered_ids.index(doc_id)
    at.session_state["doc_manager_table"] = {"selection": {"rows": [row_idx], "columns": []}}


def test_page1_document_intake_creates_document_and_charts(user_id: int):
    at = AppTest.from_file(str(ROOT / "pages" / "1_document_intake.py"))
    at.session_state["user"] = type("U", (), {"id": user_id})()
    at.run(timeout=15)
    assert not at.exception, at.exception

    at.text_input[0].set_value("Bài test GDP 2011-2021")  # label: Title
    at.file_uploader[0].upload("fig1.png", _png_bytes(), "image/png")
    at.run(timeout=15)
    assert not at.exception, at.exception

    # body_text renders only after the chart section (order: title, files, per-chart
    # config, body_text, source) — must include [CHART 1] or check_chart_placeholders blocks save
    at.text_area[0].set_value("GDP tăng dần theo thời gian. [CHART 1] Đây là toàn văn bài test.")

    text_inputs = {ti.label: ti for ti in at.text_input}
    text_inputs["Provider (vd. CafeF, GSO)"].set_value("TestProvider")
    domain_select = next(sb for sb in at.selectbox if sb.label == "Domain")
    domain_select.set_value("economics")
    at.run(timeout=15)

    save_btn = next(b for b in at.button if b.label == "Lưu document")
    save_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception

    with get_session() as s:
        docs = s.scalars(select(Document)).all()
        assert len(docs) == 1, "document was not created"
        doc = docs[0]
        assert doc.title == "Bài test GDP 2011-2021"
        assert doc.status == "intake"
        assert doc.created_by == user_id
        assert doc.source_accessed_date  # auto-set, no manual date widget anymore
        charts = s.scalars(select(Chart).where(Chart.document_id == doc.id)).all()
        assert len(charts) == 1, "chart was not created"
        assert charts[0].chart_id == "fig1"
    return doc.id


def test_page1_missing_chart_placeholder_blocks_save(user_id: int):
    """body_text thiếu [CHART 1] phải bị chặn lưu — xem validation.check_chart_placeholders."""
    at = AppTest.from_file(str(ROOT / "pages" / "1_document_intake.py"))
    at.session_state["user"] = type("U", (), {"id": user_id})()
    at.run(timeout=15)

    at.text_input[0].set_value("Bài test thiếu placeholder")
    at.file_uploader[0].upload("fig1.png", _png_bytes(), "image/png")
    at.run(timeout=15)

    at.text_area[0].set_value("Bài này không có placeholder chart nào cả.")
    text_inputs = {ti.label: ti for ti in at.text_input}
    text_inputs["Provider (vd. CafeF, GSO)"].set_value("TestProvider")
    at.run(timeout=15)

    with get_session() as s:
        before_count = len(s.scalars(select(Document)).all())

    save_btn = next(b for b in at.button if b.label == "Lưu document")
    save_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception
    assert at.error, "expected a validation error for missing [CHART 1] placeholder"

    with get_session() as s:
        after_count = len(s.scalars(select(Document)).all())
    assert after_count == before_count, "document should not be saved when placeholder check fails"


def test_page1_subplot_image_creates_one_chart_with_subplot_type(user_id: int):
    """1 ảnh ghép nhiều panel (pie + grouped bar, ảnh thật) chọn chart_type='subplot'
    phải tạo đúng 1 Chart row — không tách nhãn fig1a/fig1b vì ảnh gốc không có nhãn đó
    (xem docs/02 §Phạm vi — Ảnh có subplot)."""
    at = AppTest.from_file(str(ROOT / "pages" / "1_document_intake.py"))
    at.session_state["user"] = type("U", (), {"id": user_id})()
    at.run(timeout=15)

    at.text_input[0].set_value("Bài test subplot")
    at.file_uploader[0].upload("composite.png", _subplot_png_bytes(), "image/png")
    at.run(timeout=15)
    assert not at.exception, at.exception

    type_select = next(sb for sb in at.selectbox if sb.label == "Loại chart #1")
    type_select.set_value("subplot")
    at.run(timeout=15)

    at.text_area[0].set_value(
        "Tỷ trọng nguồn cung và giá bán sơ cấp theo địa phương, vẽ chung 1 hình 2 subplot. [CHART 1]"
    )
    text_inputs = {ti.label: ti for ti in at.text_input}
    text_inputs["Provider (vd. CafeF, GSO)"].set_value("TestProvider")
    domain_select = next(sb for sb in at.selectbox if sb.label == "Domain")
    domain_select.set_value("economics")
    at.run(timeout=15)

    save_btn = next(b for b in at.button if b.label == "Lưu document")
    save_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception

    with get_session() as s:
        doc = s.scalars(select(Document).where(Document.title == "Bài test subplot")).first()
        assert doc is not None
        charts = s.scalars(select(Chart).where(Chart.document_id == doc.id)).all()
        assert len(charts) == 1, [c.chart_id for c in charts]
        assert charts[0].chart_id == "fig1"
        assert charts[0].chart_type == "subplot"


def test_page2_document_manager_lists_and_shows_selected_document(doc_id: int, user_id: int):
    at = AppTest.from_file(str(ROOT / "pages" / "2_document_manager.py"))
    at.session_state["user"] = type("U", (), {"id": user_id, "role": "annotator"})()
    at.run(timeout=15)
    assert not at.exception, at.exception
    assert at.dataframe, "document table did not render"

    _select_doc_manager_row(at, doc_id)
    at.run(timeout=15)
    assert not at.exception, at.exception
    assert any(f"#{doc_id}" in h.value for h in at.subheader), "selected document detail did not render"


def test_page2_document_manager_hides_edit_and_delete_for_annotator(doc_id: int, user_id: int):
    at = AppTest.from_file(str(ROOT / "pages" / "2_document_manager.py"))
    at.session_state["user"] = type("U", (), {"id": user_id, "role": "annotator"})()
    at.run(timeout=15)
    _select_doc_manager_row(at, doc_id)
    at.run(timeout=15)
    assert not at.exception, at.exception
    assert not any(b.label == "Lưu thay đổi" for b in at.button), "annotator should not see the edit form"
    actions = at.dataframe[0].value["actions"].tolist()
    assert all(len(a) == 0 for a in actions), "annotator should not see the row-level delete action"


def test_page2_document_manager_edit_as_data_intake(doc_id: int, data_intake_id: int):
    at = AppTest.from_file(str(ROOT / "pages" / "2_document_manager.py"))
    at.session_state["user"] = type("U", (), {"id": data_intake_id, "role": "data_intake"})()
    at.run(timeout=15)
    _select_doc_manager_row(at, doc_id)
    at.run(timeout=15)
    assert not at.exception, at.exception

    text_inputs = {ti.label: ti for ti in at.text_input}
    text_inputs["Title"].set_value("Bài test GDP 2011-2021 (đã sửa)")
    at.run(timeout=15)

    save_btn = next(b for b in at.button if b.label == "Lưu thay đổi")
    save_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception

    with get_session() as s:
        assert s.get(Document, doc_id).title == "Bài test GDP 2011-2021 (đã sửa)"
    actions = at.dataframe[0].value["actions"].tolist()
    assert all(len(a) == 0 for a in actions), "data_intake should not see the row-level delete action"


def test_page2_document_manager_edit_blocked_by_placeholder_mismatch(doc_id: int, pm_id: int):
    at = AppTest.from_file(str(ROOT / "pages" / "2_document_manager.py"))
    at.session_state["user"] = type("U", (), {"id": pm_id, "role": "pm"})()
    at.run(timeout=15)
    _select_doc_manager_row(at, doc_id)
    at.run(timeout=15)
    assert not at.exception, at.exception

    with get_session() as s:
        title_before = s.get(Document, doc_id).title

    text_areas = {ta.label: ta for ta in at.text_area}
    text_areas["Body text"].set_value("Không có placeholder chart nào ở đây cả.")
    at.run(timeout=15)

    save_btn = next(b for b in at.button if b.label == "Lưu thay đổi")
    save_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception
    assert at.error, "expected a validation error for missing [CHART N] placeholder"

    with get_session() as s:
        assert s.get(Document, doc_id).title == title_before, "document should not be saved when validation fails"


def _make_throwaway_document_with_question(user_id: int) -> tuple[int, int]:
    """Document độc lập (không đụng doc_id chính của các test khác) có 1 chart + 1 câu
    hỏi + evidence + version — đủ để kiểm chứng xoá cascade đúng thứ tự phụ thuộc."""
    with get_session() as s:
        doc = Document(
            title="Document sẽ bị xoá",
            body_text="Nội dung test. [CHART 1]",
            source_provider="Test",
            source_domain="economics",
            status="intake",
            created_by=user_id,
        )
        s.add(doc)
        s.flush()
        s.add(
            Chart(
                document_id=doc.id,
                chart_id="fig1",
                image_path="data/images/does_not_matter.png",
                chart_type="line",
            )
        )
        q = Question(
            document_id=doc.id,
            question_text="Câu hỏi tạm",
            answer="tạm",
            answer_type="text",
            question_type="data_retrieval",
            hop_type="text",
            status="active",
            created_by=user_id,
        )
        s.add(q)
        s.flush()
        s.add(Evidence(question_id=q.id, hop_order=1, source="text", quote="Nội dung test."))
        s.flush()
        record_version(s, q, user_id, "created")
        s.commit()
        return doc.id, q.id


def test_documents_delete_document_cascades_in_dependency_order(user_id: int):
    """Gọi thẳng documents.delete_document() (không qua UI) — đây là phần logic thật
    sự cần kiểm chứng: FK constraints (PRAGMA foreign_keys=ON, xem db.py) đòi hỏi
    Evidence/QuestionVersion phải bị xoá trước Chart/Question/Document, và
    Evidence.chart_id không có relationship() nên SQLAlchemy không tự đảm bảo thứ tự
    đó nếu chỉ gọi session.delete(document)."""
    target_doc_id, target_question_id = _make_throwaway_document_with_question(user_id)

    with get_session() as s:
        delete_document(s, target_doc_id)

    with get_session() as s:
        assert s.get(Document, target_doc_id) is None
        assert s.get(Question, target_question_id) is None
        assert not s.scalars(select(Chart).where(Chart.document_id == target_doc_id)).all()
        assert not s.scalars(select(Evidence).where(Evidence.question_id == target_question_id)).all()
        assert not s.scalars(select(QuestionVersion).where(QuestionVersion.question_id == target_question_id)).all()


def test_page2_document_manager_delete_button_requires_pm(pm_id: int, user_id: int):
    """UI-level: cột "actions" trong bảng chỉ có nút xoá cho role pm. Nút xoá là 1
    st.column_config.ButtonColumn bên trong st.dataframe — AppTest không có API
    set_value()/click() cho kiểu widget này, nên mô phỏng cú click bằng cách set thẳng
    session_state mà on_click handler (handle_row_delete_click) ghi vào, rồi kiểm tra
    đúng modal xác nhận mở ra (nêu tên document, không xoá ngay). Hoàn tất thao tác
    xoá 2 bước qua st.dialog được kiểm chứng riêng bằng
    test_documents_delete_document_cascades_in_dependency_order ở trên —
    streamlit.testing.v1.AppTest không mô phỏng đáng tin cậy việc 1 dialog vẫn "mở"
    qua nhiều lần rerun khi nút mở dialog ở ngoài không còn ở trạng thái "vừa được
    bấm" nữa."""
    target_doc_id, _ = _make_throwaway_document_with_question(user_id)

    at = AppTest.from_file(str(ROOT / "pages" / "2_document_manager.py"))
    at.session_state["user"] = type("U", (), {"id": user_id, "role": "annotator"})()
    at.run(timeout=15)
    assert all(len(a) == 0 for a in at.dataframe[0].value["actions"].tolist()), (
        "annotator should not see the row-level delete action"
    )

    at = AppTest.from_file(str(ROOT / "pages" / "2_document_manager.py"))
    at.session_state["user"] = type("U", (), {"id": pm_id, "role": "pm"})()
    at.run(timeout=15)
    assert any(len(a) > 0 for a in at.dataframe[0].value["actions"].tolist()), "pm should see the row-level delete action"

    at.session_state["pending_delete_doc_id"] = target_doc_id
    at.run(timeout=15)
    assert not at.exception, at.exception
    assert any(b.label == "Xoá vĩnh viễn" for b in at.button), "confirmation dialog did not open"
    assert any("Document sẽ bị xoá" in w.value for w in at.warning), "confirmation dialog missing document title"

    with get_session() as s:
        assert s.get(Document, target_doc_id) is not None, "should not delete until the dialog is confirmed"


def test_page3_manual_add_creates_active_question_with_version(doc_id: int, user_id: int):
    at = AppTest.from_file(str(ROOT / "pages" / "3_question_workspace.py"))
    at.session_state["user"] = type("U", (), {"id": user_id})()
    at.run(timeout=15)
    assert not at.exception, at.exception

    _select_document(at, doc_id)
    at.run(timeout=15)
    assert not at.exception, at.exception
    # ảnh chart phải thực sự render trong phần document context — không chỉ "không lỗi",
    # vì image_path.exists() sai đường dẫn sẽ âm thầm bỏ qua st.image() mà không raise gì cả
    assert at.image, "chart image did not render in the document context section"

    text_areas = {ta.label: ta for ta in at.text_area}
    text_areas["Câu hỏi"].set_value("GDP năm 2021 là bao nhiêu?")
    text_inputs = {ti.label: ti for ti in at.text_input}
    text_inputs["Đáp án"].set_value("8.4")
    # question_type/answer_type left at defaults: data_retrieval/numeric; hop_type
    # explicitly "chart" để khớp với evidence nguồn chart điền bên dưới.
    hop_select = next(sb for sb in at.selectbox if sb.label == "hop_type")
    hop_select.set_value("chart")
    at.run(timeout=15)

    # evidence: nguồn mặc định "chart" — description giờ là 1 textarea tự do (các bước
    # truy hồi giá trị), không cần data_table điền trước.
    text_areas = {ta.label: ta for ta in at.text_area}
    text_areas["Cách đọc (đánh số từng bước)"].set_value("1. Tìm đường GDP. 2. Đọc giá trị năm 2021.")
    at.run(timeout=15)
    assert not at.exception, at.exception

    save_btn = next(b for b in at.button if b.label == "Lưu câu hỏi")
    save_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception

    with get_session() as s:
        q = s.scalars(select(Question).where(Question.document_id == doc_id)).first()
        assert q is not None, "question was not created"
        assert q.question_text == "GDP năm 2021 là bao nhiêu?"
        assert q.answer == "8.4"
        assert q.status == "active"
        assert q.created_by == user_id
        assert q.hop_type == "chart"
        evidence = s.scalars(select(Evidence).where(Evidence.question_id == q.id)).all()
        assert len(evidence) == 1
        assert evidence[0].source == "chart"
        assert evidence[0].description == "1. Tìm đường GDP. 2. Đọc giá trị năm 2021."
        versions = s.scalars(select(QuestionVersion).where(QuestionVersion.question_id == q.id)).all()
        assert len(versions) == 1, versions
        assert versions[0].change_type == "created"
        assert versions[0].version_number == 1
    return q.id


def test_page3_edit_active_question_creates_second_version(doc_id: int, question_id: int, user_id: int):
    at = AppTest.from_file(str(ROOT / "pages" / "3_question_workspace.py"))
    at.session_state["user"] = type("U", (), {"id": user_id})()
    at.run(timeout=15)
    _select_document(at, doc_id)
    at.run(timeout=15)
    assert not at.exception, at.exception

    edit_btn = next(b for b in at.button if b.key == f"edit_q_{question_id}")
    edit_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception

    text_inputs = {ti.label: ti for ti in at.text_input}
    text_inputs["Đáp án"].set_value("8.5")
    at.run(timeout=15)

    save_btn = next(b for b in at.button if b.label == "Lưu câu hỏi")
    save_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception

    with get_session() as s:
        q = s.get(Question, question_id)
        assert q.answer == "8.5"
        assert q.status == "active"
        versions = sorted(
            s.scalars(select(QuestionVersion).where(QuestionVersion.question_id == question_id)).all(),
            key=lambda v: v.version_number,
        )
        assert len(versions) == 2, versions
        assert versions[-1].change_type == "edited"
        assert versions[-1].version_number == 2


def test_page3_reject_question_marks_rejected_with_version(doc_id: int, user_id: int):
    """Câu hỏi riêng cho test này (không đụng câu #manual-add) để không làm rỗng
    pool câu active mà test export bên dưới cần."""
    question_id = _insert_active_question(doc_id, user_id, "Câu hỏi sẽ bị rút lại", "tạm")

    at = AppTest.from_file(str(ROOT / "pages" / "3_question_workspace.py"))
    at.session_state["user"] = type("U", (), {"id": user_id})()
    at.run(timeout=15)
    _select_document(at, doc_id)
    at.run(timeout=15)
    assert not at.exception, at.exception

    reject_btn = next(b for b in at.button if b.key == f"reject_q_{question_id}")
    reject_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception

    with get_session() as s:
        q = s.get(Question, question_id)
        assert q.status == "rejected", q.status
        versions = sorted(
            s.scalars(select(QuestionVersion).where(QuestionVersion.question_id == question_id)).all(),
            key=lambda v: v.version_number,
        )
        assert versions[-1].change_type == "rejected"


def test_page3_llm_suggestion_prefill_requires_explicit_save(doc_id: int, user_id: int):
    """Gợi ý LLM chỉ hiển thị tham khảo — không được tự lưu vào questions; chỉ khi
    annotator bấm "Lưu câu hỏi" trên form (sau khi "Dùng làm mẫu") mới tạo bản ghi.
    LLM không sinh evidence (xem vlm_client.py) — "Dùng làm mẫu" chỉ nạp câu
    hỏi/đáp án, evidence builder phải trống, annotator tự điền tay mới lưu được."""
    at = AppTest.from_file(str(ROOT / "pages" / "3_question_workspace.py"))
    at.session_state["user"] = type("U", (), {"id": user_id})()
    at.run(timeout=15)
    _select_document(at, doc_id)
    at.run(timeout=15)
    assert not at.exception, at.exception

    # bơm thẳng 1 gợi ý giả lập vào session_state, bỏ qua lệnh gọi API thật
    at.session_state["llm_suggestions"] = [
        {
            "question": "Bài viết mô tả xu hướng GDP như thế nào?",
            "answer": "GDP tăng dần theo thời gian.",
            "answer_type": "text",
            "question_type": "data_retrieval",
            "hop_type": "chart",
            "derivation": "",
            "choices": None,
        }
    ]
    at.run(timeout=15)
    assert not at.exception, at.exception

    with get_session() as s:
        before_count = len(s.scalars(select(Question).where(Question.document_id == doc_id)).all())

    use_btn = next(b for b in at.button if b.key == "use_sug_0")
    use_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception

    with get_session() as s:
        after_prefill_count = len(s.scalars(select(Question).where(Question.document_id == doc_id)).all())
    assert after_prefill_count == before_count, "'Dùng làm mẫu' phải chỉ nạp vào form, không tự lưu"
    assert (
        at.session_state["workspace_form_initial"]["question_text"]
        == "Bài viết mô tả xu hướng GDP như thế nào?"
    )
    assert "evidence" not in at.session_state["workspace_form_initial"], "gợi ý LLM không được kèm evidence"

    # evidence builder mặc định trống (nguồn "chart", description rỗng) — Lưu ngay phải bị chặn
    save_btn = next(b for b in at.button if b.label == "Lưu câu hỏi")
    save_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception
    assert at.error, "thiếu evidence phải bị chặn lưu ngay cả khi câu hỏi đến từ gợi ý LLM"

    with get_session() as s:
        assert (
            s.scalars(
                select(Question).where(
                    Question.document_id == doc_id,
                    Question.question_text == "Bài viết mô tả xu hướng GDP như thế nào?",
                )
            ).first()
            is None
        )

    # annotator tự điền evidence tay rồi mới lưu được
    text_areas = {ta.label: ta for ta in at.text_area}
    text_areas["Cách đọc (đánh số từng bước)"].set_value("1. Tìm đường GDP. 2. Đọc giá trị năm 2011 và 2021.")
    at.run(timeout=15)

    save_btn = next(b for b in at.button if b.label == "Lưu câu hỏi")
    save_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception

    with get_session() as s:
        q = s.scalars(
            select(Question).where(
                Question.document_id == doc_id,
                Question.question_text == "Bài viết mô tả xu hướng GDP như thế nào?",
            )
        ).first()
        assert q is not None, "explicit Lưu sau khi tự điền evidence phải tạo được câu hỏi"
        assert q.status == "active"
    assert "workspace_form_initial" not in at.session_state


def test_page4_dashboard_renders_without_exception(user_id: int):
    at = AppTest.from_file(str(ROOT / "pages" / "4_dashboard.py"))
    at.session_state["user"] = type("U", (), {"id": user_id})()
    at.run(timeout=15)
    assert not at.exception, at.exception


def test_page5_export_assign_split_and_generate_file(doc_id: int, user_id: int):
    at = AppTest.from_file(str(ROOT / "pages" / "5_export.py"))
    at.session_state["user"] = type("U", (), {"id": user_id})()
    at.run(timeout=15)
    assert not at.exception, at.exception

    assign_btn = next(b for b in at.button if b.label == "Gán split cho document chưa có")
    assign_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception

    with get_session() as s:
        assert s.get(Document, doc_id).split is not None

    export_btn = next(b for b in at.button if b.label == "Tạo file export")
    export_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception
    assert at.session_state["export_preview"], "expected at least one document in the export preview"


if __name__ == "__main__":
    user_id = seed_test_user()
    pm_id = seed_pm_user()
    data_intake_id = seed_data_intake_user()
    doc_id = test_page1_document_intake_creates_document_and_charts(user_id)
    print(f"PASS test_page1 (doc_id={doc_id})")
    test_page1_missing_chart_placeholder_blocks_save(user_id)
    print("PASS test_page1_missing_placeholder")
    test_page1_subplot_image_creates_one_chart_with_subplot_type(user_id)
    print("PASS test_page1_subplot")

    test_page2_document_manager_lists_and_shows_selected_document(doc_id, user_id)
    print("PASS test_page2_document_manager_list")
    test_page2_document_manager_hides_edit_and_delete_for_annotator(doc_id, user_id)
    print("PASS test_page2_document_manager_permissions_annotator")
    test_page2_document_manager_edit_as_data_intake(doc_id, data_intake_id)
    print("PASS test_page2_document_manager_edit")
    test_page2_document_manager_edit_blocked_by_placeholder_mismatch(doc_id, pm_id)
    print("PASS test_page2_document_manager_edit_blocked")
    test_documents_delete_document_cascades_in_dependency_order(user_id)
    print("PASS test_documents_delete_document_cascade")
    test_page2_document_manager_delete_button_requires_pm(pm_id, user_id)
    print("PASS test_page2_document_manager_delete_button")

    question_id = test_page3_manual_add_creates_active_question_with_version(doc_id, user_id)
    print(f"PASS test_page3_manual_add (question_id={question_id})")
    test_page3_edit_active_question_creates_second_version(doc_id, question_id, user_id)
    print("PASS test_page3_edit")
    test_page3_reject_question_marks_rejected_with_version(doc_id, user_id)
    print("PASS test_page3_reject")
    test_page3_llm_suggestion_prefill_requires_explicit_save(doc_id, user_id)
    print("PASS test_page3_llm_suggestion_prefill")

    test_page4_dashboard_renders_without_exception(user_id)
    print("PASS test_page4_dashboard")
    test_page5_export_assign_split_and_generate_file(doc_id, user_id)
    print("PASS test_page5_export")
    print("\nAll integration tests passed.")
