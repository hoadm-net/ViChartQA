import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vlm_client import VLMError, _build_user_content, _parse_response


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


def test_build_user_content_includes_charts_and_seeds():
    content = _build_user_content(
        title="T",
        body_text="B",
        charts=[{"chart_id": "fig1", "chart_type": "line"}],
        seed_questions=["Câu 1?"],
        n=3,
    )
    joined_text = " ".join(b["text"] for b in content if b["type"] == "text")
    assert "fig1" in joined_text
    assert "Câu 1?" in joined_text
    assert "đúng 3 câu" in joined_text


def test_build_user_content_inserts_image_at_placeholder_position():
    """LLM phải THẤY ảnh chart thật ngay tại vị trí [CHART N] gốc, không chỉ đọc tên
    chart_type — đây là phần vừa bổ sung để gợi ý bám sát số liệu hơn."""
    content = _build_user_content(
        title="T",
        body_text="Trước. [CHART 1] Sau.",
        charts=[{"chart_id": "fig1", "chart_type": "line", "image_data_uri": "data:image/png;base64,AAA"}],
        seed_questions=[],
        n=1,
    )
    types = [b["type"] for b in content]
    assert "image_url" in types
    image_idx = types.index("image_url")
    assert content[image_idx]["image_url"]["url"] == "data:image/png;base64,AAA"

    before_idx = next(i for i, b in enumerate(content) if b["type"] == "text" and "Trước." in b["text"])
    after_idx = next(i for i, b in enumerate(content) if b["type"] == "text" and "Sau." in b["text"])
    assert before_idx < image_idx < after_idx, "ảnh phải nằm đúng giữa 2 đoạn text bao quanh placeholder"


def test_build_user_content_falls_back_to_text_when_image_missing():
    content = _build_user_content(
        title="T",
        body_text="X [CHART 1] Y",
        charts=[{"chart_id": "fig1", "chart_type": "line"}],  # không có image_data_uri
        seed_questions=[],
        n=1,
    )
    assert not any(b["type"] == "image_url" for b in content)


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
