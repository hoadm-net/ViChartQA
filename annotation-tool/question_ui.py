"""Streamlit UI widgets shared by pages/2_question_workspace.py — extracted from the
old data_table/seed-writing/VLM-review pages so the same form isn't duplicated.

Unlike validation.py/versioning.py this module imports streamlit — it's UI code, not
pure logic. render_question_form() does NOT write to the database: it returns a plain
dict on a valid submit (or None otherwise) and lets the caller decide whether to INSERT
a new Question or UPDATE an existing one + call versioning.record_version().
"""

from __future__ import annotations

import streamlit as st

from constants import ANSWER_TYPES, DERIVATION_REQUIRED_TYPES, HOP_TYPES, QUESTION_TYPES
from validation import check_derivation, derivation_required, is_duplicate_question, validate_evidence, word_count


def get_question_label(editing_id: int | None = None) -> str:
    """Trả về nhãn hiển thị cho hộp nhập câu hỏi dựa trên ID đang sửa."""
    return f"Câu hỏi (ID: #{editing_id})" if type(editing_id) is int and editing_id > 0 else "Câu hỏi"


def render_evidence_builder(k, charts_by_id: dict, initial_evidence: list[dict] | None = None, hop_type: str = "chart") -> list[dict]:
    init_evidence = initial_evidence or []
    if init_evidence:
        n_hops_default = len(init_evidence)
    else:
        n_hops_default = 2 if hop_type in ("text_and_chart", "charts") else 1
    
    ev_list_key = k("ev_items_state")
    ev_ver_key = k("ev_version")
    ev_ver = st.session_state.get(ev_ver_key, 0)

    if ev_list_key not in st.session_state:
        items = []
        for i in range(3):
            if i < len(init_evidence):
                items.append({
                    "source": init_evidence[i].get("source", "chart"),
                    "chart_id": init_evidence[i].get("chart_id"),
                    "description": init_evidence[i].get("description", ""),
                    "quote": init_evidence[i].get("quote", ""),
                })
            else:
                if hop_type == "text_and_chart":
                    src = "chart" if i == 0 else "text"
                elif hop_type == "text":
                    src = "text"
                else:
                    src = "chart"
                items.append({"source": src, "chart_id": None, "description": "", "quote": ""})
        st.session_state[ev_list_key] = items

    n_hops = st.number_input("🔢 Số hop", min_value=1, max_value=3, value=n_hops_default, key=k("n_hops"))

    chart_label_map = {c["chart_id"]: cid for cid, c in charts_by_id.items()}
    chart_labels = list(chart_label_map.keys())

    total_n = int(n_hops)

    def _sync_current_hops():
        for j in range(total_n):
            s_key = k(f"source_{ev_ver}_{j}")
            c_key = k(f"chart_{ev_ver}_{j}")
            d_key = k(f"description_{ev_ver}_{j}")
            q_key = k(f"quote_{ev_ver}_{j}")

            src = st.session_state.get(s_key, st.session_state[ev_list_key][j].get("source", "chart"))
            chart_lbl = st.session_state.get(c_key)
            cid = chart_label_map.get(chart_lbl, st.session_state[ev_list_key][j].get("chart_id"))
            desc = st.session_state.get(d_key, st.session_state[ev_list_key][j].get("description", ""))
            qte = st.session_state.get(q_key, st.session_state[ev_list_key][j].get("quote", ""))

            st.session_state[ev_list_key][j] = {
                "source": src,
                "chart_id": cid,
                "description": desc,
                "quote": qte,
            }

    evidence_items = []

    for i in range(total_n):
        with st.container(border=True):
            c_title, c_move = st.columns([3, 2])
            with c_title:
                st.markdown(f"**Hop {i + 1}**")
            with c_move:
                if total_n > 1:
                    m1, m2 = st.columns(2)
                    with m1:
                        if i > 0 and st.button("⬆️ Lên", key=k(f"move_up_{i}_{ev_ver}"), help="Đổi thứ tự với Hop phía trên"):
                            _sync_current_hops()
                            st.session_state[ev_list_key][i], st.session_state[ev_list_key][i - 1] = (
                                st.session_state[ev_list_key][i - 1],
                                st.session_state[ev_list_key][i],
                            )
                            st.session_state[ev_ver_key] = ev_ver + 1
                            st.rerun()
                    with m2:
                        if i < total_n - 1 and st.button("⬇️ Xuống", key=k(f"move_down_{i}_{ev_ver}"), help="Đổi thứ tự với Hop phía dưới"):
                            _sync_current_hops()
                            st.session_state[ev_list_key][i], st.session_state[ev_list_key][i + 1] = (
                                st.session_state[ev_list_key][i + 1],
                                st.session_state[ev_list_key][i],
                            )
                            st.session_state[ev_ver_key] = ev_ver + 1
                            st.rerun()

            ev_cur = st.session_state[ev_list_key][i]
            source_opts = ["chart", "text"]
            source_default = ev_cur.get("source", "chart")
            if source_default not in source_opts:
                source_default = "chart"

            source = st.radio(
                "Nguồn dữ liệu",
                source_opts,
                index=source_opts.index(source_default),
                key=k(f"source_{ev_ver}_{i}"),
                horizontal=True,
            )

            if source == "chart" and chart_labels:
                c1, c2 = st.columns([1, 2])
                with c1:
                    default_label = next(
                        (lbl for lbl, cid in chart_label_map.items() if cid == ev_cur.get("chart_id")),
                        chart_labels[0],
                    )
                    chart_label = st.selectbox(
                        "📌 Chọn Chart",
                        chart_labels,
                        index=chart_labels.index(default_label),
                        key=k(f"chart_{ev_ver}_{i}"),
                    )
                    sel_chart_id = chart_label_map[chart_label]
                    preview_path = charts_by_id.get(sel_chart_id, {}).get("image_path")
                    if preview_path:
                        st.image(preview_path)

                with c2:
                    description = st.text_area(
                        "📝 Cách đọc (đánh số từng bước)",
                        value=ev_cur.get("description") or "",
                        key=k(f"description_{ev_ver}_{i}"),
                        height=150,
                        help="Đánh số từng bước truy hồi giá trị, đủ để người khác đọc lại và tự tìm đúng điểm dữ liệu trên ảnh.",
                    )
                evidence_items.append({"hop": i + 1, "source": "chart", "chart_id": sel_chart_id, "description": description})
            else:
                quote = st.text_area(
                    "📝 Quote (dán nguyên văn từ body_text)",
                    value=ev_cur.get("quote") or "",
                    key=k(f"quote_{ev_ver}_{i}"),
                    height=100,
                )
                evidence_items.append({"hop": i + 1, "source": "text", "quote": quote})

    return evidence_items


