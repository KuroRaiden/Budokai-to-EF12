import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pack_validation import validate_template


class PackValidationTests(unittest.TestCase):
    def test_missing_dummy_rejected_with_repair_instruction(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, r'mdl/Dummy.fmdl'):
                validate_template(folder)

    def test_stock_empty_placeholder_is_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            model = Path(folder) / 'mdl' / 'Dummy.fmdl'
            model.parent.mkdir()
            model.touch()
            validate_template(folder)
