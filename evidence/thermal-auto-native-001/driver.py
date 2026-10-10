#!/usr/bin/env python3
"""Generated thermal repair-only diagnostic; native execution requires --validate.

Immutable original inputs; <=4 single-track copies; 60s wall/measured CPU cap.
No accepted routing receipt, comparison score, whole-body qualification or apply.
"""
import argparse,copy,fcntl,hashlib,importlib,json,math,os,resource,shutil,signal,stat,sys,time,uuid
from decimal import Decimal
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
DRAFT=ROOT/'.runs/thermal-auto-control-draft-001'
BUDGET=60.
HELPERS=('copper_path.py','diagnose.py','attempt_paths_v2.py','attempt_graph_v3.py')
class Invalid(ValueError):pass

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def observed_cpu():
    parent=resource.getrusage(resource.RUSAGE_SELF);children=resource.getrusage(resource.RUSAGE_CHILDREN)
    return parent.ru_utime+parent.ru_stime+children.ru_utime+children.ru_stime
def require(value,allowed,kind='file',new=False):
    raw=Path(value)
    if '..' in raw.parts:raise Invalid('parent traversal')
    path=raw if raw.is_absolute() else ROOT/raw
    try:relative=path.relative_to(ROOT);path.relative_to(allowed)
    except ValueError:raise Invalid('path outside allowed local subtree') from None
    current=ROOT;info=os.lstat(current)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):raise Invalid('non-directory/symlink checkout')
    for i,part in enumerate(relative.parts):
        current=current/part
        try:info=os.lstat(current)
        except FileNotFoundError:
            if new and i==len(relative.parts)-1:return path
            raise Invalid('missing input path') from None
        if stat.S_ISLNK(info.st_mode):raise Invalid('symlink in authorized path')
        if i<len(relative.parts)-1 and not stat.S_ISDIR(info.st_mode):raise Invalid('non-directory path ancestor')
    if kind=='file' and not stat.S_ISREG(info.st_mode):raise Invalid('nonregular file')
    if kind=='directory' and not stat.S_ISDIR(info.st_mode):raise Invalid('not directory')
    return path

def strict_inventory(directory):
    require(directory,ROOT,kind='directory');result={};total=0
    for q in sorted(directory.rglob('*')):
        info=os.lstat(q)
        if stat.S_ISDIR(info.st_mode):continue
        require(q,directory);total+=info.st_size
        if total>100*1024**2 or len(result)>=2000:raise Invalid('snapshot inventory cap')
        result[str(q.relative_to(directory))]=digest(q)
    return result

def load_json(path):
    require(path,ROOT)
    if path.stat().st_size>10*1024**2:raise Invalid('JSON exceeds bound')
    return json.loads(path.read_text())

def strict_dimensions(g):
    if type(g.get('native_max_error_nm')) is not int or g['native_max_error_nm']<=0:raise Invalid('nonpositive/malformed maximum error')
    for pad in g['pads']:
        h=pad['effective_hole'];w=h['width_nm'];size=pad['drill_size_nm']
        if type(w) is not int or w<0 or len(size)!=2 or any(type(x) is not int or x<0 for x in size):raise Invalid('negative/malformed pad hole dimension')
        if w==0:
            if size!=[0,0] or pad['is_pth']:raise Invalid('zero hole inconsistent with native pad')
        elif (pad['drill_is_round'] is not True or size!=[w,w] or h['start_nm']!=h['end_nm']):raise Invalid('positive physical pad hole is not exact round disk')
    for via in g['vias']:
        if type(via['drill_nm']) is not int or via['drill_nm']<=0:raise Invalid('nonpositive/malformed via hole')

