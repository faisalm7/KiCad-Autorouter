"""Explicit bounded native board-floor controls; never benchmark acceptance.

--run-native is mandatory. Geometry=60s, forced-via=120s, all=180s total wall
AND total parent+waited-child CPU. No native/engine work on import or --help.
"""
from __future__ import annotations
import argparse,copy,fcntl,json,math,os,resource,shutil,signal,sys,time,uuid
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(ROOT),str(HERE)]
from autorouter import config as c,pipeline as p,sexpr as sx,adapter
import board_floor_guidance as g
import fixture_recipe as f
PROJECT=ROOT/'.data/boards/kicad-multichannel/multichannel_mixer.kicad_pro'
PROJECT_SHA='ea1bc47355f707e1c4743af3e1c29e939bb5eaf4621c071bdac3841c43545538'
BUDGETS={'geometry':60,'forced-via':120,'all':180}
HELPERS=('driver.py','fixture_recipe.py','board_floor_guidance.py','native_context_worker.py')

def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime

def owned(path,new=False):
    path=Path(path).absolute()
    if '..' in path.parts or not path.is_relative_to(ROOT) or any(x.is_symlink() for x in (path,*path.parents)):raise p.Rejected('path outside real local checkout')
    if not new and not path.exists():raise p.Rejected('missing owned input')
    return path

class SharedJob(p.Job):
    def __init__(self,out,remaining,steps,code):
        self.remaining=remaining;self.shared_steps=steps;self.code=code
        if remaining()<=0:raise p.Rejected('whole diagnostic budget exhausted')
        super().__init__(out,remaining())
        keep={k:v for k,v in self.env.items() if not k.startswith('KICAD_') and k not in {'PYTHONPATH','PYTHONHOME'}}
        for key in ('KICAD_CONFIG_HOME','KICAD_CACHE_HOME','KICAD_DOCUMENTS_HOME'):keep[key]=self.env[key]
        (self.out/'tmp').mkdir();keep.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(self.out/'tmp'));self.env=keep
    def step(self,name,argv,allowed=(0,)):
        remaining=self.remaining();cap=remaining-20 if name=='engine' else min(20,remaining)
        if cap<=0:raise p.Rejected('whole diagnostic/native-finalization budget exhausted')
        self.deadline=time.monotonic()+cap;before=len(self.steps)
        try:return super().step(name,['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',*argv],allowed)
        finally:self.shared_steps.extend(self.steps[before:])
    def native(self,name,action,board,output,*extra):
        return self.step(name,[c.PYTHON,'-B',self.code/'native.py',action,board,output,*extra])


def context(job,board,base,project,prefix='native'):
    before=p.tree_hash(board.parent);dsn=job.out/(prefix+'.dsn');path=job.out/(prefix+'-context.json')
    job.step(prefix+'-context',[c.PYTHON,'-B',job.code/'native_context_worker.py',board,dsn,path])
    data=json.loads(path.read_text())
    if (data.get('source')!=str(board) or data.get('board_sha256')!=p.sha(board) or data.get('project_sha256')!=p.sha(board.with_suffix('.kicad_pro')) or data.get('dsn_sha256')!=p.sha(dsn) or data.get('input_hashes_before')!=before or data.get('input_hashes_after')!=before or p.tree_hash(board.parent)!=before):raise p.Rejected('fresh native context binding/input mismatch')
    qualified=g.qualify(project,data,base)
    return data,qualified,dsn,path


def audit_native_routes(tree,native):
    """Native readback must match actual saved route IDs, geometry and dimensions."""
    _,resolve=g.source_net_identity(tree);expected={}
    xy=lambda node:[g.decimal_nm(v,1000000,zero=True) for v in node[1:3]]
    for node in p.routes(tree):
        key=sx.unquote(sx.one(node,'uuid')[1])
        if key in expected:raise p.Rejected('duplicate generated route UUID')
        row={'uuid':key,'net':resolve(sx.one(node,'net')),'kind':node[0]}
        if node[0]=='segment':row.update(start_nm=xy(sx.one(node,'start')),end_nm=xy(sx.one(node,'end')),layer=sx.unquote(sx.one(node,'layer')[1]),width_nm=g.decimal_nm(sx.one(node,'width')[1],1000000))
        elif node[0]=='via':row.update(position_nm=xy(sx.one(node,'at')),width_nm=g.decimal_nm(sx.one(node,'size')[1],1000000),drill_nm=g.decimal_nm(sx.one(node,'drill')[1],1000000),layers=[sx.unquote(x) for x in sx.one(node,'layers')[1:]])
        else:raise p.Rejected('arc outside diagnostic scope')
        expected[key]=row
    observed=native.get('routes')
    if not isinstance(observed,list) or len(observed)!=len(expected):raise p.Rejected('native route count differs')
    seen=set()
    for row in observed:
        if row.get('uuid') in seen or row.get('uuid') not in expected or any(row.get(k)!=v for k,v in expected[row['uuid']].items()):raise p.Rejected('native route geometry/dimension/identity differs')
        seen.add(row['uuid'])
    return {'passed':True,'native_route_count':len(observed),'native_via_count':sum(x['kind']=='via' for x in observed)}


