"""Duplicate-document detection — pure Python, no Streamlit import (same convention as
validation.py), testable in isolation.

Nhiều annotator cùng thu thập bài từ web độc lập với nhau — cần cảnh báo khi 1
document mới nhập có URL trùng, title trùng, hoặc title gần giống (báo/tạp chí đăng
lại bài của nhau, sửa vài chữ) một document đã có trong DB, để tránh nhập trùng vào
dataset. Đây là cảnh báo (warn), không chặn lưu — annotator tự quyết định, giống quy
ước `is_duplicate_question` ở validation.py: có thể là 2 bài thật sự khác nhau dù
title giống nhau tình cờ.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

# difflib.SequenceMatcher bắt tốt "sửa vài chữ, giữ nguyên thứ tự câu" (edit thật sự
# nhỏ) nhưng yếu với đảo thứ tự cụm từ; Jaccard trên tập từ bắt tốt trường hợp đảo từ
# nhưng yếu với câu dài có nhiều từ chung ngẫu nhiên — dùng max(2 chỉ số) để bù nhau.
TITLE_SIMILARITY_THRESHOLD = 0.75


@dataclass
class DuplicateMatch:
    document_id: int
    title: str
    reason: str  # "url_exact" | "title_exact" | "title_similar"
    score: float  # 1.0 cho exact, tỉ lệ tương đồng cho "title_similar"


def _normalize_url(url: str) -> str:
    """Bỏ qua khác biệt vặt không đổi bản chất bài viết: scheme, www., query string,
    fragment, dấu / cuối — 2 URL chỉ khác mấy cái này vẫn là cùng 1 bài."""
    url = url.strip().lower()
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)
    url = url.split("?")[0].split("#")[0]
    return url.rstrip("/")


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def _word_set(title: str) -> set[str]:
    return set(re.findall(r"\w+", title.lower(), re.UNICODE))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def title_similarity(title_a: str, title_b: str) -> float:
    norm_a, norm_b = _normalize_title(title_a), _normalize_title(title_b)
    char_ratio = SequenceMatcher(None, norm_a, norm_b).ratio()
    word_ratio = _jaccard(_word_set(title_a), _word_set(title_b))
    return max(char_ratio, word_ratio)


def find_duplicates(
    title: str,
    url: str | None,
    existing: list[dict],
    exclude_id: int | None = None,
    title_threshold: float = TITLE_SIMILARITY_THRESHOLD,
) -> list[DuplicateMatch]:
    """`existing`: [{"id": int, "title": str, "source_url": str | None}, ...] — toàn bộ
    document hiện có (hoặc 1 tập con), thường lấy từ toàn DB vì không biết annotator
    khác đã nhập bài trùng ở đâu. `exclude_id`: bỏ qua chính document đang sửa (dùng
    khi gọi từ trang sửa document)."""
    norm_title = _normalize_title(title)
    norm_url = _normalize_url(url) if url else None

    matches: list[DuplicateMatch] = []
    for doc in existing:
        if doc["id"] == exclude_id:
            continue

        doc_url = doc.get("source_url")
        if norm_url and doc_url and norm_url == _normalize_url(doc_url):
            matches.append(DuplicateMatch(doc["id"], doc["title"], "url_exact", 1.0))
            continue  # URL trùng là tín hiệu mạnh nhất, khỏi cần so title nữa

        if norm_title == _normalize_title(doc["title"]):
            matches.append(DuplicateMatch(doc["id"], doc["title"], "title_exact", 1.0))
            continue

        score = title_similarity(title, doc["title"])
        if score >= title_threshold:
            matches.append(DuplicateMatch(doc["id"], doc["title"], "title_similar", score))

    matches.sort(key=lambda m: -m.score)
    return matches