def verify_proposals(g,receipt,modules):
    cp,dg,vg=(modules[k] for k in ('copper_path','diagnose','attempt_graph_v3'))
    strict_dimensions(g)
    guard=cp.Guard(seconds=8,operations=12000000)
    bodies,holes,target,terms,angle,width,margin=vg.audit_observations(g,guard)
    proposals=receipt.get('path_certificate_candidates')
    if receipt.get('status')!='diagnostic_path_candidates_found' or not isinstance(proposals,list) or not 1<=len(proposals)<=4:raise Invalid('bounded generated proposals unavailable')
    layer=g['layers'][0]['canonical'];byindex={b['native_outline_index']:b for b in bodies}
    terminals={tuple(p['terminal']):[] for p in terms}
    for term in terms:terminals[tuple(term['terminal'])].append(term)
    proofs=[]
    for proposal in proposals:
        if (proposal.get('net_code')!=g['net_code'] or proposal.get('layer')!=layer or proposal.get('width_nm')!=width or proposal.get('copper_path_margin_nm')!=margin or proposal.get('target_logical_terminal')!=target['terminal']):raise Invalid('proposal target/net/layer/width/margin mismatch')
        other=tuple(proposal['other_logical_terminal'])
        if other==tuple(target['terminal']) or len(terminals.get(other,[]))!=1:raise Invalid('destination logical terminal ambiguous/identical')
        start,end=proposal['start_nm'],proposal['end_nm']
        if not cp.valid_point(start) or not cp.valid_point(end) or not width/2<math.dist(start,end)<=8*width:raise Invalid('bridge geometry outside declared bounds')
        indexes=[proposal['source_outline_index'],proposal['destination_outline_index']]
        if indexes[0]==indexes[1] or any(i not in byindex for i in indexes):raise Invalid('distinct selected body identities required')
        for label,anchor,pad,index in [('source',start,target,indexes[0]),('destination',end,terminals[other][0],indexes[1])]:
            path=proposal[label+'_copper_path_nm'];poly=byindex[index]['outer_nm']
            if not isinstance(path,list) or not 1<=len(path)<=64 or path[0]!=anchor or not all(cp.valid_point(p) for p in path):raise Invalid('path endpoints/schema invalid')
            if not cp.annular(path[-1],pad,margin):raise Invalid('path does not end in strict independent annulus')
            legs=list(zip(path,path[1:])) or [(path[0],path[0])]
            if any(not cp.certified_leg(a,b,poly,holes,margin,guard) for a,b in legs):raise Invalid('saved copper path does not meet boundary/drill certificate')
        if not vg.bridge_clear(start,end,holes,margin,guard):raise Invalid('bridge centerline intersects physical hole/margin')
        proofs.append({'source_outline':indexes[0],'destination_outline':indexes[1],'other_terminal':list(other),'margin_nm':margin,'physical_holes_checked':len(holes),'passed':True})
    guard.charge()
    return proofs

def uuid_index(tree,sx):
    owners={}
    def walk(node):
        if not isinstance(node,list) or not node:return
        field=sx.one(node,'uuid')
        if field is not None:
            if len(field)!=2 or not isinstance(field[1],str):raise Invalid('malformed candidate UUID')
            owners.setdefault(sx.unquote(field[1]),[]).append(node)
        for child in node[1:]:walk(child)
    walk(tree)
    # Native dimensions and their nested display text may share one UUID.
    # Preserve those immutable objects; require uniqueness of referenced copper.
    return owners

def nm(atom):
    v=Decimal(atom)*1000000
    if not v.is_finite() or v!=v.to_integral_value():raise Invalid('noninteger native coordinate')
    return int(v)
def mm(value):
    if type(value) is not int:raise Invalid('noninteger track coordinate')
    return format(Decimal(value)/1000000,'f')

