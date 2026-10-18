"""Protected-via matcher/readback controls; no Native execution or acceptance."""
import copy
from pathlib import Path
import tempfile
import unittest
import uuid

from autorouter import pipeline as p, sexpr as sx


STRICT_V2 = 'exact_non_uuid_lock_position_v2'
FEATURES = (
    ['capping', 'no'],
    ['covering', ['front', 'no'], ['back', 'no']],
    ['plugging', ['front', 'no'], ['back', 'no']],
    ['filling', 'no'],
)


def uid(name):
    return '"' + str(uuid.uuid5(uuid.NAMESPACE_URL, 'owned-legacy-via-import/' + name)) + '"'


def board():
    return sx.parse(
        '(kicad_pcb (version 20241229) (net 0 "") (net 1 "A") (net 2 "B") '
        '(via (at 5 0) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") '
        f'(net 1) (uuid {uid("original-via")})) '
        '(segment (start 0 0) (end 5 0) (width 0.25) (layer "F.Cu") '
        f'(net 1) (uuid {uid("original-segment")})))')


def imported(original):
    """Authored modern serializer shape, not output from an actual importer."""
    result = copy.deepcopy(original)
    sx.one(result, 'version')[1] = '20260206'
    names = {row[1]: row[2] for row in sx.children(original, 'net')}
    result[:] = [row for row in result if row not in sx.children(result, 'net')]
    for index, route in enumerate(p.routes(result)):
        sx.one(route, 'net')[1] = names[sx.one(route, 'net')[1]]
        sx.one(route, 'uuid')[1] = uid('imported-' + str(index))
        if route[0] == 'via':
            for field in FEATURES:
                if not sx.children(route, field[0]):
                    route.append(copy.deepcopy(field))
    return result


