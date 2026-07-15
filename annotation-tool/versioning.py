"""Per-question version history — the replacement for blind cross-verification.
Every create/edit/reject of a Question is recorded as a full-snapshot QuestionVersion
row (never mutated afterward), giving an audit trail without a second annotator.

Pure Python + SQLAlchemy Session, no streamlit import (same convention as validation.py).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Question, QuestionVersion


def snapshot_question(question: Question) -> dict:
    return {
        "question_text": question.question_text,
        "answer": question.answer,
        "equivalent_answers": question.equivalent_answers,
        "answer_type": question.answer_type,
        "question_type": question.question_type,
        "hop_type": question.hop_type,
        "derivation": question.derivation,
        "choices": question.choices,
        "status": question.status,
        "evidence": [
            {
                "hop_order": e.hop_order,
                "source": e.source,
                "chart_id": e.chart_id,
                "description": e.description,
                "quote": e.quote,
            }
            for e in sorted(question.evidence, key=lambda e: e.hop_order)
        ],
    }


def record_version(
    session: Session,
    question: Question,
    edited_by: int | None,
    change_type: str,
    change_note: str | None = None,
) -> QuestionVersion:
    """Call after `question`'s fields/evidence are already updated and flushed —
    the snapshot captures the state as of that write."""
    last_version = session.scalar(
        select(func.max(QuestionVersion.version_number)).where(QuestionVersion.question_id == question.id)
    )
    version = QuestionVersion(
        question_id=question.id,
        version_number=(last_version or 0) + 1,
        snapshot=snapshot_question(question),
        change_type=change_type,
        change_note=change_note,
        edited_by=edited_by,
    )
    session.add(version)
    return version
