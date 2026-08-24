"""Pure Python validation logic — no Streamlit import here, so it's testable in isolation.

Reused by: annotation pages (block/warn on submit) and the export/cleanup script.
"""

from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass, field

from constants import (
    DERIVATION_REQUIRED_TYPES,
    HOP_TYPES,
    MULTI_HOP_TYPES,
    QUESTION_TYPE_TARGETS,
    RELAXED_ACCURACY_TOLERANCE,
)

# ---------------------------------------------------------------------------
# Numeric parsing / matching
# ---------------------------------------------------------------------------

_NUMERIC_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def parse_numeric(value: str) -> float | None:
    """Extract a float from strings like '6.2%', '1,234.5', '5.9 triệu'."""
    if value is None:
        return None
    cleaned = value.strip().replace(",", "")
    match = _NUMERIC_RE.search(cleaned)
    if not match:
        return None
    try:
        return float(match.group().replace(",", ""))
    except ValueError:
        return None


def numeric_answers_match(a: str, b: str, tolerance: float = RELAXED_ACCURACY_TOLERANCE) -> bool:
    """Relaxed accuracy: match if within `tolerance` fraction of each other."""
    na, nb = parse_numeric(a), parse_numeric(b)
    if na is None or nb is None:
        return False
    if na == nb:
        return True
    if na == 0:
        return nb == 0
    return abs(na - nb) / abs(na) <= tolerance


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def text_answers_match(a: str, b: str) -> bool:
    return _normalize_text(a) == _normalize_text(b)


def answers_match(a: str, b: str, answer_type: str, tolerance: float = RELAXED_ACCURACY_TOLERANCE) -> bool:
    if answer_type == "numeric":
        return numeric_answers_match(a, b, tolerance)
    return text_answers_match(a, b)


# ---------------------------------------------------------------------------
# Safe arithmetic eval for `derivation`
# ---------------------------------------------------------------------------

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_ALLOWED_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class DerivationError(ValueError):
    pass


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return _ALLOWED_UNARYOPS[type(node.op)](_eval_node(node.operand))
    raise DerivationError(f"Biểu thức không hợp lệ tại: {ast.dump(node)}")


def eval_derivation(formula: str) -> float:
    """Safely evaluate an arithmetic-only formula like '8.4 - 2.5' or '(14740 + 1910)/2'.

    Only numeric literals and + - * / ( ) are allowed — no names, calls, or
    attribute access, so this is safe to run on annotator-submitted text.
    """
    if not formula or not str(formula).strip():
        raise DerivationError("Công thức derivation trống.")
    cleaned = str(formula).strip()
    # Normalize Vietnamese decimal commas: e.g. 8,4 -> 8.4
    cleaned = re.sub(r"(\d+),(\d{1,2})(?!\d)", r"\1.\2", cleaned)
    # Normalize thousands separator: e.g. 14,740 -> 14740
    cleaned = re.sub(r"(\d+),(\d{3})", r"\1\2", cleaned)
    # Normalize percentage: e.g. 5% -> (5/100)
    cleaned = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"(\1 / 100)", cleaned)
    try:
        tree = ast.parse(cleaned, mode="eval")
    except SyntaxError as exc:
        raise DerivationError(f"Không parse được công thức '{formula}': {exc}") from exc
    return _eval_node(tree.body)


