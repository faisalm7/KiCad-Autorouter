"""Real preset-file and captured-byte controls; no native/engine execution."""
import copy
from dataclasses import replace
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import preferences as pref


class PreferencesTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parents[1] / '.cache'
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='preferences-test-', dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'preset.json'

    def write(self, **changes):
        value = dict(pref.DEFAULTS)
        value.update(changes)
        self.path.write_text(json.dumps(value, indent=2) + '\n')
        return pref.load(self.path)

    def encode(self, value):
        return json.dumps(value, ensure_ascii=False).encode('utf-8')

    def test_exact_file_roundtrip_and_explicit_override_precedence(self):
        captured = self.write(seconds=90, adapter='both')
        raw = pref.snapshot(captured, {'seconds': 60.5, 'profile': 'tuned'})
        effective = pref.resolve(captured, {'seconds': 60.5, 'profile': 'tuned'})
        self.assertEqual(pref.readback(raw, effective), effective)
        record = json.loads(raw)
        self.assertEqual(record['preset']['raw_utf8'].encode(), self.path.read_bytes())
        self.assertEqual(record['preset']['sha256'], hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(effective['seconds'], 60.5)
        self.assertEqual(effective['adapter'], 'both')
        self.assertEqual(record['overrides'], {'seconds': 60.5, 'profile': 'tuned'})
        self.assertEqual(pref.route_arguments(effective), {
            'seconds': 60.5, 'keep_existing': False, 'adapter': 'both', 'engine_profile': 'tuned',
            'guidance_policy': 'native', 'scoring_variant': None})

    def test_no_preset_preserves_defaults_without_implicit_file_access(self):
        with patch.object(pref, '_read', side_effect=AssertionError('implicit read')):
            self.assertEqual(pref.resolve(), dict(pref.DEFAULTS))
            self.assertEqual(pref.readback(pref.snapshot()), dict(pref.DEFAULTS))
            pref.check_fresh(None)
        with self.assertRaises(TypeError):pref.DEFAULTS['seconds'] = 900

    def test_only_optional_scoring_field_may_be_omitted(self):
        value = dict(pref.DEFAULTS);del value['scoring_preference']
        self.path.write_bytes(self.encode(value))
        self.assertIsNone(pref.resolve(pref.load(self.path))['scoring_preference'])
        for name in pref.REQUIRED:
            missing = dict(pref.DEFAULTS);del missing[name]
            with self.subTest(name=name),self.assertRaises(pref.PreferenceError):pref.validate(missing)

    def test_valid_named_scoring_is_passed_without_quality_promise(self):
        for name in (None, 'via_default', 'via_low', 'via_high'):
            with self.subTest(name=name):
                captured = self.write(scoring_preference=name)
                self.assertEqual(pref.route_arguments(pref.readback(pref.snapshot(captured)))['scoring_variant'], name)

    def test_explicit_layers_require_qualified_profile_and_roundtrip_independently(self):
        for layers in (['F.Cu'], 'F.Cu', [], None, True, 'all', 'source-all'):
            with self.subTest(layers=layers),self.assertRaises(pref.PreferenceError):self.write(layers=layers)
        for layers in (['F.Cu'], ['B.Cu'], ['B.Cu','F.Cu']):
            captured=self.write(layers=layers,profile='completion-only')
            self.assertEqual(pref.readback(pref.snapshot(captured))['layers'],layers)
            effective=pref.resolve(captured);effective['layers'].clear()
            self.assertEqual(pref.resolve(captured)['layers'],layers)
        for layers in ([], ['F.Cu','F.Cu'], ['source_all','F.Cu'], 'F.Cu', None, True):
            with self.subTest(layers=layers),self.assertRaises(pref.PreferenceError):
                self.write(layers=layers,profile='completion-only')

    def test_unsupported_and_incompatible_guidance_is_rejected(self):
        for guidance in ('board-floors-v1', 'placement-clearance-v1'):
            base = dict(pref.DEFAULTS, guidance=guidance, adapter='both', profile='completion-only')
            self.assertEqual(pref.validate(base), base)
            for changes in ({'scope':'partial_completion'}, {'adapter':'none'},
                            {'scoring_preference':'via_default'}, {'scoring_preference':'via_low'}):
                with self.subTest(guidance=guidance,changes=changes),self.assertRaises(pref.PreferenceError):
                    pref.validate(dict(base, **changes))
        with self.assertRaises(pref.PreferenceError):
            pref.validate(dict(pref.DEFAULTS, guidance='placement-clearance-v1', adapter='both'))
        self.assertTrue(pref.route_arguments(pref.resolve(overrides={'scope':'partial_completion'}))['keep_existing'])
        with self.assertRaises(pref.PreferenceError):self.write(scope='selected_nets')

    def test_invalid_scalar_types_and_budget_boundaries(self):
        for seconds in (True, False, None, '120', 4.99, 900.01, math.nan, math.inf, -math.inf, 10**400):
            with self.subTest(seconds=str(seconds)[:25]),self.assertRaises(pref.PreferenceError):
                pref.validate(dict(pref.DEFAULTS, seconds=seconds))
        for seconds in (5, 900, 120.25):self.assertEqual(pref.validate(dict(pref.DEFAULTS, seconds=seconds))['seconds'], seconds)
        for key,value in [('schema', True), ('schema', 1.0), ('schema', 2), ('adapter', ['both']),
                          ('profile', False), ('scoring_preference', False), ('scope', None)]:
            with self.subTest(key=key,value=value),self.assertRaises(pref.PreferenceError):
                pref.validate(dict(pref.DEFAULTS, **{key:value}))

    def test_unknown_keys_aliases_and_override_schema_rejected(self):
        for name in ('keep_existing', 'engine_profile', 'budget', 'nets', 'layers_enabled', 'command', 'schema'):
            with self.subTest(name=name),self.assertRaises(pref.PreferenceError):pref.resolve(overrides={name:True})
        with self.assertRaises(pref.PreferenceError):self.write(extra='ignored?')
        with self.assertRaises(pref.PreferenceError):pref.resolve(overrides=[])

    def test_duplicate_nonfinite_malformed_and_deep_json_rejected(self):
        good = json.dumps(dict(pref.DEFAULTS))
        raws = [good[:-1]+',"seconds":60}', good.replace('120', 'NaN'), good.replace('120', 'Infinity'),
                '{', '[]', 'null', '['*2000+']'*2000, '\ufeff'+good]
        for text in raws:
            with self.subTest(text=text[:50]):
                self.path.write_text(text)
                with self.assertRaises(pref.PreferenceError):pref.load(self.path)
        self.path.write_bytes(b'\xff')
        with self.assertRaises(pref.PreferenceError):pref.load(self.path)

    def test_regular_file_size_symlink_ancestors_fifo_and_parent_alias_guards(self):
        self.write()
        alias=self.root/'alias.json';alias.symlink_to(self.path)
        directory=self.root/'alias-dir';directory.symlink_to(self.root, target_is_directory=True)
        fifo=self.root/'pipe';os.mkfifo(fifo)
        for path in (alias,directory/'preset.json',fifo,self.root,self.root/'missing.json',self.root/'sub/../preset.json'):
            with self.subTest(path=path),self.assertRaises(pref.PreferenceError):pref.load(path)
        self.path.write_bytes(b' '*(pref.MAX_PRESET_BYTES+1))
        with self.assertRaises(pref.PreferenceError):pref.load(self.path)
        self.path.write_bytes(b'')
        with self.assertRaises(pref.PreferenceError):pref.load(self.path)

    def test_stale_during_run_but_old_capture_valid_after_intentional_edit(self):
        captured=self.write(seconds=60);raw=pref.snapshot(captured)
        pref.check_fresh(captured)
        self.write(seconds=90)
        with self.assertRaisesRegex(pref.PreferenceError,'changed during execution'):pref.check_fresh(captured)
        self.assertEqual(pref.readback(raw)['seconds'],60)
        self.path.unlink()
        with self.assertRaises(pref.PreferenceError):pref.check_fresh(captured)
        self.assertEqual(pref.readback(raw)['seconds'],60)

    def test_parsed_dictionary_cannot_change_resolve_or_snapshot(self):
        captured=self.write(seconds=60);before=pref.snapshot(captured)
        captured.parsed['seconds']=900;captured.parsed['scope']='selected_nets'
        self.assertEqual(pref.resolve(captured)['seconds'],60)
        self.assertEqual(pref.snapshot(captured),before)
        pref.check_fresh(captured)
        with self.assertRaises(pref.PreferenceError):pref.resolve(replace(captured,sha256='0'*64))
        with self.assertRaises(pref.PreferenceError):pref.snapshot(replace(captured,raw=b'{}'))
        with self.assertRaises(pref.PreferenceError):pref.resolve(replace(captured,path=Path('preset.json')))

    def test_rehashed_raw_cannot_hide_effective_mismatch_or_unsupported_choice(self):
        captured=self.write();record=json.loads(pref.snapshot(captured))
        for mutation in ('seconds','layers','duplicate'):
            changed=copy.deepcopy(record)
            preset=dict(pref.DEFAULTS)
            if mutation=='seconds':preset['seconds']=90
            if mutation=='layers':preset['layers']=['F.Cu']
            raw=json.dumps(preset)
            if mutation=='duplicate':raw=raw[:-1]+',"seconds":90}'
            changed['preset']['raw_utf8']=raw
            changed['preset']['sha256']=hashlib.sha256(raw.encode()).hexdigest()
            with self.subTest(mutation=mutation),self.assertRaises(pref.PreferenceError):pref.readback(self.encode(changed))

    def test_snapshot_fields_hashes_overrides_and_canonical_types_are_bound(self):
        record=json.loads(pref.snapshot(self.write()))
        cases=[]
        for key in record:
            value=copy.deepcopy(record);del value[key];cases.append(value)
        for field,value in [('effective',dict(pref.DEFAULTS,seconds=90)),('overrides',{'seconds':90}),
                            ('overrides',None),('schema',True),('schema',1.0),('extra',False)]:
            mutated=copy.deepcopy(record);mutated[field]=value;cases.append(mutated)
        for field,value in [('sha256','0'*64),('path','preset.json'),('path',str(self.root)+'/./preset.json')]:
            mutated=copy.deepcopy(record);mutated['preset'][field]=value;cases.append(mutated)
        changed=copy.deepcopy(record);changed['effective']['seconds']=120.0;cases.append(changed)
        for case in cases:
            with self.subTest(case=str(case)[:80]),self.assertRaises(pref.PreferenceError):pref.readback(self.encode(case))
        with self.assertRaises(pref.PreferenceError):pref.readback(self.encode(record),dict(pref.DEFAULTS,seconds=120.0))
        with self.assertRaises(pref.PreferenceError):pref.readback(self.encode(record),dict(pref.DEFAULTS,seconds=90))

    def test_snapshot_readback_bounds_and_unicode_raw_roundtrip(self):
        value=dict(pref.DEFAULTS);text=json.dumps(value,ensure_ascii=False)
        # Unicode escapes in JSON keys are legal, but duplicate semantic keys remain forbidden.
        text=text.replace('"seconds"','"\\u0073econds"')
        self.path.write_text(text+'\n\t ')
        captured=pref.load(self.path);raw=pref.snapshot(captured)
        self.assertEqual(json.loads(raw)['preset']['raw_utf8'].encode(),captured.raw)
        self.assertEqual(pref.readback(raw),dict(pref.DEFAULTS))
        for invalid in (b'',b' '*(pref.MAX_SNAPSHOT_BYTES+1),bytearray(raw),raw[:-2]+b',"schema":1}'):
            with self.assertRaises(pref.PreferenceError):pref.readback(invalid)

    def test_override_mutation_does_not_rewrite_captured_snapshot(self):
        captured=self.write();overrides={'seconds':60}
        raw=pref.snapshot(captured,overrides);overrides['seconds']=900
        self.assertEqual(pref.readback(raw)['seconds'],60)
        self.assertEqual(pref.resolve(captured,overrides)['seconds'],900)


if __name__=='__main__':unittest.main()
