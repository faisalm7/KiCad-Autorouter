"""Unexecuted exact writer-tail controls; synthetic workers, no Native proof.

Run with --before to substitute verbatim original writer tails. Five negative
controls should fail before correction; all seven should pass after. No real
worker or Native/engine/test controller is launched by this scaffold.
"""
import ast
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import sys
DRAFT = Path(__file__).resolve().parent
sys.path.insert(0,str(DRAFT.parents[1]))
from autorouter import pipeline as p, floor_route as f, handoff as h
from scripts import install_smoke as install
PROJECT = Path(p.__file__).resolve().parents[1]
SOURCE_MODE = 'after'
GROUPS = {'real_installed_context', 'actual_commands_and_selected_tests',
          'installed_targeted_current_changes', 'complete_source_and_installed_inventory',
          'installed_actual_native_smoke_and_current_readback',
          'outer_costs_and_publication', 'late_complete_material_and_source'}


def tail(kind):
    name = ('run-installation040-reader.py' if kind == 'reader'
            else 'run-installation040-targeted-future.py')
    if SOURCE_MODE == 'before':
        name = ('run-installation040-reader.py' if kind == 'reader'
                else 'run-installation040-targeted-001.py')
    path = (DRAFT / 'before' / name) if SOURCE_MODE == 'before' else DRAFT / name
    tree = ast.parse(path.read_text())
    marker = ('stable' if SOURCE_MODE == 'before' else 'checks_path') if kind == 'reader' else (
        'population' if SOURCE_MODE == 'before' else 'population_path')
    start = next(i for i, node in enumerate(tree.body)
                 if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == marker
                         for target in node.targets))
    return path, compile(ast.Module(body=tree.body[start:], type_ignores=[]), str(path), 'exec')


