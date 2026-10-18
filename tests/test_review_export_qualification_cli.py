"""Retained-case selection controls only; no Native, routing or PCB approval."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from scripts import qualify_review_export as q


class RetainedSelection(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();(self.root/'.runs').mkdir()
        self.root_patch=patch.object(q.c,'ROOT',self.root);self.root_patch.start();self.addCleanup(self.root_patch.stop)

    def receipt(self,name='one',schema=5):
        path=self.root/'.runs'/name/'result.json';path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'schema':schema})+'\n');return path

    def test_defaults_are_the_exact_original_population(self):
        self.assertIs(q.selected_cases(),q.CASES)
        self.assertEqual([row[3] for row in q.selected_cases()],[False,False,False,True,False])

    def test_one_supported_receipt_derives_schema_and_scopes_render(self):
        for schema in (1,3,4,5):
            path=self.receipt(str(schema),schema)
            self.assertEqual(q.selected_cases(path),(('retained',str(path),schema,False),))
            self.assertEqual(q.selected_cases(path.relative_to(self.root),render=True),
                (('retained',str(path),schema,True),))

    def test_unsupported_boolean_and_nonobject_schema_inputs_refuse(self):
        for index,schema in enumerate((True,False,2,6,'5',None)):
            with self.subTest(schema=schema),self.assertRaises(q.p.Rejected):
                q.selected_cases(self.receipt(str(index),schema))
        path=self.receipt('nonobject');path.write_text('[]\n')
        with self.assertRaises(q.p.Rejected):q.selected_cases(path)
        path.write_text('{corrupt}\n')
        with self.assertRaises(q.p.Rejected):q.selected_cases(path)

    def test_missing_outside_nonresult_and_directory_paths_refuse(self):
        path=self.receipt();outside=self.root/'result.json';outside.write_text('{}\n')
        other=path.with_name('export.json');other.write_text('{"schema":5}\n')
        directory=self.root/'.runs/directory/result.json';directory.mkdir(parents=True)
        for value in (outside,other,directory,self.root/'.runs/missing/result.json',self.root/'.runs/result.json'):
            with self.subTest(path=value),self.assertRaises(q.p.Rejected):q.selected_cases(value)

    def test_symlink_receipt_parent_and_parent_traversal_refuse(self):
        path=self.receipt();alias=path.with_name('alias.json');alias.symlink_to(path)
        parent=self.root/'.runs/alias';parent.symlink_to(path.parent,target_is_directory=True)
        for value in (alias,parent/'result.json',path.parent/'..'/path.parent.name/'result.json'):
            with self.subTest(path=value),self.assertRaises(q.p.Rejected):q.selected_cases(value)

    def test_render_requires_an_explicit_receipt_and_boolean(self):
        with self.assertRaisesRegex(q.p.Rejected,'requires one explicit'):q.selected_cases(render=True)
        with self.assertRaisesRegex(q.p.Rejected,'explicit boolean'):q.selected_cases(self.receipt(),render=1)

    def test_cli_render_without_receipt_refuses_before_qualification(self):
        with patch.object(q,'qualify') as qualify,contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as stopped:q.main(['--output',str(self.root/'.runs/out'),'--run-native','--render'])
        self.assertEqual(stopped.exception.code,2);qualify.assert_not_called()

    def test_cli_dispatch_preserves_defaults_and_one_explicit_selection(self):
        result=dict(status='completed',controls_passed=True,routing_accepted=False,new_routing_executed=False,
                    wall_seconds=0.,total_cpu_seconds=0.)
        for explicit in (False,True):
            args=['--output',str(self.root/'.runs/out'),'--run-native']
            receipt=self.receipt('dispatch') if explicit else None
            if explicit:args+=['--receipt',str(receipt),'--render']
            with patch.object(q,'qualify',return_value=result) as qualify,patch.object(q.fcntl,'flock'),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(q.main(args),0)
            qualify.assert_called_once_with(self.root/'.runs/out',run_native=True,receipt=receipt,render=explicit)

    def test_unqualified_selected_receipt_stops_before_review_or_native(self):
        receipt=self.receipt();controller=Path(q.__file__).read_bytes()
        with patch.object(q.p,'check_storage') as storage,patch.object(q.p,'tool_manifest',return_value={'git_head':'a'*40}),\
                patch.object(q.subprocess,'run',return_value=SimpleNamespace(stdout=controller)),\
                patch.object(q.p,'check_result',side_effect=q.p.Rejected('unqualified retained receipt')) as check,\
                patch.object(q.h,'review_copy') as review,patch.object(q.e,'export') as export:
            result=q.qualify(self.root/'.runs/refused',run_native=True,receipt=receipt,render=True)
        check.assert_called_once_with(receipt);review.assert_not_called();export.assert_not_called()
        storage.assert_called_once_with(active_root=self.root/'.runs/refused')
        self.assertFalse(result['controls_passed']);self.assertFalse(result['accepted'])
        self.assertIn('unqualified retained receipt',result['reason'])
        self.assertEqual(result['cases'],[])


if __name__=='__main__':unittest.main()