def fill_binding(tree,g,sx):
    items=uuid_index(tree,sx);zones=items.get(g['zone_uuid'],[]);targets=items.get(g['target_pad_uuid'],[])
    if len(zones)!=1 or zones[0][0]!='zone' or len(targets)!=1 or targets[0][0]!='pad':raise Invalid('native finding UUID not typed/unique in board')
    zone,target=zones[0],targets[0]
    layer=g['layers'][0]['canonical']
    if sx.one(zone,'net')!=['net',str(g['net_code'])] or sx.one(zone,'layer')!=['layer','"'+layer+'"']:raise Invalid('saved zone net/layer differs from native observation')
    saved=sx.children(zone,'filled_polygon')
    native=[b for b in g['bodies'] if b['layer_id']==g['layers'][0]['id']]
    if len(saved)!=len(native):raise Invalid('saved/native filled-body count differs')
    for b in native:
        index=b['native_outline_index']
        if type(index) is not int or not 0<=index<len(saved):raise Invalid('native outline index outside saved fill')
        poly=saved[index]
        if sx.one(poly,'layer')!=['layer','"'+layer+'"'] or b['hole_count'] or b['holes_nm']:raise Invalid('unsupported explicit filled hole or layer mismatch')
        points=sx.one(poly,'pts')
        if points is None or any(p[0]!='xy' or len(p)!=3 for p in points[1:]):raise Invalid('unsupported filled contour atoms')
        actual=[[nm(p[1]),nm(p[2])] for p in points[1:]]
        if actual!=b['outer_nm']:raise Invalid('saved/native fill vertices differ')
    return saved


def publish_summary(summary,out,totals,verify,save):
    """Final publication remains cancellable, including after a positive write."""
    def preserve_partial():
        partial=out/'summary.json.partial'
        if partial.exists():
            require(partial,out)
            with (out/'cancelled-summary.partial').open('xb') as kept:kept.write(partial.read_bytes())
            partial.unlink()
    def account():
        summary['wall_seconds'],summary['total_cpu_seconds']=totals()
        if any(not math.isfinite(v) or v<0 or v>BUDGET for v in (summary['wall_seconds'],summary['total_cpu_seconds'])):
            summary.update(status='budget_exceeded',validation_passed=False,selected=None)
    try:
        if summary['status']=='cancelled':preserve_partial()
        verify();account();save(out/'summary.json',summary)
        # Recheck selected final files and sources after publishing, then charge
        # the verification and publication work to the same diagnostic budget.
        verify();account()
        if not summary['validation_passed'] and summary.get('selected') is not None:summary['selected']=None
        save(out/'summary.json',summary)
        if min(BUDGET-v for v in totals())<0:
            account();summary.update(status='budget_exceeded',validation_passed=False,selected=None);save(out/'summary.json',summary)
    except KeyboardInterrupt:
        preserve_partial();summary.update(status='cancelled',validation_passed=False,selected=None)
        summary['wall_seconds'],summary['total_cpu_seconds']=totals();save(out/'summary.json',summary)
    except Exception as exc:
        preserve_partial();summary.update(status='invalidated',validation_passed=False,selected=None,original_inputs_unchanged=False,publication_reason=type(exc).__name__+': '+str(exc))
        summary['wall_seconds'],summary['total_cpu_seconds']=totals();save(out/'summary.json',summary)

