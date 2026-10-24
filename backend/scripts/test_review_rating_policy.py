"""Unit tests for spaced-review self-rating intervals; no database connection is used."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.phase5_service import apply_review_rating


class ReviewRatingPolicyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
        self.preferences = SimpleNamespace(review_frequency_days=1)

    def item(self, *, interval=1, repetitions=1, ease=2.3):
        return SimpleNamespace(interval_days=interval, repetitions=repetitions, ease_factor=ease,
                               last_result="correct", last_reviewed_at=None, due_at=self.now,
                               dismissed_until=self.now)

    def test_again_resets_to_one_day_and_clears_snooze(self):
        item = self.item(interval=7, repetitions=4, ease=2.3)
        apply_review_rating(item, self.preferences, "again", now=self.now)
        self.assertEqual(item.interval_days, 1)
        self.assertEqual(item.repetitions, 0)
        self.assertEqual(item.last_result, "again")
        self.assertEqual(item.due_at, self.now + timedelta(days=1))
        self.assertIsNone(item.dismissed_until)

    def test_good_increases_interval_after_repeated_recall(self):
        item = self.item(interval=1, repetitions=1)
        apply_review_rating(item, self.preferences, "good", now=self.now)
        self.assertEqual(item.repetitions, 2)
        self.assertEqual(item.interval_days, 2)
        self.assertEqual(item.due_at, self.now + timedelta(days=2))

    def test_easy_has_longer_but_bounded_interval(self):
        item = self.item(interval=20, repetitions=9, ease=2.5)
        apply_review_rating(item, self.preferences, "easy", now=self.now)
        self.assertEqual(item.interval_days, 65)
        self.assertEqual(item.repetitions, 10)
        self.assertLessEqual(item.ease_factor, 3.0)

    def test_intervals_are_capped_at_180_days(self):
        item = self.item(interval=180, repetitions=5, ease=3.0)
        apply_review_rating(item, self.preferences, "easy", now=self.now)
        self.assertEqual(item.interval_days, 180)

    def test_invalid_rating_is_rejected(self):
        with self.assertRaises(ValueError):
            apply_review_rating(self.item(), self.preferences, "skip", now=self.now)


if __name__ == "__main__":
    unittest.main()
