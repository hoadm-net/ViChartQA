import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validation import (
    check_chart_placeholders,
    check_derivation,
    document_has_minimum_taxonomy,
    eval_derivation,
    is_duplicate_question,
    numeric_answers_match,
    validate_evidence,
    word_count,
)


def test_eval_derivation_basic():
    assert eval_derivation("8.4 - 2.5") == 5.9
    assert eval_derivation("(14740 + 1910)/2") == 8325.0


def test_eval_derivation_rejects_code_injection():
    import validation

    for bad in ["__import__('os').system('echo hi')", "open('x')", "[].__class__"]:
        try:
            eval_derivation(bad)
            assert False, f"should have rejected: {bad}"
        except validation.DerivationError:
            pass


def test_check_derivation_match_and_mismatch():
    ok, _ = check_derivation("8.4 - 2.5", "5.9")
    assert ok
    ok, _ = check_derivation("8.4 - 2.5", "10")
    assert not ok


def test_numeric_answers_match_relaxed_tolerance():
    assert numeric_answers_match("6.2%", "6.19%")
    assert not numeric_answers_match("6.2%", "8%")


def test_validate_evidence_chart_ok():
    """description là text tự do annotator gõ tay (các bước truy hồi giá trị) — không
    có data_table để tra cứu, chỉ cần chart_id tồn tại và description không rỗng."""
    charts_by_id = {1: {"chart_id": "fig1"}}
    evidence = [{"source": "chart", "chart_id": 1, "description": "1. Tìm đường GDP. 2. Đọc giá trị năm 2011 và 2021."}]
    result = validate_evidence("chart", evidence, charts_by_id, body_text="")
    assert result.ok, result.errors


def test_validate_evidence_chart_unknown_chart_id():
    charts_by_id = {1: {"chart_id": "fig1"}}
    evidence = [{"source": "chart", "chart_id": 99, "description": "1. Tìm đường FDI."}]
    result = validate_evidence("text_and_chart", evidence, charts_by_id, body_text="")
    assert not result.ok
    assert "chart_id" in result.errors[0]


def test_validate_evidence_chart_empty_description_rejected():
    charts_by_id = {1: {"chart_id": "fig1"}}
    missing_description = [{"source": "chart", "chart_id": 1, "description": ""}]
    assert not validate_evidence("chart", missing_description, charts_by_id, body_text="").ok
    blank_description = [{"source": "chart", "chart_id": 1, "description": "   "}]
    assert not validate_evidence("chart", blank_description, charts_by_id, body_text="").ok


def test_validate_evidence_text_requires_exact_quote():
    body = "GDP tăng dần theo thời gian."
    evidence = [{"source": "text", "quote": "GDP tăng dần theo thời gian."}]
    assert validate_evidence("text_and_chart", evidence, {}, body).ok

    evidence_bad = [{"source": "text", "quote": "GDP giảm mạnh."}]
    assert not validate_evidence("text_and_chart", evidence_bad, {}, body).ok


def test_multi_hop_requires_evidence():
    result = validate_evidence("charts", [], {}, "")
    assert not result.ok


def test_single_source_hop_types_require_evidence_too():
    """Không còn xác minh chéo độc lập — evidence bắt buộc cho mọi hop_type,
    kể cả hop_type=chart hoặc text (trước đây được coi là tuỳ chọn)."""
    result = validate_evidence("chart", [], {}, "")
    assert not result.ok
    assert "evidence" in result.errors[0]

    result = validate_evidence("text", [], {}, "")
    assert not result.ok
    assert "evidence" in result.errors[0]


def test_document_minimum_taxonomy():
    ok, _ = document_has_minimum_taxonomy(["chart", "text_and_chart"])
    assert ok
    ok, msg = document_has_minimum_taxonomy(["chart", "chart"])
    assert not ok
    assert "multi-hop" in msg


def test_duplicate_question_detection():
    assert is_duplicate_question("GDP năm 2020 là bao nhiêu?", ["gdp năm 2020 là bao nhiêu?  "])
    assert not is_duplicate_question("GDP năm 2020?", ["FDI năm 2020?"])


def test_check_chart_placeholders_exact_match():
    ok, _ = check_chart_placeholders("Mở đầu [CHART 1] giữa bài [CHART 2] kết.", 2)
    assert ok


def test_check_chart_placeholders_missing():
    ok, msg = check_chart_placeholders("Chỉ có [CHART 1] thôi.", 2)
    assert not ok
    assert "[CHART 2]" in msg


def test_check_chart_placeholders_duplicate():
    ok, _ = check_chart_placeholders("[CHART 1] rồi lại [CHART 1] lần nữa.", 1)
    assert not ok


def test_check_chart_placeholders_extra():
    ok, _ = check_chart_placeholders("[CHART 1] và [CHART 2] nhưng chỉ upload 1 ảnh.", 1)
    assert not ok


def test_word_count():
    assert word_count("một hai ba") == 3
    assert word_count("") == 0


if __name__ == "__main__":
    import inspect

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