def check_derivation(formula: str, answer: str, tolerance: float = RELAXED_ACCURACY_TOLERANCE) -> tuple[bool, str]:
    """Returns (ok, message). ok=False on parse error or mismatch with `answer`."""
    if not formula or not str(formula).strip():
        return False, "Công thức derivation trống."
    try:
        computed = eval_derivation(formula)
    except DerivationError as exc:
        return False, str(exc)
    except ZeroDivisionError:
        return False, "Lỗi chia cho 0 trong công thức."
    except Exception as exc:
        return False, f"Lỗi tính toán: {exc}"
    
    target = parse_numeric(answer)
    if target is None:
        return False, f"Đáp án '{answer}' không phải số, không thể đối chiếu với kết quả công thức ({computed:g})."
    
    if abs(target) == 0:
        if abs(computed) <= 1e-9:
            return True, f"Khớp: công thức = {computed:g}, đáp án = {target:g}"
        return False, f"Lệch: công thức = {computed:g}, đáp án = {target:g}"

    diff_ratio = abs(computed - target) / abs(target)
    if diff_ratio <= tolerance or abs(computed - target) <= 1e-6:
        return True, f"Khớp: công thức = {computed:g}, đáp án = {target:g}"
    return False, f"Lệch: kết quả công thức ({computed:g}) không khớp đáp án ({target:g}) vượt quá dung sai {int(tolerance * 100)}%"


def derivation_required(answer_type: str, question_type: str) -> bool:
    return answer_type == "numeric" and question_type in DERIVATION_REQUIRED_TYPES


# ---------------------------------------------------------------------------
# Evidence validation
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def check_evidence_item(item: dict, charts_by_id: dict[int, dict], body_text: str) -> list[str]:
    """`item` is one evidence dict: {source, chart_id?, description?, quote?}.
    `charts_by_id` maps chart.id -> {"chart_id": str} (local label, e.g. "fig1").
    `description` for chart evidence is free text the annotator types directly (các
    bước truy hồi giá trị, xem docs/03) — no backing data_table to check against, only
    presence is validated.
    Returns a list of error strings (empty if valid).
    """
    errors: list[str] = []
    source = item.get("source")

    if source == "chart":
        chart_id = item.get("chart_id")
        if chart_id not in charts_by_id:
            errors.append(f"chart_id={chart_id} không tồn tại trong document này")
            return errors

        if not (item.get("description") or "").strip():
            errors.append("evidence chart thiếu mô tả cách đọc")

    elif source == "text":
        quote = (item.get("quote") or "").strip()
        if not quote:
            errors.append("evidence text thiếu quote")
        elif _normalize_text(quote) not in _normalize_text(body_text):
            errors.append(f"quote không tìm thấy nguyên văn trong body_text: '{quote[:60]}...'")
    else:
        errors.append(f"source '{source}' không hợp lệ (phải là 'chart' hoặc 'text')")

    return errors


def validate_evidence(
    hop_type: str, evidence: list[dict], charts_by_id: dict[int, dict], body_text: str
) -> ValidationResult:
    """Evidence bắt buộc cho mọi hop_type, kể cả `chart`/`text` (đơn nguồn) — không còn
    xác minh chéo độc lập nên đây là chốt kiểm chứng tự động duy nhất còn lại (xem docs/03)."""
    result = ValidationResult(ok=True)

    if not evidence:
        result.errors.append(f"hop_type={hop_type} bắt buộc phải có evidence")
    for item in evidence:
        result.errors += check_evidence_item(item, charts_by_id, body_text)

    result.ok = not result.errors
    return result


# ---------------------------------------------------------------------------
# Document-level / batch checks
# ---------------------------------------------------------------------------


def document_has_minimum_taxonomy(question_hop_types: list[str]) -> tuple[bool, str]:
    """Bước 1 yêu cầu tối thiểu 1 câu hop_type=chart + 1 câu multi-hop / document —
    giữ 1 slice chart-only để so sánh trực tiếp với ChartQA/ChartQAPro (xem docs/02)."""
    has_chart = "chart" in question_hop_types
    has_multi_hop = any(h in MULTI_HOP_TYPES for h in question_hop_types)
    if has_chart and has_multi_hop:
        return True, ""
    missing = []
    if not has_chart:
        missing.append("chart")
    if not has_multi_hop:
        missing.append("multi-hop (text_and_chart/charts)")
    return False, f"Document còn thiếu: {', '.join(missing)}"


