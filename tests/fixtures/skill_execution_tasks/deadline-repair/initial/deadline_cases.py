import unittest

from retry_policy import retry_allowed


class DeadlineTests(unittest.TestCase):
    def test_original_symptom_at_deadline(self):
        self.assertFalse(retry_allowed(100, 100))

    def test_before_and_after_deadline(self):
        self.assertTrue(retry_allowed(0, 100))
        self.assertTrue(retry_allowed(99, 100))
        self.assertFalse(retry_allowed(101, 100))

    def test_invalid_budget_remains_rejected(self):
        with self.assertRaises(ValueError):
            retry_allowed(0, 0)