class OuterPublicationControls(unittest.TestCase):
    def exercise(self, kind, fault):
        scratch = PROJECT / '.cache' / 'installation040-publication-controls'
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            root = Path(directory).resolve(); out = root / 'out'; out.mkdir()
            installed = root / 'installed'; installed.mkdir()
            source_file = root / 'source.txt'; source_file.write_text('owned immutable input')
            (installed / source_file.name).write_bytes(source_file.read_bytes())
            # Full source witness includes a file outside the shortlist PINSET.
            other = root / 'other-owned.txt'; other.write_text('owned additional tracked input')
            (installed / other.name).write_bytes(other.read_bytes())
            names = ['source.txt','other-owned.txt','autorouter/pipeline.py',
                     'scripts/install_smoke.py','LICENSE','toolchain.lock.json']
            for name in names[2:]:
                for folder in (root,installed):
                    path=folder/name;path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_text('owned inert source witness; never imported')
            listing=''.join(name+'\0' for name in names)
            head='a'*40;branch='rebuild/source-controls'
            for folder in (root,installed):
                git=folder/'.git';git.mkdir();(git/'index').write_bytes(b'owned fake index; never used by Git')
                if folder==root:
                    (git/'HEAD').write_text('ref: refs/heads/'+branch+'\n')
                    ref=git/'refs/heads'/branch;ref.parent.mkdir(parents=True);ref.write_text(head+'\n')
                else:(git/'HEAD').write_text(head+'\n')
            baseline=root/'.runs/installation-040';baseline.mkdir(parents=True)
            (baseline/'03-source-files.log').write_text(listing)
            (baseline/'source-tracked.json').write_text(json.dumps(install.tracked_inventory(root,listing)))
            retained=dict(source_inventory_sha256=p.sha(baseline/'source-tracked.json'),
                source_branch=branch,git_head=head,git_identity_witnesses={
                    str(root):install.git_identity(root,head,branch),
                    str(installed):install.git_identity(installed,head)})
            (baseline/'result.json').write_text(json.dumps(retained))
            source_path, code = tail(kind)
            controller = root / 'controller.py'; controller.write_bytes(source_path.read_bytes())
            reader = out / 'audit.py'; reader.write_text('# owned synthetic reader')
            old = root / '.runs/current-installation039-review-001/audit.py'
            old.parent.mkdir(parents=True); old.write_text('# pinned historical reader')
            process = dict(status='success', exit_code=0, cleanup_complete=True,
                           log_truncated=False, argv=['synthetic worker; never executed'])
            tools = {'git_head': 'a' * 40}
            clock = {'wall': 1.0, 'cpu': 1.0, 'fired': False}
            plan = dict(tools=tools, git_head=tools['git_head'], target_modules=['tests.owned'],
                source_sha256={'source.txt': p.sha(source_file)}, controller_sha256={},
                new_shipped_modules=[], expected_target_method_count=46, scope='synthetic software only',
                limits={'publication_allowance_seconds': 2, 'targeted_whole_wall_full_cpu_seconds': 92})
            protocol = root / 'protocol.json'; protocol.write_text(json.dumps(plan))
            receipt = root / 'installation.json'; receipt.write_text('{}')
            inputs = out / 'input-pins.json'
            pins = {'kind': 'installation040-reader-inputs-v1',
                    'files_sha256': {'source.txt': p.sha(source_file)}}
            inputs.write_text(json.dumps(pins))
            checks = {'passed': True, 'checks': {key: {'passed': True} for key in GROUPS},
                      'failures': []}
            (out / 'checks.json').write_text(json.dumps(checks))
            population = dict(successful=True, modules=plan['target_modules'], skipped=0,
                              planned=46, ran=46, shipped_modules={})
            (out / 'population.json').write_text(json.dumps(population))
            (out / 'command.log').write_text('synthetic reader; no process launched')
            (out / 'tests.log').write_text('synthetic population; no tests launched')
            ntplan = root / '.runs/installation040-native-preparation-001/protocol.json'
            ntplan.parent.mkdir(parents=True)
            native_output = installed / '.runs/owned/native'
            (native_output / 'route').mkdir(parents=True)
            (native_output / 'route/result.json').write_text('{}')
            ntplan.write_text(json.dumps({'native_toolchain': {}, 'native_output': str(native_output)}))
            real_save = p.save_json

            def emit(path, row):
                real_save(path, row)
                if Path(path).name in {'execution.json', 'result.json'} and row.get('passed') is True and not clock['fired']:
                    clock['fired'] = True
                    if fault == 'material': source_file.write_text('late changed input')
                    elif fault == 'whole_material': other.write_text('late changed full-source input')
                    elif fault == 'slow': clock.update(wall=100.0, cpu=100.0)

            namespace = dict(Path=Path, json=json, p=p, f=f, h=h, install=install, ROOT=root, out=out,
                installed=installed, __file__=str(controller), process=process, START=0.0,
                CPU0=0.0, time=SimpleNamespace(monotonic=lambda: clock['wall']),
                cpu=lambda: clock['cpu'], inputs=inputs, inputs_pin=p.sha(inputs), pins=pins,
                plan=plan, tools=tools, protocol=protocol, pin=p.sha(protocol),
                receipt_path=receipt, receipt_pin=p.sha(receipt), complete_current=lambda: True)
            # The final installed shared metadata helper is a separate boundary
            # already covered by real context tests. This control isolates only
            # publication timing/material behavior; it creates no Native proof.
            with patch.object(p, 'save_json', emit), \
                    patch.object(p, 'tool_manifest', return_value=tools), \
                    patch.object(p.ExperimentalNativeToolchain, 'from_record', return_value=object()), \
                    patch.object(p, 'check_experimental_local_settings', return_value=None), \
                    redirect_stdout(io.StringIO()):
                try:
                    exec(code, namespace)
                except SystemExit as exc:
                    status = exc.code
                else:
                    self.fail('actual writer tail did not return its exit status')
            result_path = out / ('execution.json' if SOURCE_MODE == 'before' else 'result.json')
            result = f.read_json(result_path)
            if fault is None:
                self.assertTrue(result['passed']); self.assertEqual(status, 0)
            else:
                self.assertFalse(result['passed']); self.assertEqual(status, 2)
                self.assertEqual(result['status'], 'invalidated')
                self.assertFalse(result['source_current'])
                if fault == 'slow': self.assertFalse(result['whole_delivery_within_budget'])

    def test_reader_positive(self): self.exercise('reader', None)
    def test_reader_late_material(self): self.exercise('reader', 'material')
    def test_reader_slow_publication(self): self.exercise('reader', 'slow')
    def test_reader_late_complete_source_outside_shortlist(self): self.exercise('reader', 'whole_material')
    def test_targeted_positive(self): self.exercise('targeted', None)
    def test_targeted_late_material(self): self.exercise('targeted', 'material')
    def test_targeted_slow_publication(self): self.exercise('targeted', 'slow')


if __name__ == '__main__':
    import sys
    if '--before' in sys.argv:
        SOURCE_MODE = 'before'; sys.argv.remove('--before')
    unittest.main(verbosity=2)