def is_duplicate_question(question_text: str, existing_texts: list[str]) -> bool:
    norm = _normalize_text(question_text)
    return any(norm == _normalize_text(t) for t in existing_texts)


# ---------------------------------------------------------------------------
# body_text [CHART N] placeholders (xem docs/02 §Phạm vi)
# ---------------------------------------------------------------------------

_CHART_PLACEHOLDER_RE = re.compile(r"\[CHART (\d+)\]")


def check_chart_placeholders(body_text: str, n_charts: int) -> tuple[bool, str]:
    """body_text phải chứa đúng [CHART 1]..[CHART n_charts], mỗi cái đúng 1 lần,
    theo đúng thứ tự chart xuất hiện trong bài — không thiếu, không thừa, không lặp."""
    found = [int(m) for m in _CHART_PLACEHOLDER_RE.findall(body_text)]
    expected = list(range(1, n_charts + 1))
    if sorted(found) == expected and len(found) == len(set(found)):
        return True, ""
    return (
        False,
        f"body_text cần đúng các placeholder {['[CHART %d]' % i for i in expected]} "
        f"(mỗi cái 1 lần) — hiện tìm thấy {found or '(không có)'}",
    )


def word_count(text: str) -> int:
    return len(text.split())


def get_dataset_deficit_ranking(all_active_questions: list[dict]) -> tuple[list[dict], list[str], float]:
    """Computes real-time deficit percentages across all active questions in the DB
    referencing QUESTION_TYPE_TARGETS in constants.py (docs/02-dataset-design.md).
    Returns:
      - top3_q_deficits: Top 3 question_types needing prioritization (sorted by highest deficit)
      - priority_hops: Priority hop_types needing prioritization (multi-hop text_and_chart/charts if total multi-hop < 50%)
      - multihop_pct: Current dataset-wide multi-hop percentage
    """
    total_q = len(all_active_questions)
    if total_q == 0:
        top3_defaults = [
            {"type": "compositional", "current_pct": 0.0, "target_pct": 30.0, "deficit": 30.0},
            {"type": "visual_compositional", "current_pct": 0.0, "target_pct": 20.0, "deficit": 20.0},
            {"type": "data_retrieval", "current_pct": 0.0, "target_pct": 15.0, "deficit": 15.0},
        ]
        return top3_defaults, ["text_and_chart", "charts"], 0.0

    q_counts = {k: 0 for k in QUESTION_TYPE_TARGETS}
    hop_counts = {h: 0 for h in HOP_TYPES}

    for q in all_active_questions:
        qt = q.get("question_type")
        ht = q.get("hop_type")
        if qt in q_counts:
            q_counts[qt] += 1
        if ht in hop_counts:
            hop_counts[ht] += 1

    q_deficits = []
    for qt, target_ratio in QUESTION_TYPE_TARGETS.items():
        curr_ratio = q_counts[qt] / total_q
        deficit_pct = (target_ratio - curr_ratio) * 100.0
        q_deficits.append({
            "type": qt,
            "current_pct": round(curr_ratio * 100.0, 1),
            "target_pct": round(target_ratio * 100.0, 1),
            "deficit": round(deficit_pct, 1),
        })

    top3_q_deficits = sorted(q_deficits, key=lambda x: x["deficit"], reverse=True)[:3]

    multihop_n = hop_counts.get("text_and_chart", 0) + hop_counts.get("charts", 0)
    multihop_pct = round((multihop_n / total_q) * 100.0, 1)

    priority_hops = []
    if multihop_pct < 50.0:
        if hop_counts.get("text_and_chart", 0) <= hop_counts.get("charts", 0):
            priority_hops = ["text_and_chart", "charts"]
        else:
            priority_hops = ["charts", "text_and_chart"]
    else:
        sorted_hops = sorted(hop_counts.items(), key=lambda x: x[1])
        priority_hops = [h[0] for h in sorted_hops[:2]]

    return top3_q_deficits, priority_hops, multihop_pct

