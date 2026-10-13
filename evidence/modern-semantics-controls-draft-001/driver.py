"""Prospective ROOT-only severity diagnostics; no engine or routing acceptance."""
from __future__ import annotations
import argparse,copy,hashlib,json,re,shutil,signal,sys,time,uuid
from decimal import Decimal
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
OLD=ROOT/'experiments/pic_severity_controls_v1';sys.path.insert(0,str(OLD))
import fixture,checks  # Existing modules use this established import path.
from autorouter import config as c,pipeline as p,floor_route as f,sexpr as sx,placement_clearance as io,handoff as h
from autorouter.runner import run
SECONDS=90;LIMIT=20*1024**2
PIC=ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pcb'
FLOOR=ROOT/'tests/fixtures/board-floor/fixture.kicad_pcb'
CASES=('warning_positive','warning_board_edge','ignore_positive','ignore_board_edge','hole_positive','hole_negative')
NS=uuid.UUID('d8017285-7685-4dd3-b874-dab2ad9ca621')
def uid(name):return str(uuid.uuid5(NS,name))
def inventory(path):return io.inventory(path,max_bytes=LIMIT,max_files=3000,max_entries=6000)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def size(path):return sum(len(v) for v in io.inventory(path,contents=True,max_bytes=LIMIT,max_files=3000,max_entries=6000).values())

def hole_fixture(original,project,gap):
    if gap not in ('1.4','1.1'):raise p.Rejected('fixed center separation required')
    rules=project['board']['design_settings']['rules']
    if rules['min_hole_clearance']!=0.25 or rules['min_hole_to_hole']!=0.25:raise p.Rejected('original hole floors differ')
    board=copy.deepcopy(original)
    board[:]=[n for n in board if not isinstance(n,list) or not n or n[0] not in {'footprint','segment','arc','via','zone','net'}]
    for i,x in enumerate(('20',str(Decimal('20')+Decimal(gap)))):
        board.append(['footprint','"OwnedNPTH"',['layer','"F.Cu"'],['uuid',json.dumps(uid('fp'+str(i)))],['at',x,'20'],
            ['property','"Reference"',json.dumps('H'+str(i+1)),['at','0','-3'],['layer','"F.Fab"'],['hide','yes'],['effects',['font',['size','1','1'],['thickness','0.15']]]],
            ['property','"Value"','"OwnedNPTH"',['at','0','3'],['layer','"F.Fab"'],['hide','yes'],['effects',['font',['size','1','1'],['thickness','0.15']]]],
            ['attr','board_only','exclude_from_pos_files','exclude_from_bom'],
            ['pad','""','np_thru_hole','circle',['at','0','0'],['size','1','1'],['drill','1'],['layers','"*.Cu"','"*.Mask"'],['uuid',json.dumps(uid('pad'+str(i)))]]])
    copied=copy.deepcopy(project);copied['board']['design_settings']['rule_severities']['hole_to_hole']='warning'
    return (sx.dump(board)+'\n').encode(),copied

def geometry(source,candidate,hashes):
    if p.immutable(sx.read(source))!=p.immutable(sx.read(candidate)):raise p.Rejected('immutable geometry changed')
    p.verify_candidate_files(candidate,hashes,p.sha(candidate))
    return {'passed':True,'original_sha256':p.sha(source),'candidate_sha256':p.sha(candidate)}

def text_predicate(raw,severity,negative,scene,base_ignored):
    native=checks.summary(raw);target=[r for r in native['findings'] if r['type']=='text_on_edge_cuts']
    ignored=sorted(x['key'] for x in raw['ignored_checks'])
    wanted=sorted([*base_ignored,*(['text_on_edge_cuts'] if severity=='ignore' else [])])
    if ignored!=wanted or len(ignored)!=len(set(ignored)) or native['opens'] or native['exclusions']:return False
    if negative and severity=='warning':
        if len(target)!=1 or target[0]['severity']!='warning' or [x['uuid'] for x in target[0]['items']]!=[fixture.uid('boardtext')]:return False
    elif target:return False
    residual={**raw,'violations':[r for r in raw['violations'] if r not in target]}
    rest=checks.summary(residual)
    if severity=='ignore':
        return p.native_rejection_reasons(rest)==['disabled policy-critical native check: text_on_edge_cuts']
    return p.native_accepted(rest)

