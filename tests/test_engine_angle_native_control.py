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

    def test_loader_job_uses_fresh_output_and_actual_retained_dsn_bytes(self):
        # Real shared constructor/filesystem; only JVM execution is mocked.
        # This reproduces the former folder.mkdir/BoundJob.mkdir collision.
        from tests.test_engine_angle import RAW
        from autorouter import engine_angle as angle
        import json
        out=self.scratch();route=out/'retained-route';route.mkdir()
        (route/'task.dsn').write_bytes(RAW);angle.prepare(route)
        before=p.tree_hash(route);calls=[]
        def step(job,name,argv,allowed=(0,)):
            calls.append(name);path=Path(argv[-2]);expected=argv[-1]
            text='loaded mode differs: FORTYFIVE_DEGREE' if allowed==(1,) else json.dumps(dict(input_sha256=p.sha(path),loaded_angle='NONE' if expected=='none' else 'FORTYFIVE_DEGREE',parse_warnings=[]))
            (job.out/(name+'.log')).write_text(text+'\n')
            return dict(name=name,status='success' if allowed==(0,) else 'nonzero_exit',exit_code=allowed[0])
        with patch.object(control,'OUT',out),patch.object(control.shared.BoundJob,'step',step):
            rows=control.loaders({},dict(candidate=str(route/'candidate/owned.kicad_pcb')),lambda:30)
        self.assertEqual(calls,['omitted45','canonicalNone','explicit45','misspelledNone'])
        self.assertEqual(len(rows),4);self.assertEqual(p.tree_hash(route),before)

    def test_owned_source_has_oblique_route_and_original_protected_keep(self):
        files=fixture.files();tree=sx.parse(files[fixture.STEM+'.kicad_pcb'].decode())
        at={next(sx.unquote(row[2]) for row in sx.children(fp,'property') if sx.unquote(row[1])=='Reference'):sx.one(fp,'at')[1:] for fp in sx.children(tree,'footprint')}
        self.assertEqual(at['J1'],['12','10']);self.assertEqual(at['J2'],['26','13'])
        self.assertEqual(len(p.routes(tree)),1)
        self.assertEqual(len(p.protected_for_record({'scope':'whole_board_unlocked_routing'},tree)),1)
        import json
        pro=json.loads(files[fixture.STEM+'.kicad_pro']);default=pro['net_settings']['classes'][0]
        self.assertEqual(default['priority'],2147483647);self.assertEqual(default['track_width'],.3)
        self.assertEqual(pro['board']['design_settings']['rules']['min_track_width'],.25)
        self.assertEqual(len(files),4);self.assertIn(fixture.STEM+'.kicad_sch',files)
