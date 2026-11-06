"""Pure refusal controls; optional retained-evidence replay executes no Native.

Set PLACEMENT_EVIDENCE_OUTPUT, PLACEMENT_EVIDENCE_RUNTIME and
PLACEMENT_EVIDENCE_PROTOCOL to exercise an existing multipad receipt. Tests alter
only decoded in-memory records, never the retained evidence or its source files.
"""
import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from experiments import placement_native_evidence as evidence


class Refusals(unittest.TestCase):
    def test_unbounded_or_ambiguous_resources_are_refused(self):
        for value in (True, -1, 10**400, float('inf'), float('nan'), '1'):
            with self.subTest(value=str(value)), self.assertRaises(ValueError):
                evidence._number(value)

    def test_no_implicit_approval_or_completed_process(self):
        for record in ({}, {'accepted': 0}, {'accepted': True}):
            with self.assertRaises(ValueError): evidence._false(record, 'accepted')
        for record in ({}, {'status':'success', 'exit_code':False, 'cleanup_complete':True, 'log_truncated':False},
                       {'status':'success', 'exit_code':0, 'cleanup_complete':True, 'log_truncated':True}):
            with self.assertRaises(ValueError): evidence._success(record)


@unittest.skipUnless(all(os.environ.get(name) for name in (
    'PLACEMENT_EVIDENCE_OUTPUT', 'PLACEMENT_EVIDENCE_RUNTIME', 'PLACEMENT_EVIDENCE_PROTOCOL')),
    'optional current retained Native evidence not supplied')
class RetainedReadback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = Path(os.environ['PLACEMENT_EVIDENCE_OUTPUT'])
        cls.runtime = Path(os.environ['PLACEMENT_EVIDENCE_RUNTIME'])
        cls.protocol = Path(os.environ['PLACEMENT_EVIDENCE_PROTOCOL'])
        from experiments.placement_native_proposal_v1 import driver
        cls.driver = driver
        _, cls.p, cls.f, _, _, _ = driver.context(cls.runtime)

    def check(self):
        return evidence.check(self.output, self.runtime, self.protocol, 'multipad-preserve-v1')

    def changed_record(self, path, change):
        original = self.f.read_json
        def read(candidate):
            value = original(candidate)
            if Path(candidate) == path:
                value = copy.deepcopy(value); change(value)
            return value
        return patch.object(self.f, 'read_json', side_effect=read)

    def test_actual_retained_readback_grants_no_authority(self):
        value = self.check()
        self.assertTrue(value['current'])
        self.assertFalse(value['accepted'])
        self.assertFalse(value['execution_authorized'])
        self.assertFalse(value['human_approval'])
        self.assertEqual(value['candidate_sha256'], self.p.sha(Path(value['candidate'])))
        self.assertEqual(set(value['Native_findings']), {'source_native','refill_native','final_native'})

    def test_wrong_explicit_scope_refuses_before_readback(self):
        with self.assertRaisesRegex(ValueError, 'scope differs'):
            evidence.check(self.output, self.runtime, self.protocol, 'single-pad-unrouted-v1')

    def test_pose_and_selected_uuid_changes_refuse(self):
        path = self.output / 'work/proposal.json'
        def move(value): value['moves_nm'][next(iter(value['moves_nm']))][0] += 1
        def selected(value): value['selected_footprints'].reverse()
        for mutation in (move, selected):
            with self.changed_record(path, mutation), self.assertRaises(ValueError): self.check()

    def test_native_finding_and_observation_changes_refuse(self):
        def native(value): value['final_native']['opens'] += 1
        def detail(value): value['details']['native_pad_netcodes'].pop(next(iter(value['details']['native_pad_netcodes'])))
        for path, mutation in ((self.output / 'work/result.json', native),
                               (self.output / 'work/final-capture-observation.json', detail)):
            with self.changed_record(path, mutation), self.assertRaises(ValueError): self.check()

    def test_search_budget_must_be_rechecked_on_retained_readback(self):
        path=self.output/'work/result.json'
        for name in ('sampled_wall_seconds','sampled_cpu_seconds'):
            def change(value): value['search'][name]=2.0
            with self.subTest(name=name), self.changed_record(path,change):
                with self.assertRaisesRegex(ValueError,'search exceeded'): self.check()

    def test_changed_late_source_manifest_refuses(self):
        spec = self.f.read_json(self.protocol)
        manifest = self.driver.ROOT / spec['seed_manifest']
        original_sha, original_tools = self.p.sha, self.driver.runtime_unchanged
        after_tools = False
        def sha(path):
            return '0' * 64 if after_tools and Path(path) == manifest else original_sha(path)
        def tools(*args):
            nonlocal after_tools
            value = original_tools(*args); after_tools = True; return value
        with patch.object(self.p, 'sha', side_effect=sha), patch.object(self.driver, 'runtime_unchanged', side_effect=tools):
            with self.assertRaisesRegex(ValueError, 'source provenance manifest changed'): self.check()

    def test_late_tools_still_precede_native_metadata_replay(self):
        from autorouter import local_settings
        original_tools = self.driver.runtime_unchanged
        after_tools = False
        def tools(*args):
            nonlocal after_tools
            value = original_tools(*args); after_tools = True; return value
        original_metadata = local_settings.check_current_metadata
        def metadata(path):
            if after_tools: raise self.p.Rejected('injected changed retained PRL flags')
            return original_metadata(path)
        with patch.object(self.driver, 'runtime_unchanged', side_effect=tools), patch.object(local_settings, 'check_current_metadata', side_effect=metadata):
            with self.assertRaisesRegex(self.p.Rejected, 'changed retained PRL flags'): self.check()


if __name__ == '__main__':
    unittest.main()
