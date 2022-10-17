import unittest

from Hinkskalle.util.name_check import validate_name


class TestNameCheck(unittest.TestCase):
    def test_validate_empty(self):
        errors = validate_name({})
        self.assertDictEqual(errors, {})
        errors = validate_name({"name": ""})
        self.assertDictEqual(errors, {})

    def test_validate_good(self):
        for good in ["test.hase", "Test.Hase", "test-hase", "test_hase", "t3st", "123"]:
            errors = validate_name({"name": good})
            self.assertDictEqual(errors, {}, f"check {good}")

    def test_validate_chars(self):
        for invalid in ["test&hase", "test hase", "test%%hase"]:
            errors = validate_name({"name": invalid})
            self.assertDictEqual(errors, {"name": f"name contains invalid characters"}, f"check {invalid}")

    def test_validate_start(self):
        for invalid in ["-test", ".test", "_test"]:
            errors = validate_name({"name": invalid})
            self.assertDictEqual(
                errors, {"name": f"name must start and end with a letter or number"}, f"check {invalid}"
            )

    def test_validate_end(self):
        for invalid in ["test-", "test.", "test_"]:
            errors = validate_name({"name": invalid})
            self.assertDictEqual(
                errors, {"name": f"name must start and end with a letter or number"}, f"check {invalid}"
            )
