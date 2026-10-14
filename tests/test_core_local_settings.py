"""Owned-file/metadata/controller controls only; no Native acceptance proof."""
import copy,json,os,stat,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,floor_route as f,local_settings as ls
from experiments.original_project_native_v1.local_settings import preserve as experimental

@unittest.skipUnless(sys.platform=='darwin' and hasattr(os,'chflags'),'actual Mac flags required')
class CoreLocalSettingsControls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='core-prl-owned-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.source=self.root/'source';self.source.mkdir()
        self.board=self.source/'board.kicad_pcb';self.board.write_text('(kicad_pcb)\n')
        self.prl=self.board.with_suffix('.kicad_prl');self.prl.write_bytes(b'{"old_schema":"retain exact bytes"}\n')
        self.original=p.tree_hash(self.source)
    def job(self,name='job'):
        return p.Job(self.root/name,30,protect_local_settings=True)
    def staged_worker(self,job,cleanup=True,fail=False):
        # Authored process/report seam, no Native executable or routing claim.
        def step(name,argv,allowed):
            board=Path(argv[-1]);prl=board.with_suffix('.kicad_prl')
            if prl.exists():
                self.assertEqual(prl.stat().st_flags,stat.UF_IMMUTABLE)
                with self.assertRaises(PermissionError):prl.write_bytes(b'forbidden rewrite')
            result={'name':name,'cwd':str(job.out),'argv':[str(x) for x in argv],
                    'status':'timeout' if fail else 'success','exit_code':-15 if fail else 0,'cleanup_complete':cleanup}
            job.steps.append(result);p.save_json(job.out/(name+'-process.json'),result)
            if fail:raise p.Rejected('authored worker failure; no Native launched')
            report={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':board.name,
                    'violations':[],'unconnected_items':[],'schematic_parity':[],'ignored_checks':[],
                    'included_severities':['error','warning','exclusion']}
            p.save_json(job.out/(name+'.json'),report);return result
        return step
    def test_opt_in_clones_only_owned_input_and_retains_guard_binding(self):
        job=self.job();job.step=self.staged_worker(job);job.drc('drc',self.board)
        binding=f.read_json(job.out/'drc-binding.json');process=f.read_json(job.out/'drc-process.json')
        self.assertEqual(p.tree_hash(self.source),self.original);self.assertEqual(self.prl.stat().st_flags,0)
        self.assertEqual(binding['local_settings_policy'],ls.JOB_POLICY)
        self.assertEqual(Path(binding['input']).parent,job.out/'drc-input')
        ls.check_event(job.out,binding,process)
        self.assertTrue(process['local_settings_protection']['flags_restored'])
        self.assertEqual(process['local_settings_protection']['sha256'],self.original[self.prl.name])
    def test_external_saved_source_and_symlink_output_refuse_before_worker_or_flag(self):
        job=self.job();job.step=lambda *a,**k:self.fail('external saved source reached worker')
        with self.assertRaisesRegex(p.Rejected,'must belong to Job root'):job.drc('drc',self.board,save=True)
        self.assertEqual(self.prl.stat().st_flags,0);self.assertEqual(p.tree_hash(self.source),self.original)
        link=self.root/'alias';link.symlink_to(self.source,target_is_directory=True)
        with self.assertRaisesRegex(p.Rejected,'canonical'):p.Job(link/'run',30,protect_local_settings=True)
        self.assertFalse((self.source/'run').exists())
        with self.assertRaises(p.Rejected):
            with experimental(self.prl,self.source,job._local_settings_owner):pass
    def test_unknown_cleanup_keeps_owned_copy_immutable_and_journals_both_failures(self):
        job=self.job();job.step=self.staged_worker(job,cleanup=False,fail=True)
        copied=job.out/'drc-input'/self.prl.name
        try:
            with self.assertRaisesRegex(p.Rejected,'cleanup not confirmed'):job.drc('drc',self.board)
            process=f.read_json(job.out/'drc-process.json');event=process['local_settings_protection']
            self.assertFalse(process['cleanup_complete']);self.assertFalse(event['flags_restored'])
            self.assertIn('authored worker failure',event['native_error']);self.assertIn('cleanup not confirmed',event['guard_error'])
            self.assertEqual(copied.stat().st_flags,stat.UF_IMMUTABLE)
            failure=f.read_json(job.out/'drc-failure.json');self.assertFalse(failure['passed']);self.assertEqual(failure['binding']['local_settings_policy'],ls.JOB_POLICY)
            self.assertEqual(p.tree_hash(self.source),self.original);self.assertEqual(self.prl.stat().st_flags,0)
        finally:
            if copied.exists() and copied.stat().st_flags:os.chflags(copied,0,follow_symlinks=False)
    def test_absent_prl_does_not_waive_unknown_worker_cleanup(self):
        self.prl.unlink();job=self.job();job.step=self.staged_worker(job,cleanup=False)
        with self.assertRaisesRegex(p.Rejected,'cleanup not confirmed'):job.drc('drc',self.board)
        process=f.read_json(job.out/'drc-process.json');self.assertFalse(process['cleanup_complete'])
        self.assertFalse(process['local_settings_protection']['present']);self.assertTrue((job.out/'drc-failure.json').exists())
    def test_marked_event_cannot_drop_marker_rebind_path_or_weaken_flags(self):
        job=self.job();job.step=self.staged_worker(job);job.drc('drc',self.board)
        binding=f.read_json(job.out/'drc-binding.json');process=f.read_json(job.out/'drc-process.json')
        for mutation in ('binding_marker','process_marker','event','path','hash','restored','typed_boolean','cleanup'):
            with self.subTest(mutation=mutation):
                b,s=copy.deepcopy(binding),copy.deepcopy(process)
                if mutation=='binding_marker':b.pop('local_settings_policy')
                elif mutation=='process_marker':s.pop('local_settings_policy')
                elif mutation=='event':s.pop('local_settings_protection')
                elif mutation=='path':s['local_settings_protection']['path']=str(self.prl)
                elif mutation=='hash':s['local_settings_protection']['sha256']='0'*64
                elif mutation=='restored':s['local_settings_protection']['flags_restored']=False
                elif mutation=='typed_boolean':s['local_settings_protection']['present']=1
                else:s['cleanup_complete']=False
                with self.assertRaises(p.Rejected):ls.check_event(job.out,b,s)
        # Existing unmarked experimental/legacy receipts keep their old reader.
        ls.check_event(job.out,{}, {'local_settings_protection':{'legacy':'not core-owned'}})
    def test_replaced_root_hardlink_preflag_and_nested_guard_refuse(self):
        job=self.job();owned=job.out/'copied.kicad_prl';owned.write_bytes(self.prl.read_bytes());owner=job._local_settings_owner
        hardlink=job.out/'other.kicad_prl';os.link(owned,hardlink)
        with self.assertRaisesRegex(p.Rejected,'exclusive'):
            with ls.preserve(owned,job.out,owner):pass
        hardlink.unlink()
        with ls.preserve(owned,job.out,owner):
            with self.assertRaisesRegex(p.Rejected,'unflagged'):
                with ls.preserve(owned,job.out,owner):pass
        moved=job.out.with_name('moved');job.out.rename(moved);job.out.mkdir();replacement=job.out/owned.name;replacement.write_bytes(b'unrelated')
        with self.assertRaisesRegex(p.Rejected,'replaced'):
            with ls.preserve(replacement,job.out,owner):pass
        self.assertEqual(replacement.stat().st_flags,0)
    def test_floor_passthrough_is_explicit_and_default_remains_disabled(self):
        default=p.Job(self.root/'default',30);self.assertFalse(default.protect_local_settings)
        job=f.FloorJob(self.root/'floor',30,lambda:30,protect_local_settings=True);self.assertTrue(job.protect_local_settings)
        self.assertEqual(job._local_settings_owner['destination'],job.out)

if __name__=='__main__':unittest.main()
