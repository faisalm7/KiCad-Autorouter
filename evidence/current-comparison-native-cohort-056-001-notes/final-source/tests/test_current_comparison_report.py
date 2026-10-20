"""Constructed reporting controls only; inert files, no Native/routing/readers.

These tests check byte custody/classification, not PCB semantics or GUI support.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts import report_current_comparison as q


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(data, sort_keys=True) + '\n').encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


class ComparisonReportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.folder = self.root / 'route'
        candidate = self.folder / 'candidate/owned.kicad_pcb'
        candidate.parent.mkdir(parents=True)
        candidate.write_bytes(b'inert owned candidate, never parsed\n')
        source = {'owned.kicad_pcb': 'a' * 64, 'owned.kicad_pro': 'b' * 64, 'owned.kicad_sch': 'c' * 64}
        original = {'owned.kicad_pcb': b'original', 'owned.kicad_pro': b'original rules', 'owned.kicad_sch': b'original full SCH'}
        source = {name: hashlib.sha256(raw).hexdigest() for name, raw in original.items()}
        final = dict(original, **{candidate.name: candidate.read_bytes()})
        inputs = self.folder / 'final-drc-input'
        inputs.mkdir()
        for name, raw in final.items(): (inputs / name).write_bytes(raw)
        expected = q.io.inventory(inputs)
        self.tools = dict(kicad='10.0.7', source_provenance=dict(git_head='d' * 40, manifest_sha256='e' * 64),
                          files={str(self.root / 'kicad-cli'): 'f' * 64},
                          implementation_sha256={name:q.digest(q.ROOT/name) for name in
                            ('autorouter/pipeline.py','autorouter/schematic_field_evidence.py',
                             'autorouter/schematic_fields.py','autorouter/sexpr.py')})
        self.plan = dict(source_hashes=source, tools=self.tools, source_head='d' * 40, runtime_manifest_sha256='e' * 64)
        self.binding = dict(source=str(candidate), input=str(inputs / candidate.name), before=expected, after=expected, saved=False)
        write(self.folder / 'final-drc-binding.json', self.binding)
        self.raw = {'$schema': 'https://schemas.kicad.org/drc.v1.json', 'kicad_version': '10.0.7', 'source': candidate.name,
                    'included_severities': ['error', 'warning', 'exclusion'], 'violations': [], 'unconnected_items': [],
                    'schematic_parity': [], 'ignored_checks': [dict(key='lib_footprint_issues')]}
        self.report_pin = write(self.folder / 'final-drc.json', self.raw)
        self.step = dict(name='final-drc', argv=[str(self.root / 'kicad-cli'), 'pcb', 'drc', '--schematic-parity',
            '--all-track-errors', '--refill-zones', '--exit-code-violations', '--output', str(self.folder / 'final-drc.json'), str(inputs / candidate.name)],
            cwd=str(self.folder), status='success', exit_code=0, cleanup_complete=True, log_truncated=False, pid=123)
        write(self.folder / 'final-drc-process.json', self.step)
        self.data = dict(source_hashes=source, tools=self.tools, schematic_parity='checked by final native DRC', accepted=True,
            invariants_unchanged=True, candidate=str(candidate), candidate_sha256=q.digest(candidate), native_report_sha256=self.report_pin,
            native=dict(opens=0, blocking=0, warnings=0, exclusions=0, findings=[], ignored_checks=[dict(key='lib_footprint_issues')]),
            whole_project_drc_clean=True, protected_route_import=dict(matches=[{'synthetic': 'protected identity'}]), steps=[self.step])
        self.receipt = self.folder / 'result.json'
        write(self.receipt, self.data)

    def own(self, accepted=True):
        return q.own_final(self.receipt, export=False, plan=self.plan, allowed=[self.root], accepted=accepted)

    def test_own_final_uses_exact_output_not_first_trial_phase(self):
        trial = copy.deepcopy(self.step)
        trial['argv'][trial['argv'].index('--output') + 1] = str(self.root / 'trial/final-drc.json')
        self.data['steps'].insert(0, trial)
        write(self.receipt, self.data)
        result = self.own()
        self.assertEqual(result['Native_counts'], [0, 0, 0, 0])
        self.assertEqual(result['protected_count'], 1)
        self.assertTrue(result['full_schematic_flag'])

    def test_candidate_or_report_tamper_refuses(self):
        for path in (Path(self.data['candidate']), self.folder / 'final-drc.json'):
            with self.subTest(path=path.name):
                before = path.read_bytes()
                path.write_bytes(before + b'changed')
                with self.assertRaises(ValueError): self.own()
                path.write_bytes(before)

    def test_same_counts_different_findings_refuses_even_with_rebound_report_hash(self):
        self.raw['ignored_checks'] = ['different_check']
        self.data['native_report_sha256'] = write(self.folder / 'final-drc.json', self.raw)
        write(self.receipt, self.data)
        with self.assertRaises(ValueError): self.own()

    def test_missing_cleanup_or_full_schematic_flag_refuses(self):
        old = copy.deepcopy(self.data)
        for mutation in ('cleanup', 'schematic', 'input'):
            with self.subTest(mutation=mutation):
                self.data = copy.deepcopy(old)
                if mutation == 'cleanup': del self.data['steps'][0]['cleanup_complete']
                elif mutation == 'schematic': self.data['steps'][0]['argv'].remove('--schematic-parity')
                else: self.data['steps'][0]['argv'][-1] = str(self.root / 'unbound.kicad_pcb')
                write(self.receipt, self.data)
                with self.assertRaises(ValueError): self.own()

    def test_warning_exit5_and_complete_negative_keep_original_counts(self):
        finding = dict(severity='warning', type='lib_footprint_issues', items=[])
        self.raw['violations'] = [finding]
        self.data['native_report_sha256'] = write(self.folder / 'final-drc.json', self.raw)
        self.data['native'].update(warnings=1, findings=[finding])
        self.data['steps'][0].update(status='nonzero_exit', exit_code=5)
        write(self.folder / 'final-drc-process.json', self.data['steps'][0])
        write(self.receipt, self.data)
        self.assertEqual(self.own()['Native_counts'], [0, 0, 1, 0])
        finding['severity'] = 'error'
        self.data['native'].update(warnings=0, blocking=1)
        self.data['accepted'] = False
        self.data['native_report_sha256'] = write(self.folder / 'final-drc.json', self.raw)
        write(self.receipt, self.data)
        self.assertEqual(self.own(accepted=False)['Native_counts'], [0, 1, 0, 0])
        with self.assertRaises(ValueError): self.own(accepted=True)

    def test_warning_only_application_policy_negative_keeps_zero_error_counts(self):
        finding=dict(severity='warning',type='footprint_symbol_field_mismatch',items=[])
        self.raw['schematic_parity']=[finding]
        self.data['native_report_sha256']=write(self.folder/'final-drc.json',self.raw)
        self.data['native'].update(warnings=1,findings=[finding],field_parity=dict(qualification=dict(qualified=False)))
        self.data['accepted']=False
        self.data['steps'][0].update(status='nonzero_exit',exit_code=5)
        write(self.folder/'final-drc-process.json',self.data['steps'][0]);write(self.receipt,self.data)
        result=self.own(accepted=False)
        self.assertEqual(result['Native_counts'],[0,0,1,0])
        self.assertIs(result['Native_application_policy']['accepted'],False)
        with self.assertRaises(ValueError):self.own(accepted=True)

    def test_application_policy_cannot_use_a_different_recorded_source(self):
        pins=self.plan['tools']['implementation_sha256']
        for name in pins:
            original=pins[name];pins[name]='0'*64
            write(self.receipt,self.data)
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'application-policy source differs'):
                self.own()
            pins[name]=original
            write(self.receipt,self.data)

    def test_disabled_critical_check_is_policy_negative_even_without_count_errors(self):
        self.raw['ignored_checks']=[dict(key='clearance')]
        self.data['native'].update(ignored_checks=self.raw['ignored_checks'])
        self.data['native_report_sha256']=write(self.folder/'final-drc.json',self.raw)
        self.data['accepted']=False;write(self.receipt,self.data)
        result=self.own(accepted=False)
        self.assertEqual(result['Native_counts'],[0,0,0,0])
        self.assertIs(result['Native_application_policy']['accepted'],False)

    def test_cap_or_cleanup_failure_never_promotes_negative(self):
        outer = dict(passed=True, status='completed', process=dict(status='success', exit_code=0, cleanup_complete=True, log_truncated=False))
        data = dict(status='completed', controls_passed=True, accepted=False, production_admitted=False,
            attempt_qualified=True, workflow_delivered=False, outcome='validated_completed_negative', method_wall_seconds=10, method_full_cpu_seconds=9)
        self.assertTrue(q.classify(outer, data, dict(wall_seconds=12, CPU_seconds=11), 'B0')['validated_completed_negative'])
        for metric in ('wall_seconds', 'CPU_seconds'):
            cost = dict(wall_seconds=12, CPU_seconds=11); cost[metric] = 600.01
            self.assertFalse(q.classify(outer, data, cost, 'B0')['attempt_qualified'])
        for value in (False, None):
            outer['process']['cleanup_complete'] = value
            self.assertFalse(q.classify(outer, data, dict(wall_seconds=12, CPU_seconds=11), 'B0')['attempt_qualified'])
        outer['process']['cleanup_complete'] = True
        data['method_full_cpu_seconds'] = 450.01
        self.assertFalse(q.classify(outer, data, dict(wall_seconds=12, CPU_seconds=11), 'B0')['attempt_qualified'])

    def test_omitted_arm_or_native_only_promotion_refuses(self):
        pop = dict(schema=1, kind='frozen-runtime043-labelled-IR-native-support-followup-v1', population=list(q.frozen.POPULATION),
            planned_arm_order=list(q.frozen.ARM_ORDER), limits=q.frozen.LIMITS, planned_family_order=['owned'], families={'owned': {}},
            outputs={'owned': dict.fromkeys(q.frozen.POPULATION, 'path')}, administration_head='a' * 40, source_head='b' * 40, runtime='/owned/runtime', runtime_manifest_sha256='c' * 64,
            qualification=dict(kind='runtime043-labelled-native-only-IR-followup-prerequisites-v1', source_head='b' * 40, runtime='/owned/runtime', runtime_manifest_sha256='c' * 64, actual_GUI_qualified=False, full_GUI_claim=False))
        children = dict(schema=1, administration_head='a' * 40, policy_or_board_changes_after_first_arm=False,
                        protocols={'owned': dict.fromkeys(q.frozen.POPULATION, {})})
        self.assertEqual(q.population_shape(pop, children), ['owned'])
        original = copy.deepcopy(children)
        del children['protocols']['owned']['B0']
        with self.assertRaises(ValueError): q.population_shape(pop, children)
        pop['qualification']['actual_GUI_qualified'] = True
        with self.assertRaises(ValueError): q.population_shape(pop, original)

    def native049_population(self):
        population = dict(schema=1, kind='frozen-runtime049-labelled-Devobordo-native-CLI-development-followup-v1',
            population=list(q.frozen.POPULATION), planned_arm_order=list(q.frozen.ARM_ORDER), limits=q.frozen.LIMITS,
            planned_family_order=['devobordo'], families={'devobordo': {}},
            outputs={'devobordo': dict.fromkeys(q.frozen.POPULATION, 'path')}, administration_head='a' * 40,
            source_head='b' * 40, runtime='/owned/runtime049', runtime_manifest_sha256='c' * 64,
            qualification=dict(kind='runtime049-labelled-native-CLI-Devobordo-prerequisites-v1', source_head='b' * 40,
                runtime='/owned/runtime049', runtime_manifest_sha256='c' * 64, actual_GUI_qualified=False, full_GUI_claim=False))
        children = dict(schema=1, administration_head='a' * 40, policy_or_board_changes_after_first_arm=False,
            protocols={'devobordo': dict.fromkeys(q.frozen.POPULATION, {})})
        return population, children

    def test_exact_runtime049_native_only_labels_are_supported(self):
        population, children = self.native049_population()
        self.assertEqual(q.population_shape(population, children), ['devobordo'])
        self.assertIn('GUI qualification NOT supplied', q.KINDS[population['kind']])

    def test_runtime049_cannot_promote_or_substitute_qualification(self):
        original, children = self.native049_population()
        mutations = [('actual_GUI_qualified', True), ('actual_GUI_qualified', 0), ('full_GUI_claim', True),
            ('full_GUI_claim', 0), ('kind', q.frozen.QUALIFICATION_KIND),
            ('kind', 'runtime043-labelled-native-only-IR-followup-prerequisites-v1'), ('kind', 'unqualified'),
            ('source_head', 'd' * 40), ('runtime', '/other/runtime'), ('runtime_manifest_sha256', 'e' * 64)]
        for name, value in mutations:
            with self.subTest(field=name, value=value):
                population = copy.deepcopy(original); population['qualification'][name] = value
                with self.assertRaises(ValueError): q.population_shape(population, children)
        population = copy.deepcopy(original); population['kind'] += '-unknown'
        with self.assertRaises(ValueError): q.population_shape(population, children)

    def native050_population(self):
        population, children = self.native049_population()
        population.update(kind='frozen-runtime050-labelled-Devobordo-native-CLI-development-followup-v1',
            source_head='aa0072c6b3d8090de2603e5ecb42a95968fb873b', runtime='/owned/runtime050',
            runtime_manifest_sha256='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8')
        population['qualification'].update(kind='runtime050-labelled-native-CLI-Devobordo-prerequisites-v1',
            source_head=population['source_head'], runtime=population['runtime'],
            runtime_manifest_sha256=population['runtime_manifest_sha256'])
        return population, children

    def test_exact_runtime050_native_CLI_only_labels_are_supported(self):
        population, children = self.native050_population()
        self.assertEqual(q.population_shape(population, children), ['devobordo'])
        self.assertIn('GUI qualification NOT supplied', q.KINDS[population['kind']])
        self.assertIs(population['qualification']['actual_GUI_qualified'], False)
        self.assertIs(population['qualification']['full_GUI_claim'], False)

    def test_runtime050_rejects_GUI_promotion_foreign_identity_and_old_qualification(self):
        original, children = self.native050_population()
        mutations = [('actual_GUI_qualified', True), ('actual_GUI_qualified', 0),
            ('full_GUI_claim', True), ('full_GUI_claim', 0), ('source_head', 'd' * 40),
            ('runtime', '/owned/runtime049'), ('runtime_manifest_sha256', 'e' * 64),
            ('kind', 'runtime049-labelled-native-CLI-Devobordo-prerequisites-v1'),
            ('kind', 'runtime043-labelled-native-only-IR-followup-prerequisites-v1'),
            ('kind', q.frozen.QUALIFICATION_KIND)]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                population = copy.deepcopy(original); population['qualification'][key] = value
                with self.assertRaises(ValueError): q.population_shape(population, children)
        population, old_children = self.native049_population()
        population['qualification']['kind'] = original['qualification']['kind']
        with self.assertRaises(ValueError): q.population_shape(population, old_children)
        population = copy.deepcopy(original); population['kind'] += '-unknown'
        with self.assertRaises(ValueError): q.population_shape(population, children)

    def test_runtime050_label_does_not_bypass_complete_population_or_fixed_budgets(self):
        original, children = self.native050_population()
        missing = copy.deepcopy(children); del missing['protocols']['devobordo']['B0']
        with self.assertRaises(ValueError): q.population_shape(original, missing)
        population = copy.deepcopy(original); population['limits'] = dict(population['limits'], whole_wall_seconds=601)
        with self.assertRaises(ValueError): q.population_shape(population, children)

    def test_existing_public_and_runtime043_labels_keep_their_qualification_contracts(self):
        original, children = self.native049_population()
        pairs = [('frozen-current-six-arm-exposed-development-v1', q.frozen.QUALIFICATION_KIND),
            ('frozen-runtime043-labelled-IR-native-support-followup-v1',
             'runtime043-labelled-native-only-IR-followup-prerequisites-v1')]
        for kind, qualification in pairs:
            with self.subTest(kind=kind):
                population = copy.deepcopy(original); population['kind'] = kind
                population['qualification']['kind'] = qualification
                self.assertEqual(q.population_shape(population, children), ['devobordo'])
                population['qualification']['kind'] = original['qualification']['kind']
                with self.assertRaises(ValueError): q.population_shape(population, children)

    def native_cohort_population(self):
        population, children = self.native049_population()
        population.update(kind=q.frozen.IMPROVE_POPULATION_KIND,
            population=list(q.frozen.IMPROVE_POPULATION),
            planned_arm_order=list(q.frozen.IMPROVE_ARM_ORDER),
            outputs={'devobordo': dict.fromkeys(q.frozen.IMPROVE_POPULATION, 'path')})
        population['qualification'].update(kind=q.frozen.NATIVE_COHORT_QUALIFICATION_KIND,
            Native_cohort_only=True)
        children['protocols'] = {'devobordo': dict.fromkeys(q.frozen.IMPROVE_POPULATION, {})}
        return population, children

    def test_native_cohort_report_keeps_CLI_only_identity_and_complete_population(self):
        population, children = self.native_cohort_population()
        self.assertEqual(q.population_shape(population, children), ['devobordo'])
        self.assertIn('GUI qualification NOT supplied', q.KINDS[population['kind']])
        missing = copy.deepcopy(children); del missing['protocols']['devobordo']['B0']
        with self.assertRaises(ValueError): q.population_shape(population, missing)
        original = copy.deepcopy(population)
        for key, value in [('Native_cohort_only', False), ('Native_cohort_only', 1),
                ('actual_GUI_qualified', True), ('actual_GUI_qualified', 0),
                ('full_GUI_claim', True), ('full_GUI_claim', 0), ('source_head', 'd' * 40),
                ('runtime', '/other/runtime'), ('runtime_manifest_sha256', 'e' * 64),
                ('kind', 'unqualified')]:
            with self.subTest(field=key, value=value):
                population = copy.deepcopy(original); population['qualification'][key] = value
                with self.assertRaises(ValueError): q.population_shape(population, children)
        for key in ('Native_cohort_only', 'runtime', 'source_head', 'runtime_manifest_sha256'):
            population = copy.deepcopy(original); del population['qualification'][key]
            with self.assertRaises(ValueError): q.population_shape(population, children)
        population = copy.deepcopy(original)
        population.update(kind='frozen-current-six-arm-exposed-development-v1',
            population=list(q.frozen.POPULATION), planned_arm_order=list(q.frozen.ARM_ORDER),
            outputs={'devobordo': dict.fromkeys(q.frozen.POPULATION, 'path')})
        children['protocols'] = {'devobordo': dict.fromkeys(q.frozen.POPULATION, {})}
        with self.assertRaises(ValueError): q.population_shape(population, children)

    def test_existing050_Improve_CLI_report_contract_is_preserved(self):
        population, children = self.native_cohort_population()
        population['qualification'] = dict(kind=q.frozen.IMPROVE_QUALIFICATION_KIND,
            actual_GUI_qualified=False, full_GUI_claim=False)
        self.assertEqual(q.population_shape(population, children), ['devobordo'])

    def test_public_sanitize_preserves_failure_reference_not_text(self):
        value = 'unsupported source design conflict; local detail'
        plain = q.field_fact(value, self.receipt, 'reason', False)
        public = q.field_fact(value, self.receipt, 'reason', True)
        self.assertEqual(plain['sha256'], public['sha256'])
        self.assertEqual(public['field'], 'reason')
        self.assertNotIn('value', public)
        self.assertIn('text_not_retained', public)

    def test_actual_native_metrics_keep_track_length_and_version(self):
        native = dict(version='10.0.7', pads=6, footprints=2, zones=1, vias=2,
                      track_length_mm=167.425062867, copper_layers=2)
        self.assertEqual(q.metric_facts(native), native)
        for value in (True, -1, float('inf')):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    q.metric_facts(dict(native, track_length_mm=value))

    def test_public_ignored_checks_keep_keys_without_descriptions(self):
        checks = [dict(key='lib_footprint_issues', description='private source detail'),
                  dict(key='lib_footprint_mismatch', description='another detail')]
        plain = q.ignored_check_facts(checks, self.receipt, 'native.ignored_checks', False)
        public = q.ignored_check_facts(checks, self.receipt, 'native.ignored_checks', True)
        self.assertEqual(public['keys'], ['lib_footprint_issues', 'lib_footprint_mismatch'])
        self.assertEqual(public['count'], 2)
        self.assertEqual(public['sha256'], plain['sha256'])
        self.assertNotIn('value', public)
        self.assertNotIn('private source detail', json.dumps(public))
        with self.assertRaises(ValueError):
            q.ignored_check_facts([dict(key='unsafe description / coordinates')], self.receipt, 'ignored_checks', True)

    def test_complete_exit_cost_does_not_add_method_sample(self):
        path = self.root / 'time.log'
        path.write_text('real 11.25\nuser 6.50\nsys 1.25\n')
        self.assertEqual(q.complete_cost(path)['CPU_seconds'], 7.75)
        path.write_text('11.25 real 6.50 user 1.25 sys\n')
        self.assertEqual(q.complete_cost(path)['wall_seconds'], 11.25)


if __name__ == '__main__': unittest.main()
