"""SQLAlchemy ORM models. Table shapes match docs/08-annotation-tool-design.md §3.1.

`choices` and `x` use the generic JSON type so the same code works against SQLite
(stored as TEXT) or Postgres (JSONB) if ever migrated.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from constants import (
    ANSWER_TYPES,
    CHART_COMPLEXITY,
    CHART_TYPES,
    DOCUMENT_STATUSES,
    DOMAINS,
    EVIDENCE_SOURCES,
    HOP_TYPES,
    PODS,
    QUESTION_STATUSES,
    QUESTION_TYPES,
    QUESTION_VERSION_CHANGE_TYPES,
    ROLES,
    SPLITS,
)


class Base(DeclarativeBase):
    pass


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _today_str() -> str:
    return str(dt.date.today())


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    pod: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    password_hash: Mapped[str] = mapped_column(String)

    __table_args__ = (
        CheckConstraint(f"pod IN {tuple(PODS)}", name="ck_users_pod"),
        CheckConstraint(f"role IN {tuple(ROLES)}", name="ck_users_role"),
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    body_text: Mapped[str] = mapped_column(Text)

    source_provider: Mapped[str] = mapped_column(String)
    source_domain: Mapped[str] = mapped_column(String)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_accessed_date: Mapped[str] = mapped_column(String, default=_today_str)  # luôn = ngày intake

    split: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="intake")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    charts: Mapped[list["Chart"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    questions: Mapped[list["Question"]] = relationship(back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(f"status IN {tuple(DOCUMENT_STATUSES)}", name="ck_documents_status"),
        CheckConstraint(f"split IS NULL OR split IN {tuple(SPLITS)}", name="ck_documents_split"),
        CheckConstraint(f"source_domain IN {tuple(DOMAINS)}", name="ck_documents_domain"),
    )


class Chart(Base):
    __tablename__ = "charts"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    chart_id: Mapped[str] = mapped_column(String)  # local label: "fig1", "fig2", ...
    image_path: Mapped[str] = mapped_column(String)
    chart_type: Mapped[str] = mapped_column(String)
    chart_complexity: Mapped[str | None] = mapped_column(String, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="charts")

    __table_args__ = (
        CheckConstraint(f"chart_type IN {tuple(CHART_TYPES)}", name="ck_charts_type"),
        CheckConstraint(
            f"chart_complexity IS NULL OR chart_complexity IN {tuple(CHART_COMPLEXITY)}",
            name="ck_charts_complexity",
        ),
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))

    question_text: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    equivalent_answers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    answer_type: Mapped[str] = mapped_column(String)
    question_type: Mapped[str] = mapped_column(String)
    hop_type: Mapped[str] = mapped_column(String)
    derivation: Mapped[str | None] = mapped_column(Text, nullable=True)
    choices: Mapped[list | None] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(String, default="active")

    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    document: Mapped["Document"] = relationship(back_populates="questions")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="question", cascade="all, delete-orphan")
    versions: Mapped[list["QuestionVersion"]] = relationship(back_populates="question", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(f"answer_type IN {tuple(ANSWER_TYPES)}", name="ck_questions_answer_type"),
        CheckConstraint(f"question_type IN {tuple(QUESTION_TYPES)}", name="ck_questions_question_type"),
        CheckConstraint(f"hop_type IN {tuple(HOP_TYPES)}", name="ck_questions_hop_type"),
        CheckConstraint(f"status IN {tuple(QUESTION_STATUSES)}", name="ck_questions_status"),
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    hop_order: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str] = mapped_column(String)
    chart_id: Mapped[int | None] = mapped_column(ForeignKey("charts.id"), nullable=True)
    series: Mapped[str | None] = mapped_column(String, nullable=True)  # tự do, annotator gõ tay
    x: Mapped[list | None] = mapped_column(JSON, nullable=True)  # tự do, annotator gõ tay
    quote: Mapped[str | None] = mapped_column(Text, nullable=True)

    question: Mapped["Question"] = relationship(back_populates="evidence")

    __table_args__ = (CheckConstraint(f"source IN {tuple(EVIDENCE_SOURCES)}", name="ck_evidence_source"),)


class QuestionVersion(Base):
    """Full-snapshot edit log — thay cho blind verification: mỗi lần tạo/sửa/rút một
    Question đều ghi 1 dòng ở đây, không sửa/xoá dòng cũ (xem versioning.py)."""

    __tablename__ = "question_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    version_number: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON)
    change_type: Mapped[str] = mapped_column(String)
    change_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    edited_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_now)

    question: Mapped["Question"] = relationship(back_populates="versions")

    __table_args__ = (
        CheckConstraint(f"change_type IN {tuple(QUESTION_VERSION_CHANGE_TYPES)}", name="ck_qversions_change_type"),
    )
