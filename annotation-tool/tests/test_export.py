import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TEST_DB = ROOT / "tests" / "_test_export.db"
for suffix in ("", "-wal", "-shm"):
    p = Path(str(TEST_DB) + suffix)
    if p.exists():
        p.unlink()
os.environ["VICHARTQA_DB_PATH"] = str(TEST_DB)

from sqlalchemy import select  # noqa: E402

from db import get_session, init_db  # noqa: E402
from export import assign_splits, build_dataset  # noqa: E402
from models import Chart, Document, Evidence, Question  # noqa: E402

init_db()


def _make_document(session, domain="economics", n_questions=1, question_status="active"):
    doc = Document(
        title="Bài test",
        body_text="GDP tăng dần theo thời gian.",
        source_provider="Test",
        source_domain=domain,
        status="in_progress",
    )
    session.add(doc)
    session.flush()

    chart = Chart(
        document_id=doc.id,
        chart_id="fig1",
        image_path="images/x.png",
        chart_type="line",
    )
    session.add(chart)
    session.flush()

    q1 = Question(
        document_id=doc.id,
        question_text="GDP 2021 là bao nhiêu?",
        answer="8.4",
        answer_type="numeric",
        question_type="data_retrieval",
        hop_type="chart",
        status=question_status,
    )
    session.add(q1)
    session.flush()
    session.add(
        Evidence(question_id=q1.id, hop_order=1, source="chart", chart_id=chart.id, description="1. Đọc giá trị GDP năm 2021.")
    )

    if n_questions > 1:
        q2 = Question(
            document_id=doc.id,
            question_text="Vậy chênh lệch với 2011 là bao nhiêu?",
            answer="5.9",
            answer_type="numeric",
            question_type="compositional",
            hop_type="chart",
            derivation="8.4 - 2.5",
            status=question_status,
        )
        session.add(q2)
        session.flush()
        session.add(
            Evidence(
                question_id=q2.id,
                hop_order=1,
                source="chart",
                chart_id=chart.id,
                description="1. Đọc giá trị GDP năm 2011 và 2021.",
            )
        )

    session.commit()
    return doc.id


def test_build_dataset_shapes_json_per_docs02_schema():
    with get_session() as s:
        doc_id = _make_document(s, n_questions=2)
        s.get(Document, doc_id).split = "train"
        s.commit()

    with get_session() as s:
        dataset = build_dataset(s)

    assert len(dataset) == 1
    record = dataset[0]
    assert record["id"] == f"vichartqa_economics_{doc_id:05d}"
    assert record["split"] == "train"
    assert len(record["charts"]) == 1
    assert record["charts"][0]["chart_id"] == "fig1"

    assert len(record["qa"]) == 2
    q1, q2 = record["qa"]
    assert q1["id"] == "q1"
    assert q1["evidence"][0]["chart_id"] == "fig1"  # local label, not DB int id
    assert q2["derivation"] == "8.4 - 2.5"


def test_build_dataset_skips_documents_without_eligible_questions():
    with get_session() as s:
        doc_id = _make_document(s, question_status="rejected")  # not active
        s.get(Document, doc_id).split = "train"
        s.commit()

    with get_session() as s:
        dataset = build_dataset(s)
    assert all(r["id"] != f"vichartqa_economics_{doc_id:05d}" for r in dataset)


def test_build_dataset_require_split_excludes_unsplit_documents():
    with get_session() as s:
        _make_document(s)  # split left as None

    with get_session() as s:
        dataset_strict = build_dataset(s, require_split=True)
        dataset_loose = build_dataset(s, require_split=False)

    # the unsplit doc must be excluded when require_split=True, included otherwise
    assert len(dataset_loose) >= len(dataset_strict) + 1


def test_assign_splits_respects_ratio_and_is_idempotent():
    with get_session() as s:
        before_unsplit = len(s.scalars(select(Document).where(Document.split.is_(None))).all())
        for _ in range(20):
            _make_document(s)

    with get_session() as s:
        assigned = assign_splits(s)
        s.commit()
    assert assigned == before_unsplit + 20, (assigned, before_unsplit)

    with get_session() as s:
        docs = s.scalars(select(Document).where(Document.split.isnot(None))).all()
        splits = [d.split for d in docs]
    assert all(sp in SPLITS_ALL for sp in splits)
    counts = {sp: splits.count(sp) for sp in set(splits)}
    assert counts.get("train", 0) >= 14  # ~77% of the >=20 split documents

    # idempotent: re-running should not reassign already-split documents
    with get_session() as s:
        assigned_again = assign_splits(s)
    assert assigned_again == 0


SPLITS_ALL = {"train", "val", "test"}


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    if failed:
        raise SystemExit(1)
