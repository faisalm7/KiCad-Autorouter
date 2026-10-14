"""Preset CLI forwarding and exclusive starter creation; no routing execution."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import __main__ as cli, placement_strategy as placement, preferences as pref, strategy


class ImprovePreferencesCLI(unittest.TestCase):
    def setUp(self):
        parent=Path(__file__).resolve().parents[1]/'.cache'
        parent.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='improve-preferences-cli-',dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.output=self.root/'candidate'

    def invoke(self,*args):
        with patch('sys.argv',['autorouter',*args]),contextlib.redirect_stdout(io.StringIO()) as out:
            code=cli.main()
        return code,json.loads(out.getvalue())

    def improve(self,*args):
        return self.invoke('improve','board.kicad_pcb','--output',str(self.output),*args)

    def test_no_preferences_preserves_legacy_call_and_budget(self):
        for extra,seconds in [((),120),(('--seconds','90'),90)]:
            with self.subTest(extra=extra),patch.object(strategy,'prune',return_value={'accepted':False}) as native:
                self.assertEqual(self.improve(*extra)[0],2)
                native.assert_called_once_with('board.kicad_pcb',str(self.output),seconds,proposal_policy='single')

    def test_preset_omitted_seconds_is_not_an_override(self):
        with patch.object(strategy,'prune',return_value={'accepted':True}) as native:
            self.assertEqual(self.improve('--settings','preset.json')[0],0)
            native.assert_called_once_with('board.kicad_pcb',str(self.output),proposal_policy='single',
                                          settings_path='preset.json',preference_overrides={})

    def test_named_scoring_without_preset_keeps_seconds_omitted(self):
        for scoring in sorted(pref.SCORING):
            with self.subTest(scoring=scoring),patch.object(strategy,'prune',return_value={'accepted':True}) as native:
                self.assertEqual(self.improve('--scoring-preference',scoring)[0],0)
                native.assert_called_once_with('board.kicad_pcb',str(self.output),proposal_policy='single',
                                              settings_path=None,preference_overrides={'scoring_preference':scoring})

    def test_explicit_seconds_and_scoring_only_are_forwarded_as_overrides(self):
        with patch.object(strategy,'prune',return_value={'accepted':True}) as native:
            self.assertEqual(self.improve('--settings','preset.json','--seconds','90.5',
                                         '--scoring-preference','via_high','--proposal-policy','feedback')[0],0)
            native.assert_called_once_with('board.kicad_pcb',str(self.output),proposal_policy='feedback',
                                          settings_path='preset.json',
                                          preference_overrides={'seconds':90.5,'scoring_preference':'via_high'})

    def test_explicit_zero_is_left_for_backend_rejection_not_defaulted(self):
        with patch.object(strategy,'prune',side_effect=ValueError('budget rejected')) as native:
            code,result=self.improve('--settings','preset.json','--seconds','0')
            self.assertEqual(code,2);self.assertEqual(result,{'accepted':False,'error':'budget rejected'})
            self.assertEqual(native.call_args.kwargs['preference_overrides'],{'seconds':0.0})
            self.assertFalse(self.output.exists())

    def test_placement_preferences_are_rejected_before_dispatch_and_output(self):
        for args in [('--settings','missing.json'),('--scoring-preference','via_low'),
                     ('--settings','missing.json','--scoring-preference','via_default')]:
            with self.subTest(args=args),patch.object(strategy,'prune') as native,patch.object(placement,'prune') as guided:
                code,result=self.improve('--guidance','placement-search-v1',*args)
                self.assertEqual(code,2);self.assertIn('require native improvement guidance',result['error'])
                native.assert_not_called();guided.assert_not_called();self.assertFalse(self.output.exists())

    def test_placement_without_preferences_preserves_default_budget(self):
        with patch.object(placement,'prune',return_value={'accepted':False}) as guided:
            self.assertEqual(self.improve('--guidance','placement-search-v1')[0],2)
            guided.assert_called_once_with('board.kicad_pcb',str(self.output),120,allocation=placement.STANDARD_ALLOCATION)

    def test_native_allocation_still_rejects_even_with_settings(self):
        with patch.object(strategy,'prune') as native:
            code,result=self.improve('--settings','missing.json','--allocation','standard-85-v1')
            self.assertEqual(code,2);self.assertIn('--allocation requires',result['error'])
            native.assert_not_called();self.assertFalse(self.output.exists())

    def test_backend_preset_rejection_remains_visible(self):
        with patch.object(strategy,'prune',side_effect=pref.PreferenceError('improve requires whole-board scope')):
            code,result=self.improve('--settings','partial.json')
            self.assertEqual(code,2);self.assertIn('whole-board scope',result['error'])
            self.assertFalse(self.output.exists())

    def test_route_starter_is_unchanged_for_default_and_explicit_purpose(self):
        for args in [(),('--purpose','route')]:
            with self.subTest(args=args):
                target=self.root/('default.json' if not args else 'route.json')
                self.assertEqual(self.invoke('settings-init','--output',str(target),*args)[0],0)
                self.assertEqual(json.loads(target.read_text()),dict(pref.DEFAULTS))
                self.assertEqual(target.stat().st_mode&0o777,0o600)

    def test_improve_starter_uses_existing_schema_and_fixed_native_policy(self):
        target=self.root/'improve.json'
        code,result=self.invoke('settings-init','--output',str(target),'--purpose','improve')
        self.assertEqual(code,0);self.assertEqual(result['created'],str(target))
        expected=dict(pref.DEFAULTS,adapter='both',profile='tuned')
        self.assertEqual(json.loads(target.read_text()),expected)
        self.assertEqual(pref.resolve(pref.load(target)),expected)
        self.assertEqual(target.stat().st_mode&0o777,0o600)

    def test_starter_never_overwrites_existing_file(self):
        target=self.root/'existing.json';original=b'owner bytes\n';target.write_bytes(original)
        for purpose in ('route','improve'):
            with self.subTest(purpose=purpose):
                code,result=self.invoke('settings-init','--output',str(target),'--purpose',purpose)
                self.assertEqual(code,2);self.assertEqual(result['status'],'rejected')
                self.assertEqual(target.read_bytes(),original)

    def test_invalid_scoring_is_rejected_by_parser_without_dispatch(self):
        with patch.object(strategy,'prune') as native,contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as raised:
            self.improve('--scoring-preference','invented')
        self.assertEqual(raised.exception.code,2);native.assert_not_called();self.assertFalse(self.output.exists())


if __name__=='__main__':unittest.main()
