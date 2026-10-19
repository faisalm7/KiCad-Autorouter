"""Producer reporting controls with synthetic stages, never Native qualification."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import test_recovery as fixture
from autorouter import pipeline as p


CHECKED = 'checked by final native DRC'


class SchematicRecoveryHarness(fixture.Harness):
    """Reuse the recovery transaction while separating incumbent/parent checks."""
    def __init__(self, base, mode='normal'):
        super().__init__(base, mode)
        self.source.with_suffix('.kicad_sch').write_text(
            '(kicad_sch (version 20250114) '
            '(uuid "e89e2fe7-1981-49d6-b263-ac3803e95cf9"))\n')

    def baseline(self, source, out, seconds, *args):
        result = super().baseline(source, out, seconds, *args)
        candidate = Path(result['candidate'])
        candidate.with_suffix('.kicad_sch').write_bytes(
            self.source.with_suffix('.kicad_sch').read_bytes())
        result.update(schematic_parity=CHECKED, source_hashes=p.tree_hash(self.source.parent))
        result['steps'].append(self.step('final-drc', 0, 0))
        (Path(out) / 'result.json').write_text(json.dumps(result))
        return result

    def validate(self, job, original, candidate, hashes, protected):
        if self.mode == 'interrupt_parent_refill':
            self.validation_calls += 1
            self.advance(parent=.1, child=.5, wall=.5)
            job.steps.append(dict(self.step('refill-drc', .5, .5),
                                  status='cancelled', exit_code=-9))
            raise KeyboardInterrupt
        digest, native = super().validate(job, original, candidate, hashes, protected)
        if self.mode == 'completed_negative':
            native = copy.deepcopy(native)
            native.update(blocking=1, findings=[dict(type='clearance', severity='error', items=[])])
            job.steps[-1].update(status='nonzero_exit', exit_code=5)
        return digest, native

    def native(self, job, name, action, board, output, *args):
        if self.mode == 'post_validation_cancel' and name == 'metrics':
            job.steps.append(dict(self.step('metrics', 0, 0), status='cancelled', exit_code=-9))
            raise KeyboardInterrupt
        return super().native(job, name, action, board, output, *args)


class ParityReporting(unittest.TestCase):
    def exercise(self, mode):
        with tempfile.TemporaryDirectory(dir=fixture.ROOT) as folder:
            harness = SchematicRecoveryHarness(folder, mode)
            before = p.tree_hash(harness.source.parent)
            result = harness.run()
            stored = json.loads((harness.out / 'result.json').read_bytes())
            incumbent = json.loads((harness.out / 'incumbent/result.json').read_bytes())
            self.assertEqual(p.tree_hash(harness.source.parent), before)
            self.assertEqual(result, stored)
            return stored, incumbent, harness.validation_calls

    def test_completed_incumbent_does_not_label_interrupted_parent_checked(self):
        result, incumbent, calls = self.exercise('interrupt_parent_refill')
        self.assertEqual(calls, 1)
        self.assertTrue(incumbent['accepted'])
        self.assertEqual(incumbent['schematic_parity'], CHECKED)
        self.assertEqual(result['status'], 'cancelled')
        self.assertFalse(result['accepted'])
        self.assertEqual(result['schematic_parity'], 'not checked')
        self.assertTrue(any(row['name'] == 'final-drc' and row.get('phase') == 'incumbent'
                            for row in result['steps']))
        self.assertEqual([(row['name'], row['status']) for row in result['steps']
                          if row.get('phase') != 'incumbent'], [('refill-drc', 'cancelled')])

    def test_own_completed_validation_preserves_accepted_declaration(self):
        result, _, calls = self.exercise('normal')
        self.assertEqual(calls, 1)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['schematic_parity'], CHECKED)
        self.assertTrue(p.selected_parity_required(result))

    def test_completed_negative_still_truthfully_reports_checked(self):
        result, _, calls = self.exercise('completed_negative')
        self.assertEqual(calls, 1)
        self.assertEqual(result['status'], 'drc_rejected')
        self.assertFalse(result['accepted'])
        self.assertEqual(result['native']['blocking'], 1)
        self.assertEqual(result['schematic_parity'], CHECKED)

    def test_cancellation_after_own_validation_does_not_erase_completed_check(self):
        result, _, calls = self.exercise('post_validation_cancel')
        self.assertEqual(calls, 1)
        self.assertEqual(result['status'], 'cancelled')
        self.assertFalse(result['accepted'])
        self.assertEqual(result['schematic_parity'], CHECKED)

    def test_publication_cancellation_preserves_completed_check(self):
        result, _, calls = self.exercise('publish_interrupt')
        self.assertEqual(calls, 1)
        self.assertEqual(result['status'], 'cancelled')
        self.assertFalse(result['accepted'])
        self.assertEqual(result['schematic_parity'], CHECKED)

    def test_completed_source_without_schematic_remains_explicitly_unavailable(self):
        with tempfile.TemporaryDirectory(dir=fixture.ROOT) as folder:
            result = fixture.Harness(folder).run()
            self.assertTrue(result['accepted'])
            self.assertEqual(result['schematic_parity'],
                             'unavailable: no native schematic in source project')


if __name__ == '__main__':
    unittest.main()
