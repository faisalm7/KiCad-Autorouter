"""Narrow fresh thermal repair inside the caller's existing routing budget.

No historical board/result/proposal lookup. Returns a job-owned trial candidate;
the caller must adopt it and produce its ordinary final native-validated receipt.
"""
from __future__ import annotations
import copy,json,math,os,shutil,stat,time,uuid
from pathlib import Path
from . import config as cfg,pipeline as p,sexpr as sx,thermal_geometry as geom


def _owned(value,root,kind='file',new=False):
    value=Path(value)
    if not value.is_absolute() or '..' in value.parts:raise p.Rejected('thermal paths must be absolute/canonical')
    try:parts=value.relative_to(root).parts;root.relative_to(cfg.ROOT)
    except ValueError:raise p.Rejected('thermal path outside caller workspace') from None
    current=cfg.ROOT
    # Authorize every component, including the supplied ownership root.
    for i,part in enumerate(value.relative_to(cfg.ROOT).parts):
        current=current/part
        try:info=os.lstat(current)
        except FileNotFoundError:
            if new and i==len(value.relative_to(cfg.ROOT).parts)-1:return value
            raise p.Rejected('thermal input missing') from None
        if stat.S_ISLNK(info.st_mode):raise p.Rejected('thermal input symlink')
        if current!=value and not stat.S_ISDIR(info.st_mode):raise p.Rejected('thermal path ancestor not directory')
    if kind=='file' and not stat.S_ISREG(info.st_mode):raise p.Rejected('thermal input not regular')
    if kind=='directory' and not stat.S_ISDIR(info.st_mode):raise p.Rejected('thermal input not directory')
    return value


def sole_thermal(native):
    """Return the one actionable error; no other critical finding can be hidden."""
    if not isinstance(native,dict) or any(type(native.get(k)) is not int for k in ('opens','blocking','warnings','exclusions')) or native.get('opens')!=0 or native.get('exclusions')!=0 or native.get('blocking')!=1:return None
    if not isinstance(native.get('findings'),list) or any(not isinstance(f,dict) for f in native['findings']):return None
    errors=[f for f in native.get('findings',[]) if f.get('severity')=='error']
    if len(errors)!=1 or errors[0].get('type')!='starved_thermal':return None
    finding=errors[0]
    items=finding.get('items')
    if not isinstance(items,list) or len(items)!=2 or any(not isinstance(i,dict) or not isinstance(i.get('uuid'),str) for i in items) or len({i['uuid'] for i in items})!=2:return None
    rest=copy.deepcopy(native);rest['blocking']=0;rest['findings']=[f for f in native['findings'] if f is not finding]
    if not p.native_accepted(rest):return None
    return finding


def _report_binding(candidate,report,binding,source_hashes,native):
    expected=dict(source_hashes);expected[candidate.name]=p.sha(candidate)
    p.verify_candidate_files(candidate,source_hashes,expected[candidate.name])
    data=json.loads(binding.read_text());native_input=_owned(data['input'],report.parent)
    if (data.get('source')!=str(candidate) or data.get('saved') is not False or data.get('before')!=expected or native_input!=report.parent/'final-drc-input'/candidate.name):raise p.Rejected('thermal native input binding mismatch')
    after=data.get('after')
    if not isinstance(after,dict) or any(after.get(k)!=v for k,v in expected.items()) or set(after)-set(expected)-{candidate.with_suffix('.kicad_prl').name}:raise p.Rejected('thermal native validation changed input/rules')
    if p.tree_hash(native_input.parent)!=after or p.parse_report(report,candidate.name)!=native:raise p.Rejected('thermal native report/input stale')
    return expected



class _SharedJob(p.Job):
    """Sequential child whose native cost is registered on the caller once."""
    def __init__(self,parent,path,remaining,native_helper):
        self.parent_job=parent;self.shared_remaining=remaining;self.native_helper=native_helper
        left=remaining()
        if left<=0:raise p.Rejected('thermal shared budget exhausted')
        super().__init__(path,left,protect_local_settings=True)
        kept={k:v for k,v in self.env.items() if not k.startswith('KICAD_') and k not in ('PYTHONPATH','PYTHONHOME')}
        for key in ('KICAD_CONFIG_HOME','KICAD_CACHE_HOME','KICAD_DOCUMENTS_HOME'):kept[key]=self.env[key]
        (self.out/'tmp').mkdir();kept.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(self.out/'tmp'));self.env=kept
    def step(self,name,argv,allowed=(0,)):
        left=self.shared_remaining()
        if left<=0:raise p.Rejected('thermal shared budget exhausted')
        self.deadline=time.monotonic()+left;before=len(self.steps)
        try:return super().step(name,['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',*argv],allowed)
        finally:self.parent_job.steps.extend(self.steps[before:])
    def native(self,name,action,board,output,*extra):
        return self.step(name,[cfg.PYTHON,'-B',self.native_helper,action,board,output,*extra])