def hole_predicate(native,negative):
    hits=[r for r in native['findings'] if r['type']=='hole_to_hole']
    if native['opens'] or native['blocking'] or native['exclusions']:return False
    if not negative:return not hits and p.native_accepted(native)
    if len(hits)!=1 or hits[0]['severity']!='warning' or len(hits[0]['items'])!=2 or {i['uuid'] for i in hits[0]['items']}!={uid('pad0'),uid('pad1')}:return False
    detail=hits[0].get('description')
    match=re.fullmatch(r'Drilled hole too close to other hole \(([^;\n]+) ([0-9]+\.[0-9]+) mm; actual ([0-9]+\.[0-9]+) mm\)',detail) if isinstance(detail,str) else None
    if not match or not match[1].startswith('board setup constraints ') or 'hole' not in match[1] or Decimal(match[2])!=Decimal('0.25') or Decimal(match[3])!=Decimal('0.1'):return False
    residual={**native,'findings':[r for r in native['findings'] if r not in hits],'warnings':native['warnings']-1}
    return p.native_accepted(residual) and not p.native_accepted(native)

class ControlJob(f.FloorJob):
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        actual=[str(a) for a in (argv if already_sandboxed else [*f.SANDBOX,*argv])]
        inner=actual[len(f.SANDBOX):]
        native_drc=(len(inner)>2 and inner[:3]==[str(c.CLI),'pcb','drc'])
        observer=(len(inner)==4 and inner[:2]==[str(c.PYTHON),str(OLD/'worker.py')])
        if actual[:len(f.SANDBOX)]!=f.SANDBOX or not(native_drc or observer):raise p.Rejected('only declared DRC/observer stages allowed')
        if self.remaining()<=0 or size(self.out)>LIMIT:raise p.Rejected('shared native resource cap exhausted')
        result=run(actual,cwd=self.out,log=self.out/(name+'.log'),timeout=min(30,self.remaining()),env=self.env,
                   max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=2*1024**3)
        result['name']=name;self.steps.append(result);p.save_json(self.out/(name+'-process.json'),result)
        if result['status']=='cancelled':raise KeyboardInterrupt
        if result['status'] not in {'success','nonzero_exit'} or result['exit_code'] not in allowed or not result.get('cleanup_complete'):raise p.Rejected(name+': '+result['status'])
        if self.remaining()<=0 or size(self.out)>LIMIT:raise p.Rejected('shared cap exceeded after native stage')
        return result

def experiment(output,*,run_native=False):
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in previous:signal.signal(sig,interrupted)
        return _experiment(output,run_native=run_native)
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)

