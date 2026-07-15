"""Gọi LLM qua OpenRouter để sinh câu hỏi gợi ý (xem docs/03). Model phải là multimodal
(GPT/Gemini) — ảnh chart thật được chèn ngay tại vị trí placeholder [CHART N] trong
body_text khi gửi cho model, không chỉ mô tả bằng tên chart_type.

Trả về list[dict] khớp field của Question — chỉ mang tính tham khảo, không tự lưu vào
DB. KHÔNG sinh evidence: annotator luôn tự đọc chart/text và điền evidence tay qua
form ở pages/3_question_workspace.py, để giảm lỗi/sai lệch so với để LLM tự bịa
series/x/quote.
"""

from __future__ import annotations

import json
import re

import streamlit as st

from constants import HOP_TYPES, QUESTION_TYPES, VLM_MODEL_SLUGS

_PLACEHOLDER_RE = re.compile(r"\[CHART (\d+)\]")

SYSTEM_PROMPT = """Bạn là annotator sinh câu hỏi cho bộ dữ liệu ViChartQA (Hỏi-Đáp biểu đồ tiếng Việt,
multi-hop reasoning trên text + chart). Nhiệm vụ: đọc 1 document (title + body_text + danh sách chart
kèm loại biểu đồ), sinh thêm các câu hỏi ứng viên rải đều theo 2 chiều taxonomy sau, KHÔNG trùng các câu đã có.

Chiều 1 — question_type ({n_question_types} giá trị): {question_types}
Chiều 2 — hop_type ({n_hop_types} giá trị): {hop_types}
  - single_chart: trả lời được chỉ từ 1 chart.
  - text_to_chart: 1 claim/số liệu CHỈ có trong body_text, đối chiếu/tính toán với chart.
  - chart_to_chart: cần ≥2 chart, body_text là cầu nối.
  - fact_check_dual: 1 phát biểu cần cả text lẫn chart để xác minh đúng/sai.

CHỈ sinh câu hỏi + đáp án, KHÔNG sinh evidence — annotator sẽ tự đọc chart/text và điền
evidence (series/x hoặc quote) sau khi dùng gợi ý làm mẫu.

Với mỗi câu hỏi trả về JSON object:
{{
  "question": str, "answer": str, "answer_type": "numeric"|"text"|"unanswerable"|"boolean",
  "question_type": one of question_types, "hop_type": one of hop_types,
  "derivation": str (công thức số học nếu answer_type=numeric và question_type compositional/visual_compositional, else ""),
  "choices": [str,str,str,str] nếu question_type=multiple_choice else null
}}

Chỉ trả về JSON: {{"questions": [...]}}. Không thêm giải thích ngoài JSON.
""".format(
    question_types=QUESTION_TYPES,
    hop_types=HOP_TYPES,
    n_question_types=len(QUESTION_TYPES),
    n_hop_types=len(HOP_TYPES),
)


def _build_user_content(title: str, body_text: str, charts: list[dict], seed_questions: list[str], n: int) -> list[dict]:
    """Trả về multimodal content block cho OpenAI-compatible chat API. Model phải THẤY
    ảnh chart thật, không chỉ đọc tên chart_type, mới sinh được câu hỏi bám đúng số liệu
    — chèn ảnh (data URI, do caller chuẩn bị qua `charts[i]["image_data_uri"]`) ngay tại
    vị trí placeholder `[CHART N]` gốc trong body_text, thay vì chỉ liệt kê rời rạc.
    """
    charts_by_id = {c["chart_id"]: c for c in charts}
    charts_desc = "\n".join(f"- {c['chart_id']} ({c['chart_type']})" for c in charts)

    content: list[dict] = [{"type": "text", "text": f"Title: {title}\n\nCharts:\n{charts_desc}\n\nBody text:\n"}]
    pos = 0
    for m in _PLACEHOLDER_RE.finditer(body_text):
        content.append({"type": "text", "text": body_text[pos : m.start()]})
        chart = charts_by_id.get(f"fig{m.group(1)}")
        image_data_uri = chart.get("image_data_uri") if chart else None
        if image_data_uri:
            content.append({"type": "text", "text": m.group(0)})
            content.append({"type": "image_url", "image_url": {"url": image_data_uri}})
        else:
            content.append({"type": "text", "text": m.group(0)})
        pos = m.end()
    content.append({"type": "text", "text": body_text[pos:]})

    seeds_desc = "\n".join(f"- {q}" for q in seed_questions) or "(chưa có)"
    content.append(
        {"type": "text", "text": f"\n\nCâu hỏi đã có (không lặp lại):\n{seeds_desc}\n\nSinh đúng {n} câu hỏi ứng viên mới."}
    )
    return content


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


def _call_openrouter(model_slug: str, system: str, user_content: list[dict]) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=st.secrets["OPENROUTER_API_KEY"], base_url=OPENROUTER_BASE_URL)
    resp = client.chat.completions.create(
        model=model_slug,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user_content}],
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
    """`charts[i]` cần {"chart_id", "chart_type", "image_data_uri"} — image_data_uri do
    caller tự đọc file + base64-encode (xem pages/3_question_workspace.py), None nếu
    ảnh không đọc được (khi đó chart chỉ còn được nhắc tới bằng chart_type qua text)."""
    if model not in VLM_MODEL_SLUGS:
        raise VLMError(f"Model không hỗ trợ: {model}")
    user_content = _build_user_content(title, body_text, charts, seed_questions, n)
    raw = _call_openrouter(VLM_MODEL_SLUGS[model], SYSTEM_PROMPT, user_content)
    return _parse_response(raw)