def _audit_map(candidate, protected, mapping):
    # Explicit even if a caller's broad netclass policy omits Default-only work.
    if (mapping.get('source') != str(candidate) or mapping.get('board_sha256') != p.sha(candidate)
            or mapping.get('project_sha256') != p.sha(candidate.with_suffix('.kicad_pro'))
            or mapping.get('board_saved') is not False):
        raise p.Rejected('thermal class map not bound to final board/project')
    return p.audit_candidate_netclasses(candidate, protected, mapping)


def _publish_result(directory, result, stable, recheck_selected, remaining):
    """Never leave a canonical positive receipt after final failure/cancellation."""
    path = directory / 'repair.json'
    def invalidate(exc):
        result.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'invalidated',
                      candidate=None, candidate_sha256=None, validation_passed=False,
                      unsupported_reason=type(exc).__name__ + ': ' + str(exc))
        # Keep partial/final evidence but vacate canonical names before another
        # write, including an ordinary write exception that left .partial.
        for old in (directory/'repair.json.partial', path):
            if old.exists():old.rename(directory/('invalidated-'+uuid.uuid4().hex+'-'+old.name))
        p.save_json(path, result)
    try:
        stable();recheck_selected();p.save_json(path, result)
        stable();recheck_selected()
        if remaining() <= 0:
            raise p.Rejected('thermal shared budget exhausted during publication')
    except (Exception, KeyboardInterrupt) as exc:
        invalidate(exc)
        if isinstance(exc, KeyboardInterrupt):raise



