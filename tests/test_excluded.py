"""Focused parser regression controls; no native acceptance claim."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
from autorouter import pipeline as p

class ExclusionReportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'report.json'
        self.shape={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0',
                    'source':'board.kicad_pcb','included_severities':['error','warning','exclusion'],
                    'ignored_checks':[],'violations':[],'unconnected_items':[],'schematic_parity':[]}

    def parse(self, finding, collection='violations', parser=p.parse_report):
        data=copy.deepcopy(self.shape)
        data[collection]=[finding]
        self.path.write_text(json.dumps(data))
        return parser(self.path,'board.kicad_pcb')

    def test_excluded_warning_regression_across_all_collections(self):
        for collection in ('violations','unconnected_items','schematic_parity'):
            with self.subTest(collection=collection):
                finding={'severity':'warning','type':'lib_footprint_mismatch','items':[],'excluded':True}
                candidate=self.parse(finding,collection)
                self.assertEqual(candidate['exclusions'],1)
                self.assertEqual(candidate['warnings'],1)
                self.assertEqual(candidate['findings'],[finding])
                self.assertFalse(candidate['opens']==candidate['blocking']==candidate['exclusions']==0)

    def test_missing_and_false_flags_keep_unexcluded_native_behavior(self):
        for flag in ('absent',False):
            finding={'severity':'warning','type':'lib_footprint_mismatch','items':[]}
            if flag!='absent':finding['excluded']=flag
            got=self.parse(finding)
            self.assertEqual((got['opens'],got['blocking'],got['warnings'],got['exclusions']),(0,0,1,0))

    def test_present_non_boolean_flags_fail_closed(self):
        for flag in (None,0,1,'false','true',[],{}):
            with self.subTest(flag=flag):
                with self.assertRaisesRegex(p.Rejected,'exclusion flag'):
                    self.parse({'severity':'warning','type':'padstack','items':[],'excluded':flag})

    def test_legacy_exclusion_severity_is_not_double_counted(self):
        for flag in ('absent',False,True):
            finding={'severity':'exclusion','type':'padstack','items':[]}
            if flag!='absent':finding['excluded']=flag
            self.assertEqual(self.parse(finding)['exclusions'],1)

    def test_excluded_errors_remain_errors_and_exclusions(self):
        got=self.parse({'severity':'error','type':'clearance','items':[],'excluded':True})
        self.assertEqual((got['blocking'],got['exclusions'],got['warnings']),(1,1,0))

    def test_saved_native_nonexcluded_warning_keeps_identical_summary(self):
        path=ROOT/'evidence/adapter-ablation-001/combined/final-drc.json'
        data=json.loads(path.read_text())
        summary=p.parse_report(path,data['source'])
        self.assertEqual((summary['opens'],summary['blocking'],summary['warnings'],summary['exclusions']),(0,0,1,0))

if __name__=='__main__':
    unittest.main()
