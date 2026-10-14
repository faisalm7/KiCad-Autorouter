"""Regress the demonstrated pre-witness controller journal-rebinding defect.

Executes the controller's exact final bound closure with real process/raw-file
guards and explicitly synthetic DRC/geometry/DSN semantics. No native execution,
routing correctness, board-family admission or .runs preparation is involved.
"""
import ast
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from autorouter import config as c, floor_route as f, netclass as n
from autorouter import pipeline as p, placement_clearance as io, sexpr as sx


def authored_map():
    """Stable authored parent scalars; no claimed native observation."""
    classes = [
        {'name': 'Default', 'priority': 2147483647, 'track_width': .4},
        {'name': 'POWER', 'priority': 1, 'track_width': .6},
        {'name': 'SIGNAL', 'priority': 0, 'track_width': .5},
    ]
    for cls in classes:
        cls.update(clearance=.35, via_diameter=1.5, via_drill=.6)
    project = {
        'net_settings': {'classes': classes, 'netclass_assignments': None,
                         'netclass_patterns': [{'pattern': '/PWR_*', 'netclass': 'POWER'}]},
        'board': {'design_settings': {'rules': {
            'min_track_width': .3, 'min_clearance': .2,
            'min_via_diameter': 1., 'min_through_hole_diameter': .5}}},
    }
    rows = []
    for code, cls in enumerate(classes[:2], 1):
        row = {'name': '/NET_' + str(code), 'netcode': code, 'copper_pad_count': 1,
               'class': cls['name'] if cls['name'] == 'Default' else cls['name'] + ',Default'}
        row['parameter_parents'] = {}
        for key, source_key, _ in n._DIMENSIONS:
            value = int(cls[source_key] * 1000000)
            row[key] = value
            row['parameter_parents'][key] = {'name': cls['name'], 'value_nm': value,
                                            'specified': True, 'priority': cls['priority']}
        rows.append(row)
    native = {'schema': 1, 'native_version': '10.0.0', 'units': 'integer nanometres', 'nets': rows}
    return project, native


