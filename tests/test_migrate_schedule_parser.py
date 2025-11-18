from apps.courses.management.commands.migrate_schedule import Command


def test_parse_simple_formats():
    cmd = Command()
    assert cmd._parse_entry('Lun 08:00-10:00') == (0, '08:00', '10:00')
    assert cmd._parse_entry('Mar 8-10') == (1, '08:00', '10:00')
    assert cmd._parse_entry('Mie 9:30-11:00') == (2, '09:30', '11:00')


def test_parse_comma_separator_and_invalid():
    cmd = Command()
    # comma is handled by handle (replaced with ';'), but parser should parse entry
    assert cmd._parse_entry('Jue 7-9') == (3, '07:00', '09:00')
    assert cmd._parse_entry('InvalidEntry') is None
