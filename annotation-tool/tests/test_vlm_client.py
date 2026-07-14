import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vlm_client import VLMError, _build_user_prompt, _parse_response


def test_parse_response_plain_json():
    text = '{"questions": [{"question": "GDP 2020?", "answer": "5"}]}'
    result = _parse_response(text)
    assert result == [{"question": "GDP 2020?", "answer": "5"}]


def test_parse_response_markdown_fenced_json():
    text = '```json\n{"questions": [{"question": "x"}]}\n```'
    result = _parse_response(text)
    assert result == [{"question": "x"}]


def test_parse_response_bare_list():
    text = '[{"question": "x"}]'
    result = _parse_response(text)
    assert result == [{"question": "x"}]


def test_parse_response_invalid_json_raises():
    try:
        _parse_response("not json at all")
        assert False, "should have raised"
    except VLMError:
        pass


def test_build_user_prompt_includes_charts_and_seeds():
    prompt = _build_user_prompt(
        title="T",
        body_text="B",
        charts=[{"chart_id": "fig1", "chart_type": "line"}],
        seed_questions=["Câu 1?"],
        n=3,
    )
    assert "fig1" in prompt
    assert "Câu 1?" in prompt
    assert "đúng 3 câu" in prompt


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
