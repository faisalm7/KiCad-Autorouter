"""Exact-body HFE raw-capture cancellation controls; no project imports or Native.

Run with HFE_CONTROLLER pointing to the untouched001 or corrected reviewed script.
The first two methods predict before failures and after passes; not executed here.
"""
import ast
import collections
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

ROOT=next(parent for parent in Path(__file__).resolve().parents if (parent/'autorouter/pipeline.py').is_file())
CONTROLLER=Path(os.environ.get('HFE_CONTROLLER',str(ROOT/'experiments/hfe_original_native_v1/driver.py')))


class HfeRawCaptureCancellation(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temporary.cleanup)
        self.directory=Path(self.temporary.name)
        self.report=self.directory/'original-final.json'
        self.report.write_text(json.dumps(dict(kicad_version='10.0.7',source='owned.kicad_pcb',
            violations=[],unconnected_items=[],schematic_parity=[],ignored_checks=[],included_severities=['error','warning','exclusion'])))
        self.tree=ast.parse(CONTROLLER.read_text())
        worker=next(node for node in self.tree.body if isinstance(node,ast.FunctionDef) and node.name=='worker')
        self.worker=worker
        raw_stage=next(node for node in self.tree.body if isinstance(node,ast.FunctionDef) and node.name=='raw_stage')
        self.namespace=dict(hashlib=hashlib,collections=collections,
            io=SimpleNamespace(read_bytes=lambda path,limit:path.read_bytes()),
            f=SimpleNamespace(read_json=lambda path:json.loads(path.read_text())),
            p=SimpleNamespace(sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest(),Rejected=ValueError))
        exec(compile(ast.Module(body=[raw_stage],type_ignores=[]),str(CONTROLLER),'exec'),self.namespace)
        self.job=SimpleNamespace(out=self.directory)

    def test_raw_stage_propagates_actual_keyboard_interrupt(self):
        def interrupted(*_):raise KeyboardInterrupt('owned cancellation')
        self.namespace['io'].read_bytes=interrupted
        with self.assertRaises(KeyboardInterrupt):self.namespace['raw_stage'](self.job,'original-final')

    def test_actual_post_stage_capture_records_cancelled_before_publication(self):
        def interrupted(*_):raise KeyboardInterrupt('owned cancellation')
        self.namespace['io'].read_bytes=interrupted
        # Execute the exact worker statements after its main diagnostic try and
        # before material capture/publication, not a rewritten cancellation model.
        start=next(i for i,node in enumerate(self.worker.body)
            if isinstance(node,ast.Assign) and any(isinstance(target,ast.Subscript)
                and isinstance(target.value,ast.Name) and target.value.id=='record'
                and isinstance(target.slice,ast.Constant) and target.slice.value=='raw_reports' for target in node.targets))
        stop=next(i for i,node in enumerate(self.worker.body) if isinstance(node,ast.Assign)
            and any(isinstance(target,ast.Name) and target.id=='completed' for target in node.targets)
            and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='material')
        record=dict(passed=True,status='completed',observation_complete=True)
        self.namespace.update(record=record,job=self.job,stages=[('original-final',)])
        exec(compile(ast.Module(body=self.worker.body[start:stop],type_ignores=[]),str(CONTROLLER),'exec'),self.namespace)
        self.assertIs(record['passed'],False)
        self.assertEqual(record['status'],'cancelled')
        self.assertTrue(record['observation_complete'])
        self.assertEqual(record['raw_reports'],{})
        self.assertIn('KeyboardInterrupt',record['error'])

    def test_ordinary_raw_read_failure_stays_unqualified_error(self):
        def failed(*_):raise OSError('owned read failure')
        self.namespace['io'].read_bytes=failed
        observed=self.namespace['raw_stage'](self.job,'original-final')
        self.assertIs(observed['qualified'],False)
        self.assertIn('OSError: owned read failure',observed['raw_capture_error'])
        self.assertIsNone(observed['raw_population'])

    def test_valid_raw_report_is_diagnostic_only(self):
        observed=self.namespace['raw_stage'](self.job,'original-final')
        self.assertIs(observed['qualified'],False)
        self.assertEqual(observed['raw_population'],dict(violations=0,unconnected_items=0,schematic_parity=0))
        self.assertEqual(observed['report_sha256'],hashlib.sha256(self.report.read_bytes()).hexdigest())
        self.assertNotIn('raw_capture_error',observed)


if __name__=='__main__':unittest.main(verbosity=2)
