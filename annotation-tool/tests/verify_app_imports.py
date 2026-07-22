import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent.parent
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

print("[1/3] Importing question_ui...")
import question_ui
print("[1/3] OK!")

print("[2/3] Verifying question_ui symbols...")
assert hasattr(question_ui, "word_count")
assert hasattr(question_ui, "render_doc_context")
assert hasattr(question_ui, "render_question_form")
assert hasattr(question_ui, "render_evidence_builder")
print("[2/3] OK!")

print("[3/3] Testing render_evidence_builder logic...")
evidence = question_ui.render_evidence_builder(lambda x: f"test_{x}", {1: {"chart_id": "fig1"}}, hop_type="text_and_chart")
assert len(evidence) == 2
assert evidence[0]["source"] == "chart"
assert evidence[1]["source"] == "text"
print("[3/3] OK!")

print("\n=== VERIFICATION PASSED: NO ERRORS FOUND IN APP UI MODULES ===")
