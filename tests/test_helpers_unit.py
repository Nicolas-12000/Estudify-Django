from apps.api.v1.helpers import normalize_student_ids


def test_normalize_none():
    assert normalize_student_ids(None) == []


def test_normalize_comma_string():
    assert normalize_student_ids("1,2, 3") == [1, 2, 3]


def test_normalize_mixed_iterable():
    assert normalize_student_ids(["4", 5, "six", None]) == [4, 5]


def test_normalize_single_int():
    assert normalize_student_ids(7) == [7]
