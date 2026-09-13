"""Kiểm thử tính năng chọn ngẫu nhiên tài liệu có >= 2 biểu đồ, ưu tiên tài liệu có ít câu hỏi nhất.
Chạy trực tiếp trên dataset thật data/cloud/vichartqa.db (ở chế độ read-only).
"""

import random
import time
from pathlib import Path
import pytest
from sqlalchemy import case, create_engine, func, select
from sqlalchemy.orm import sessionmaker

# Path tới dataset cloud thực tế
CLOUD_DB_PATH = Path(r"c:\Users\Admin\HUIT - Học Tập\Năm 3\Research\data\cloud\vichartqa.db")

# Import models
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from models import Chart, Document, Question


@pytest.fixture(scope="module")
def cloud_session():
    assert CLOUD_DB_PATH.exists(), f"Không tìm thấy database thực tế tại: {CLOUD_DB_PATH}"
    # Mở ở chế độ read-only URI để tuyệt đối không làm thay đổi dữ liệu thật
    engine = create_engine(
        f"sqlite:///file:{CLOUD_DB_PATH.as_posix()}?mode=ro&uri=true",
        connect_args={"check_same_thread": False},
    )
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_cloud_db_query_and_multi_chart_counts(cloud_session):
    """Xác minh truy vấn đếm chart và câu hỏi trên dataset thật 1.473 documents."""
    start_t = time.perf_counter()
    chart_cnt_subq = (
        select(Chart.document_id, func.count(Chart.id).label("chart_cnt"))
        .group_by(Chart.document_id)
        .subquery()
    )
    doc_stmt = (
        select(
            Document.id,
            Document.title,
            func.coalesce(chart_cnt_subq.c.chart_cnt, 0).label("chart_cnt"),
            func.count(case((Question.status == "active", Question.id))).label("active_cnt"),
            func.count(Question.id).label("total_cnt"),
        )
        .outerjoin(chart_cnt_subq, Document.id == chart_cnt_subq.c.document_id)
        .outerjoin(Question, Document.id == Question.document_id)
        .group_by(Document.id, Document.title, chart_cnt_subq.c.chart_cnt)
        .order_by(Document.id)
    )
    doc_rows = cloud_session.execute(doc_stmt).all()
    duration_ms = (time.perf_counter() - start_t) * 1000

    # Kiểm tra tổng số documents
    assert len(doc_rows) == 1473, f"Kỳ vọng 1473 documents nhưng nhận được {len(doc_rows)}"
    # Kiểm tra hiệu năng: dưới 500ms cho truy vấn toàn bộ 1.473 docs và 10.009 questions
    assert duration_ms < 500, f"Truy vấn mất quá nhiều thời gian: {duration_ms:.1f}ms"

    # Lọc danh sách multi_chart_docs có chart_cnt >= 2 và active_cnt >= 2
    multi_chart_docs = [(d_id, active_cnt) for d_id, d_title, chart_cnt, active_cnt, total_cnt in doc_rows if chart_cnt >= 2 and active_cnt >= 2]
    assert len(multi_chart_docs) == 463, f"Kỳ vọng 463 documents có >= 2 charts và >= 2 quests nhưng nhận được {len(multi_chart_docs)}"

    # Kiểm tra nhóm ít câu hỏi nhất (min_q = 2)
    min_q = min(cnt for _, cnt in multi_chart_docs)
    assert min_q == 2, f"Kỳ vọng min active questions là 2, nhận được {min_q}"

    two_q_docs = [did for did, cnt in multi_chart_docs if cnt == 2]
    assert len(two_q_docs) == 1, f"Kỳ vọng 1 document có 2 questions, nhận được {len(two_q_docs)}"