def attempt_repair(parent_job,original_tree,candidate,source_hashes,protected_routes,native_summary,*,report_path,binding_path,remaining_seconds,out):
    """Fresh candidate/report -> geometry -> <=4 proposals -> native trial.

    remaining_seconds() returns min remaining TOTAL wall/CPU minus the caller's
    finalization reserve. Every child step is appended to parent_job.steps once.
    CPU/wall caps are cooperative here; caller's final acceptance cap is required.
    Returns candidate absolute path or null, validation_passed, trials, receipt
    paths, and explicit unsupported reason. No live-board apply or final receipt.
    """
    started=time.monotonic();result={'schema':1,'status':'not_attempted','candidate':None,'candidate_sha256':None,'validation_passed':False,'routing_accepted':False,'comparison_eligible':False,'whole_body_certificate_qualified':False,'proposal_scene_qualified':False,'scope':'one sole native thermal; two layers; round PTH target; round physical drills; saved target-zone fill unchanged','trials':[],'geometry_receipt':None,'proposal_receipt':None,'unsupported_reason':None}
    finding=sole_thermal(native_summary)
    if finding is None:result.update(status='unsupported',unsupported_reason='not one sole unexcluded thermal error with no other critical finding');return result
    def remaining():
        value=remaining_seconds()
        if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value):raise p.Rejected('invalid shared thermal budget')
        return min(value,parent_job.deadline-time.monotonic())
    watched={};watched_trees={};prepared=False;directory=None
    def stable():
        if not prepared:raise p.Rejected('thermal preparation incomplete')
        for path in watched:_owned(path,cfg.ROOT)
        for path in watched_trees:_owned(path,cfg.ROOT,kind='directory')
        if any(p.sha(path)!=digest for path,digest in watched.items()) or any(p.tree_hash(path)!=value for path,value in watched_trees.items()):raise p.Rejected('thermal source/code/current-candidate evidence changed')
        if remaining()<=0:raise p.Rejected('thermal shared budget exhausted')
    def watch(path):watched[Path(path)]=p.sha(path)
    def watchtree(path):watched_trees[Path(path)]=p.tree_hash(path)
    try:
        root=_owned(Path(parent_job.out),cfg.ROOT/'.runs',kind='directory')
        candidate=_owned(Path(candidate),root);report=_owned(Path(report_path),root);binding=_owned(Path(binding_path),root)
        output=_owned(Path(out),root,kind='directory',new=True)
        if output.exists() or report.name!='final-drc.json' or binding!=report.parent/'final-drc-binding.json':raise p.Rejected('thermal expects fresh output and standard bound final DRC')
        snapshot=_owned(root/'snapshot',root,kind='directory');source=_owned(snapshot/candidate.name,snapshot)
        if p.tree_hash(snapshot)!=source_hashes or p.preflight(source)!=original_tree:raise p.Rejected('thermal original source snapshot mismatch')
        base=sx.read(candidate)
        if p.immutable(base)!=p.immutable(original_tree) or any(r not in p.routes(base) for r in protected_routes):raise p.Rejected('thermal incumbent modified original geometry/protected route')
        expected=_report_binding(candidate,report,binding,source_hashes,native_summary)
        if remaining()<8:raise p.Rejected('less than eight seconds of shared repair budget')
        worker_job=_SharedJob(parent_job,output,remaining,output/'code/native.py');directory=worker_job.out;code=directory/'code';code.mkdir()
        # Snapshot every production Python file plus draft module files. Promoted
        # module files coincide with production files; no external script import.
        sources={q.name:q for q in (cfg.ROOT/'autorouter').glob('*.py')}
        for name in ('thermal.py','thermal_geometry.py','thermal_worker.py'):sources[name]=Path(__file__).parent/name
        for name,path in sorted(sources.items()):
            _owned(path,cfg.ROOT);watch(path);shutil.copy2(path,code/name)
            if p.sha(code/name)!=watched[path]:raise p.Rejected('thermal code snapshot mismatch')
        watchtree(code);watchtree(snapshot);watchtree(candidate.parent);watch(report);watch(binding);watchtree(report.parent/'final-drc-input')
        shutil.copytree(candidate.parent,directory/'input');shutil.copy2(report,directory/'input-drc.json');shutil.copy2(code/'thermal_worker.py',directory/'worker.py')
        p.save_json(directory/'request.json',{'schema':1,'candidate_files':expected,'final_drc_sha256':p.sha(report)})
        for path in (directory/'request.json',directory/'input-drc.json',directory/'worker.py'):watch(path)
        watchtree(directory/'input');prepared=True;stable()
        worker_job.step('thermal-geometry',[cfg.PYTHON,'-B',directory/'worker.py',directory/'input'/candidate.name,directory/'request.json',directory/'geometry.json'])
        g=json.loads((directory/'geometry.json').read_text())
        if g.get('status')!='observations_complete' or g.get('source_unchanged') is not True or g.get('board_sha256')!=expected[candidate.name] or g.get('project_sha256')!=expected[candidate.with_suffix('.kicad_pro').name] or g.get('finding')!=finding:raise p.Rejected('fresh thermal native geometry incomplete/stale')
        saved_fill=geom.fill_binding(base,g,sx);watch(directory/'geometry.json');stable()
        proposals=geom.propose(g,remaining_seconds=remaining,binding_verified=True)
        p.save_json(directory/'proposals.json',proposals);watch(directory/'proposals.json')
        result.update(geometry_receipt=str(directory/'geometry.json'),proposal_receipt=str(directory/'proposals.json'))
        if not proposals['path_certificate_candidates']:raise geom.Unsupported('bounded graph found no certified path')
        geom.verify_proposals(g,proposals,remaining_seconds=remaining);stable()
        ids=geom.uuid_index(base,sx)
        for index,proposal in enumerate(proposals['path_certificate_candidates']):
            stable()
            if remaining()<6:raise p.Rejected('thermal final trial reserve exhausted')
            trial_job=_SharedJob(parent_job,directory/('trial-%02d'%(index+1)),remaining,code/'native.py');trialdir=trial_job.out;shutil.copytree(candidate.parent,trialdir/'candidate');board=trialdir/'candidate'/candidate.name
            uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'thermal-repair:'+p.sha(candidate)+':'+p.sha(directory/'proposals.json')+':'+str(index)))
            if uid in ids:raise p.Rejected('thermal new track UUID collision')
            node=['segment',['start',*map(geom.mm,proposal['start_nm'])],['end',*map(geom.mm,proposal['end_nm'])],['width',geom.mm(proposal['width_nm'])],['layer','"'+proposal['layer']+'"'],['net',str(proposal['net_code'])],['uuid','"'+uid+'"']]
            new=copy.deepcopy(base);new.append(node);sx.write(board,new)
            trial={'id':trialdir.name,'proposal_index':index,'candidate':str(board),'validation_passed':False,'status':'created','steps':trial_job.steps};result['trials'].append(trial)
            try:
                final,native=p.validate_candidate(trial_job,original_tree,board,source_hashes,protected_routes)
                final_tree=sx.read(board)
                if p.immutable(final_tree)!=p.immutable(base) or p.routes(final_tree)!=p.routes(base)+[node]:raise p.Rejected('thermal trial changed more than one track')
                if geom.fill_binding(final_tree,g,sx)!=saved_fill:raise p.Rejected('thermal final saved fill changed; fresh saved-fill witness invalid')
                # Default-only classes also receive a fresh native map here.
                mapping_path=trialdir/'final-netclasses.json'
                if not mapping_path.exists():trial_job.native('thermal-final-netclasses','netclasses',board,mapping_path)
                mapping=json.loads(mapping_path.read_text());_audit_map(board,protected_routes,mapping)
                rows=[r for r in mapping['nets'] if r['netcode']==proposal['net_code']]
                if len(rows)!=1 or rows[0]['width_nm']!=proposal['width_nm']:raise p.Rejected('thermal fresh native width target changed')
                geom.verify_proposals(g,proposals,remaining_seconds=remaining)
                _report_binding(board,trialdir/'final-drc.json',trialdir/'final-drc-binding.json',source_hashes,native)
                warnings=lambda n:{(f['type'],tuple(sorted(i['uuid'] for i in f['items']))) for f in n['findings'] if f['severity']=='warning'}
                valid=p.native_accepted(native) and warnings(native)<=warnings(native_summary)
                stable();trial.update(status='validated' if valid else 'native_rejected',validation_passed=valid,candidate_sha256=final,native=native,native_report_sha256=p.sha(trialdir/'final-drc.json'),native_rejection_reasons=p.native_rejection_reasons(native),saved_fill_unchanged=True,pad_via_geometry_unchanged=True,final_map_sha256=p.sha(mapping_path))
                if valid:
                    p.verify_candidate_files(board,source_hashes,final)
                    result.update(status='validated_trial_candidate',candidate=str(board),candidate_sha256=final,validation_passed=True)
            except (p.Rejected,geom.Unsupported,ValueError,KeyError) as exc:trial.update(status='rejected',unsupported_reason=type(exc).__name__+': '+str(exc))
            p.save_json(trialdir/'trial.json',trial)
            if any(s.get('status')=='cancelled' for s in trial_job.steps):raise KeyboardInterrupt
            if result['validation_passed']:break
        if not result['validation_passed']:result['status']='no_validated_repair'
        stable()
    except KeyboardInterrupt:
        result.update(status='cancelled',candidate=None,candidate_sha256=None,validation_passed=False,unsupported_reason='cancelled');raise
    except (p.Rejected,geom.Unsupported,ValueError,KeyError,OSError) as exc:
        result.update(status='unsupported',candidate=None,candidate_sha256=None,validation_passed=False,unsupported_reason=type(exc).__name__+': '+str(exc))
    finally:
        result['elapsed_wall_seconds']=time.monotonic()-started
        def recheck_selected():
            if not result['validation_passed']:return
            selected=_owned(result['candidate'],directory);trialdir=selected.parent.parent
            matched=[t for t in result['trials'] if t['candidate']==str(selected)]
            if len(matched)!=1:raise p.Rejected('selected thermal trial ambiguous')
            trial=matched[0];p.verify_candidate_files(selected,source_hashes,trial['candidate_sha256'])
            report=trialdir/'final-drc.json';mapping=trialdir/'final-netclasses.json'
            if p.sha(report)!=trial['native_report_sha256'] or p.sha(mapping)!=trial['final_map_sha256'] or p.parse_report(report,selected.name)!=trial['native']:raise p.Rejected('selected thermal report/class map stale')
            _audit_map(selected,protected_routes,json.loads(mapping.read_text()))
            _report_binding(selected,report,trialdir/'final-drc-binding.json',source_hashes,trial['native'])
            if geom.fill_binding(sx.read(selected),g,sx)!=saved_fill:raise p.Rejected('selected thermal fill changed')
        if directory is not None:
            _publish_result(directory,result,stable if prepared else lambda:None,recheck_selected,remaining)
    return result
