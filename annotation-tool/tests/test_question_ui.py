import os
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent.parent
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

from validation import validate_evidence


def test_validate_evidence_text_and_chart():
    # Test valid text_and_chart evidence (1 chart + 1 text)
    charts_by_id = {1: {"chart_id": "fig1"}}
    body_text = "Tốc độ tăng trưởng GDP năm 2024 ước tính tăng 7,09% so với năm trước."

    valid_evidence = [
        {"hop": 1, "source": "chart", "chart_id": 1, "description": "1. Đọc trục tung tìm GDP 2024"},
        {"hop": 2, "source": "text", "quote": "Tốc độ tăng trưởng GDP năm 2024 ước tính tăng 7,09%"},
    ]

    res = validate_evidence("text_and_chart", valid_evidence, charts_by_id, body_text)
    assert res.ok, f"Validation failed: {res.errors}"


def test_validate_evidence_invalid_text_quote():
    charts_by_id = {1: {"chart_id": "fig1"}}
    body_text = "Tốc độ tăng trưởng GDP năm 2024 ước tính tăng 7,09% so với năm trước."

    invalid_evidence = [
        {"hop": 1, "source": "chart", "chart_id": 1, "description": "1. Đọc trục tung"},
        {"hop": 2, "source": "text", "quote": "Quote nay khong co trong text"},
    ]

    res = validate_evidence("text_and_chart", invalid_evidence, charts_by_id, body_text)
    assert not res.ok
    assert any("quote không tìm thấy" in e for e in res.errors)


from question_ui import get_question_label, render_doc_context, render_evidence_builder, render_question_form, word_count


def test_question_ui_imports_and_symbols():
    assert callable(word_count)
    assert word_count("Xin chào Việt Nam") == 4
    assert callable(render_doc_context)
    assert callable(render_evidence_builder)
    assert callable(render_question_form)
    assert callable(get_question_label)


def test_q_label_logic():
    # Các trường hợp test biên và các kiểu dữ liệu khác nhau
    assert get_question_label(1) == "Câu hỏi (ID: #1)"            # ID nhỏ nhất hợp lệ
    assert get_question_label(42) == "Câu hỏi (ID: #42)"          # ID số nguyên dương hợp lệ
    assert get_question_label(2**63 - 1) == f"Câu hỏi (ID: #{2**63 - 1})"  # ID số nguyên cực lớn (MAX_INT64)
    assert get_question_label(None) == "Câu hỏi"                  # ID là None (tạo mới)
    assert get_question_label(0) == "Câu hỏi"                     # ID là 0 (không hợp lệ)
    assert get_question_label(-5) == "Câu hỏi"                    # ID là số âm (không hợp lệ)
    assert get_question_label("42") == "Câu hỏi"                  # ID dạng chuỗi (không hợp lệ)
    assert get_question_label(42.0) == "Câu hỏi"                  # ID dạng số thực (không hợp lệ)
    assert get_question_label(True) == "Câu hỏi"                  # ID dạng bool True (không hợp lệ)
    assert get_question_label(False) == "Câu hỏi"                 # ID dạng bool False (không hợp lệ)


if __name__ == "__main__":
    test_validate_evidence_text_and_chart()
    test_validate_evidence_invalid_text_quote()
    test_question_ui_imports_and_symbols()
    test_q_label_logic()
    print("[SUCCESS] ALL UI & EVIDENCE VALIDATION UNIT TESTS PASSED!")