def _experiment(output,*,run_native=False):
    if run_native is not True:raise p.Rejected('--run-native required; ROOT native lane only')
    start=time.monotonic();cpu0=h.cpu_seconds();remaining=lambda:max(0,min(SECONDS-time.monotonic()+start,SECONDS-h.cpu_seconds()+cpu0))
    out=h.real_path(output,existing=False)
    if out.parent!=ROOT/'.runs' or out.exists():raise p.Rejected('fresh direct .runs output required')
    lifecycle={};job=ControlJob(out,SECONDS,remaining);h.capture_destination(lifecycle,out)
    record={'schema':1,'kind':'modern-semantics-controls-v1','accepted':False,'whole_project_drc_clean':False,
            'controls_passed':False,'status':'incomplete','budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,
            'output_ceiling_bytes':LIMIT,'new_engine_execution':False,'production_support_changed':False,'cases':[],
            'constraints_meaning':'Original error/warning/ignore retained; a deliberate finding/suppression control is never routing acceptance.',
            'accounting_point':'Shared publisher records self+waited-child cost before final publication; post-publication caps are enforced, and ROOT enclosing execution must retain complete outer cost.'}
    pins=f.read_json(HERE/'pins.json');completed={};runtime={};sourcehashes={};tools=None
    def owned():h.owned_destination(lifecycle)
    def account():
        record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=h.cpu_seconds()-cpu0,
                      child_step_cpu_seconds=sum(s.get('cpu_seconds') or 0 for s in job.steps),
                      monitor_cpu_seconds=sum(s.get('monitor_cpu_seconds') or 0 for s in job.steps),steps=job.steps)
        record['within_budget']=remaining()>0 and size(out)<=LIMIT
        if not record['within_budget'] or record['status'] in ('invalidated','cancelled','failed'):
            record['controls_passed']=False
        if not record['within_budget']:record['status']='budget_exceeded'
    def stable():
        owned()
        for path,sha in pins['files'].items():
            if p.sha(ROOT/path)!=sha:raise p.Rejected('pinned input changed: '+path)
        if inventory(PIC.parent)!=sourcehashes:raise p.Rejected('immutable PIC source changed')
        if any(p.sha(ROOT/path)!=sha for path,sha in runtime.items()) or inventory(out/'code')!=runtime:raise p.Rejected('current helper/code freeze changed')
        if tools is not None and p.tool_manifest()!=tools:raise p.Rejected('tool/HEAD freeze changed')
        if 'pad_movement_negative' in record:
            proof=record['pad_movement_negative'];path=out/'pad_movement_negative'
            if proof['passed'] is not True or proof['native_calls']!=0 or inventory(path/'original')!=proof['source_inventory'] or inventory(path/'candidate')!=proof['candidate_inventory']:raise p.Rejected('pad movement counterfactual evidence changed')
        for case,witness in completed.items():
            if inventory(out/case)!=witness:raise p.Rejected('completed case material changed')
        for row in record['cases']:
            if 'native' not in row:continue
            case=row['case'];name=PIC.name if not case.startswith('hole_') else 'fixture.kicad_pcb';stage=case+'-drc'
            checked=out/case/'observe-input'/name
            for suffix,key in (('.json','report_sha256'),('-binding.json','binding_sha256'),('-process.json','process_sha256')):
                if p.sha(out/(stage+suffix))!=row[key]:raise p.Rejected('final native artifact changed: '+stage+suffix)
            actual=f.check_drc_stage(out,{'steps':job.steps},stage,checked,out/(stage+'-input')/name,False,row['source_hashes'])
            if actual!=row['native'] or p.sha(checked)!=row['final_candidate_sha256']:raise p.Rejected('actual final candidate/native binding changed')
            predicate=text_predicate(f.read_json(out/(stage+'.json')),row['severity'],case.endswith('board_edge'),row['scene'],pins['original_error_ignored_keys']) if not case.startswith('hole_') else hole_predicate(actual,case=='hole_negative')
            if predicate is not row['control_passed']:raise p.Rejected('native control predicate changed')
        if record['accepted'] is not False or record['production_support_changed'] is not False:raise p.Rejected('diagnostic scope changed')
        if record['controls_passed'] and (len(record['cases'])!=6 or not all(r['control_passed'] for r in record['cases'])):raise p.Rejected('missing control proof')
    try:
        if 'text_on_edge_cuts' not in p.KNOWN_CHECKS:raise p.Rejected('ROOT must integrate qualified text metadata/intent guard before native')
        sourcehashes=inventory(PIC.parent)
        if sourcehashes!=pins['pic_source_inventory']:raise p.Rejected('complete PIC source inventory differs')
        for path,sha in pins['files'].items():
            if p.sha(ROOT/path)!=sha:raise p.Rejected('pinned source/cache/error control differs')
        tools=p.tool_manifest()
        extra=[Path(__file__),HERE/'pins.json',HERE/'PROTOCOL.json',OLD/'fixture.py',OLD/'worker.py',OLD/'checks.py',FLOOR,FLOOR.with_suffix('.kicad_pro')]
        merged={**tools['implementation_sha256'],**{str(x.relative_to(ROOT)):p.sha(x) for x in extra}}
        freeze=io.capture_freeze({**tools,'implementation_sha256':merged});runtime=freeze['files_sha256']
        for path,sha in runtime.items():
            target=out/'code'/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,target)
        record.update(tools=tools,runtime_source_sha256=runtime,pinned_inputs=pins,controller_sha256=p.sha(Path(__file__)))
        original=sx.read(PIC);project=f.read_json(PIC.with_suffix('.kicad_pro'));floor=sx.read(FLOOR);floorpro=f.read_json(FLOOR.with_suffix('.kicad_pro'))
        old=f.read_json(ROOT/pins['original_error_receipt']);base_ignored=pins['original_error_ignored_keys']
        if old['controls_passed'] is not True:raise p.Rejected('original error controls did not pass')
        # Actual shared candidate validator must reject movement before touching native.
        geomdir=out/'pad_movement_negative';geomdir.mkdir();raw,pro=hole_fixture(floor,floorpro,'1.4')
        src=geomdir/'original';src.mkdir();(src/'fixture.kicad_pcb').write_bytes(raw);p.save_json(src/'fixture.kicad_pro',pro)
        cand=geomdir/'candidate';shutil.copytree(src,cand);mutant=sx.read(cand/'fixture.kicad_pcb');sx.one(sx.children(mutant,'footprint')[1],'at')[1]='23';sx.write(cand/'fixture.kicad_pcb',mutant)
        class NeverNative:
            calls=0
            def drc(self,*a,**k):self.calls+=1;raise AssertionError('geometry mutation reached native')
        never=NeverNative()
        try:p.validate_candidate(never,sx.read(src/'fixture.kicad_pcb'),cand/'fixture.kicad_pcb',inventory(src),[])
        except p.Rejected as exc:
            if str(exc)!='immutable geometry changed' or never.calls:raise
        else:raise p.Rejected('pad-movement counterfactual not rejected')
        record['pad_movement_negative']={'passed':True,'native_calls':never.calls,'original_sha256':p.sha(src/'fixture.kicad_pcb'),'candidate_sha256':p.sha(cand/'fixture.kicad_pcb'),'source_inventory':inventory(src),'candidate_inventory':inventory(cand)}
        for case in CASES:
            stable();caseout=out/case;caseout.mkdir();row={'case':case,'control_passed':False,'accepted':False,'status':'incomplete'};record['cases'].append(row)
            text=not case.startswith('hole_');negative=case.endswith(('board_edge','negative'))
            if text:
                scene_case='board_edge_text' if negative else 'positive';board,pro,scene=fixture.prepare(original,project,scene_case)
                severity=case.split('_',1)[0];pro['board']['design_settings']['rule_severities']['text_on_edge_cuts']=severity
                row.update(scene=scene,severity=severity)
                source=caseout/'original';shutil.copytree(PIC.parent,source);name=PIC.name
            else:
                board,pro=hole_fixture(floor,floorpro,'1.1' if negative else '1.4');source=caseout/'original';source.mkdir();name='fixture.kicad_pcb'
            (source/name).write_bytes(board);p.save_json(source/Path(name).with_suffix('.kicad_pro'),pro)
            candidate=caseout/'observe-input';shutil.copytree(source,candidate);checked=candidate/name;hashes=inventory(source)
            row.update(source_hashes=hashes,project_sha256=p.sha(checked.with_suffix('.kicad_pro')),candidate_sha256=p.sha(checked),geometry=geometry(source/name,checked,hashes))
            if text:
                observation=caseout/'observation.json';stage='observe-'+case
                argv=[*f.SANDBOX,str(c.PYTHON),str(OLD/'worker.py'),str(checked),str(observation)]
                job.step(stage,argv,already_sandboxed=True);observed=f.read_json(observation)
                if observed['source']!=str(checked) or observed['input_hashes_before']!=hashes or observed['input_hashes_after']!=hashes or observed['board_sha256']!=hashes[name] or observed['project_sha256']!=hashes[Path(name).with_suffix('.kicad_pro').name]:raise p.Rejected('same-load observation identity differs')
                row['same_load_geometry']=checks.observe(observed,scene,pro);row['observation_sha256']=p.sha(observation)
                f.process_check(out,{'steps':job.steps},stage,argv)
            stage=case+'-drc';native=job.drc(stage,checked,save=False);report=out/(stage+'.json')
            rechecked=f.check_drc_stage(out,{'steps':job.steps},stage,checked,out/(stage+'-input')/name,False,hashes)
            if native!=rechecked:raise p.Rejected('final native summary differs')
            row.update(final_geometry=geometry(source/name,checked,hashes),native=native,native_rejection_reasons=p.native_rejection_reasons(native),
                       report_sha256=p.sha(report),binding_sha256=p.sha(out/(stage+'-binding.json')),process_sha256=p.sha(out/(stage+'-process.json')),
                       final_candidate_sha256=p.sha(checked),control_passed=text_predicate(f.read_json(report),severity,negative,scene,base_ignored) if text else hole_predicate(native,negative))
            row['status']='passed' if row['control_passed'] else 'failed';completed[case]=inventory(caseout)
            if not row['control_passed']:raise p.Rejected('declared native predicate failed: '+case)
        record.update(status='controls_passed',controls_passed=True)
        stable();account()
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
    # Shared publisher, original ownership identity and full cost are retained.
    try:
        f.publish(out,record,stable,account,remaining,owned=owned);owned()
        if remaining()<=0 or size(out)>LIMIT:
            record.update(status='budget_exceeded',controls_passed=False,reason='post-publication shared cap exceeded');f.publish(out,record,stable,account,remaining,owned=owned)
        owned()
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',controls_passed=False)
        record.setdefault('error',type(exc).__name__+': '+str(exc))
        f.publish(out,record,stable,account,remaining,owned=owned);owned()
    return record

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);parser.add_argument('--run-native',action='store_true');args=parser.parse_args()
    result=experiment(args.output,run_native=args.run_native);print(json.dumps({'status':result['status'],'controls_passed':result['controls_passed'],'accepted':False}));raise SystemExit(0 if result['controls_passed'] else 2)
