"""Gọi LLM qua OpenRouter để sinh câu hỏi gợi ý (xem docs/03, docs/08).

Trả về list[dict] khớp field của Question/Evidence — chỉ mang tính tham khảo, không
tự lưu vào DB; annotator phải tự soạn/sửa lại qua form ở pages/2_question_workspace.py.
"""

from __future__ import annotations

import json

import streamlit as st

from constants import HOP_TYPES, QUESTION_TYPES, VLM_MODEL_SLUGS

SYSTEM_PROMPT = """Bạn là annotator sinh câu hỏi cho bộ dữ liệu ViChartQA (Hỏi-Đáp biểu đồ tiếng Việt,
multi-hop reasoning trên text + chart). Nhiệm vụ: đọc 1 document (title + body_text + danh sách chart
kèm loại biểu đồ), sinh thêm các câu hỏi ứng viên rải đều theo 2 chiều taxonomy sau, KHÔNG trùng các câu đã có.

Chiều 1 — question_type (8 giá trị): {question_types}
Chiều 2 — hop_type (4 giá trị): {hop_types}
  - single_chart: trả lời được chỉ từ 1 chart.
  - text_to_chart: 1 claim/số liệu CHỈ có trong body_text, đối chiếu/tính toán với chart.
  - chart_to_chart: cần ≥2 chart, body_text là cầu nối.
  - fact_check_dual: 1 phát biểu cần cả text lẫn chart để xác minh đúng/sai.

Với mỗi câu hỏi trả về JSON object:
{{
  "question": str, "answer": str, "answer_type": "numeric"|"text"|"unanswerable"|"boolean",
  "question_type": one of question_types, "hop_type": one of hop_types,
  "derivation": str (công thức số học nếu answer_type=numeric và question_type compositional/visual_compositional, else ""),
  "choices": [str,str,str,str] nếu question_type=multiple_choice else null,
  "evidence": [{{"source":"chart","chart_id":str,"series":str,"x":[str,...]}} hoặc {{"source":"text","quote":str}}]
}}

Chỉ trả về JSON: {{"questions": [...]}}. Không thêm giải thích ngoài JSON.
""".format(question_types=QUESTION_TYPES, hop_types=HOP_TYPES)


def _build_user_prompt(title: str, body_text: str, charts: list[dict], seed_questions: list[str], n: int) -> str:
    charts_desc = "\n".join(f"- {c['chart_id']} ({c['chart_type']})" for c in charts)
    seeds_desc = "\n".join(f"- {q}" for q in seed_questions) or "(chưa có)"
    return (
        f"Title: {title}\n\nBody text:\n{body_text}\n\nCharts:\n{charts_desc}\n\n"
        f"Câu hỏi đã có (không lặp lại):\n{seeds_desc}\n\n"
        f"Sinh đúng {n} câu hỏi ứng viên mới."
    )


class VLMError(RuntimeError):
    pass


def _parse_response(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise VLMError(f"Không parse được JSON từ VLM: {exc}\nRaw: {text[:300]}") from exc
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict):
        questions = data.get("questions", [])
    else:
        questions = []
    if not isinstance(questions, list):
        raise VLMError(f"Response không đúng dạng {{questions: [...]}}: {data}")
    return questions


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _call_openrouter(model_slug: str, system: str, user: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=st.secrets["OPENROUTER_API_KEY"], base_url=OPENROUTER_BASE_URL)
    resp = client.chat.completions.create(
        model=model_slug,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        extra_headers={
            "HTTP-Referer": st.secrets.get("SITE_URL", "https://github.com/hoadm-net/ViChartQA"),
            "X-Title": "ViChartQA Annotation Tool",
        },
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content


def generate_candidates(
    model: str, title: str, body_text: str, charts: list[dict], seed_questions: list[str], n: int = 5
) -> list[dict]:
    if model not in VLM_MODEL_SLUGS:
        raise VLMError(f"Model không hỗ trợ: {model}")
    user_prompt = _build_user_prompt(title, body_text, charts, seed_questions, n)
    raw = _call_openrouter(VLM_MODEL_SLUGS[model], SYSTEM_PROMPT, user_prompt)
    return _parse_response(raw)
