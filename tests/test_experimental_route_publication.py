"""Actual route-stable/NormalPolicyReceipt software control.

Synthetic metadata and a checker seam; no Native/version/routing proof. Borrow
setup methods only, never inherit the other class's complete test population.
"""
import ast
import time
import copy
from pathlib import Path
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from autorouter import pipeline as p, floor_route as f, local_settings as ls
from tests import test_normal_local_settings_policy as normal


class LateRoutePublicationMetadata(unittest.TestCase):
    setUp = normal.NormalPolicyReceiptControls.setUp
    save_receipt = normal.NormalPolicyReceiptControls.save_receipt
    _put_prl_in_fixture = normal.NormalPolicyReceiptControls._put_prl_in_fixture

    def test_explicit_pin_validation_starts_inside_route_budget(self):
        source=Path(p.__file__)
        # The public route wrapper now owns signal lifetime; the unchanged
        # intake/publication work lives in its internal task implementation.
        route=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_route')
        # Execute only the actual intake prefix, ending before filesystem setup.
        stop=next(i for i,n in enumerate(route.body) if isinstance(n,ast.ImportFrom) and n.module=='local_settings')
        clock={'now':10.0}
        def intake(*args):clock['now']=41.0;return {'controlled_intake':True}
        namespace=dict(vars(p));namespace.update(native_toolchain=object(),experimental_schematic_parity=True,
            comparison_context=None,output=self.run,
            settings_path=None,preference_overrides=None,_preferences=None,_fanout_enabled=None,_optimizer_enabled=None,_engine_clearance_margin_nm=None,_engine_global_width_policy=None,keep_existing=False,
            adapter='none',engine_profile='standard',scoring_variant=None,guidance_policy='native',
            experimental_route_record=intake,time=SimpleNamespace(monotonic=lambda:clock['now'],process_time=lambda:clock['now']))
        wrapper=ast.FunctionDef(name='_intake_control',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),
            body=route.body[:stop]+ast.parse('return operation_started,operation_cpu').body,decorator_list=[])
        module=ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[]))
        with patch.object(f,'child_cpu',return_value=0):
            exec(compile(module,str(source),'exec'),namespace)
            started,parent=namespace['_intake_control']()
        self.assertEqual(started,10.0)
        self.assertEqual(parent,10.0)
        self.assertEqual(clock['now'],41.0)

    def test_actual_route_publication_rechecks_restored_prl_flags_after_reader(self):
        self._put_prl_in_fixture()
        source = Path(p.__file__)
        route = next(n for n in ast.parse(source.read_text()).body
                     if isinstance(n, ast.FunctionDef) and n.name == '_route')
        stable = next(n for n in ast.walk(route)
                      if isinstance(n, ast.FunctionDef) and n.name == 'stable')
        target = self.run / 'final-drc-input' / self.source.with_suffix('.kicad_prl').name
        raw = target.read_bytes()
        real_stat, real_policy = Path.stat, ls.check_normal_policy
        flag = getattr(stat, 'UF_IMMUTABLE', 2)
        tools = copy.deepcopy(self.data['tools'])
        args = {'expected_version': '10.0.7'}
        for name in ('cli', 'python', 'pcbnew'):
            path = self.root / ('never-executed-' + name)
            path.write_text('owned synthetic tool; never executed')
            args[name] = path
            args[name + '_sha256'] = p.sha(path)
        nt = p.ExperimentalNativeToolchain(**args)
        for fault in (False, True):
            with self.subTest(late_nonzero_flag=fault):
                record = copy.deepcopy(self.data)
                state = {'after_reader': False, 'flags': 0, 'policy_calls': 0}

                def observed(path, *args, **kwargs):
                    info = real_stat(path, *args, **kwargs)
                    if path == target:
                        values = {name: getattr(info, name) for name in dir(info)
                                  if name.startswith('st_')}
                        values['st_flags'] = state['flags']
                        return SimpleNamespace(**values)
                    return info

                def manifest(*, native_toolchain=None):
                    if fault and state['after_reader']:
                        state['flags'] = flag  # Expected retained/restored flags are ZERO.
                    return tools

                def policy(directory, data, *, native_toolchain=None):
                    # This fixture is deliberately 1000 synthetic data. Its real
                    # normal reader proves the PRL metadata. Explicit-version
                    # dispatch is a separate existing control population.
                    state['policy_calls'] += 1
                    return real_policy(directory, data)

                def reader(path):
                    real_policy(self.run, record)
                    state['after_reader'] = True
                    return {'current': True, 'synthetic_only': True}

                namespace = dict(vars(p))
                namespace.update(report=record, output=self.run,
                    source=self.source, before=self.data['source_hashes'],
                    completed=f.evidence_inventory(self.run),
                    evidence_inventory=f.evidence_inventory,
                    native_toolchain=nt, comparison_context=None, _preferences=None, _fanout_enabled=None, engine_profile='standard',class_requirement=None,
                    preferences_fresh=lambda *_: None,
                    tool_manifest=manifest, check_normal_policy=policy)
                exec(compile(ast.Module(body=[stable], type_ignores=[]),
                             str(source), 'exec'), namespace)
                with patch.object(Path, 'stat', observed), \
                        patch.object(ls.stat, 'UF_IMMUTABLE', flag, create=True), \
                        patch.object(ls, 'check_normal_policy', policy), \
                        patch.object(p, 'tool_manifest', manifest):
                    f.publish(self.run, record, namespace['stable'], lambda: None,
                              lambda: 30, result_checker=reader,
                              final_check=namespace['stable'])
                self.assertEqual(target.read_bytes(), raw)
                if fault:
                    self.assertFalse(record['accepted'])
                    self.assertEqual(record['status'], 'invalidated')
                    self.assertGreater(state['policy_calls'], 0)
                else:
                    self.assertTrue(record['accepted'])


if __name__ == '__main__':
    unittest.main()
