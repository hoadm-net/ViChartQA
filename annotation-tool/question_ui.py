"""Streamlit UI widgets shared by pages/2_question_workspace.py — extracted from the
old data_table/seed-writing/VLM-review pages so the same form isn't duplicated.

Unlike validation.py/versioning.py this module imports streamlit — it's UI code, not
pure logic. render_question_form() does NOT write to the database: it returns a plain
dict on a valid submit (or None otherwise) and lets the caller decide whether to INSERT
a new Question or UPDATE an existing one + call versioning.record_version().
"""

from __future__ import annotations

import streamlit as st

from constants import ANSWER_TYPES, HOP_TYPES, QUESTION_TYPES
from validation import check_derivation, derivation_required, is_duplicate_question, validate_evidence


def render_evidence_builder(k, charts_by_id: dict, initial_evidence: list[dict] | None = None) -> list[dict]:
    """`k(name)` is the caller's widget-key function (shares its form_gen reset).
    `charts_by_id`: {chart.id: {"chart_id": str, "image_path": str | None}}. series/x
    for chart evidence are free text the annotator types directly — không có
    data_table để tra cứu, nên preview ảnh ngay tại chỗ để annotator nhìn mà gõ."""
    init_evidence = initial_evidence or []
    n_hops_default = len(init_evidence) or 1
    n_hops = st.number_input("Số hop", min_value=1, max_value=3, value=n_hops_default, key=k("n_hops"))

    evidence_items = []
    chart_label_map = {c["chart_id"]: cid for cid, c in charts_by_id.items()}
    chart_labels = list(chart_label_map.keys())

    for i in range(int(n_hops)):
        ev_init = init_evidence[i] if i < len(init_evidence) else {}
        st.markdown(f"_Hop {i + 1}_")
        source_opts = ["chart", "text"]
        source_default = ev_init.get("source", "chart")
        source = st.radio(
            "Nguồn",
            source_opts,
            index=source_opts.index(source_default) if source_default in source_opts else 0,
            key=k(f"source_{i}"),
            horizontal=True,
        )
        if source == "chart" and chart_labels:
            default_label = next(
                (lbl for lbl, cid in chart_label_map.items() if cid == ev_init.get("chart_id")), chart_labels[0]
            )
            chart_label = st.selectbox(
                "Chart", chart_labels, index=chart_labels.index(default_label), key=k(f"chart_{i}")
            )
            sel_chart_id = chart_label_map[chart_label]

            preview_path = charts_by_id[sel_chart_id].get("image_path")
            if preview_path:
                st.image(preview_path, width=280)

            series = st.text_input(
                "Series/chiều dữ liệu (vd. tên đường/cột trên chart)",
                value=ev_init.get("series") or "",
                key=k(f"series_{i}"),
            )
            x_default = ", ".join(ev_init.get("x") or [])
            x_text = st.text_input(
                "Giá trị/nhãn trục x (phân cách bằng dấu phẩy nếu nhiều)",
                value=x_default,
                key=k(f"x_{i}"),
            )
            x_vals = [v.strip() for v in x_text.split(",") if v.strip()]
            evidence_items.append(
                {"hop": i + 1, "source": "chart", "chart_id": sel_chart_id, "series": series, "x": x_vals}
            )
        else:
            quote = st.text_area(
                "Quote (dán nguyên văn từ body_text)", value=ev_init.get("quote", ""), key=k(f"quote_{i}")
            )
            evidence_items.append({"hop": i + 1, "source": "text", "quote": quote})

    return evidence_items