def native_case_pass(case,native,expected):
    if native['opens'] or native['exclusions']:return False,[]
    if case=='positive':return p.native_accepted(native),[]
    kind,ids=expected
    findings=[x for x in native['findings'] if x['type']==kind and x['severity']=='error' and not x.get('excluded',False) and set(ids)<={y.get('uuid') for y in x['items']}]
    return (not p.native_accepted(native) and bool(findings)),findings


def final_binding(job,board,hashes,native):
    binding=json.loads((job.out/'final-drc-binding.json').read_text());expected=dict(hashes);expected[board.name]=p.sha(board)
    input_board=job.out/'final-drc-input'/board.name
    if (binding.get('source')!=str(board) or binding.get('input')!=str(input_board) or binding.get('saved') is not False or binding.get('before')!=expected):raise p.Rejected('final DRC binding mismatch')
    after=binding.get('after',{})
    if any(after.get(k)!=v for k,v in expected.items()) or set(after)-set(expected)-{board.with_suffix('.kicad_prl').name} or p.tree_hash(input_board.parent)!=after:raise p.Rejected('final DRC rules/input mutated')
    if p.parse_report(job.out/'final-drc.json',board.name)!=native:raise p.Rejected('final native summary mismatch')
    process=json.loads((job.out/'final-drc-process.json').read_text())
    if process.get('cleanup_complete') is not True or process.get('exit_code') not in (0,5):raise p.Rejected('final native process incomplete')
    return {'final_drc_sha256':p.sha(job.out/'final-drc.json'),'binding_sha256':p.sha(job.out/'final-drc-binding.json'),'candidate_sha256':p.sha(board)}


