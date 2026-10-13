"""File/evidence control only; fabricated native work cannot qualify DRC."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import pipeline as p


class DrcFailureBinding(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'source'; self.source.mkdir()
        self.board = self.source / 'board.kicad_pcb'
        for name, data in {'board.kicad_pcb':'(kicad_pcb)', 'board.kicad_pro':'{"rules":"original"}',
                           'board.kicad_dru':'(version 1)', 'board.kicad_prl':'{"state":"original"}'}.items():
            (self.source / name).write_text(data)
        self.before = p.tree_hash(self.source)
        self.job = object.__new__(p.Job); self.job.out = self.root / 'run'; self.job.out.mkdir(); self.job.steps = []
        self.problem = None; self.mode = 'positive'
        self.job.step = self.step

    def step(self, name, argv, allowed):
        board = Path(argv[-1]); self.validated = board
        (self.job.out / (name+'.log')).write_text('fabricated stage; no native execution\n')
        result = {'name':name,'status':'success','exit_code':0,'argv':[str(x) for x in argv]}
        self.job.steps.append(result); p.save_json(self.job.out/(name+'-process.json'),result)
        if self.mode in ('prl','project','rules'):
            suffix = {'prl':'.kicad_prl','project':'.kicad_pro','rules':'.kicad_dru'}[self.mode]
            board.with_suffix(suffix).write_text('changed by controlled fake native')
        if self.mode=='saved_board':board.write_text('(kicad_pcb (refilled))')
        if self.mode=='new_prl':board.with_suffix('.kicad_prl').write_text('{"state":"new"}')
        report = {'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':board.name,
                  'violations':[],'unconnected_items':[],'schematic_parity':[],'ignored_checks':[],
                  'included_severities':['error','warning','exclusion']}
        if self.mode=='malformed': (self.job.out/(name+'.json')).write_text('{malformed')
        elif self.mode!='crash': p.save_json(self.job.out/(name+'.json'),report)
        if self.mode=='exit_mismatch':
            result['exit_code']=5; p.save_json(self.job.out/(name+'-process.json'),result)
        if self.mode in ('crash','cancel'):
            result.update(status='crashed' if self.mode=='crash' else 'cancelled',exit_code=-9)
            p.save_json(self.job.out/(name+'-process.json'),result)
            self.problem = p.Rejected('controlled native crash') if self.mode=='crash' else KeyboardInterrupt('controlled cancellation')
            raise self.problem
        return result

    def failure(self):
        record=json.loads((self.job.out/'drc-failure.json').read_text())
        binding=json.loads((self.job.out/'drc-binding.json').read_text())
        self.assertFalse(record['passed']); self.assertEqual(record['binding'],binding)
        self.assertEqual(binding['source'],str(self.board)); self.assertEqual(binding['input'],str(self.validated))
        self.assertEqual(binding['before'],self.before); self.assertEqual(record['validation_copy_before'],self.before)
        self.assertEqual(binding['after'],p.tree_hash(self.validated.parent)); self.assertIs(binding['saved'],False)
        self.assertEqual(set(record['artifacts']),{'drc.json','drc.log','drc-process.json'})
        if self.mode!='crash':self.assertIsNotNone(record['artifacts']['drc.json'])
        for name, entry in record['artifacts'].items():
            if entry is not None:self.assertEqual(entry['sha256'],p.sha(self.job.out/name))
        self.assertEqual(p.tree_hash(self.source),self.before)
        return record

    def test_unchanged_positive_keeps_binding_schema(self):
        parsed=self.job.drc('drc',self.board)
        self.assertTrue(p.native_accepted(parsed)); self.assertFalse((self.job.out/'drc-failure.json').exists())
        self.assertEqual(json.loads((self.job.out/'drc-binding.json').read_text()),
                         {'source':str(self.board),'input':str(self.validated),'before':self.before,'after':self.before,'saved':False})
        self.assertEqual(p.tree_hash(self.source),self.before)

    def test_new_prl_remains_allowed(self):
        self.board.with_suffix('.kicad_prl').unlink();self.before=p.tree_hash(self.source);self.mode='new_prl'
        self.assertTrue(p.native_accepted(self.job.drc('drc',self.board)))
        binding=json.loads((self.job.out/'drc-binding.json').read_text())
        self.assertEqual(binding['before'],self.before);self.assertEqual(set(binding['after'])-set(self.before),{'board.kicad_prl'})
        self.assertFalse((self.job.out/'drc-failure.json').exists());self.assertEqual(p.tree_hash(self.source),self.before)

    def test_parity_request_checks_the_same_preserved_full_project(self):
        self.board.with_suffix('.kicad_sch').write_text('captured schematic; fabricated native seam')
        self.before=p.tree_hash(self.source)
        self.assertTrue(p.native_accepted(self.job.drc('drc',self.board,schematic_parity=True)))
        process=json.loads((self.job.out/'drc-process.json').read_text())
        self.assertIn('--schematic-parity',process['argv'])
        self.assertEqual(self.validated.with_suffix('.kicad_sch').read_bytes(),self.board.with_suffix('.kicad_sch').read_bytes())
        self.assertEqual(p.tree_hash(self.source),self.before)

    def test_changed_copy_cannot_be_restored_by_native_to_hide_bad_input(self):
        copytree=p.shutil.copytree; native=self.job.step; calls=[]
        def changed_copy(source,target):
            value=copytree(source,target)
            (Path(target)/'board.kicad_pro').write_text('wrong rules before native')
            return value
        def restore_during_native(name,argv,allowed):
            calls.append(name)
            Path(argv[-1]).with_suffix('.kicad_pro').write_bytes(self.board.with_suffix('.kicad_pro').read_bytes())
            return native(name,argv,allowed)
        self.job.step=restore_during_native
        with patch.object(p.shutil,'copytree',side_effect=changed_copy):
            with self.assertRaisesRegex(p.Rejected,'validation copy differs before native'):self.job.drc('drc',self.board)
        self.assertEqual(calls,[])
        record=json.loads((self.job.out/'drc-failure.json').read_text())
        self.assertFalse(record['passed']);self.assertEqual(record['phase'],'input_snapshot')
        self.assertEqual(record['binding']['before'],self.before)
        self.assertNotEqual(record['validation_copy_before']['board.kicad_pro'],self.before['board.kicad_pro'])
        self.assertEqual(record['binding']['after'],record['validation_copy_before'])
        self.assertTrue(all(value is None for value in record['artifacts'].values()))
        self.assertEqual(p.tree_hash(self.source),self.before)

    def test_saved_board_remains_the_only_content_exemption(self):
        self.mode='saved_board'
        self.assertTrue(p.native_accepted(self.job.drc('drc',self.board,save=True)))
        binding=json.loads((self.job.out/'drc-binding.json').read_text())
        self.assertEqual(binding,{'source':str(self.board),'input':str(self.board),'before':self.before,'after':p.tree_hash(self.source),'saved':True})
        self.assertFalse((self.job.out/'drc-failure.json').exists())
        self.assertEqual({k:v for k,v in binding['after'].items() if k!=self.board.name},
                         {k:v for k,v in self.before.items() if k!=self.board.name})

    def test_existing_prl_change_stays_rejected_and_bound(self):
        self.mode='prl'
        with self.assertRaisesRegex(p.Rejected,'modified input or rules: board.kicad_prl'):self.job.drc('drc',self.board)
        record=self.failure(); self.assertEqual(record['phase'],'project_preservation')
        self.assertNotEqual(record['binding']['after']['board.kicad_prl'],self.before['board.kicad_prl'])

    def test_changed_rules_stay_rejected_and_bound(self):
        self.mode='rules'
        with self.assertRaisesRegex(p.Rejected,'modified input or rules: board.kicad_dru'):self.job.drc('drc',self.board)
        self.assertEqual(self.failure()['phase'],'project_preservation')

    def test_changed_project_stays_rejected_and_bound(self):
        self.mode='project'
        with self.assertRaisesRegex(p.Rejected,'modified input or rules: board.kicad_pro'):self.job.drc('drc',self.board)
        self.assertEqual(self.failure()['phase'],'project_preservation')

    def test_malformed_report_retains_exact_raw_bytes(self):
        self.mode='malformed'
        with self.assertRaises(json.JSONDecodeError):self.job.drc('drc',self.board)
        record=self.failure();self.assertEqual(record['phase'],'report_parse')
        self.assertEqual(record['error']['type'],'JSONDecodeError')
        self.assertEqual((self.job.out/'drc.json').read_text(),'{malformed')

    def test_exit_report_mismatch_remains_rejected_and_bound(self):
        self.mode='exit_mismatch'
        with self.assertRaisesRegex(p.Rejected,'exit/report mismatch'):self.job.drc('drc',self.board)
        self.assertEqual(self.failure()['phase'],'exit_report')

    def test_crash_retains_available_artifacts_and_exception(self):
        self.mode='crash'
        with self.assertRaises(p.Rejected) as caught:self.job.drc('drc',self.board)
        self.assertIs(caught.exception,self.problem)
        record=self.failure();self.assertEqual(record['phase'],'native')
        self.assertIsNone(record['artifacts']['drc.json'])
        self.assertIsNotNone(record['artifacts']['drc.log']);self.assertIsNotNone(record['artifacts']['drc-process.json'])

    def test_cancel_retains_binding_and_original_exception(self):
        self.mode='cancel'
        with self.assertRaises(KeyboardInterrupt) as caught:self.job.drc('drc',self.board)
        self.assertIs(caught.exception,self.problem);self.assertEqual(self.failure()['error']['type'],'KeyboardInterrupt')

    def test_binding_write_failure_preserves_original_failure_and_source_evidence(self):
        self.mode='prl'; save=p.save_json
        def fail(path,value):
            if Path(path).name=='drc-binding.json':raise OSError('binding write denied')
            save(path,value)
        with patch.object(p,'save_json',side_effect=fail):
            with self.assertRaisesRegex(p.Rejected,'board.kicad_prl') as caught:self.job.drc('drc',self.board)
        record=json.loads((self.job.out/'drc-failure.json').read_text())
        self.assertFalse(record['passed']);self.assertEqual(record['binding']['before'],self.before)
        self.assertIn('binding write denied',' '.join(record['capture_errors']))
        self.assertIn('binding write denied',' '.join(caught.exception.__notes__))

    def test_failure_record_write_failure_cannot_replace_original_or_pass(self):
        self.mode='prl'; save=p.save_json
        def fail(path,value):
            if Path(path).name=='drc-failure.json':raise OSError('failure write denied')
            save(path,value)
        with patch.object(p,'save_json',side_effect=fail):
            with self.assertRaisesRegex(p.Rejected,'board.kicad_prl') as caught:self.job.drc('drc',self.board)
        self.assertFalse((self.job.out/'drc-failure.json').exists())
        self.assertIn('failure write denied',' '.join(caught.exception.__notes__))
        self.assertEqual(json.loads((self.job.out/'drc-binding.json').read_text())['before'],self.before)

    def test_after_snapshot_failure_preserves_source_and_first_failure(self):
        self.mode='crash'; tree=p.tree_hash
        def capture(path):
            if Path(path)!=self.source and self.job.steps:raise p.Rejected('controlled after snapshot failure')
            return tree(path)
        with patch.object(p,'tree_hash',side_effect=capture):
            with self.assertRaises(p.Rejected) as caught:self.job.drc('drc',self.board)
        self.assertIs(caught.exception,self.problem)
        record=json.loads((self.job.out/'drc-failure.json').read_text())
        self.assertEqual(record['binding']['before'],self.before);self.assertIsNone(record['binding']['after'])
        self.assertIn('after snapshot failure',' '.join(record['capture_errors']))
        self.assertEqual(p.tree_hash(self.source),self.before)

if __name__=='__main__':unittest.main()
