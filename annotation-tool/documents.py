"""Document-lifecycle operations that need to be called from a page but tested
directly, without going through Streamlit — same convention as validation.py/versioning.py.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models import Chart, Document, Evidence, Question, QuestionVersion


def delete_document(session: Session, doc_id: int) -> None:
    """Xoá 1 document cùng toàn bộ câu hỏi/evidence/lịch sử liên quan.

    Xoá tường minh theo đúng thứ tự phụ thuộc (evidence/question_versions → questions
    → charts → document) thay vì dựa vào cascade ORM một mình: Evidence.chart_id là
    cột FK trần (không có relationship() riêng tới Chart), nên SQLAlchemy không đảm
    bảo thứ tự xoá đúng giữa 2 nhánh anh em (Document.charts vs Document.questions) —
    xoá sai thứ tự sẽ vỡ FK khi PRAGMA foreign_keys=ON (xem db.py).
    """
    question_ids = session.scalars(select(Question.id).where(Question.document_id == doc_id)).all()
    if question_ids:
        session.execute(delete(Evidence).where(Evidence.question_id.in_(question_ids)))
        session.execute(delete(QuestionVersion).where(QuestionVersion.question_id.in_(question_ids)))
        session.execute(delete(Question).where(Question.id.in_(question_ids)))
    session.execute(delete(Chart).where(Chart.document_id == doc_id))
    session.execute(delete(Document).where(Document.id == doc_id))
    session.commit()
