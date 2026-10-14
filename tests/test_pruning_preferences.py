"""Preset constraint, provenance and freshness falsifiers; native proof is separate."""
import copy, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import strategy as s, preferences as pref, pipeline as p


class PruningPreferences(unittest.TestCase):
    def setUp(self):
        cache=Path(__file__).resolve().parents[1]/'.cache';cache.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=cache);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.preset=self.root/'settings.json'
        self.config=dict(pref.DEFAULTS);self.config.update(adapter='both',profile='tuned',seconds=65,scoring_preference='via_high')

    def capture(self,config=None):
        self.preset.write_text(json.dumps(self.config if config is None else config))
        return pref.load(self.preset)

    def receipt(self):
        captured=self.capture();raw=pref.snapshot(captured,{'seconds':70})
        path=self.root/'pruning-preferences.json';path.write_bytes(raw)
        code=self.root/'code/strategy.py';code.parent.mkdir();code.write_bytes(b'PRUNING_PREFERENCES_POLICY = "native-pruning-preferences-v1"\n')
        effective=pref.readback(raw)
        data=dict(pruning_preferences_policy=s.PRUNING_PREFERENCES_POLICY,
            pruning_preferences=dict(file=path.name,sha256=p.sha(path),effective=effective),
            tools={'implementation_sha256':{'autorouter/strategy.py':p.sha(code)}},
            scope='whole_board_unlocked_routing',adapter='both',engine_profile='tuned',
            budget_seconds=70,cpu_budget_seconds=70,incumbent_scoring_variant='via_high')
        return captured,data

    def test_explicit_override_preserves_other_captured_choices(self):
        captured=self.capture();captured.parsed['seconds']=900
        resolved=s.pruning_preferences(captured,{'seconds':70})
        self.assertEqual(resolved['seconds'],70);self.assertEqual(resolved['scoring_preference'],'via_high')
        self.assertEqual(s.pruning_preferences(captured)['seconds'],65)

    def test_unsupported_presets_stop_before_output_or_worker(self):
        changes=[{'scope':'partial_completion'},{'scope':'selected_nets','nets':['GND'],'profile':'completion-only'},
                 {'adapter':'none'},{'profile':'standard'},
                 {'guidance':'board-floors-v1','scoring_preference':None},
                 {'layers':['F.Cu'],'profile':'completion-only'}, {'seconds':29}]
        for change in changes:
            config={**self.config,**change};self.capture(config);out=self.root/'uncreated'
            with self.subTest(change=change),patch.object(p,'Job',side_effect=AssertionError('worker must not start')):
                with self.assertRaises((p.Rejected,pref.PreferenceError)):
                    s.prune(self.root/'absent.kicad_pcb',out,settings_path=self.preset)
            self.assertFalse(out.exists())

    def test_mixed_legacy_and_captured_arguments_reject_before_output(self):
        self.capture()
        for args in ({'seconds':61},{'incumbent_scoring':'via_low'}):
            with self.subTest(args=args),self.assertRaisesRegex(p.Rejected,'mixed arguments'):
                s.prune(self.root/'absent',self.root/'uncreated',settings_path=self.preset,**args)
            self.assertFalse((self.root/'uncreated').exists())

    def test_snapshot_is_authoritative_and_external_edits_are_stale_during_run(self):
        captured,data=self.receipt();self.assertEqual(s.check_pruning_preferences(self.root,data)['seconds'],70)
        self.preset.write_text(json.dumps({**self.config,'seconds':80}))
        with self.assertRaisesRegex(pref.PreferenceError,'changed'):pref.check_fresh(captured)
        self.assertEqual(s.check_pruning_preferences(self.root,data)['seconds'],70)

    def test_policy_binding_inline_choice_and_root_budget_changes_reject(self):
        _,data=self.receipt()
        for mutation in ('missing-binding','missing-policy','inline-scoring','root-scoring','wall','cpu'):
            changed=copy.deepcopy(data)
            if mutation=='missing-binding':del changed['pruning_preferences']
            elif mutation=='missing-policy':del changed['pruning_preferences_policy']
            elif mutation=='inline-scoring':changed['pruning_preferences']['effective']['scoring_preference']='via_low'
            elif mutation=='root-scoring':changed['incumbent_scoring_variant']='via_low'
            elif mutation=='wall':changed['budget_seconds']=80
            else:changed['cpu_budget_seconds']=80
            with self.subTest(mutation=mutation),self.assertRaises((p.Rejected,pref.PreferenceError)):
                s.check_pruning_preferences(self.root,changed)

    def test_removing_all_marker_fields_cannot_downgrade_new_captured_code(self):
        _,data=self.receipt();(self.root/'pruning-preferences.json').unlink()
        del data['pruning_preferences'];del data['pruning_preferences_policy']
        with self.assertRaisesRegex(p.Rejected,'binding'):s.check_pruning_preferences(self.root,data)

    def test_changed_snapshot_symlink_and_code_digest_reject(self):
        _,data=self.receipt();path=self.root/'pruning-preferences.json';raw=path.read_bytes()
        path.write_bytes(raw+b' ')
        with self.assertRaisesRegex(p.Rejected,'snapshot changed'):s.check_pruning_preferences(self.root,data)
        target=self.root/'aliased';target.write_bytes(raw);path.unlink();path.symlink_to(target)
        with self.assertRaises(p.Rejected):s.check_pruning_preferences(self.root,data)
        path.unlink();path.write_bytes(raw);(self.root/'code/strategy.py').write_bytes(b'changed')
        with self.assertRaisesRegex(p.Rejected,'implementation changed'):s.check_pruning_preferences(self.root,data)

    def test_legacy_code_keeps_its_actual_missing_preferences_evidence(self):
        code=self.root/'code/strategy.py';code.parent.mkdir();code.write_bytes(b'legacy native pruning implementation\n')
        data={'tools':{'implementation_sha256':{'autorouter/strategy.py':p.sha(code)}}}
        self.assertIsNone(s.check_pruning_preferences(self.root,data))


if __name__=='__main__':unittest.main()
