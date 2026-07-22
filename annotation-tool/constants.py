"""Enum values shared by models.py, validation.py, and the Streamlit pages.
Source of truth for the question taxonomy: docs/02-dataset-design.md.
"""

QUESTION_TYPES = [
    "data_retrieval",
    "visual",
    "compositional",
    "visual_compositional",
    "multiple_choice",
    "fact_check",
    "unanswerable",
]

# question_type values that require a `derivation` formula when answer_type == "numeric"
DERIVATION_REQUIRED_TYPES = {"compositional", "visual_compositional"}

HOP_TYPES = ["text", "chart", "text_and_chart", "charts"]
MULTI_HOP_TYPES = {"text_and_chart", "charts"}

ANSWER_TYPES = ["numeric", "text", "unanswerable", "boolean"]

# "combo" = 1 vùng vẽ trộn từ 2 loại mark trở lên (vd cột doanh thu + đường tăng trưởng,
# grouped/stacked bar kèm 1 hoặc nhiều đường) — khác "subplot" ở chỗ vẫn chỉ 1 vùng vẽ,
# không tách nhiều panel. "subplot" = 1 ảnh ghép nhiều panel khác loại chart (vd pie +
# bar cạnh nhau) — không tách chart_id riêng cho từng panel (ảnh không có nhãn (a)/(b)
# để phân biệt, model đọc ảnh cũng không biết đâu là đâu), coi cả ảnh là 1 chart entry,
# type="subplot".
CHART_TYPES = ["bar", "line", "pie", "combo", "subplot"]

MAX_BODY_TEXT_WORDS = 2000  # xem docs/02 §Phạm vi

# Kinh tế = neo (nguồn dồi dào), còn lại là miền mở rộng — xem docs/02 §Miền dữ liệu
DOMAINS = ["economics", "science", "education", "health", "environment", "energy", "society"]

EVIDENCE_SOURCES = ["chart", "text"]

DOCUMENT_STATUSES = ["intake", "in_progress"]

# Không có "llm_suggested": gợi ý LLM chỉ tồn tại tạm thời trong session, không lưu vào
# bảng questions — chỉ khi annotator tự soạn/sửa qua form và bấm Lưu mới tạo Question,
# nên Question luôn bắt đầu ở active. "rejected" dùng khi rút lại 1 câu đã lưu.
QUESTION_STATUSES = ["active", "rejected"]

QUESTION_VERSION_CHANGE_TYPES = ["created", "edited", "rejected"]

PODS = ["A", "B", "C", "D", "E"]
ROLES = ["annotator", "pm", "data_intake"]

SPLITS = ["train", "val", "test"]

# Tỷ trọng mục tiêu chuẩn per docs/02-dataset-design.md
QUESTION_TYPE_TARGETS = {
    "compositional": 0.30,
    "visual_compositional": 0.20,
    "data_retrieval": 0.15,
    "visual": 0.15,
    "multiple_choice": 0.08,
    "fact_check": 0.06,
    "unanswerable": 0.06,
}

# Tất cả model gọi qua OpenRouter (1 API key, 1 SDK OpenAI-compatible) — slug xác nhận
# trực tiếp qua https://openrouter.ai/api/v1/models ngày 13/07/2026 (đều hỗ trợ
# response_format/structured_outputs, cần cho JSON output của generate_candidates()).
VLM_MODEL_SLUGS = {
    "gpt-5.4-nano": "openai/gpt-5.4-nano",
    "gemini-3.1-flash-lite": "google/gemini-3.1-flash-lite",
}
VLM_MODELS = list(VLM_MODEL_SLUGS.keys())

RELAXED_ACCURACY_TOLERANCE = 0.05  # 5%, per docs/03 Quy tắc viết đáp án
