"""Build the final dataset JSON per docs/02 §Schema dữ liệu đề xuất, and assign
train/val/test splits by document. Pure functions (take a Session, return data)
so this is reusable from the Tuần 5 freeze script and unit-testable.
"""

from __future__ import annotations

import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from constants import SPLITS
from models import Chart, Document, Question

EXPORT_ELIGIBLE_STATUSES = {"active"}


def assign_splits(session: Session, ratios: tuple[float, float, float] = (0.77, 0.10, 0.13), seed: int = 42) -> int:
    """Assigns split to documents that don't have one yet. Returns count assigned.
    Deterministic given `seed` — re-running is a no-op for already-split documents.
    """
    docs = session.scalars(select(Document).where(Document.split.is_(None)).order_by(Document.id)).all()
    if not docs:
        return 0
    rng = random.Random(seed)
    order = list(docs)
    rng.shuffle(order)
    n = len(order)
    n_train = round(n * ratios[0])
    n_val = round(n * ratios[1])
    for i, doc in enumerate(order):
        if i < n_train:
            doc.split = "train"
        elif i < n_train + n_val:
            doc.split = "val"
        else:
            doc.split = "test"
    return n


def _export_document(doc: Document) -> dict | None:
    charts = sorted(doc.charts, key=lambda c: c.chart_id)
    chart_label_by_id = {c.id: c.chart_id for c in charts}

    eligible_questions = [q for q in doc.questions if q.status in EXPORT_ELIGIBLE_STATUSES]
    if not eligible_questions:
        return None

    eligible_questions = sorted(eligible_questions, key=lambda q: q.id)
    local_label_by_qid = {q.id: f"q{i + 1}" for i, q in enumerate(eligible_questions)}

    qa = []
    for q in eligible_questions:
        evidence = [
            {
                "hop": e.hop_order,
                "source": e.source,
                **({"chart_id": chart_label_by_id.get(e.chart_id)} if e.source == "chart" else {}),
                **({"description": e.description} if e.source == "chart" else {}),
                **({"quote": e.quote} if e.source == "text" else {}),
            }
            for e in sorted(q.evidence, key=lambda e: e.hop_order)
        ]
        qa.append(
            {
                "id": local_label_by_qid[q.id],
                "question": q.question_text,
                "answer": q.answer,
                "equivalent_answers": q.equivalent_answers or [],
                "answer_type": q.answer_type,
                "question_type": q.question_type,
                "hop_type": q.hop_type,
                "derivation": q.derivation or "",
                "choices": q.choices,
                "evidence": evidence,
            }
        )

    return {
        "id": f"vichartqa_{doc.source_domain}_{doc.id:05d}",
        "title": doc.title,
        "body_text": doc.body_text,
        "source": {
            "provider": doc.source_provider,
            "domain": doc.source_domain,
            "url": doc.source_url,
            "accessed_date": doc.source_accessed_date,
        },
        "charts": [
            {
                "chart_id": c.chart_id,
                "image": c.image_path,
                "chart_type": c.chart_type,
            }
            for c in charts
        ],
        "qa": qa,
        "split": doc.split,
    }


def build_dataset(session: Session, require_split: bool = True) -> list[dict]:
    """Returns one dict per document (docs/02 schema), skipping documents with no
    export-eligible question. If `require_split`, documents without a split are
    skipped too (use assign_splits() first for a real export)."""
    query = select(Document)
    if require_split:
        query = query.where(Document.split.isnot(None))
    docs = session.scalars(query.order_by(Document.id)).all()

    out = []
    for doc in docs:
        record = _export_document(doc)
        if record is not None:
            out.append(record)
    return out
