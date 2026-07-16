import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dedup import find_duplicates, title_similarity


def test_url_exact_match_ignores_scheme_www_query():
    existing = [{"id": 1, "title": "Bài A", "source_url": "https://www.example.vn/bai-a?utm_source=fb"}]
    matches = find_duplicates("Bài A (bản khác)", "http://example.vn/bai-a/", existing)
    assert len(matches) == 1
    assert matches[0].reason == "url_exact"
    assert matches[0].score == 1.0


def test_title_exact_match_case_and_whitespace_insensitive():
    existing = [{"id": 1, "title": "GDP  Việt Nam   tăng trưởng 2024", "source_url": None}]
    matches = find_duplicates("gdp việt nam tăng trưởng 2024", None, existing)
    assert len(matches) == 1
    assert matches[0].reason == "title_exact"


def test_title_similar_catches_minor_edit_same_word_order():
    """Báo B đăng lại bài báo A, sửa vài chữ — giữ nguyên cấu trúc câu."""
    original = "Nửa đầu tháng 12/2024: Xu hướng nào đang định hình thị trường xuất nhập khẩu?"
    copied = "Nửa đầu tháng 12/2024: Xu hướng nào đang chi phối thị trường xuất nhập khẩu?"
    assert title_similarity(original, copied) >= 0.75


def test_title_similar_catches_reordered_words():
    """Tiêu đề bị đảo cụm từ nhưng cùng nội dung/từ vựng — char-sequence ratio yếu ở
    ca này, Jaccard trên tập từ phải gánh vai trò chính."""
    original = "Nửa đầu tháng 12/2024: Xu hướng nào đang định hình thị trường xuất nhập khẩu?"
    reordered = "Xu hướng định hình thị trường xuất nhập khẩu nửa đầu tháng 12/2024"
    assert title_similarity(original, reordered) >= 0.6


def test_unrelated_titles_not_flagged():
    existing = [{"id": 1, "title": "GDP Việt Nam tăng trưởng 2024", "source_url": None}]
    matches = find_duplicates("Cuộc thi TÔI KHỎE ĐẸP HƠN thu hút hàng chục nghìn người", None, existing)
    assert matches == []


def test_exclude_id_skips_the_document_being_edited():
    existing = [{"id": 5, "title": "Bài đang sửa", "source_url": "https://a.vn/x"}]
    matches = find_duplicates("Bài đang sửa", "https://a.vn/x", existing, exclude_id=5)
    assert matches == []


def test_url_match_takes_priority_over_title_similarity_check():
    """1 document trùng URL không nên bị liệt kê thêm lần nữa vì title cũng giống."""
    existing = [{"id": 1, "title": "Bài A", "source_url": "https://a.vn/bai-a"}]
    matches = find_duplicates("Bài A", "https://a.vn/bai-a", existing)
    assert len(matches) == 1
    assert matches[0].reason == "url_exact"


def test_matches_sorted_by_score_descending():
    existing = [
        {"id": 1, "title": "GDP Việt Nam tăng trưởng mạnh trong năm 2024", "source_url": None},
        {"id": 2, "title": "GDP Việt Nam tăng trưởng năm 2024", "source_url": None},
    ]
    matches = find_duplicates("GDP Việt Nam tăng trưởng năm 2024", None, existing)
    assert matches[0].document_id == 2  # exact match trước
    assert matches[0].score >= matches[1].score


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
