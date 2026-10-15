from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from shared_labels import COMMON,shared_label

class SharedLabelTests(unittest.TestCase):
    def test_common_bank_fully_described(self):
        self.assertEqual(set(COMMON),set(range(265)))

    def test_selected_clip_has_description_and_search_tags(self):
        result=shared_label(Path('0000_BCCMN.AMB/0002.amm'),7)
        self.assertEqual(result['label'],'Braced defensive hold')
        self.assertEqual(result['label_kind'],'description')
        self.assertIn('guard',result['tags'])
        self.assertIn('not an original game label',result['label_note'])

    def test_indices_do_not_leak_to_another_bank(self):
        self.assertIsNone(shared_label(Path('Goku__0092_BCGOK.amb/0002.amm'),7))
        self.assertIsNone(shared_label(Path('0000_BCCMN.AMB/0003.amm'),7))
        self.assertIsNone(shared_label(Path('0000_BCCMN.AMB/0002.amm'),265))

    def test_directional_labels_keep_air_variant_distinct(self):
        self.assertEqual(COMMON[2],'Forward dash')
        self.assertEqual(COMMON[21],'Air forward dash')
        self.assertIn('backward',COMMON[22].lower())

    def test_environment_bank_not_named_as_fighter_motion(self):
        result=shared_label(Path('0012_BBSNW.AMB/0005.amm'),0)
        self.assertEqual(result['label_kind'],'bank')
        self.assertIn('Environment',result['label'])

if __name__=='__main__':unittest.main()
