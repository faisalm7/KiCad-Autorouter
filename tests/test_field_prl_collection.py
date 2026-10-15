"""Field commands share one owned PRL guard; no Native correctness claim."""
from contextlib import contextmanager
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,schematic_field_evidence as fields,local_settings as local

class FieldCollectionGuard(unittest.TestCase):
    def scene(self):
        from autorouter import config as c
        (c.ROOT/'.cache').mkdir(exist_ok=True)
        temp=tempfile.TemporaryDirectory(dir=c.ROOT/'.cache');self.addCleanup(temp.cleanup)
        root=Path(temp.name).resolve();job=p.Job(root/'job',30,protect_local_settings=True)
        project=job.out/'candidate';project.mkdir();board=project/'owned.kicad_pcb';board.write_text('owned temporary data; never loaded by Native')
        board.with_suffix('.kicad_prl').write_text('original owned local settings')
        return job,board
    def test_both_actual_field_argument_lists_execute_inside_one_guard_and_bind_both_journals(self):
        job,board=self.scene();state={'frozen':False,'calls':0,'complete':None}
        event={'owned':'synthetic guard event only'}
        @contextmanager
        def guard(path,root,owner,*,cleanup_complete):
            self.assertEqual(path,board.with_suffix('.kicad_prl'));self.assertEqual(root,job.out)
            state.update(frozen=True,calls=state['calls']+1)
            try:yield event
            finally:state.update(frozen=False,complete=cleanup_complete())
        def step(name,argv):
            self.assertTrue(state['frozen'])
            row=dict(name=name,cwd=str(job.out),argv=argv,status='success',exit_code=0,cleanup_complete=True,log_truncated=False)
            job.steps.append(row);p.save_json(job.out/(name+'-process.json'),row)
        with patch.object(local,'preserve',side_effect=guard),patch.object(job,'step',side_effect=step),patch.object(fields,'derive',return_value={'synthetic':'test only'}):
            fields.collect(job,'final',board,{})
        self.assertEqual(state,{'frozen':False,'calls':1,'complete':True})
        receipt=json.loads(fields.local_settings_path(job.out,'final').read_text())
        self.assertEqual(receipt['before'],receipt['after']);self.assertEqual(receipt['protection'],event)
        self.assertEqual(receipt['processes_sha256'],{name:p.sha(job.out/(name+'-process.json')) for name in fields.names('final')})
        self.assertEqual([row['argv'] for row in job.steps],list(fields.arguments(job.out,'final',board)))
    def test_failed_first_child_exposes_cleanup_state_and_never_emits_positive_field_proof(self):
        job,board=self.scene();seen=[]
        @contextmanager
        def guard(*args,cleanup_complete,**kwargs):
            try:yield {'synthetic':'event'}
            finally:seen.append(cleanup_complete())
        def step(name,argv):
            job.steps.append(dict(name=name,cleanup_complete=False));raise p.Rejected('controlled failed child')
        with patch.object(local,'preserve',side_effect=guard),patch.object(job,'step',side_effect=step),self.assertRaisesRegex(p.Rejected,'controlled failed child'):
            fields.collect(job,'final',board,{})
        self.assertEqual(seen,[False]);self.assertFalse(fields.paths(job.out,'final')[2].exists())
    def test_missing_second_journal_cannot_reuse_first_child_cleanup(self):
        job,board=self.scene();seen=[]
        @contextmanager
        def guard(*args,cleanup_complete,**kwargs):
            try:yield {'synthetic':'event'}
            finally:seen.append(cleanup_complete())
        def step(name,argv):
            if job.steps:raise p.Rejected('controlled second journal absent')
            job.steps.append(dict(name=name,cleanup_complete=True))
        with patch.object(local,'preserve',side_effect=guard),patch.object(job,'step',side_effect=step),self.assertRaisesRegex(p.Rejected,'second journal absent'):
            fields.collect(job,'final',board,{})
        self.assertEqual(seen,[False]);self.assertFalse(fields.paths(job.out,'final')[2].exists())
    def test_project_drift_still_refuses_and_does_not_emit_proof_or_success_guard(self):
        job,board=self.scene()
        @contextmanager
        def guard(*args,**kwargs):yield {'synthetic':'event'}
        def step(name,argv):
            job.steps.append(dict(name=name,cleanup_complete=True));board.with_suffix('.kicad_prl').write_text('controlled drift')
        with patch.object(local,'preserve',side_effect=guard),patch.object(job,'step',side_effect=step),self.assertRaisesRegex(p.Rejected,'changed DRC project'):
            fields.collect(job,'final',board,{})
        self.assertFalse(fields.paths(job.out,'final')[2].exists());self.assertFalse(fields.local_settings_path(job.out,'final').exists())

if __name__=='__main__':unittest.main()