def test_priority_random_selection_logic(cloud_session):
    """Kiểm tra thuật toán chọn ngẫu nhiên có ưu tiên ít câu hỏi nhất (với điều kiện >= 2 câu hỏi)."""
    chart_cnt_subq = (
        select(Chart.document_id, func.count(Chart.id).label("chart_cnt"))
        .group_by(Chart.document_id)
        .subquery()
    )
    doc_stmt = (
        select(
            Document.id,
            func.coalesce(chart_cnt_subq.c.chart_cnt, 0).label("chart_cnt"),
            func.count(case((Question.status == "active", Question.id))).label("active_cnt"),
        )
        .outerjoin(chart_cnt_subq, Document.id == chart_cnt_subq.c.document_id)
        .outerjoin(Question, Document.id == Question.document_id)
        .group_by(Document.id, chart_cnt_subq.c.chart_cnt)
    )
    doc_rows = cloud_session.execute(doc_stmt).all()
    multi_chart_docs = [(d_id, active_cnt) for d_id, chart_cnt, active_cnt in doc_rows if chart_cnt >= 2 and active_cnt >= 2]
    doc_q_map = dict(multi_chart_docs)

    # Lần 1: Chưa có curr_id, phải chọn doc có min_q (2 câu hỏi)
    min_q = min(cnt for _, cnt in multi_chart_docs)
    assert min_q == 2
    pool = [did for did, cnt in multi_chart_docs if cnt == min_q]
    chosen_1 = random.choice(pool)
    assert doc_q_map[chosen_1] == 2

    # Lần 2: curr_id là chosen_1 (doc duy nhất có 2 câu hỏi). Anti-deadlock phải nhảy sang mức kế tiếp (4 câu hỏi)
    candidates = [did for did in pool if did != chosen_1]
    assert len(candidates) == 0
    next_pool = [did for did, cnt in multi_chart_docs if cnt > min_q]
    next_min_q = min(cnt for did, cnt in multi_chart_docs if cnt > min_q)
    assert next_min_q == 4
    candidates = [did for did, cnt in multi_chart_docs if cnt == next_min_q and did != chosen_1]
    assert len(candidates) == 11  # có 11 doc có 4 câu hỏi
    chosen_2 = random.choice(candidates)
    assert doc_q_map[chosen_2] == 4

    # Lần 3: curr_id là chosen_2 (1 trong 11 doc có 4 câu hỏi). Thuật toán tiếp tục chọn trong 10 doc còn lại của mức 4 câu hỏi
    candidates_2 = [did for did, cnt in multi_chart_docs if cnt == next_min_q and did != chosen_2]
    assert len(candidates_2) == 10
    chosen_3 = random.choice(candidates_2)
    assert doc_q_map[chosen_3] == 4
    assert chosen_3 != chosen_2


def test_anti_deadlock_when_min_group_has_single_element():
    """Kiểm tra cơ chế chống kẹt khi chỉ có đúng 1 tài liệu ở mức min_q và trùng với doc hiện tại."""
    # Mock danh sách multi_chart_docs:
    # Doc 101 có 0 câu hỏi (duy nhất 1 doc có 0 câu hỏi)
    # Doc 102, 103 có 1 câu hỏi
    # Doc 104 có 2 câu hỏi
    multi_chart_docs = [
        (101, 0),
        (102, 1),
        (103, 1),
        (104, 2),
    ]

    curr_id = 101  # Người dùng đang mở doc 101 và bấm random để tìm bài khác

    min_q = min(cnt for _, cnt in multi_chart_docs)
    pool = [did for did, cnt in multi_chart_docs if cnt == min_q]  # [101]
    candidates = [did for did in pool if did != curr_id]  # [] -> bị rỗng!

    assert len(candidates) == 0

    # Cơ chế anti-deadlock kích hoạt:
    next_pool = [did for did, cnt in multi_chart_docs if cnt > min_q]
    if next_pool:
        next_min_q = min(cnt for did, cnt in multi_chart_docs if cnt > min_q)
        candidates = [did for did, cnt in multi_chart_docs if cnt == next_min_q and did != curr_id] or [curr_id]
    else:
        candidates = pool

    # Candidates phải mở rộng sang nhóm có 1 câu hỏi: [102, 103]
    assert set(candidates) == {102, 103}
    chosen_id = random.choice(candidates)
    assert chosen_id in (102, 103)
    assert chosen_id != 101


def test_apptest_random_button_click():
    """Kiểm tra mô phỏng UI qua AppTest khi click button '🎲 Random doc (≥2 charts)'."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "pages" / "3_question_workspace.py"))
    at.session_state["user"] = type("U", (), {"id": 1, "role": "annotator"})()
    at.run(timeout=15)
    assert not at.exception, at.exception

    # Tìm button random
    random_btn = next((b for b in at.button if "Random doc" in b.label), None)
    assert random_btn is not None, "Không tìm thấy button Random doc trên giao diện"

    # Click button và chạy rerun
    random_btn.click()
    at.run(timeout=15)
    assert not at.exception, at.exception

    # Kiểm tra session_state có doc_id hợp lệ
    assert "workspace_doc_id" in at.session_state, "workspace_doc_id không được set sau khi click"
    selected_doc_id = at.session_state["workspace_doc_id"]
    assert selected_doc_id is not None, "workspace_doc_id là None"

