"""Replay actual retained native summary serialization without native execution."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import driver as new
ACTUAL=HERE.parent/'board-floor-geometry-001'
OLD=ACTUAL/'code/driver.py'
# Load only the exact old publication function from the executed source. This
# avoids import-time path/module ambiguity and never invokes its native entry.
import ast
syntax=ast.parse(OLD.read_text());node=next(n for n in syntax.body if isinstance(n,ast.FunctionDef) and n.name=='publish')
namespace=dict(p=new.p,json=json,uuid=new.uuid)
exec(compile(ast.Module(body=[node],type_ignores=[]),str(OLD),'exec'),namespace)
old_publish=namespace['publish']

class ActualRegression(unittest.TestCase):
    def record(self):
        candidates=list(ACTUAL.glob('invalidated-*-summary.json'));self.assertEqual(len(candidates),1)
        record=json.loads(candidates[0].read_text());self.assertTrue(record['controls_passed']);self.assertTrue(all(r['passed'] for r in record['cases']))
        base=new.sx.read(HERE/'fixture/fixture.kicad_pcb')
        for row in record['cases']:
            _,expected=new.f.candidate(base,row['case'])
            self.assertEqual(json.loads(json.dumps(expected)),row['expected']);row['expected']=expected
        self.assertTrue(any(isinstance(row['expected'],tuple) for row in record['cases']))
        return record
    def test_actual001_failure_reproduced_by_executed_publish(self):
        record=self.record()
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            out=Path(td);old_publish(out,record,lambda:None,lambda:None)
            stored=json.loads((out/'summary.json').read_text());self.assertFalse(stored['controls_passed']);self.assertEqual(stored['error'],'Rejected: summary changed')
            self.assertEqual(len(list(out.glob('invalidated-*-summary.json'))),1)
    def test_actual001_record_publishes_without_false_difference(self):
        record=self.record()
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            out=Path(td);new.publish(out,record,lambda:None,lambda:None)
            stored=json.loads((out/'summary.json').read_text());self.assertTrue(stored['controls_passed']);self.assertEqual(stored['status'],'completed')
            self.assertEqual(new.canonical_json(stored),new.canonical_json(record));self.assertFalse(list(out.glob('invalidated-*')))
    def test_actual_receipt_still_rejects_semantic_postwrite_tamper(self):
        record=self.record();original=new.p.save_json
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            out=Path(td);called=[False]
            def save(path,data):
                original(path,data)
                if not called[0]:
                    called[0]=True;corrupt=json.loads(Path(path).read_text());corrupt['cases'][1]['targeted_native_findings'][0]['type']='wrong';Path(path).write_text(json.dumps(corrupt))
            with patch.object(new.p,'save_json',save):new.publish(out,record,lambda:None,lambda:None)
            self.assertFalse(json.loads((out/'summary.json').read_text())['controls_passed']);self.assertIn('summary changed',record['error'])
    def test_expected_snapshot_precedes_mutating_writer(self):
        record={'controls_passed':True,'within_budget':True,'cases':[('width',['target'])]};original=new.p.save_json
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            out=Path(td);called=[False]
            def save(path,data):
                if not called[0]:called[0]=True;data['cases'][0]=('unapproved',['target'])
                original(path,data)
            with patch.object(new.p,'save_json',save):new.publish(out,record,lambda:None,lambda:None)
            self.assertFalse(json.loads((out/'summary.json').read_text())['controls_passed'])
    def test_boolean_integer_tamper_not_hidden_by_python_equality(self):
        self.assertNotEqual(new.canonical_json({'passed':True}),new.canonical_json({'passed':1}))
    def test_nonfinite_json_rejected(self):
        for value in (float('nan'),float('inf')):
            with self.assertRaises(ValueError):new.canonical_json({'x':value})
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path=Path(td)/'input.json';path.write_text('{"x":NaN}')
            with self.assertRaises(new.p.Rejected):new.read_json_strict(path)
    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            path=Path(td)/'input.json';path.write_text('{"passed":false,"passed":true}')
            with self.assertRaises(new.p.Rejected):new.read_json_strict(path)
    def test_canonical_order_and_array_roundtrip(self):
        self.assertEqual(new.canonical_json({'b':('x',[1]),'a':0.5}),new.canonical_json({'a':0.5,'b':['x',[1]]}))

if __name__=='__main__':unittest.main(verbosity=2)
