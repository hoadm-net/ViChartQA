"""Pure Python validation logic — no Streamlit import here (see docs/08 §3).

Reused by: annotation pages (block/warn on submit) and the Tuần 5 export/cleanup script.
"""

from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass, field

from constants import DERIVATION_REQUIRED_TYPES, MULTI_HOP_TYPES, RELAXED_ACCURACY_TOLERANCE

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
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError as exc:
        raise DerivationError(f"Không parse được công thức: {exc}") from exc
    return _eval_node(tree.body)


def check_derivation(formula: str, answer: str, tolerance: float = RELAXED_ACCURACY_TOLERANCE) -> tuple[bool, str]:
    """Returns (ok, message). ok=False on parse error or mismatch with `answer`."""
    try:
        computed = eval_derivation(formula)
    except DerivationError as exc:
        return False, str(exc)
    target = parse_numeric(answer)
    if target is None:
        return False, "Answer không phải số, không so sánh được với derivation."
    if abs(computed - target) <= max(abs(target) * tolerance, 1e-9):
        return True, f"Khớp: công thức = {computed:g}, answer = {target:g}"
    return False, f"Lệch: công thức = {computed:g}, answer = {target:g}"


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
    """`item` is one evidence dict: {source, chart_id?, series?, x?, quote?}.
    `charts_by_id` maps chart.id -> {"chart_id": str} (local label, e.g. "fig1").
    `series`/`x` for chart evidence are free text the annotator types directly — no
    backing data_table to check against, only presence is validated.
    Returns a list of error strings (empty if valid).
    """
    errors: list[str] = []
    source = item.get("source")

    if source == "chart":
        chart_id = item.get("chart_id")
        if chart_id not in charts_by_id:
            errors.append(f"chart_id={chart_id} không tồn tại trong document này")
            return errors

        if not (item.get("series") or "").strip():
            errors.append("evidence chart thiếu series/chiều dữ liệu")

        x_values = item.get("x") or []
        if not x_values:
            errors.append("evidence chart thiếu giá trị x")

    elif source == "text":
        quote = (item.get("quote") or "").strip()
        if not quote:
            errors.append("evidence text thiếu quote")
        elif quote not in body_text:
            errors.append(f"quote không tìm thấy nguyên văn trong body_text: '{quote[:60]}...'")
    else:
        errors.append(f"source '{source}' không hợp lệ (phải là 'chart' hoặc 'text')")

    return errors


def validate_evidence(
    hop_type: str, evidence: list[dict], charts_by_id: dict[int, dict], body_text: str
) -> ValidationResult:
    """Evidence bắt buộc cho mọi hop_type, kể cả single_chart — không còn xác minh
    chéo độc lập nên đây là chốt kiểm chứng tự động duy nhất còn lại (xem docs/03)."""
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
    """Bước 1 yêu cầu tối thiểu 1 câu single_chart + 1 câu multi-hop / document."""
    has_single = "single_chart" in question_hop_types
    has_multi_hop = any(h in MULTI_HOP_TYPES for h in question_hop_types)
    if has_single and has_multi_hop:
        return True, ""
    missing = []
    if not has_single:
        missing.append("single_chart")
    if not has_multi_hop:
        missing.append("multi-hop (text_to_chart/chart_to_chart/fact_check_dual)")
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