def render_doc_context(doc, charts_by_id: dict):
    st.markdown(
        "<div style='background-color:#ecfdf5; border-left:5px solid #10b981; padding:10px 14px; border-radius:6px; font-weight:bold; font-size:1.1em; color:#047857; margin-bottom:12px;'>📖 Ngữ cảnh Document (Tham chiếu)</div>",
        unsafe_allow_html=True,
    )
    with st.container(border=True, height=580):
        st.markdown(f"**body_text ({word_count(doc.body_text)} từ):**")
        st.markdown(f"<div style='white-space: pre-wrap;'>{doc.body_text}</div>", unsafe_allow_html=True)
        if doc.charts:
            st.divider()
            st.markdown("**Biểu đồ (Charts):**")
            for c in doc.charts:
                st.markdown(f"**{c.chart_id}** ({c.chart_type})")
                img_path = charts_by_id.get(c.id, {}).get("image_path")
                if img_path:
                    st.image(img_path, width="stretch")


def render_question_form(prefix: str, doc, charts_by_id: dict, existing_questions: list, initial: dict | None = None) -> dict | None:
    """Returns a submitted-question dict on a valid "Lưu", else None."""
    gen = st.session_state.setdefault(f"{prefix}_form_gen", 0)
    k = lambda name: f"{prefix}_{name}_{gen}"  # noqa: E731 — reset widget keys after each save
    initial = initial or {}
    editing_id = initial.get("id")
    other_questions = [q for q in existing_questions if (q.id if hasattr(q, "id") else q.get("id")) != editing_id]

    # Row 1: Content (Left) | Classification (Right)
    col_q, col_cat = st.columns([1, 1])
    with col_q:
        with st.container(border=True):
            st.markdown(
                "<div style='background-color:#eff6ff; border-left:5px solid #3b82f6; padding:10px 14px; border-radius:6px; font-weight:bold; font-size:1.1em; color:#1e40af; margin-bottom:12px;'>📝 Nội dung câu hỏi</div>",
                unsafe_allow_html=True,
            )

            # Dropdown chọn câu hỏi hoặc tạo mới
            q_options = ["➕ [Tạo câu hỏi mới]"]
            q_map = {"➕ [Tạo câu hỏi mới]": None}

            is_llm_draft = (editing_id is None and bool(initial.get("question_text")))
            if is_llm_draft:
                draft_label = f"💡 [Mẫu gợi ý / Nháp] {initial.get('question_text', '')[:45]}..."
                q_options.append(draft_label)
                q_map[draft_label] = "draft"

            for q in existing_questions:
                q_id = q.id if hasattr(q, "id") else q.get("id")
                q_txt = q.question_text if hasattr(q, "question_text") else q.get("question_text", "")
                q_type = q.question_type if hasattr(q, "question_type") else q.get("question_type", "")
                h_type = q.hop_type if hasattr(q, "hop_type") else q.get("hop_type", "")
                status_str = f" ({q.status})" if hasattr(q, "status") and q.status != "active" else ""
                short_txt = q_txt.replace("\n", " ")[:45]
                lbl = f"#{q_id}: [{q_type}/{h_type}] {short_txt}...{status_str}"
                q_options.append(lbl)
                q_map[lbl] = q

            default_idx = 0
            if editing_id is not None:
                for idx, opt in enumerate(q_options):
                    target_q = q_map.get(opt)
                    if target_q is not None and not isinstance(target_q, str):
                        t_id = target_q.id if hasattr(target_q, "id") else target_q.get("id")
                        if t_id == editing_id:
                            default_idx = idx
                            break
            elif is_llm_draft and len(q_options) > 1:
                default_idx = 1

            selected_q_opt = st.selectbox(
                "📋 Chọn câu hỏi để sửa hoặc tạo mới:",
                q_options,
                index=default_idx,
                key=k("select_question_dropdown"),
                help="Chọn một câu hỏi đã có để sửa trực tiếp, hoặc chọn [Tạo câu hỏi mới].",
            )

            # Trigger reload if user selects a different question from dropdown
            if selected_q_opt != q_options[default_idx]:
                chosen = q_map.get(selected_q_opt)
                if chosen is None:
                    st.session_state.pop(f"{prefix}_form_initial", None)
                elif chosen == "draft":
                    pass
                else:
                    if isinstance(chosen, dict):
                        q_dict = dict(chosen)
                    else:
                        q_dict = {
                            "id": chosen.id,
                            "question_text": chosen.question_text,
                            "answer": chosen.answer,
                            "equivalent_answers": chosen.equivalent_answers,
                            "answer_type": chosen.answer_type,
                            "question_type": chosen.question_type,
                            "hop_type": chosen.hop_type,
                            "derivation": chosen.derivation,
                            "choices": chosen.choices,
                            "status": chosen.status,
                            "evidence": [
                                {
                                    "hop": e.hop_order,
                                    "source": e.source,
                                    "chart_id": e.chart_id,
                                    "description": e.description,
                                    "quote": e.quote,
                                }
                                for e in sorted(chosen.evidence, key=lambda e: e.hop_order)
                            ] if hasattr(chosen, "evidence") and chosen.evidence else [],
                        }
                    st.session_state[f"{prefix}_form_initial"] = q_dict
                st.session_state[f"{prefix}_form_gen"] = gen + 1
                st.rerun()

            q_label = get_question_label(editing_id)
            is_editing = q_label != "Câu hỏi"
            question_text = st.text_area(
                q_label,
                value=initial.get("question_text", ""),
                key=k("question_text"),
                height=100,
                help="ID của câu hỏi trong cơ sở dữ liệu (chỉ hiển thị khi đang sửa)" if is_editing else None,
            )
            
            c1, c2 = st.columns(2)
            with c1:
                answer = st.text_input("Đáp án", value=initial.get("answer", ""), key=k("answer"))
            with c2:
                equiv_default = "\n".join(initial.get("equivalent_answers") or [])
                equiv_text = st.text_area(
                    "Đáp án tương đương (mỗi dòng 1 cái, không bắt buộc)", value=equiv_default, key=k("equiv"), height=68
                )
            equivalent_answers = [s.strip() for s in equiv_text.split("\n") if s.strip()] or None

    with col_cat:
        with st.container(border=True):
            st.markdown(
                "<div style='background-color:#fffbeb; border-left:5px solid #f59e0b; padding:10px 14px; border-radius:6px; font-weight:bold; font-size:1.1em; color:#b45309; margin-bottom:12px;'>🏷️ Phân loại</div>",
                unsafe_allow_html=True,
            )
            c1, c2, c3 = st.columns(3)
            with c1:
                qtype_default = initial.get("question_type") if initial.get("question_type") in QUESTION_TYPES else QUESTION_TYPES[0]
                question_type = st.selectbox(
                    "Loại câu hỏi (question_type)", QUESTION_TYPES, index=QUESTION_TYPES.index(qtype_default), key=k("question_type")
                )
            with c2:
                hop_default = initial.get("hop_type") if initial.get("hop_type") in HOP_TYPES else HOP_TYPES[0]
                hop_type = st.selectbox("Loại bằng chứng (hop_type)", HOP_TYPES, index=HOP_TYPES.index(hop_default), key=k("hop_type"))
            
            with c3:
                if question_type == "multiple_choice":
                    answer_type = "text"
                    st.caption("answer_type = text (trắc nghiệm)")
                elif question_type == "unanswerable":
                    answer_type = "unanswerable"
                    st.caption("answer_type = unanswerable")
                else:
                    at_opts = [a for a in ANSWER_TYPES if a != "unanswerable"]
                    at_default = initial.get("answer_type") if initial.get("answer_type") in at_opts else at_opts[0]
                    answer_type = st.selectbox("Loại đáp án (answer_type)", at_opts, index=at_opts.index(at_default), key=k("answer_type"))

            if question_type == "multiple_choice":
                st.markdown("**Các lựa chọn (Choices)**")
                ch_cols = st.columns(4)
                init_choices = initial.get("choices") or []
                choices = []
                for i, col in enumerate(ch_cols):
                    with col:
                        choices.append(st.text_input(f"Lựa chọn {i + 1}", value=(init_choices[i] if i < len(init_choices) else ""), key=k(f"choice_{i}")))
            else:
                choices = None

            derivation = initial.get("derivation") or ""
            show_derivation = question_type in DERIVATION_REQUIRED_TYPES or derivation_required(answer_type, question_type) or bool(derivation)
            if show_derivation:
                st.divider()
                c_deriv, c_btn = st.columns([3, 1])
                with c_deriv:
                    derivation = st.text_input(
                        "derivation (công thức tính toán, vd: 8.4 - 2.5)",
                        value=derivation,
                        key=k("derivation"),
                        help="Bắt buộc khi đáp án là số đối với câu hỏi compositional / visual_compositional.",
                    )
                with c_btn:
                    st.write("") 
                    st.write("") 
                    if derivation and st.button("Kiểm tra", key=k("check_derivation")):
                        ok, msg = check_derivation(derivation, answer)
                        if ok:
                            st.success(f"✅ {msg}")
                        else:
                            st.error(f"❌ {msg}")

    # Row 2: Document Context (Left) | Evidence Builder & Save (Right)
    col_ctx, col_ev = st.columns([1, 1])
    with col_ctx:
        render_doc_context(doc, charts_by_id)

    with col_ev:
        st.markdown(
            "<div style='background-color:#f5f3ff; border-left:5px solid #8b5cf6; padding:10px 14px; border-radius:6px; font-weight:bold; font-size:1.1em; color:#6d28d9; margin-bottom:12px;'>🔍 Evidence (Dẫn chứng)</div>",
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.markdown("**Bắt buộc** — chart nào + các bước đọc, hoặc đoạn text nào")
            evidence_items = render_evidence_builder(k, charts_by_id, initial.get("evidence"), hop_type=hop_type)

        if st.button("💾 Lưu câu hỏi", type="primary", key=k("submit")):
            errors, warnings = [], []

            if not question_text.strip():
                errors.append("Thiếu câu hỏi.")
            if answer_type != "unanswerable" and not answer.strip():
                errors.append("Thiếu đáp án.")
            if question_type == "multiple_choice" and (not choices or any(not c.strip() for c in choices)):
                errors.append("Trắc nghiệm cần đủ 4 lựa chọn.")

            ev_result = validate_evidence(hop_type, evidence_items, charts_by_id, doc.body_text)
            errors += ev_result.errors

            # Kiểm tra derivation:
            if derivation and str(derivation).strip():
                d_ok, d_msg = check_derivation(derivation, answer)
                if not d_ok:
                    errors.append(f"❌ Derivation không hợp lệ: {d_msg}. Vui lòng kiểm tra và viết lại công thức.")
            elif derivation_required(answer_type, question_type):
                errors.append("❌ Loại câu hỏi này (compositional / visual_compositional với đáp án số) bắt buộc phải điền derivation.")

            existing_texts = [
                q.question_text if hasattr(q, "question_text") else q.get("question_text", "")
                for q in other_questions
            ]
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
                "derivation": derivation.strip() if derivation else None,
                "choices": choices,
                "evidence": evidence_items,
            }

    return None