def canonical_json(value):
    """Compare the actual JSON representation, including tuples as JSON arrays."""
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def read_json_strict(path):
    def object_pairs(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise p.Rejected('duplicate summary JSON key')
            result[key]=value
        return result
    def nonfinite(value):raise p.Rejected('nonfinite summary JSON value')
    return json.loads(path.read_text(),object_pairs_hook=object_pairs,parse_constant=nonfinite)


def publish(out,record,stable,account):
    try:
        stable();account();expected_json=canonical_json(record)
        p.save_json(out/'summary.json',record)
        if canonical_json(read_json_strict(out/'summary.json'))!=expected_json:raise p.Rejected('summary changed')
        stable();account()
        if not record['within_budget']:raise p.Rejected('final publication budget exhausted')
    except (Exception,KeyboardInterrupt) as exc:
        for path in (out/'summary.json',out/'summary.json.partial'):
            if path.exists():path.rename(out/('invalidated-'+uuid.uuid4().hex+'-'+path.name))
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',controls_passed=False,error=type(exc).__name__+': '+str(exc))
        account();p.save_json(out/'summary.json',record)


def experiment(out,stage,*,run_native=False):
    if run_native is not True:raise p.Rejected('explicit --run-native required; preparation never launches tools')
    if stage not in BUDGETS:raise p.Rejected('unknown stage')
    start,cpu0=time.monotonic(),cpu();seconds=BUDGETS[stage];steps=[];out=owned(out,new=True)
    if out.parent!=ROOT/'.runs' or out.exists():raise p.Rejected('output must be fresh direct .runs child')
    source=owned(HERE/'fixture/fixture.kicad_pcb');project_path=owned(source.with_suffix('.kicad_pro'));owned(PROJECT)
    if p.sha(PROJECT)!=PROJECT_SHA or p.sha(project_path)!=PROJECT_SHA or PROJECT.with_suffix('.kicad_dru').exists():raise p.Rejected('complete original project/rule identity changed')
    base=p.preflight(source);fixture_hashes=p.tree_hash(source.parent);topology=f.force_via_topology(base)
    if base!=f.original(sx.read(owned(ROOT/'fixtures/smoke/smoke.kicad_pcb'))):raise p.Rejected('fixture differs from owned recipe')
    project=json.loads(project_path.read_text());tools=p.tool_manifest();p.check_storage()
    originals={str(PROJECT):p.sha(PROJECT),str(ROOT/'fixtures/smoke/smoke.kicad_pcb'):p.sha(ROOT/'fixtures/smoke/smoke.kicad_pcb')}
    for name in HELPERS:originals[str(owned(HERE/name))]=p.sha(HERE/name)
    out.mkdir();code=out/'code';code.mkdir();shutil.copytree(source.parent,out/'source')
    for relative,digest in tools['implementation_sha256'].items():
        shutil.copy2(ROOT/relative,code/Path(relative).name)
        if p.sha(code/Path(relative).name)!=digest:raise p.Rejected('production snapshot changed')
    for name in HELPERS:shutil.copy2(HERE/name,code/name)
    code_hashes=p.tree_hash(code);completed={}
    record={'schema':1,'status':'running','stage':stage,'seconds_ceiling':seconds,'cpu_seconds_ceiling':seconds,'controls_passed':False,'routing_accepted':False,'production_support_qualified':False,'comparison_eligible':False,'physical_electrical_validation':False,'fixture_exposure':'original diagnostic development only; not an independent routing family','fixture_topology':topology,'tools':tools,'source_hashes':fixture_hashes,'original_inputs':originals,'steps':steps,'cases':[],'cpu_enforcement':'cooperative per-step remaining wall/CPU plus final measured cap, no OS aggregate quota','accounting_point':'Stored totals precede final summary publication and freshness recheck; acceptance caps include both, and rejected correction can finish outside cap'}
    def remaining():return max(0.,min(start+seconds-time.monotonic(),seconds-(cpu()-cpu0)))
    def stable():
        if PROJECT.with_suffix('.kicad_dru').exists() or PROJECT.with_suffix('.kicad_dru').is_symlink():raise p.Rejected('new original custom rules require qualification')
        if any(p.sha(owned(path))!=digest for path,digest in originals.items()) or p.tool_manifest()!=tools:raise p.Rejected('original source/helper/tool freeze changed')
        if p.tree_hash(source.parent)!=fixture_hashes or p.tree_hash(out/'source')!=fixture_hashes or p.tree_hash(code)!=code_hashes:raise p.Rejected('immutable fixture/code snapshot changed')
        for path,inventory in completed.items():
            if p.tree_hash(Path(path))!=inventory:raise p.Rejected('completed native evidence changed')
    def account():
        record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=cpu()-cpu0,child_cpu_seconds=sum(x.get('cpu_seconds') or 0 for x in steps),monitor_cpu_seconds=sum(x.get('monitor_cpu_seconds') or 0 for x in steps))
        record['within_budget']=record['wall_seconds']<=seconds and record['total_cpu_seconds']<=seconds
        if not record['within_budget']:record['controls_passed']=False
    try:
        stable();job=SharedJob(out/'context',remaining,steps,code);shutil.copytree(source.parent,job.out/'native-input');board=job.out/'native-input'/source.name
        native,qualified,dsn,context_path=context(job,board,base,project)
        encoded,receipt=g.transform(dsn.read_bytes(),native,project_path.read_bytes(),source.read_bytes())
        if qualified['derived_nm']!={'width_nm':300000,'clearance_nm':300000,'via_diameter_nm':1500000,'via_drill_nm':300000}:raise p.Rejected('fixture recipe does not match derived targets')
        (job.out/'floor-guided.dsn').write_bytes(encoded);p.save_json(job.out/'guidance.json',receipt);record['native_context_receipt']=str(context_path);completed[str(job.out)]=p.tree_hash(job.out)
        if stage in ('geometry','all'):
            for case in f.CASES:
                stable();job=SharedJob(out/('geometry-'+case),remaining,steps,code);shutil.copytree(source.parent,job.out/'candidate');board=job.out/'candidate'/source.name
                tree,expected=f.candidate(base,case);sx.write(board,tree)
                entry={'case':case,'passed':False,'expected':expected,'prepared_candidate_sha256':p.sha(board),'changed_routes_only':p.immutable(tree)==base};record['cases'].append(entry)
                try:
                    final,native=p.validate_candidate(job,base,board,fixture_hashes,[])
                    if sx.read(board)!=tree:raise p.Rejected('refill changed explicit no-zone fixture')
                    final_context,final_qualified,_,_=context(job,board,base,project,'final')
                    entry['native_route_readback']=audit_native_routes(tree,final_context)
                    if final_qualified!=qualified:raise p.Rejected('final loaded floors/classes/pads changed')
                    try:entry['generated_dimensions']=g.audit_generated_routes(tree,qualified)
                    except ValueError as exc:entry['generated_dimension_rejection']=str(exc)
                    passed,hits=native_case_pass(case,native,expected)
                    expected_dimension_valid=case in ('positive','clearance')
                    entry.update(native=native,targeted_native_findings=hits,**final_binding(job,board,fixture_hashes,native))
                    entry['passed']=passed and ('generated_dimensions' in entry)==expected_dimension_valid
                    p.verify_candidate_files(board,fixture_hashes,final)
                except Exception as exc:entry.update(error=type(exc).__name__+': '+str(exc),passed=False)
                if any(s.get('status')=='cancelled' for s in job.steps):raise KeyboardInterrupt
                p.save_json(job.out/'case.json',entry);completed[str(job.out)]=p.tree_hash(job.out)
        if stage in ('forced-via','all'):
            stable();job=SharedJob(out/'forced-via',remaining,steps,code);shutil.copytree(source.parent,job.out/'candidate');board=job.out/'candidate'/source.name
            entry={'case':'forced-via-engine','passed':False,'solver_executed':False,'zero_via_is_failure':True};record['cases'].append(entry)
            try:
                native,context_now,dsn,_=context(job,board,base,project)
                encoded,receipt=g.transform(dsn.read_bytes(),native,project_path.read_bytes(),source.read_bytes());(job.out/'floor-guided.dsn').write_bytes(encoded);p.save_json(job.out/'guidance.json',receipt)
                task_dsn=job.out/'task.dsn';task_dsn.write_bytes(encoded);before_network=adapter._network_summary(adapter._parse_dsn(encoded.decode()))
                adapter_receipt=adapter.adapt_dsn(task_dsn,'both',[])
                if adapter._network_summary(adapter._parse_dsn(task_dsn.read_text()))!=before_network:raise p.Rejected('adapter changed guided network')
                config=job.out/'engine-config';config.mkdir();settings=p.engine_profile_settings('completion-only',remaining(),strict_class_targets=True)
                entry.update(engine_settings=settings,adapter=adapter_receipt,native_dsn_sha256=p.sha(dsn),guided_dsn_sha256=p.sha(job.out/'floor-guided.dsn'),task_dsn_sha256=p.sha(task_dsn),solver_executed=True)
                job.step('engine',[c.JAVA,'-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',c.JAR,'--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da','--user_data_path='+str(config),'--logging.file.enabled=false',*settings['argv'],'-de',task_dsn,'-do',job.out/'routes.ses'])
                ses=owned(job.out/'routes.ses')
                if not ses.is_file() or not ses.stat().st_size:raise p.Rejected('engine emitted no nonempty SES')
                imported=job.out/'imported.kicad_pcb';job.native('import','import',board,imported,ses)
                sx.write(board,p.transplant_routes(base,sx.read(imported)))
                g.audit_generated_routes(sx.read(board),context_now)
                if not sx.children(sx.read(board),'via'):raise p.Rejected('zero-via output cannot qualify forced-via import')
                final,native=p.validate_candidate(job,base,board,fixture_hashes,[])
                final_context,final_qualified,_,_=context(job,board,base,project,'final')
                if final_qualified!=qualified:raise p.Rejected('final loaded floors/classes/pads changed')
                readback=audit_native_routes(sx.read(board),final_context);g.audit_generated_routes(sx.read(board),qualified)
                signal_vias=[x for x in final_context['routes'] if x['kind']=='via' and x['net']==topology['net']]
                entry.update(native=native,native_route_readback=readback,signal_vias=len(signal_vias),ses_sha256=p.sha(ses),**final_binding(job,board,fixture_hashes,native))
                entry['passed']=p.native_accepted(native) and bool(signal_vias)
                p.verify_candidate_files(board,fixture_hashes,final)
            except Exception as exc:entry.update(error=type(exc).__name__+': '+str(exc),passed=False)
            if any(s.get('status')=='cancelled' for s in job.steps):raise KeyboardInterrupt
            p.save_json(job.out/'case.json',entry);completed[str(job.out)]=p.tree_hash(job.out)
        stable();record.update(status='completed',original_inputs_unchanged=True,controls_passed=bool(record['cases']) and all(x['passed'] for x in record['cases']),completed_evidence=completed)
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
    publish(out,record,stable,account)
    return record


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--stage',choices=tuple(BUDGETS),default='geometry');parser.add_argument('--run-native',action='store_true');args=parser.parse_args(argv)
    if not args.run_native:parser.error('--run-native is required; no native work has been performed')
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in previous:signal.signal(sig,interrupted)
        lock=owned(ROOT/'.runs/quality-experiment.lock',new=True)
        with lock.open('a') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);record=experiment(args.out,args.stage,run_native=True)
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
    print(json.dumps({'status':record['status'],'controls_passed':record['controls_passed'],'out':str(args.out)}))
    return 0 if record['controls_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
