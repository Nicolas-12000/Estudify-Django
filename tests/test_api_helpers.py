from apps.api.v1.helpers import normalize_student_ids


def test_normalize_from_list_of_ints():
    assert normalize_student_ids([1, 2, 3]) == [1, 2, 3]


def test_normalize_from_comma_string():
    assert normalize_student_ids('1,2, 3') == [1, 2, 3]


def test_normalize_from_single_value():
    assert normalize_student_ids('5') == [5]
    assert normalize_student_ids(6) == [6]


def test_normalize_skips_invalid_values():
    assert normalize_student_ids(['1', 'a', None, '2']) == [1, 2]
