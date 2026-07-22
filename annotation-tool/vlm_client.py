"""Gọi LLM qua OpenRouter để sinh câu hỏi gợi ý (xem docs/03). Model phải là multimodal
(GPT/Gemini) — ảnh chart thật được chèn ngay tại vị trí placeholder [CHART N] trong
body_text khi gửi cho model, không chỉ mô tả bằng tên chart_type.

Trả về list[dict] khớp field của Question — chỉ mang tính tham khảo, không tự lưu vào
DB. KHÔNG sinh evidence: annotator luôn tự đọc chart/text và điền evidence tay qua
form ở pages/3_question_workspace.py, để giảm lỗi/sai lệch so với để LLM tự bịa
description/quote.
"""

from __future__ import annotations

import json
import re

import streamlit as st

from constants import HOP_TYPES, QUESTION_TYPES, VLM_MODEL_SLUGS

_PLACEHOLDER_RE = re.compile(r"\[CHART (\d+)\]")

def build_dynamic_system_prompt(
    target_q_types: list[str] | None = None,
    target_hops: list[str] | None = None,
    n: int = 5,
) -> str:
    """Constructs a token-optimized system prompt with Dynamic Chain-of-Thought (CoT) Injection."""
    target_q_str = ", ".join(target_q_types) if target_q_types else ", ".join(QUESTION_TYPES)
    target_hop_str = ", ".join(target_hops) if target_hops else ", ".join(HOP_TYPES)

    prompt = f"""You are a VLM question generator for ViChartQA dataset.
Task: Read 1 document (title + body_text + inlined chart images) & generate exactly {n} NEW candidate questions.

TARGET PRIORITY (MUST FOLLOW):
- Target Question Types (prioritize these): [{target_q_str}]
- Target Hop Types (prioritize these): [{target_hop_str}]
"""

    cot_rules = []
    active_hops = target_hops or HOP_TYPES
    active_q_types = target_q_types or QUESTION_TYPES

    if "text_and_chart" in active_hops:
        cot_rules.append("👉 For 'text_and_chart': Pick 1 number/fact ONLY in body_text (NOT in any chart) -> Compare/calculate with a chart value.")

    if "charts" in active_hops:
        cot_rules.append("👉 For 'charts': Find 1 common metric/entity bridging Chart 1 & Chart 2 -> Compare across charts.")

    if "multiple_choice" in active_q_types:
        cot_rules.append("👉 For 'multiple_choice': Provide exactly 4 options in 'choices': ['A...', 'B...', 'C...', 'D...'].")

    if "fact_check" in active_q_types:
        cot_rules.append("👉 For 'fact_check': Question requires BOTH text + chart verification -> 'answer' MUST be 'Đúng' or 'Sai'.")

    if "unanswerable" in active_q_types:
        cot_rules.append("👉 For 'unanswerable': Ask a reasonable question whose answer CANNOT be derived from text/charts -> 'answer'='unanswerable'.")

    if cot_rules:
        prompt += "\nGENERATION GUIDELINES:\n" + "\n".join(cot_rules) + "\n"

    prompt += f"""
OUTPUT FORMAT: Return raw JSON object ONLY, NO markdown codeblock:
{{
  "questions": [
    {{
      "question": "text in Vietnamese",
      "answer": "exact answer",
      "answer_type": "numeric"|"text"|"unanswerable"|"boolean",
      "question_type": "one of target_q_types",
      "hop_type": "one of target_hops",
      "derivation": "math formula if numeric compositional else ''",
      "choices": ["A...", "B...", "C...", "D..."]
    }}
  ]
}}"""
    return prompt


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
    model: str,
    title: str,
    body_text: str,
    charts: list[dict],
    seed_questions: list[str],
    n: int = 5,
    target_q_types: list[str] | None = None,
    target_hops: list[str] | None = None,
) -> list[dict]:
    """`charts[i]` cần {"chart_id", "chart_type", "image_data_uri"}. Accepts optional
    target_q_types and target_hops to generate questions prioritizing dataset deficits."""
    if model not in VLM_MODEL_SLUGS:
        raise VLMError(f"Model không hỗ trợ: {model}")
    system_prompt = build_dynamic_system_prompt(target_q_types=target_q_types, target_hops=target_hops, n=n)
    user_content = _build_user_content(title, body_text, charts, seed_questions, n)
    raw = _call_openrouter(VLM_MODEL_SLUGS[model], system_prompt, user_content)
    return _parse_response(raw)