class LegacyViaImportTests(unittest.TestCase):
    def setUp(self):
        self.original = board()
        self.imported = imported(self.original)
        self.protected = copy.deepcopy(p.routes(self.original))
        self.policy = p.PROTECTED_VIA_IMPORT_POLICY

    def apply(self, *, original=None, saved=None, protected=None, policy=None, audit=None):
        return p.transplant_routes(
            self.original if original is None else original,
            self.imported if saved is None else saved,
            protected=self.protected if protected is None else protected,
            policy=self.policy if policy is None else policy,
            audit=audit)

    def test_source_derived_policy_and_complete_original_records_are_preserved(self):
        self.assertEqual(self.policy, 'legacy-via-off-source-v3')
        self.assertEqual(p.normal_strict_import_policy(self.original, self.protected), self.policy)
        self.assertEqual(p.normal_strict_import_policy(self.original, []), STRICT_V2)
        before = copy.deepcopy((self.original, self.imported, self.protected))
        proof = {}
        candidate = self.apply(audit=proof)
        self.assertEqual(candidate, self.original)
        self.assertEqual(p.routes(candidate), self.protected)
        self.assertEqual(sx.one(candidate, 'version'), ['version', '20241229'])
        self.assertEqual(proof['policy'], self.policy)
        self.assertEqual(len(proof['matches']), len(self.protected))
        self.assertEqual((self.original, self.imported, self.protected), before)

    def test_generated_routes_remain_exact_after_required_net_conversion(self):
        saved = copy.deepcopy(self.imported)
        generated = sx.parse(
            '(segment (start 5 0) (end 8 0) (width 0.25) (layer "B.Cu") '
            f'(net "A") (uuid {uid("generated")}))')
        saved.append(generated)
        candidate = self.apply(saved=saved)
        expected = p.convert_route_nets(generated, saved, self.original)
        self.assertEqual(p.routes(candidate), self.protected + [expected])
        self.assertEqual(sx.one(expected, 'net'), ['net', '1'])

    def test_modern_import_omission_is_not_legacy_off(self):
        saved = copy.deepcopy(self.imported)
        via = p.routes(saved)[0]
        via[:] = [row for row in via if not isinstance(row, list) or not row or row[0] not in {f[0] for f in FEATURES}]
        with self.assertRaises(p.Rejected):
            self.apply(saved=saved)

    def test_only_qualified_source_and_saved_format_are_admitted(self):
        for version in ('20240108', '20250228', '20260206', '20261231'):
            with self.subTest(source_version=version):
                original = copy.deepcopy(self.original)
                sx.one(original, 'version')[1] = version
                self.assertEqual(p.normal_strict_import_policy(original, p.routes(original)), STRICT_V2)
                with self.assertRaises(p.Rejected):
                    self.apply(original=original, protected=p.routes(original))
        for version in ('20241229', '20250228', '20261231'):
            with self.subTest(imported_version=version):
                saved = copy.deepcopy(self.imported)
                sx.one(saved, 'version')[1] = version
                with self.assertRaises(p.Rejected):
                    self.apply(saved=saved)

    def test_missing_or_duplicate_format_cannot_authorize_new_policy(self):
        for target in ('source', 'imported'):
            for mode in ('missing', 'duplicate'):
                with self.subTest(target=target, mode=mode):
                    original = copy.deepcopy(self.original)
                    saved = copy.deepcopy(self.imported)
                    tree = original if target == 'source' else saved
                    version = sx.one(tree, 'version')
                    if mode == 'missing':
                        tree.remove(version)
                    else:
                        tree.append(copy.deepcopy(version))
                    with self.assertRaises((p.Rejected, ValueError)):
                        self.apply(original=original, saved=saved, protected=p.routes(original))

    def test_original_explicit_manufacturing_intent_keeps_strict_policy(self):
        for group in FEATURES:
            with self.subTest(group=group[0]):
                original = copy.deepcopy(self.original)
                p.routes(original)[0].append(copy.deepcopy(group))
                self.assertEqual(p.normal_strict_import_policy(original, p.routes(original)), STRICT_V2)
                with self.assertRaises(p.Rejected):
                    self.apply(original=original, saved=imported(original), protected=p.routes(original))

    def test_all_explicit_features_preserve_true_false_and_side_values_under_v2(self):
        original = copy.deepcopy(self.original)
        via = p.routes(original)[0]
        via.extend(copy.deepcopy(FEATURES))
        sx.one(via, 'capping')[1] = 'yes'
        sx.one(sx.one(via, 'covering'), 'front')[1] = 'yes'
        saved = imported(original)
        # Keep the same literal field order: strictv2 grants no new ordering waiver.
        self.assertEqual(self.apply(original=original, saved=saved,
                                    protected=p.routes(original), policy=STRICT_V2), original)
        for field, side in (('capping', None), ('covering', 'front'), ('covering', 'back'),
                            ('plugging', 'front'), ('plugging', 'back'), ('filling', None)):
            with self.subTest(field=field, side=side):
                changed = copy.deepcopy(saved)
                row = sx.one(p.routes(changed)[0], field)
                if side is not None:
                    row = sx.one(row, side)
                row[1] = 'no' if row[1] == 'yes' else 'yes'
                with self.assertRaises(p.Rejected):
                    self.apply(original=original, saved=changed, protected=p.routes(original), policy=STRICT_V2)

    def test_mixed_population_restores_omitted_via_without_relaxing_explicit_via(self):
        original = copy.deepcopy(self.original)
        explicit = copy.deepcopy(p.routes(original)[0])
        sx.one(explicit, 'at')[1] = '9'
        sx.one(explicit, 'uuid')[1] = uid('explicit-original')
        explicit.extend(copy.deepcopy(FEATURES))
        sx.one(explicit, 'capping')[1] = 'yes'
        original.append(explicit)
        saved = imported(original)
        protected = copy.deepcopy(p.routes(original))
        self.assertEqual(p.normal_strict_import_policy(original, protected), self.policy)
        proof = {}
        self.assertEqual(self.apply(original=original, saved=saved, protected=protected, audit=proof), original)
        self.assertIs(proof['matches'][0]['legacy_explicit_off_restored'], True)
        self.assertNotIn('legacy_explicit_off_restored', proof['matches'][1])
        self.assertNotIn('legacy_explicit_off_restored', proof['matches'][2])
        sx.one(p.routes(saved)[2], 'capping')[1] = 'no'
        with self.assertRaises(p.Rejected):
            self.apply(original=original, saved=saved, protected=protected)

    def test_each_of_six_imported_off_modes_is_required(self):
        for field, side in (('capping', None), ('covering', 'front'), ('covering', 'back'),
                            ('plugging', 'front'), ('plugging', 'back'), ('filling', None)):
            with self.subTest(field=field, side=side):
                saved = copy.deepcopy(self.imported)
                row = sx.one(p.routes(saved)[0], field)
                if side is not None:
                    row = sx.one(row, side)
                row[1] = 'yes'
                with self.assertRaises(p.Rejected):
                    self.apply(saved=saved)

    def test_missing_duplicate_extra_or_changed_manufacturing_fields_reject(self):
        for group in FEATURES:
            modes = ('missing', 'duplicate', 'extra', 'changed')
            if group[0] in ('covering', 'plugging'):
                modes += ('missing_side', 'duplicate_side', 'unknown_side')
            for mode in modes:
                with self.subTest(group=group[0], mode=mode):
                    saved = copy.deepcopy(self.imported)
                    via = p.routes(saved)[0]
                    row = sx.one(via, group[0])
                    if mode == 'missing':
                        via.remove(row)
                    elif mode == 'duplicate':
                        via.append(copy.deepcopy(row))
                    elif mode == 'extra':
                        row.append(['unknown', 'no'])
                    elif mode == 'changed':
                        if group[0] in ('covering', 'plugging'):
                            sx.one(row, 'back')[1] = 'yes'
                        else:
                            row[1] = 'yes'
                    elif mode == 'missing_side':
                        row.remove(sx.one(row, 'back'))
                    elif mode == 'duplicate_side':
                        row.append(copy.deepcopy(sx.one(row, 'front')))
                    else:
                        row.append(['inner', 'no'])
                    with self.assertRaises((p.Rejected, ValueError)):
                        self.apply(saved=saved)

    def test_geometry_net_drill_layer_and_unrelated_fields_remain_exact(self):
        for field, value in (('at', '5.001'), ('size', '0.9'), ('drill', '0.3'),
                             ('layers', '"B.Cu"'), ('net', '"B"')):
            with self.subTest(field=field):
                saved = copy.deepcopy(self.imported)
                sx.one(p.routes(saved)[0], field)[1] = value
                with self.assertRaises(p.Rejected):
                    self.apply(saved=saved)
        for row in (['tenting', ['front', 'no'], ['back', 'no']], ['unknown', 'no']):
            with self.subTest(extra=row[0]):
                saved = copy.deepcopy(self.imported)
                p.routes(saved)[0].append(row)
                with self.assertRaises(p.Rejected):
                    self.apply(saved=saved)

    def test_lock_position_can_change_but_lock_presence_and_value_cannot(self):
        original = copy.deepcopy(self.original)
        p.routes(original)[0].append(['locked', 'yes'])
        saved = imported(original)
        via = p.routes(saved)[0]
        lock = sx.one(via, 'locked')
        via.remove(lock)
        via.insert(1, lock)
        self.assertEqual(self.apply(original=original, saved=saved, protected=p.routes(original)), original)
        for mutation in ('missing', 'no', 'duplicate', 'bare'):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(saved)
                via = p.routes(changed)[0]
                lock = sx.one(via, 'locked')
                if mutation == 'missing':
                    via.remove(lock)
                elif mutation == 'no':
                    lock[1] = 'no'
                elif mutation == 'duplicate':
                    via.append(copy.deepcopy(lock))
                else:
                    via.remove(lock)
                    via.append('locked')
                with self.assertRaises(p.Rejected):
                    self.apply(original=original, saved=changed, protected=p.routes(original))
        changed = copy.deepcopy(self.imported)
        p.routes(changed)[0].append(['locked', 'yes'])
        with self.assertRaises(p.Rejected):
            self.apply(saved=changed)

    def test_missing_ambiguous_or_foreign_protected_via_rejects(self):
        for mode in ('missing', 'ambiguous', 'foreign', 'repeated'):
            with self.subTest(mode=mode):
                saved = copy.deepcopy(self.imported)
                protected = copy.deepcopy(self.protected)
                if mode == 'missing':
                    saved.remove(p.routes(saved)[0])
                elif mode == 'ambiguous':
                    extra = copy.deepcopy(p.routes(saved)[0])
                    sx.one(extra, 'uuid')[1] = uid('ambiguous-via')
                    saved.append(extra)
                elif mode == 'foreign':
                    sx.one(protected[0], 'at')[1] = '6'
                else:
                    protected.append(copy.deepcopy(protected[0]))
                with self.assertRaises(p.Rejected):
                    self.apply(saved=saved, protected=protected)

    def test_missing_duplicate_or_colliding_uuid_cannot_be_restored(self):
        for mode in ('source_missing', 'import_missing', 'source_duplicate',
                     'import_duplicate', 'import_collision', 'restored_collision'):
            with self.subTest(mode=mode):
                original = copy.deepcopy(self.original)
                saved = copy.deepcopy(self.imported)
                via = p.routes(original if mode.startswith('source_') else saved)[0]
                if mode.endswith('missing'):
                    via.remove(sx.one(via, 'uuid'))
                elif mode in ('source_duplicate', 'import_duplicate'):
                    via.append(['uuid', uid('duplicate-field')])
                elif mode == 'import_collision':
                    sx.one(p.routes(saved)[1], 'uuid')[1] = sx.one(via, 'uuid')[1]
                else:
                    extra = copy.deepcopy(p.routes(saved)[1])
                    sx.one(extra, 'end')[1] = '6'
                    sx.one(extra, 'uuid')[1] = sx.one(p.routes(original)[0], 'uuid')[1]
                    saved.append(extra)
                with self.assertRaises((p.Rejected, ValueError)):
                    self.apply(original=original, saved=saved, protected=p.routes(original))

    def test_historical_strict_policies_do_not_gain_a_manufacturing_waiver(self):
        for policy in ('exact_non_uuid_v1', STRICT_V2):
            with self.subTest(policy=policy):
                with self.assertRaises(p.Rejected):
                    self.apply(policy=policy)
                saved = copy.deepcopy(self.original)
                for index, route in enumerate(p.routes(saved)):
                    sx.one(route, 'uuid')[1] = uid('old-strict-' + str(index))
                self.assertEqual(self.apply(saved=saved, policy=policy), self.original)

    def test_readback_requires_independent_strict_policy_and_bound_import(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name).resolve()
        imported_path = directory / 'imported.kicad_pcb'
        candidate_path = directory / 'candidate.kicad_pcb'
        sx.write(imported_path, self.imported)
        proof = {'imported_sha256': p.sha(imported_path)}
        sx.write(candidate_path, self.apply(audit=proof))
        data = {'scope': 'partial_completion', 'protected_route_import': proof}

        def check(record=None, **options):
            return p.check_protected_import(directory, data if record is None else record,
                                            self.original, candidate_path, self.protected, **options)

        check(strict_expected_policy=self.policy)
        with self.assertRaises(p.Rejected):
            check()
        with self.assertRaises(p.Rejected):
            check(strict_expected_policy=STRICT_V2)
        with self.assertRaises(p.Rejected):
            check({}, strict_expected_policy=self.policy)
        for field in ('policy', 'matches', 'transplanted_routes_sha256', 'imported_sha256'):
            with self.subTest(field=field):
                changed = copy.deepcopy(data)
                changed['protected_route_import'].pop(field)
                with self.assertRaises((p.Rejected, ValueError, KeyError)):
                    check(changed, strict_expected_policy=self.policy)
        changed = copy.deepcopy(self.imported)
        sx.one(p.routes(changed)[0], 'drill')[1] = '0.3'
        sx.write(imported_path, changed)
        data['protected_route_import']['imported_sha256'] = p.sha(imported_path)
        with self.assertRaises(p.Rejected):
            check(strict_expected_policy=self.policy)


if __name__ == '__main__':
    unittest.main()
