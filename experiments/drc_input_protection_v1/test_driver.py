"""Tiny pure controls only; no sandbox, native, Git or network invocation."""
from pathlib import Path
import copy,errno,json,sys,tempfile,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
sys.dont_write_bytecode=True;sys.path[:0]=[str(HERE),str(ROOT)]
import driver as d,canary
from autorouter import pipeline as p,sexpr as sx

class Controls(unittest.TestCase):
    def directory(self):return tempfile.TemporaryDirectory(dir=HERE)
    def inputs(self,root):
        root.mkdir()
        for name in ('overwrite','append','truncate','unlink','rename','replace','chmod'):(root/name).write_bytes(canary.SENTINEL)
    def test_canary_requires_every_operation_denied(self):
        for bad in (None,'create','replace','rename_root','chmod'):
            with self.subTest(bad=bad),self.directory() as temp:
                out=Path(temp);folder=out/'input';self.inputs(folder)
                def deny():raise PermissionError(errno.EPERM,'owned mocked sandbox denial')
                ops=[(lambda:None) if name==bad else deny for name in canary.NAMES]
                with patch.object(canary,'attempts',return_value=ops):raw=canary.probe(folder,out/'canary.json')
                self.assertTrue((out/'canary.json').is_file())
                if bad is None:d.canary_check(raw,folder)
                else:
                    with self.assertRaises(p.Rejected):d.canary_check(raw,folder)
                raw['attempts'][0]['errno']=errno.ENOENT
                with self.assertRaises(p.Rejected):d.canary_check(raw,folder)
    def test_real_unprotected_canary_is_negative(self):
        with self.directory() as temp:
            out=Path(temp);folder=out/'input';self.inputs(folder);raw=canary.probe(folder,out/'canary.json')
            self.assertFalse(raw['passed']);self.assertTrue((out/'input-renamed').is_dir())
            with self.assertRaises(p.Rejected):d.canary_check(raw,folder)
    def test_exact_protection_and_drc_arguments(self):
        with self.directory() as temp:
            out=Path(temp);folder=out/'drc-input';folder.mkdir();argv=d.prefix(folder)
            self.assertEqual(argv[:3],['/usr/bin/sandbox-exec','-D','INPUT='+str(folder)])
            self.assertEqual(argv[3:],['-p','(version 1)(allow default)(deny network*)(deny file-write* (literal (param "INPUT")) (subpath (param "INPUT")))'])
            command=d.stage_argv(out,'drc','fixture.kicad_pcb')
            self.assertEqual(command,[str(d.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(out/'drc.json'),str(folder/'fixture.kicad_pcb')])
            self.assertNotIn('--save-board',command)
            link=out/'alias';link.symlink_to(folder,target_is_directory=True)
            with self.assertRaises(p.Rejected):d.prefix(link)
            with self.assertRaises(p.Rejected):d.stage_argv(out,'export','fixture.kicad_pcb')
    def test_fixed_actual_recipe_preserves_project_and_original(self):
        proto=d.shared.read(HERE/'PROTOCOL.json');receipt=d.shared.read(ROOT/proto['fixture_receipt']);source=Path(receipt['candidate'])
        board=source.read_bytes();project=source.with_suffix('.kicad_pro').read_bytes();before=p.sha(source)
        changed,unchanged,expected=d.fixture.prepare('missing_via',board,project)
        original=sx.parse(board.decode());negative=sx.parse(changed.decode());via=sx.children(original,'via')[0]
        self.assertEqual(unchanged,project);self.assertEqual(len(sx.children(original,'via')),1);self.assertEqual(sx.children(negative,'via'),[])
        self.assertEqual([x for x in original if x!=via],negative);self.assertEqual(p.immutable(original),p.immutable(negative))
        self.assertEqual(len(expected['adjacent_route_uuids']),2);self.assertEqual(p.sha(source),before)
        legacy=json.loads((ROOT/proto['owned_legacy_prl']).read_bytes());self.assertEqual(legacy['meta']['version'],3);self.assertIs(legacy['board']['prototype_zone_fills'],False)
        self.assertEqual([len(proto[k]) for k in ('fixture_explicit_ignored','fixture_effective_ignored','paw_explicit_ignored','paw_effective_ignored')],[5,7,5,8])
    def test_negative_requires_raw_error_pair(self):
        ignored=[];expected={'adjacent_route_uuids':['a','b']}
        row={'type':'unconnected_items','severity':'error','items':[{'uuid':'a'},{'uuid':'b'}]}
        native={'opens':1,'blocking':0,'warnings':0,'exclusions':0,'ignored_checks':ignored,'findings':[row]};raw={'unconnected_items':[row]}
        d.negative_check(raw,native,expected,ignored)
        for mutate in (lambda r,n:r.update(unconnected_items=[]),lambda r,n:r['unconnected_items'][0].update(severity='warning'),lambda r,n:r['unconnected_items'][0].update(excluded=True),lambda r,n:r['unconnected_items'][0]['items'][0].update(uuid='unrelated'),lambda r,n:n.update(blocking=1),lambda r,n:n.update(ignored_checks=[{'key':'clearance'}])):
            r=copy.deepcopy(raw);n=copy.deepcopy(native);mutate(r,n)
            with self.assertRaises(p.Rejected):d.negative_check(r,n,expected,ignored)
    def test_stage_capture_precedes_interpretation_and_detects_change(self):
        for mutation in ('report','input','added_rule'):
            with self.subTest(mutation=mutation),self.directory() as temp:
                job=d.ProtectedJob(Path(temp)/'work',lambda:30,'fixture.kicad_pcb');folder=job.out/'drc-input';folder.mkdir();(folder/'fixture.kicad_pcb').write_text('owned fake board')
                def fake(argv,**kwargs):
                    (job.out/'drc.json').write_text('{}');(job.out/'drc.log').write_text('owned fake worker')
                    return {'status':'success','exit_code':0,'cleanup_complete':True,'argv':argv,'cwd':str(job.out)}
                with patch.object(d,'run',side_effect=fake):job.step('drc',d.stage_argv(job.out,'drc',job.board_name))
                d.check_capture(job)
                if mutation=='report':(job.out/'drc.json').write_text('{"changed":true}')
                elif mutation=='input':(folder/'fixture.kicad_pcb').write_text('late change')
                else:(folder/'fixture.kicad_dru').write_text('(version 1)')
                with self.assertRaises(p.Rejected):d.check_capture(job)
                with patch.object(d,'run') as call:
                    with self.assertRaises(p.Rejected):job.step('drc',d.stage_argv(job.out,'drc',job.board_name)+['--save-board'])
                    call.assert_not_called()
    def test_shared_publication_stale_cancel_cap_no_success(self):
        for mode in ('positive','stale','cancel','cap'):
            with self.subTest(mode=mode),self.directory() as temp:
                out=Path(temp);file=out/'input';file.write_text('frozen');expected=p.sha(file)
                record={'status':'observations_complete','observations_complete':True,**{x:False for x in d.FALSE_FLAGS}}
                def stable():
                    if p.sha(file)!=expected:raise p.Rejected('input changed')
                def account():record.update({x:False for x in d.FALSE_FLAGS})
                def final_size(_):
                    if mode=='stale':file.write_text('changed during final scan')
                    if mode=='cancel':raise KeyboardInterrupt
                    return d.LIMIT+1 if mode=='cap' else 1
                with patch.object(d.shared,'size',side_effect=final_size):got=d.shared.publish(out,record,stable,account,lambda:30)
                self.assertEqual(got['observations_complete'],mode=='positive');self.assertEqual(d.shared.read(out/'summary.json')['observations_complete'],mode=='positive')
                self.assertTrue(all(got[x] is False for x in d.FALSE_FLAGS))
                self.assertEqual(bool(list(out.glob('invalidated-*'))),mode!='positive')
    def test_no_draft_or_unrequested_execution(self):
        for here,native in ((ROOT/'.runs/explicit-owned-draft',True),(ROOT/'experiments/drc_input_protection_v1',False)):
            with patch.object(d,'HERE',here),patch.object(d,'ProtectedJob') as job:
                with self.assertRaisesRegex(p.Rejected,'promote'):d.experiment(HERE/'must-not-exist',run_native=native)
                job.assert_not_called()
        self.assertFalse((HERE/'must-not-exist').exists())
if __name__=='__main__':unittest.main()
