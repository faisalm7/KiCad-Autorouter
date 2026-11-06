"""Inspection intake/authority controls; actual Native qualification is separate."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import project_inspection as inspection, pipeline as p


class ProjectInspectionTests(unittest.TestCase):
    def test_budget_is_finite_and_bounded(self):
        for value in (True, False, None, '60', 0, 4, 91, float('inf'), float('nan')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                inspection._seconds(value)
        self.assertEqual(inspection._seconds(60), 60)

    def test_output_never_overwrites_source_or_existing_workspace(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            board = root/'source'/'test.kicad_pcb'; board.parent.mkdir()
            board.write_text('(kicad_pcb)')
            existing = root/'existing'; existing.mkdir()
            for target in (board.parent, board.parent/'inspection', existing):
                with self.subTest(target=target), patch.object(p, 'Job') as job:
                    with self.assertRaises(ValueError): inspection.inspect(board, target)
                    job.assert_not_called()

    def test_failed_or_accepted_receipts_cannot_be_current_inspection(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve()/'inspection.json'
            base = dict(schema=1,policy=inspection.POLICY,status='inspection_ready',
                        accepted=False,native_validation_performed=True)
            for key, value in (('accepted',True),('status','inspection_cancelled'),
                               ('native_validation_performed',False),('policy','other')):
                record=copy.deepcopy(base);record[key]=value;p.save_json(path,record)
                with self.subTest(key=key), self.assertRaises(ValueError): inspection.check(path)
                path.unlink()

    def test_retained_process_cost_cannot_be_hidden_by_smaller_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary).resolve()/'inspection.json'
            record=dict(schema=1,policy=inspection.POLICY,status='inspection_ready',accepted=False,
                native_validation_performed=True,source='/unreached/source.kicad_pcb',source_hashes={},
                static={},tools={},budget_seconds=5,cpu_budget_seconds=5,native={},
                steps=[dict(wall_seconds=10,cpu_seconds=30,monitor_cpu_seconds=0)],
                wall_seconds=1,parent_cpu_seconds=0,child_cpu_seconds=30,
                control_child_cpu_seconds=0,monitor_cpu_seconds=0,total_cpu_seconds=1,
                native_report_sha256='0'*64,note='inspection only')
            p.save_json(path,record)
            with self.assertRaisesRegex(p.Rejected,'receipt exceeds its recorded wall budget'):
                inspection.check(path)


if __name__ == '__main__': unittest.main()
