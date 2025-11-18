import pytest

from django.core.exceptions import ValidationError

from apps.core import validators


def test_validate_name_field_allows_valid_names():
    # Regular unicode name
    validators.validate_name_field('José Martínez')
    validators.validate_name_field("O'Connor")
    validators.validate_name_field('Ana-María')


def test_validate_name_field_rejects_invalid_characters():
    with pytest.raises(ValidationError):
        validators.validate_name_field('John$Doe')


def test_validate_name_field_too_short_and_too_long():
    with pytest.raises(ValidationError):
        validators.validate_name_field('A')

    long_name = 'A' * 151
    with pytest.raises(ValidationError):
        validators.validate_name_field(long_name)


def test_validate_username_field_valid_and_invalid():
    validators.validate_username_field('user.name_123')

    with pytest.raises(ValidationError):
        validators.validate_username_field('ab')  # too short

    with pytest.raises(ValidationError):
        validators.validate_username_field('bad!name')


def test_validate_code_field_cases():
    # uppercase and digits allowed
    validators.validate_code_field('CS101')

    # lowercase should be rejected by pattern
    with pytest.raises(ValidationError):
        validators.validate_code_field('cs101')

    with pytest.raises(ValidationError):
        validators.validate_code_field('A')


def test_validate_text_field_blocks_html_and_allows_plain_text():
    validators.validate_text_field('Este es un texto seguro, con puntuación.')

    with pytest.raises(ValidationError):
        validators.validate_text_field('<script>alert(1)</script>')


def test_validate_alphanumeric_with_spaces():
    validators.validate_alphanumeric_with_spaces("Calle 123, Bogotá.")

    with pytest.raises(ValidationError):
        validators.validate_alphanumeric_with_spaces('Bad<>Tag')


def test_validators_edge_cases_and_malicious_payloads():
    # Name field: exact minimum and maximum lengths
    validators.validate_name_field('Ab')  # 2 chars valid
    validators.validate_name_field('A' * 150)  # 150 chars valid

    with pytest.raises(ValidationError):
        validators.validate_name_field('B')  # 1 char invalid

    with pytest.raises(ValidationError):
        validators.validate_name_field('A' * 151)  # too long

    # Username: allowed characters and long username (150 chars) should be accepted
    uname = 'user_' + ('x' * 145)
    validators.validate_username_field(uname)

    # Code field: must be uppercase letters/numbers/underscore/dash
    validators.validate_code_field('A1')
    with pytest.raises(ValidationError):
        validators.validate_code_field('a1')  # lowercase not allowed

    # Alphanumeric with spaces: allow accents and punctuation
    validators.validate_alphanumeric_with_spaces('Ñandú, Calle 7 - Apt. 3')

    # validate_text_field: several malicious payloads should be rejected
    malicious = [
        '<script>alert(1)</script>',
        '<IFRAME src="http://evil" ></IFRAME>',
        'javascript:alert(1)',
        '<img src=x onerror=alert(1)>',
        '<div onclick="doBad()">x</div>',
        '<embed src="malicious">',
        '<object data="bad">',
        'normal text <script>bad</script> and more'
    ]

    for payload in malicious:
        with pytest.raises(ValidationError, match='no permitido'):
            validators.validate_text_field(payload)

    # But benign HTML-escaped content should be allowed (entities)
    validators.validate_text_field('Less than &lt; and ampersand &amp; are fine')


def test_validate_name_field_unicode_and_length_edges():
    # Exactly 150 characters should be allowed
    part = "José-"
    times = 150 // len(part)
    name150 = (part * times)[:150]
    assert len(name150) == 150
    validators.validate_name_field(name150)

    # 151 characters should be rejected
    name151 = name150 + 'A'
    assert len(name151) == 151
    with pytest.raises(ValidationError):
        validators.validate_name_field(name151)


def test_validate_text_field_rejects_many_malicious_variants():
    bad_inputs = [
        '<script>alert(1)</script>',
        '<ScRiPt>alert(1)</ScRiPt>',
        '<iframe src="http://example.com"></iframe>',
        'javascript:alert(1)',
        '<img src=x onerror=alert(1)>',
        '<div onload="doEvil()">',
        '<object data="evil"></object>',
        '<embed src="evil.swf">',
        "<a href=\"javascript:alert(1)\">x</a>",
        'something onclick=doEvil()',
    ]

    for s in bad_inputs:
        with pytest.raises(ValidationError):
            validators.validate_text_field(s)

    # Some benign HTML-like content that isn't in the dangerous list should pass
    validators.validate_text_field('<b>bold text</b>')


def test_validate_username_and_code_length_edges_and_chars():
    # username: allowed chars
    validators.validate_username_field('user.name-123_')
    # username with space is invalid
    with pytest.raises(ValidationError):
        validators.validate_username_field('user name')

    # code: uppercase allowed, test upper bound (50)
    code50 = 'A' * 50
    assert len(code50) == 50
    validators.validate_code_field(code50)

    # code of length 1 should fail
    with pytest.raises(ValidationError):
        validators.validate_code_field('Z')

    # code with lowercase should fail
    with pytest.raises(ValidationError):
        validators.validate_code_field('abc123')
