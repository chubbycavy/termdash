"""Pure-function tests for timer digit parsing and formatting."""

import pytest

from termdash.widgets.timer import TimerDisplay


class TestParseBuffer:
    @staticmethod
    def test_empty_input_is_rejected():
        assert TimerDisplay.parse_buffer("") is None

    @staticmethod
    def test_single_digit_right_aligns_to_seconds():
        assert TimerDisplay.parse_buffer("1") == 1

    @staticmethod
    def test_five_digits_parse_as_mmss_with_hours():
        assert TimerDisplay.parse_buffer("00130") == 90

    @staticmethod
    def test_six_digits_parse_as_full_time():
        assert TimerDisplay.parse_buffer("123456") == 12 * 3600 + 34 * 60 + 56

    @staticmethod
    def test_sixty_minutes_is_rejected():
        assert TimerDisplay.parse_buffer("126060") is None

    @staticmethod
    def test_sixty_seconds_is_rejected():
        assert TimerDisplay.parse_buffer("000060") is None

    @staticmethod
    def test_zero_total_is_rejected():
        assert TimerDisplay.parse_buffer("000000") is None

    @staticmethod
    def test_maximum_ninety_nine_hours_is_accepted():
        assert TimerDisplay.parse_buffer("995959") == 99 * 3600 + 59 * 60 + 59


class TestFormatDigits:
    @staticmethod
    @pytest.mark.parametrize(
        ("digits", "expected"),
        [
            ("", "00:00:00"),
            ("1", "00:00:01"),
            ("130", "00:01:30"),
            ("1234", "00:12:34"),
            ("123456", "12:34:56"),
            ("1234567", "23:45:67"),
        ],
    )
    def test_digits_renders_right_aligned(digits, expected):
        assert TimerDisplay.format_digits(digits) == expected


class TestFormatSeconds:
    @staticmethod
    @pytest.mark.parametrize(
        ("total", "expected"),
        [
            (0, "00:00:00"),
            (1, "00:00:01"),
            (61, "00:01:01"),
            (600, "00:10:00"),
            (359999, "99:59:59"),
        ],
    )
    def test_seconds_render_as_hhmmss(total, expected):
        assert TimerDisplay.format_seconds(total) == expected
