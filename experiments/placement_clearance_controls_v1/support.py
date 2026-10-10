"""Exact reused bounded-job, raw-DRC and publication guards; no import-time work."""
import resource
import time
import uuid
from pathlib import Path
from autorouter import pipeline as p,config as c,floor_route as f
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'toolchain.lock.json').is_file())

def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime

def owned(path,*,exists=True):
    path=Path(path).absolute()
    if '..' in path.parts or not path.is_relative_to(ROOT) or any(x.is_symlink() for x in (path,*path.parents)):
        raise p.Rejected('path must be a real path inside this checkout')
    if exists and not path.exists():raise p.Rejected('missing owned input')
    return path

class SharedJob(f.FloorJob):
    def __init__(self,out,remaining,steps):
        available=remaining()
        if available<=0:raise p.Rejected('shared diagnostic budget exhausted')
        self.all_steps=steps
        super().__init__(out,available,remaining)
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        before=len(self.steps)
        try:return super().step(name,argv,allowed,already_sandboxed=already_sandboxed)
        finally:
            self.all_steps.extend(self.steps[before:])
            if any(x.get('status')=='cancelled' for x in self.steps[before:]):raise KeyboardInterrupt

def check_drc(job,name,board,native):
    """Bind actual raw report/process/copied native input to an exact candidate."""
    before=p.tree_hash(board.parent);path=job.out/(name+'-binding.json');binding=f.read_json(path)
    copied=job.out/(name+'-input')/board.name
    if binding.get('source')!=str(board) or binding.get('input')!=str(copied) or binding.get('saved') is not False or binding.get('before')!=before:
        raise p.Rejected('native candidate binding differs')
    after=binding.get('after')
    if not isinstance(after,dict) or any(after.get(k)!=v for k,v in before.items()) or set(after)-set(before)-{board.with_suffix('.kicad_prl').name}:
        raise p.Rejected('native copy/rules changed')
    if p.tree_hash(copied.parent)!=after or p.parse_report(job.out/(name+'.json'),board.name)!=native:
        raise p.Rejected('raw native report/input mismatch')
    expected=[*f.SANDBOX,str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones',
              '--exit-code-violations','--output',str(job.out/(name+'.json')),str(copied)]
    f.process_check(job.out,{'steps':job.steps},name,expected,allowed=(5 if native['findings'] else 0,))
    step=next(x for x in job.steps if x['name']==name)
    if step.get('validated_input_sha256')!=p.sha(board)or step.get('emitted_candidate')!=str(board):
        raise p.Rejected('final native step/candidate binding differs')
    return {'candidate_sha256':p.sha(board),'native_report_sha256':p.sha(job.out/(name+'.json')),'native_binding_sha256':p.sha(path),'input_hashes':after}

def publish(out,record,stable,account):
    """Never retain a canonical positive after failed final validation/write."""
    def archive():
        for path in (out/'summary.json',out/'summary.json.partial'):
            if path.exists():path.rename(out/('invalidated-'+uuid.uuid4().hex+'-'+path.name))
    try:
        stable();account()
        if not record['within_budget']:raise p.Rejected('shared budget exceeded before publication')
        expected=f.canonical(record)
        p.save_json(out/'summary.json',record)
        if f.canonical(f.read_json(out/'summary.json'))!=expected:raise p.Rejected('summary changed during write')
        stable();account()
        if f.canonical(f.read_json(out/'summary.json'))!=expected:raise p.Rejected('summary changed during final check')
        if not record['within_budget']:raise p.Rejected('shared budget exceeded during publication')
        account()
        if not record['within_budget']:raise p.Rejected('shared budget exceeded after final readback')
    except (Exception,KeyboardInterrupt) as exc:
        archive();record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',controls_passed=False,
                                error=type(exc).__name__+': '+str(exc))
        account()
        try:p.save_json(out/'summary.json',record)
        except (Exception,KeyboardInterrupt):archive()
    return record