def render_question_form(prefix: str, doc, charts_by_id: dict, existing_questions: list, initial: dict | None = None) -> dict | None:
    """Returns a submitted-question dict on a valid "Lưu", else None. Never writes to
    the DB itself — see module docstring."""
    gen = st.session_state.setdefault(f"{prefix}_form_gen", 0)
    k = lambda name: f"{prefix}_{name}_{gen}"  # noqa: E731 — reset widget keys after each save
    initial = initial or {}
    editing_id = initial.get("id")

    question_text = st.text_area("Câu hỏi", value=initial.get("question_text", ""), key=k("question_text"))
    answer = st.text_input("Đáp án", value=initial.get("answer", ""), key=k("answer"))
    equiv_default = "\n".join(initial.get("equivalent_answers") or [])
    equiv_text = st.text_area(
        "Đáp án tương đương (mỗi dòng 1 cái, không bắt buộc)", value=equiv_default, key=k("equiv")
    )
    equivalent_answers = [s.strip() for s in equiv_text.split("\n") if s.strip()] or None

    qtype_default = initial.get("question_type") if initial.get("question_type") in QUESTION_TYPES else QUESTION_TYPES[0]
    question_type = st.selectbox(
        "question_type", QUESTION_TYPES, index=QUESTION_TYPES.index(qtype_default), key=k("question_type")
    )
    hop_default = initial.get("hop_type") if initial.get("hop_type") in HOP_TYPES else HOP_TYPES[0]
    hop_type = st.selectbox("hop_type", HOP_TYPES, index=HOP_TYPES.index(hop_default), key=k("hop_type"))

    if question_type == "multiple_choice":
        answer_type = "text"
        st.caption("answer_type = text (trắc nghiệm)")
        init_choices = initial.get("choices") or []
        choices = [
            st.text_input(f"Lựa chọn {i + 1}", value=(init_choices[i] if i < len(init_choices) else ""), key=k(f"choice_{i}"))
            for i in range(4)
        ]
    elif question_type == "unanswerable":
        answer_type = "unanswerable"
        st.caption("answer_type = unanswerable")
        choices = None
    else:
        at_opts = [a for a in ANSWER_TYPES if a != "unanswerable"]
        at_default = initial.get("answer_type") if initial.get("answer_type") in at_opts else at_opts[0]
        answer_type = st.selectbox("answer_type", at_opts, index=at_opts.index(at_default), key=k("answer_type"))
        choices = None

    other_questions = [q for q in existing_questions if q.id != editing_id]

    derivation = initial.get("derivation") or ""
    if derivation_required(answer_type, question_type):
        derivation = st.text_input("derivation (công thức số học, vd: 8.4 - 2.5)", value=derivation, key=k("derivation"))
        if derivation and st.button("Kiểm tra derivation", key=k("check_derivation")):
            ok, msg = check_derivation(derivation, answer)
            (st.success if ok else st.warning)(msg)

    st.markdown("**Evidence** (bắt buộc — chart số mấy/series/x nào, hoặc đoạn text nào)")
    evidence_items = render_evidence_builder(k, charts_by_id, initial.get("evidence"))

    if st.button("Lưu câu hỏi", type="primary", key=k("submit")):
        errors, warnings = [], []

        if not question_text.strip():
            errors.append("Thiếu câu hỏi.")
        if answer_type != "unanswerable" and not answer.strip():
            errors.append("Thiếu đáp án.")
        if question_type == "multiple_choice" and (not choices or any(not c.strip() for c in choices)):
            errors.append("Trắc nghiệm cần đủ 4 lựa chọn.")

        ev_result = validate_evidence(hop_type, evidence_items, charts_by_id, doc.body_text)
        errors += ev_result.errors

        if derivation:
            d_ok, d_msg = check_derivation(derivation, answer)
            if not d_ok:
                warnings.append(f"derivation: {d_msg}")

        existing_texts = [q.question_text for q in other_questions]
        if is_duplicate_question(question_text, existing_texts):
            warnings.append("Câu hỏi có vẻ trùng với câu đã có trong document này.")

        for w in warnings:
            st.warning(w)

        if errors:
            for e in errors:
                st.error(e)
            return None

        return {
            "id": editing_id,
            "question_text": question_text.strip(),
            "answer": answer.strip() if answer_type != "unanswerable" else "unanswerable",
            "equivalent_answers": equivalent_answers,
            "answer_type": answer_type,
            "question_type": question_type,
            "hop_type": hop_type,
            "derivation": derivation or None,
            "choices": choices,
            "evidence": evidence_items,
        }

    return None