def main(args):
    started=time.monotonic();cpu_started=observed_cpu();jobs=[]
    out=require(args.output,DRAFT,kind='directory',new=True)
    if out.parent!=DRAFT or out.exists():raise Invalid('output must be a fresh direct child of draft')
    receipt_path=require(args.receipt,ROOT/'.runs');proposal_path=require(args.proposals,ROOT/'.runs');export_path=require(args.export_summary,ROOT/'.runs')
    if receipt_path.name!='result.json' or export_path.name!='summary.json':raise Invalid('expected retained result and export summary')
    # Capture source bytes before importing current production code.
    current_code={str(q.relative_to(ROOT)):digest(require(q,ROOT/'autorouter')) for q in sorted((ROOT/'autorouter').glob('*.py'))}
    sys.path.insert(0,str(ROOT));from autorouter import pipeline as p,config as cfg,sexpr as sx
    class DiagnosticJob(p.Job):
        def step(self,name,argv,allowed=(0,)):
            remaining=budget_remaining()
            if remaining<=2:raise p.Rejected('diagnostic total budget reserve reached')
            self.deadline=time.monotonic()+remaining-1
            return super().step(name,['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',*argv],allowed)
        def native(self,name,action,board,output,*extra):
            return self.step(name,[cfg.PYTHON,'-B',out/'code/autorouter/native.py',action,board,output,*extra])
    def totals():
        # Includes waited metadata/git subprocesses as well as native children.
        # Child descendants count only where accumulated by the child wait.
        return time.monotonic()-started,observed_cpu()-cpu_started
    def budget_remaining():
        wall,cpu=totals();return min(BUDGET-wall,BUDGET-cpu)
    out.mkdir();summary={'schema':1,'status':'not_prepared','native_executed':False,'validation_passed':False,'routing_accepted':False,'comparison_eligible':False,'applied':False,'whole_body_certificate_qualified':False,'proposal_scene_qualified':False,'physical_electrical_validation':False,'wall_budget_seconds':BUDGET,'cpu_budget_seconds':BUDGET,'cost_scope':'repair only; excludes failed incumbent acquisition and prior exporter/proposal research','trials':[],'original_inputs_unchanged':None}
    watched={};trees={};prepared=False;tools=None
    def watch(path):
        path=require(path,ROOT);watched[str(path)]=digest(path);return path
    def watch_tree(path):
        path=require(path,ROOT,kind='directory');trees[str(path)]=strict_inventory(path);return trees[str(path)]
    def stable():
        if not prepared:raise Invalid('no stability claim before complete preparation')
        for name in watched:require(name,ROOT)
        for name in trees:require(name,ROOT,kind='directory')
        if any(digest(name)!=value for name,value in watched.items()):raise Invalid('watched evidence/helper bytes changed')
        if any(strict_inventory(Path(name))!=value for name,value in trees.items()):raise Invalid('source/candidate/snapshot/native input changed')
        if p.tool_manifest()!=tools:raise Invalid('tool/code/HEAD freeze changed')
    try:
        receipt=load_json(watch(receipt_path));proposal_receipt=load_json(watch(proposal_path));export=load_json(watch(export_path));base=receipt_path.parent;exportdir=export_path.parent;qual=proposal_path.parent
        source=require(receipt['source'],ROOT/'.data/boards');candidate=require(receipt['candidate'],base/'candidate')
        if source.suffix!='.kicad_pcb' or candidate!=base/'candidate'/source.name:raise Invalid('receipt candidate path not fixed source board')
        hashes=receipt['source_hashes'];candidate_hash=receipt['candidate_sha256'];expected=dict(hashes);expected[source.name]=candidate_hash
        if watch_tree(source.parent)!=hashes or watch_tree(base/'snapshot')!=hashes or watch_tree(candidate.parent)!=expected:raise Invalid('source/candidate snapshot hashes differ')
        final_report=watch(base/'final-drc.json');binding=load_json(watch(base/'final-drc-binding.json'));input_hashes=watch_tree(base/'final-drc-input')
        if binding.get('source')!=str(candidate) or binding.get('input')!=str(base/'final-drc-input'/source.name) or binding['before']!=expected or input_hashes!=binding['after'] or any(input_hashes.get(k)!=v for k,v in expected.items()):raise Invalid('native report input tree/binding mismatch')
        baseline=p.parse_report(final_report,source.name)
        errors=[f for f in baseline['findings'] if f['severity']=='error']
        if baseline!=receipt['native'] or digest(final_report)!=receipt['native_report_sha256'] or baseline['opens'] or baseline['exclusions'] or len(errors)!=1 or errors[0]['type']!='starved_thermal':raise Invalid('retained result is not sole unexcluded thermal failure')
        original=p.preflight(source);base_tree=sx.read(candidate)
        if p.immutable(base_tree)!=p.immutable(original):raise Invalid('source immutable geometry differs')
        protected=[r for r in p.routes(original) if p.locked(r)]
        geometry_path=watch(exportdir/'geometry.json');g=load_json(geometry_path);request=load_json(watch(exportdir/'request.json'));export_report=watch(exportdir/'final-drc.json')
        if export['status']!='observations_complete' or export['original_inputs_unchanged'] is not True or export['api_error_count']!=0:raise Invalid('native export incomplete')
        if export['receipt']!=str(receipt_path) or export['receipt_sha256']!=digest(receipt_path) or export['candidate_sha256']!=candidate_hash or export['source_files']!=hashes or export['candidate_files']!=expected:raise Invalid('native export source receipt mismatch')
        if export['geometry_sha256']!=digest(geometry_path) or proposal_receipt['geometry_sha256']!=digest(geometry_path) or g['board_sha256']!=candidate_hash or g['project_sha256']!=digest(candidate.with_suffix('.kicad_pro')) or g['finding']!=errors[0]:raise Invalid('geometry/report/project binding mismatch')
        if request!={'schema':1,'candidate_files':expected,'final_drc_sha256':digest(final_report)} or digest(export_report)!=digest(final_report) or watch_tree(exportdir/'native-input')!=expected:raise Invalid('native exporter input tree/request stale')
        target_ids={g['target_pad_uuid'],g['zone_uuid']}
        if {i['uuid'] for i in errors[0]['items']}!=target_ids or len(target_ids)!=2:raise Invalid('thermal target item identities differ')
        manifest=load_json(watch(qual/'manifest.json'))
        helper_hashes={}
        for name in HELPERS:
            path=watch(qual/name);expected_hash=manifest['files'][name]['sha256']
            if digest(path)!=expected_hash:raise Invalid('helper does not match retained manifest: '+name)
            helper_hashes[name]=expected_hash
        if helper_hashes['attempt_graph_v3.py']!=proposal_receipt['script_sha256'] or helper_hashes['copper_path.py']!=proposal_receipt['copper_path_sha256']:raise Invalid('proposal algorithm/source hash mismatch')
        exporter_script=watch(exportdir/'native_geometry_probe.py')
        if digest(exporter_script)!=export['script_sha256']:raise Invalid('exporter source hash mismatch')
        tools=p.tool_manifest()
        if tools['implementation_sha256']!=current_code or tools['files']!=export['tools']['files'] or tools['kicad']!=export['tools']['kicad']:raise Invalid('loaded code or native tool pins changed')
        watch(ROOT/'toolchain.lock.json');watch(Path(__file__))
        (out/'helpers').mkdir()
        for name in HELPERS:shutil.copy2(qual/name,out/'helpers'/name)
        shutil.copy2(exporter_script,out/'helpers/native_geometry_probe.py')
        for relative,h in current_code.items():
            dest=out/'code'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/relative,dest)
            if digest(dest)!=h:raise Invalid('production snapshot changed during copy')
        for name in HELPERS:
            if digest(out/'helpers'/name)!=helper_hashes[name]:raise Invalid('helper copy changed')
        if any(name[:-3] in sys.modules for name in HELPERS):raise Invalid('unexpected preloaded geometry helper')
        sys.path.insert(0,str(out/'helpers'));modules={name[:-3]:importlib.import_module(name[:-3]) for name in HELPERS}
        proofs=verify_proposals(g,proposal_receipt,modules);saved_fill=fill_binding(base_tree,g,sx)
        # Existing source, output snapshot and every code copy remain immutable.
        shutil.copytree(source.parent,out/'snapshot');shutil.copytree(candidate.parent,out/'base-candidate')
        evidence=out/'evidence';evidence.mkdir()
        for name,path in [('result.json',receipt_path),('proposals.json',proposal_path),('export-summary.json',export_path),('geometry.json',geometry_path),('baseline-drc.json',final_report),('baseline-binding.json',base/'final-drc-binding.json'),('helper-manifest.json',qual/'manifest.json')]:shutil.copy2(path,evidence/name)
        shutil.copy2(__file__,out/'driver.py');shutil.copy2(ROOT/'toolchain.lock.json',out/'toolchain.lock.json')
        for folder in ('snapshot','base-candidate','helpers','code','evidence'):watch_tree(out/folder)
        watch(out/'driver.py');watch(out/'toolchain.lock.json')
        for relative in current_code:watch(ROOT/relative)
        protocol={'schema':1,'kind':'generated thermal repair-only diagnostic','native_validation_requested':args.validate,'wall_budget_seconds':BUDGET,'cpu_budget_seconds':BUDGET,'cpu_enforcement':'RUSAGE_SELF + waited RUSAGE_CHILDREN, including metadata subprocesses; cooperative step assignment/postcompletion acceptance cap, not OS total-CPU quota','source':str(source),'candidate':str(candidate),'source_hashes':hashes,'candidate_sha256':candidate_hash,'input_files':watched,'input_trees':trees,'tools':tools,'helper_hashes':helper_hashes,'proposal_proofs':proofs,'proposals':proposal_receipt['path_certificate_candidates'],'cost_scope':summary['cost_scope'],'routing_accepted':False,'comparison_eligible':False,'whole_body_certificate_qualified':False}
        p.save_json(out/'protocol.json',protocol);watch(out/'protocol.json');prepared=True;stable();summary['status']='prepared';summary['protocol_sha256']=digest(out/'protocol.json')
        owner_ids=uuid_index(base_tree,sx)
        for index,proposal in enumerate(proposal_receipt['path_certificate_candidates']):
            stable()
            if budget_remaining()<8:summary['status']='budget_reserve_reached';break
            directory=out/('candidate-%02d'%(index+1));job=DiagnosticJob(directory,max(.001,budget_remaining()-2));jobs.append(job)
            env={k:v for k,v in job.env.items() if not k.startswith('KICAD_') and k not in ('PYTHONPATH','PYTHONHOME')}
            for key in ('KICAD_CONFIG_HOME','KICAD_CACHE_HOME','KICAD_DOCUMENTS_HOME'):env[key]=job.env[key]
            (directory/'tmp').mkdir();env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(directory/'tmp'));job.env=env
            shutil.copytree(candidate.parent,directory/'candidate');board=directory/'candidate'/source.name
            uid=str(uuid.uuid5(uuid.NAMESPACE_URL,'kicad-autorouter:generated-thermal:'+candidate_hash+':'+digest(proposal_path)+':'+str(index)))
            if uid in owner_ids:raise Invalid('generated track UUID collision')
            node=['segment',['start',*map(mm,proposal['start_nm'])],['end',*map(mm,proposal['end_nm'])],['width',mm(proposal['width_nm'])],['layer','"'+proposal['layer']+'"'],['net',str(proposal['net_code'])],['uuid','"'+uid+'"']]
            new=copy.deepcopy(base_tree);new.append(node)
            if p.immutable(new)!=p.immutable(original) or p.routes(new)!=p.routes(base_tree)+[node]:raise Invalid('more than one track changed')
            sx.write(board,new);trial={'id':directory.name,'candidate':str(board),'added_track_uuid':uid,'proposal_index':index,'proposed_candidate_sha256':digest(board),'status':'generated_only','validation_passed':False,'routing_accepted':False,'comparison_eligible':False,'steps':job.steps};summary['trials'].append(trial)
            if args.validate:
                try:
                    final,native=p.validate_candidate(job,original,board,hashes,protected)
                    final_tree=sx.read(board)
                    if p.routes(final_tree)!=p.routes(base_tree)+[node] or p.immutable(final_tree)!=p.immutable(base_tree):raise Invalid('final pad/via/protected/other geometry changed')
                    if fill_binding(final_tree,g,sx)!=saved_fill:raise Invalid('refill changed target-zone saved geometry; historical witness invalid')
                    verify_proposals(g,proposal_receipt,modules)
                    p.verify_candidate_files(board,hashes,final)
                    # Class resolver from this final hash must confirm the bridge target.
                    mapping=load_json(directory/'final-netclasses.json');rows=[r for r in mapping['nets'] if r['netcode']==proposal['net_code']]
                    if len(rows)!=1 or rows[0]['width_nm']!=proposal['width_nm'] or mapping['board_sha256']!=final or mapping['project_sha256']!=digest(board.with_suffix('.kicad_pro')):raise Invalid('fresh native class target/hash mismatch')
                    warnings=lambda report:{(f['type'],tuple(sorted(i['uuid'] for i in f['items']))) for f in report['findings'] if f['severity']=='warning'}
                    valid=p.native_accepted(native) and warnings(native)<=warnings(baseline)
                    stable();trial.update(status='diagnostic_native_pass' if valid else 'native_rejected',validation_passed=valid,candidate_sha256=final,native=native,native_rejection_reasons=p.native_rejection_reasons(native),native_report_sha256=digest(directory/'final-drc.json'),saved_fill_unchanged=True,pad_via_geometry_unchanged=True,geometric_witnesses_rechecked=True,final_netclass_map_sha256=digest(directory/'final-netclasses.json'))
                except (p.Rejected,Invalid,ValueError,KeyError) as exc:trial.update(status='validation_rejected',reason=type(exc).__name__+': '+str(exc),validation_passed=False)
            trial.update(steps=job.steps,elapsed_wall_seconds=totals()[0],elapsed_cpu_seconds=totals()[1]);p.save_json(directory/'diagnostic-result.json',trial)
            if any(s.get('status')=='cancelled' for s in job.steps):raise KeyboardInterrupt
            if trial['validation_passed']:summary.update(status='diagnostic_native_pass',validation_passed=True,selected=directory.name,selected_trial_receipt_sha256=digest(directory/'diagnostic-result.json'));break
        if summary['status']=='prepared':summary['status']='no_native_pass' if args.validate else 'generated_only'
    except KeyboardInterrupt:summary.update(status='cancelled',validation_passed=False)
    except Exception as exc:summary.update(status='invalidated',validation_passed=False,reason=type(exc).__name__+': '+str(exc))
    finally:
        summary['preparation_completed']=prepared;summary['native_executed']=any(j.steps for j in jobs)
        def final_bindings():
            if not prepared:return
            stable();summary['original_inputs_unchanged']=True
            if not summary['validation_passed']:return
            selected=[t for t in summary['trials'] if t['id']==summary['selected']]
            if len(selected)!=1:raise Invalid('selected trial identity ambiguous')
            trial=selected[0];directory=require(out/trial['id'],out,kind='directory');board=require(trial['candidate'],directory/'candidate')
            if directory.parent!=out or board.parent!=directory/'candidate':raise Invalid('selected output path mismatch')
            if digest(directory/'diagnostic-result.json')!=summary['selected_trial_receipt_sha256']:raise Invalid('selected trial receipt changed')
            p.verify_candidate_files(board,hashes,trial['candidate_sha256'])
            report=require(directory/'final-drc.json',directory);mapping_path=require(directory/'final-netclasses.json',directory)
            if digest(report)!=trial['native_report_sha256'] or digest(mapping_path)!=trial['final_netclass_map_sha256']:raise Invalid('selected report/class map changed')
            parsed=p.parse_report(report,source.name)
            if parsed!=trial['native'] or not p.native_accepted(parsed):raise Invalid('selected native report no longer accepted')
            mapping=load_json(mapping_path);p.audit_candidate_netclasses(board,protected,mapping)
            final_binding=load_json(require(directory/'final-drc-binding.json',directory));final_input=require(directory/'final-drc-input',directory,kind='directory');now=strict_inventory(board.parent)
            if (final_binding.get('source')!=str(board) or final_binding.get('input')!=str(final_input/board.name) or final_binding['before']!=now or strict_inventory(final_input)!=final_binding['after'] or any(final_binding['after'].get(k)!=v for k,v in now.items())):raise Invalid('selected native report copied-input binding changed')
            if fill_binding(sx.read(board),g,sx)!=saved_fill:raise Invalid('selected target-zone fill changed')
        publish_summary(summary,out,totals,final_bindings,p.save_json)
    print(json.dumps({k:summary[k] for k in ('status','validation_passed','routing_accepted','comparison_eligible','native_executed','original_inputs_unchanged','wall_seconds','total_cpu_seconds')}))
    return 0 if summary['status'] in ('generated_only','diagnostic_native_pass') else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('receipt','proposals','export-summary','output'):parser.add_argument('--'+name,required=True,type=Path)
    parser.add_argument('--validate',action='store_true',help='Run native tools only in lead-assigned quiet slot')
    args=parser.parse_args()
    def cancel(signum,frame):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,cancel)
    lock=require(ROOT/'.runs/quality-experiment.lock',ROOT/'.runs',new=True)
    with lock.open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        raise SystemExit(main(args))
