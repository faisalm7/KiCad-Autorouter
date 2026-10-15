"""Real filesystem publication regressions; no Native/engine correctness claim."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import pipeline as p,floor_route as f,sexpr as sx
from experiments.free_angle_baseline_v1 import controls as control,fixture

class FreeAngleDeliveryControls(unittest.TestCase):
    def scratch(self):
        folder=tempfile.TemporaryDirectory(dir=p.c.ROOT/'.cache');self.addCleanup(folder.cleanup);return Path(folder.name)

    def test_late_invalidation_clears_passed_and_keeps_the_failed_receipt(self):
        out=self.scratch();source=out/'owned-source';source.write_text('original')
        record=dict(status='completed',passed=True,accepted=False);save=p.save_json;changed=[]
        def write(path,data):
            save(path,data)
            if not changed:source.write_text('changed');changed.append(True)
        def stable():
            if source.read_text()!='original':raise p.Rejected('late source mutation')
        with patch.object(p,'save_json',side_effect=write):
            f.publish(out,record,stable,lambda:control.account_delivery(record,.1,.1,10),lambda:10)
        self.assertEqual(record['status'],'invalidated');self.assertFalse(record['passed'])
        self.assertFalse(f.read_json(out/'result.json')['passed'])
        self.assertTrue(list(out.glob('invalidated-result-*')))

    def test_actual_cancelled_journal_and_route_are_distinct_from_failure(self):
        out=self.scratch();journal=out/'owned-process.json'
        for status,expected in [('success',False),('nonzero_exit',False),('cancelled',True)]:
            p.save_json(journal,dict(status=status))
            self.assertEqual(control.cancelled_execution(None,out),expected)
        journal.unlink();self.assertTrue(control.cancelled_execution(dict(status='cancelled'),out))
        record=dict(status='cancelled',passed=True)
        control.account_delivery(record,181,181,-1)
        self.assertEqual(record['status'],'cancelled');self.assertFalse(record['passed'])

    def test_owned_source_has_oblique_route_and_original_protected_keep(self):
        files=fixture.files();tree=sx.parse(files[fixture.STEM+'.kicad_pcb'].decode())
        at={next(sx.unquote(row[2]) for row in sx.children(fp,'property') if sx.unquote(row[1])=='Reference'):sx.one(fp,'at')[1:] for fp in sx.children(tree,'footprint')}
        self.assertEqual(at['J1'],['12','10']);self.assertEqual(at['J2'],['26','13'])
        self.assertEqual(len(p.routes(tree)),1)
        self.assertEqual(len(p.protected_for_record({'scope':'whole_board_unlocked_routing'},tree)),1)
        self.assertEqual(len(files),4);self.assertIn(fixture.STEM+'.kicad_sch',files)
