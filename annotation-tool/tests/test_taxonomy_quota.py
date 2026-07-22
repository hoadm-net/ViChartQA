import os
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent.parent
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

from validation import get_dataset_deficit_ranking
from vlm_client import build_dynamic_system_prompt


def test_get_dataset_deficit_ranking_empty():
    top3, priority_hops, multihop_pct = get_dataset_deficit_ranking([])
    assert len(top3) == 3
    assert multihop_pct == 0.0
    assert priority_hops == ["text_and_chart", "charts"]
    assert top3[0]["type"] == "compositional"
    assert top3[0]["deficit"] == 30.0


def test_get_dataset_deficit_ranking_with_questions():
    sample_questions = [
        {"question_type": "data_retrieval", "hop_type": "chart"},
        {"question_type": "data_retrieval", "hop_type": "chart"},
        {"question_type": "visual", "hop_type": "chart"},
        {"question_type": "compositional", "hop_type": "text_and_chart"},
    ]
    top3, priority_hops, multihop_pct = get_dataset_deficit_ranking(sample_questions)
    assert len(top3) == 3
    assert multihop_pct == 25.0  # 1 out of 4 is text_and_chart
    assert "charts" in priority_hops  # Should prioritize multi-hop because < 50%
    # data_retrieval is 50% actual vs 15% target -> negative deficit
    # compositional is 25% actual vs 30% target -> 5% deficit
    # visual_compositional is 0% actual vs 20% target -> 20% deficit
    assert top3[0]["type"] in ["compositional", "visual_compositional", "multiple_choice", "fact_check", "unanswerable"]


def test_build_dynamic_system_prompt_selective_cot():
    # Test 1: Only text_and_chart & compositional
    prompt1 = build_dynamic_system_prompt(
        target_q_types=["compositional"],
        target_hops=["text_and_chart"],
        n=3,
    )
    assert "Target Question Types (prioritize these): [compositional]" in prompt1
    assert "Target Hop Types (prioritize these): [text_and_chart]" in prompt1
    assert "For 'text_and_chart'" in prompt1
    assert "For 'charts'" not in prompt1
    assert "For 'multiple_choice'" not in prompt1

    # Test 2: Multi-chart & multiple_choice
    prompt2 = build_dynamic_system_prompt(
        target_q_types=["multiple_choice"],
        target_hops=["charts"],
        n=5,
    )
    assert "For 'charts'" in prompt2
    assert "For 'multiple_choice'" in prompt2
    assert "For 'text_and_chart'" not in prompt2


if __name__ == "__main__":
    test_get_dataset_deficit_ranking_empty()
    test_get_dataset_deficit_ranking_with_questions()
    test_build_dynamic_system_prompt_selective_cot()
    print("[SUCCESS] ALL TAXONOMY QUOTA AND DYNAMIC COT UNIT TESTS PASSED!")

