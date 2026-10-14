"""Actual native positive/disconnected controls for immutable copied PRL bytes."""
from pathlib import Path
import argparse
import copy
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,sexpr as sx
from experiments.original_project_native_v1.local_settings import preserve


def experiment(out):
    if out.parent!=ROOT/'.runs' or out.exists() or out.is_symlink():raise p.Rejected('fresh direct controls output required')
    out.mkdir();started=time.monotonic();cpu=time.process_time()+f.child_cpu();tools=p.tool_manifest()
    receipt=f.read_json(ROOT/'.runs/installation-025/result.json')['native_receipt']['path']
    valid=f.read_json(Path(receipt));board=Path(valid['candidate'])
    p.verify_candidate_files(board,valid['source_hashes'],valid['candidate_sha256'])
    prl=ROOT/'.data/audio-player-my1690x-demo-001/project/Hardware/SparkFun_Audio_Player_Breakout_MY1690X-16S.kicad_prl'
    original_bytes=prl.read_bytes();rows=[]
    def remaining():return min(90-(time.monotonic()-started),90-(time.process_time()+f.child_cpu()-cpu))
    for name in ('positive','disconnected'):
        case=out/name;case.mkdir();candidate=case/'input'/board.name;shutil.copytree(board.parent,candidate.parent)
        local=candidate.with_suffix('.kicad_prl');local.write_bytes(original_bytes)
        tree=sx.read(candidate)
        if name=='disconnected':tree.remove(p.routes(tree)[0]);sx.write(candidate,tree)
        before=p.tree_hash(candidate.parent);owner={};h.capture_destination(owner,case)
        class GuardedJob(f.FloorJob):
            def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
                protection=None
                try:
                    if [str(x) for x in argv[:3]]==[str(p.c.CLI),'pcb','drc']:
                        with preserve(Path(argv[-1]).with_suffix('.kicad_prl'),case,owner,
                                cleanup_complete=lambda:bool(self.steps and self.steps[-1].get('cleanup_complete') is True)) as protection:
                            return super().step(name,argv,allowed,already_sandboxed=already_sandboxed)
                    return super().step(name,argv,allowed,already_sandboxed=already_sandboxed)
                except (Exception,KeyboardInterrupt) as exc:
                    if protection is not None:protection['guard_error']=type(exc).__name__+': '+str(exc)
                    raise
                finally:
                    if protection is not None and self.steps and self.steps[-1].get('name')==name:
                        self.steps[-1]['local_settings_protection']=protection
                        p.save_json(self.out/(name+'-process.json'),self.steps[-1])
        job=GuardedJob(case/'job',30,lambda:min(30,remaining()))
        entry={'case':name,'expected_native_accepted':name=='positive','passed':False,
               'before':before,'candidate':str(candidate),'prl_sha256':p.sha(prl)}
        try:
            digest,native=p.validate_candidate(job,tree,candidate,before,[])
            refill=job.out/'refill'/candidate.name
            saved=f.check_drc_stage(job.out,{'steps':job.steps},'refill-drc',refill,refill,True,before)
            checked=f.check_drc_stage(job.out,{'steps':job.steps},'final-drc',candidate,job.out/'final-drc-input'/candidate.name,False,{**before,candidate.name:digest})
            rebuilt=p.transplant_fill(tree,sx.read(refill))
            if (checked!=native or candidate.read_bytes()!=(sx.dump(rebuilt)+'\n').encode()
                    or p.immutable(sx.read(candidate))!=p.immutable(tree)):
                raise p.Rejected('native original-shell/report provenance differs')
            protections=[x['local_settings_protection']for x in job.steps if 'local_settings_protection'in x]
            if len(protections)!=2 or any(x.get('bytes_unchanged')is not True or x.get('flags_restored')is not True for x in protections):raise p.Rejected('native PRL protection incomplete')
            entry.update(native=native,saved_native=saved,protection=protections,candidate_sha256=digest,report_sha256=p.sha(job.out/'final-drc.json'),
                passed=p.native_accepted(native)==entry['expected_native_accepted'] and local.read_bytes()==original_bytes,
                steps=job.steps)
        except (Exception,KeyboardInterrupt) as exc:
            entry.update(error=type(exc).__name__+': '+str(exc),steps=job.steps)
        p.save_json(case/'result.json',entry);rows.append(entry)
        if not entry['passed']:break
    record={'schema':1,'accepted':False,'production_admitted':False,'controls_passed':len(rows)==2 and all(x['passed']for x in rows),
            'cases':rows,'tools':tools,'valid_owned_fixture_candidate_sha256':valid['candidate_sha256'],
            'original_public_prl_sha256':p.sha(prl),'source_still_exact':prl.read_bytes()==original_bytes,
            'wall_seconds':time.monotonic()-started,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu,
            'scope':'Owned synthetic validation fixture, not new family/benchmark. Only copiedlocalPRL replaced with exactoldSchemaAudioPRL before eachcontrol, then immutable during eachactualNative invocation. Existing saved-refill/original-shell/freshfinal sharedpipeline preserves exactoriginalgeometry. EveryPRL hash unchanged, flagsrestored afterchildcleanup; deliberate one-route deletion is negative only. No fieldwaiver, actualAudioadmission, productionchange or routing gain.'}
    if p.tool_manifest()!=tools:record['controls_passed']=False
    p.save_json(out/'result.json',record);return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    if not a.run_native:parser.error('explicit native execution required')
    result=experiment(a.output);print({k:result[k]for k in ('controls_passed','wall_seconds','full_cpu_seconds')});raise SystemExit(0 if result['controls_passed']else 2)
