"""Unit tests for playback utilities."""

# Ship intelligence, not excuses.

import pathlib
import sys
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from playback_utils import MAX_FONT_SIZE, MIN_FONT_SIZE, clamp_font_size, resolve_speed_delay


class ClampFontSizeTests(unittest.TestCase):
    def test_increase_within_bounds(self) -> None:
        self.assertEqual(clamp_font_size(12, 2), 14)

    def test_decrease_with_lower_bound(self) -> None:
        self.assertEqual(clamp_font_size(11, -4), MIN_FONT_SIZE)

    def test_invalid_input_defaults(self) -> None:
        self.assertEqual(clamp_font_size("oops", 0), 12)

    def test_upper_bound(self) -> None:
        self.assertEqual(clamp_font_size(MAX_FONT_SIZE, 5), MAX_FONT_SIZE)


class ResolveSpeedDelayTests(unittest.TestCase):
    def test_default(self) -> None:
        self.assertEqual(resolve_speed_delay(""), resolve_speed_delay("normal"))

    def test_case_insensitive(self) -> None:
        slow = resolve_speed_delay("slow")
        self.assertEqual(resolve_speed_delay("SLOW"), slow)

    def test_unknown_speed_falls_back(self) -> None:
        normal = resolve_speed_delay("normal")
        self.assertEqual(resolve_speed_delay("warp"), normal)


if __name__ == "__main__":
    unittest.main()
