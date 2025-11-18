from typing import Iterable, List


def normalize_student_ids(raw_student_ids) -> List[int]:
    """Normalize various encodings of student_ids into a list of ints.

    Accepts:
    - list of values (strings/ints)
    - comma-separated string
    - single int or string

    Returns list of ints, skipping non-convertible values.
    """
    if raw_student_ids is None:
        return []

    # If it's a Django QueryDict-like object with getlist, the caller
    # should pass the value from request.data.getlist already. Here we
    # handle simple python values.
    if isinstance(raw_student_ids, str):
        parts = [s.strip() for s in raw_student_ids.split(',') if s.strip()]
    elif isinstance(raw_student_ids, Iterable) and not isinstance(raw_student_ids, (bytes, str)):
        parts = list(raw_student_ids)
    else:
        parts = [raw_student_ids]

    normalized: List[int] = []
    for p in parts:
        try:
            normalized.append(int(p))
        except (TypeError, ValueError):
            # skip non-int values
            continue

    return normalized