class FinalTransportBinding(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='netclass-binding-')
        self.addCleanup(self.temp.cleanup)
        # macOS /var aliases are resolved before bounded file guards see them.
        self.out = Path(self.temp.name).resolve(strict=True)
        self.case = self.out / 'completed-case'
        self.jobdir = self.case / 'job'
        self.jobdir.mkdir(parents=True)
        self.candidate = self.case / 'candidate/fixture.kicad_pcb'
        self.candidate.parent.mkdir()
        self.candidate.write_text('(kicad_pcb)\n')
        original = self.case / 'original'
        original.mkdir()
        self.source = original / self.candidate.name
        self.source.write_bytes(self.candidate.read_bytes())
        project, native = authored_map()
        self.source.with_suffix('.kicad_pro').write_text(json.dumps(project))
        (self.jobdir / 'native.dsn').write_bytes(b'(pcb synthetic)\n')
        (self.jobdir / 'task.dsn').write_bytes(b'(pcb synthetic)\n')
        (self.jobdir / 'imported.kicad_pcb').write_bytes(self.candidate.read_bytes())
        (self.jobdir / 'refill').mkdir()
        (self.jobdir / 'refill' / self.candidate.name).write_bytes(self.candidate.read_bytes())
        self.engine_argv = ['synthetic-engine', 'task.dsn', 'routes.ses']
        self.steps = []
        for name, action, board, target, args in [
            ('export', 'export', self.source, self.jobdir / 'native.dsn', [self.jobdir / 'native-netclasses.json']),
            ('import', 'import', self.source, self.jobdir / 'imported.kicad_pcb', [self.jobdir / 'routes.ses']),
            ('final-netclasses', 'netclasses', self.candidate, self.jobdir / 'final-netclasses.json', []),
        ]:
            argv = [*f.SANDBOX, str(c.PYTHON), str(ROOT / 'autorouter/native.py'),
                    action, str(board), str(target), *[str(x) for x in args]]
            self.steps.append({'name': name, 'argv': argv, 'cwd': str(self.jobdir),
                               'exit_code': 0, 'status': 'success', 'cleanup_complete': True})
        self.steps.append({'name': 'engine', 'argv': self.engine_argv, 'cwd': str(self.jobdir),
                           'exit_code': 0, 'status': 'success', 'cleanup_complete': True})
        job = SimpleNamespace(out=self.jobdir, steps=copy.deepcopy(self.steps))
        self.row = {'case': 'completed-case', 'final_candidate': str(self.candidate),
                    'geometry': {'passed': True}, 'route_dimensions': {'passed': True},
                    'dsn_audit': {'passed': True}, 'engine_settings': {'argv': ['synthetic-settings']},
                    'protected_import': {'preserved': True}}

        def synthetic_transplant(original, imported, **kwargs):
            kwargs['audit'].update(preserved=True)
            return ['kicad_pcb']

        namespace = {
            'checks': [(job, 'final-drc', self.candidate, {}, False, {'passed': True})],
            'native_binding': lambda *a, **k: {'passed': True},
            'record': {'cases': [self.row]}, 'out': self.out, 'Path': Path,
            'f': f, 'c': c, 'ROOT': ROOT, 'io': io, 'sx': sx, 'jobs': [job],
            'sources': {'completed-case': {}},
            'p': SimpleNamespace(Rejected=p.Rejected, routes=lambda _: [], tree_hash=lambda _: {},
                                 audit_route_dimensions=lambda *a: self.row['route_dimensions'],
                                 engine_argv=lambda *a: self.engine_argv,
                                 transplant_routes=synthetic_transplant,
                                 transplant_fill=lambda rebuilt, refill: rebuilt),
            'geometry': lambda *a: self.row['geometry'], 'observed': lambda *a: native,
            'n': SimpleNamespace(audit_native=n.audit_native,
                                 audit_dsn=lambda *a, **k: self.row['dsn_audit']),
        }
        path = ROOT / 'experiments/netclass_parent_transport_v1/driver.py'
        module = ast.parse(path.read_bytes())
        experiment = next(x for x in module.body if isinstance(x, ast.FunctionDef) and x.name == 'experiment')
        bound = next(x for x in experiment.body if isinstance(x, ast.FunctionDef) and x.name == 'bound')
        exec(compile(ast.Module(body=[bound], type_ignores=[]), str(path), 'exec'), namespace)
        self.bound = namespace['bound']
        self.run_guard = mock.patch.object(subprocess, 'run', side_effect=AssertionError('No subprocess permitted'))
        self.popen_guard = mock.patch.object(subprocess, 'Popen', side_effect=AssertionError('No subprocess permitted'))
        self.run_guard.start()
        self.popen_guard.start()
        self.addCleanup(self.run_guard.stop)
        self.addCleanup(self.popen_guard.stop)
        self.reset()

    def reset(self):
        for step in self.steps:
            (self.jobdir / (step['name'] + '-process.json')).write_text(json.dumps(step))
        (self.jobdir / 'native.dsn').write_bytes((self.jobdir / 'task.dsn').read_bytes())
        self.candidate.write_text('(kicad_pcb)\n')
        self.row['protected_import'] = {'preserved': True}

    def test_controlling_positive_then_seven_late_drift_controls(self):
        self.bound()
        mutations = [
            ('engine_argv', 'engine', 'argv', ['unexpected'], 'floor process provenance differs: engine'),
            ('export_argv', 'export', 'argv', ['unexpected'], 'floor process provenance differs: export'),
            ('import_cwd', 'import', 'cwd', '/unexpected', 'floor process provenance differs: import'),
            ('final_map_status', 'final-netclasses', 'status', 'crash', 'floor process provenance differs: final-netclasses'),
            ('raw_dsn_drift', None, None, None, 'exact unmodified native DSN transport changed'),
            ('candidate_drift', None, None, None, 'final candidate differs from actual retained native import/refill'),
            ('protected_receipt_drift', None, None, None, 'final candidate differs from actual retained native import/refill'),
        ]
        for name, stage, key, value, reason in mutations:
            with self.subTest(control=name):
                self.reset()
                if stage:
                    path = self.jobdir / (stage + '-process.json')
                    process = json.loads(path.read_text())
                    process[key] = value
                    path.write_text(json.dumps(process))
                elif name == 'raw_dsn_drift':
                    (self.jobdir / 'native.dsn').write_bytes(b'(pcb changed)\n')
                elif name == 'candidate_drift':
                    self.candidate.write_text('(kicad_pcb (review_tamper))\n')
                else:
                    self.row['protected_import'] = {'preserved': False}
                with self.assertRaises(p.Rejected) as caught:
                    self.bound()
                self.assertEqual(str(caught.exception), reason)
        self.reset()
        self.bound()


if __name__ == '__main__':
    unittest.main()
