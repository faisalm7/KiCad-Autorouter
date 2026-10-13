"""ROOT-only engineered pruning controls; no measured-board quality claim."""
from pathlib import Path
import argparse,copy,datetime,fcntl,json,shutil,signal,subprocess,sys,time
ROOT=next(path for path in Path(__file__).resolve().parents if (path/'autorouter/pipeline.py').is_file())
HERE=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
sys.path.append(str(ROOT/'experiments/lipo_native_diagnostic_v1'))
from autorouter import config as c,pipeline as p,sexpr as sx,floor_route as f,placement_clearance as pc,placement_strategy as ps,strategy as s
from experiments.lipo_native_diagnostic_v1 import driver as shared
SECONDS=180;LIMIT=64*1024**2;HELPERS=('driver.py','test_driver.py','PROTOCOL.json','README.md')
CASES=('redundant','necessary');ARMS=('standard','tuned','C','necessary_tuned')
BASE=ROOT/'fixtures/smoke';TEMPLATE=ROOT/'evidence/placement-area-native-001/allowed_placement/candidate'
BRIDGE_UUID='7372ac93-5b96-4a58-8d4e-b5f715a12451'
OUTSIDE_PAD='91b55d41-261e-40fb-b066-cea4f05adfc3'
INSIDE_PAD='3770420a-a201-4704-85a8-70c7666bf2cf'
ZONE_UUID='5a4bb95a-e244-41cb-b650-8e9f3573eb0f'
AREA='''(zone (net 0) (net_name "") (layers "F.Cu" "B.Cu") (uuid "b174e2d7-dd52-4aba-bb1a-8049a0a48564") (name "owned-pruning-allowed") (hatch none 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) (filled_areas_thickness no) (keepout (tracks allowed) (vias allowed) (pads allowed) (copperpour allowed) (footprints allowed)) (placement (enabled yes) (sheetname "/OwnedPruning/")) (fill (thermal_gap 0.5) (thermal_bridge_width 0.5)) (polygon (pts (xy 20 19) (xy 30 19) (xy 30 21) (xy 20 21))))'''
NOTICE='''# Engineered placement-pruning controls\n\nOriginal six-terminal smoke geometry and this control generator are project-owned GPL-3.0 work. The derived sources add one all-allowed placement area; the necessary-copper source additionally shortens the B.Cu GND zone at x=24mm. Every original smoke file remains unchanged. These are development-exposed engineered controls, not independent board families or quality-comparison evidence.\n\nfixture.kicad_pro is the unchanged KiCad multichannel demo settings template, SHA-256 ea1bc47355f707e1c4743af3e1c29e939bb5eaf4621c071bdac3841c43545538, from the already audited/pinned project manifest. It remains separately CC BY-SA 4.0; original license/notice copies remain in _licenses. Its existing five explicit ignored checks are inherited unchanged and fully reported. No new severity/exclusion is introduced.\n'''


def inventory(path):return pc.inventory(path,max_bytes=LIMIT,max_files=4000,max_entries=8000)
def size(path):return sum((path/name).stat().st_size for name in inventory(path))


def control_output(path):
    path=shared.owned(path)
    direct=path.parent==ROOT/'.runs'
    monitored=(path.name=='run' and path.parent.parent==ROOT/'.runs' and path.parent.name.startswith('placement-pruning-controls-') and path.parent.is_dir())
    if path.exists() or not (direct or monitored):raise p.Rejected('fresh direct or monitored control output required')
    return path


def derive(board,case):
    """Create owned control sources before routing; never mutate caller bytes."""
    if case not in CASES:raise p.Rejected('unknown pruning control')
    tree=sx.parse(board.decode());original=copy.deepcopy(tree);zones=sx.children(tree,'zone')
    if p.routes(tree) or len(zones)!=1 or sx.one(zones[0],'net')!=['net','"GND"'] or sx.one(zones[0],'uuid')!=['uuid',json.dumps(ZONE_UUID)]:
        raise p.Rejected('owned smoke scene differs')
    points=sx.one(sx.one(zones[0],'polygon'),'pts')
    if points!=['pts',['xy','6','6'],['xy','44','6'],['xy','44','34'],['xy','6','34']]:raise p.Rejected('smoke zone outline differs')
    if case=='necessary':points[2][1]=points[3][1]='24'
    tree.append(sx.parse(AREA));restored=copy.deepcopy(tree);restored.pop()
    if case=='necessary':sx.one(sx.one(sx.children(restored,'zone')[0],'polygon'),'pts')[2][1]=sx.one(sx.one(sx.children(restored,'zone')[0],'polygon'),'pts')[3][1]='44'
    if restored!=original:raise p.Rejected('unexpected owned source edit')
    pc.narrow_source(tree)
    return (sx.dump(tree)+'\n').encode()


def bridge_parent(candidate,nets):
    """Engineered parent: replace eligible GND copper with one known bridge."""
    if nets!={'"GND"'}:raise p.Rejected('one GND zone-net required')
    original=copy.deepcopy(candidate);eligible=s.eligible_routes(candidate,nets,[])
    if any(p.locked(route) for route in p.routes(candidate)):raise p.Rejected('protected control route unsupported')
    if any(sx.one(route,'uuid')==['uuid',json.dumps(BRIDGE_UUID)] for route in p.routes(candidate)):raise p.Rejected('bridge UUID collision')
    result=s.delete_routes(candidate,[s.route_id(route) for route in eligible],nets,[]) if eligible else copy.deepcopy(candidate)
    bridge=sx.parse('(segment (start 10 30) (end 40 30) (width 0.3) (layer "B.Cu") (net "GND") (uuid "'+BRIDGE_UUID+'"))')
    result.append(bridge)
    if p.immutable(result)!=p.immutable(original) or [route for route in p.routes(result) if sx.one(route,'net')[1] not in nets]!=[route for route in p.routes(original) if sx.one(route,'net')[1] not in nets]:
        raise p.Rejected('engineered parent changed non-GND or immutable geometry')
    return result,{'removed_generated_zone_route_ids':[s.route_id(route) for route in eligible],
        'added_bridge_uuid':BRIDGE_UUID,'added_bridge_route_id':s.route_id(bridge),'reference_route_used_for_optimizer':False,
        'scope':'Authored validation witness; never an ordinary SES receipt or C optimizer improvement.'}


def control_observation(case,parent_native,native,parent_metrics,metrics):
    if case not in CASES:raise p.Rejected('unknown pruning control')
    if not p.native_accepted(parent_native):return False,[]
    if native['exclusions'] or not ps.warnings(native)<=ps.warnings(parent_native):return False,[]
    if case=='redundant':return p.native_accepted(native) and ps.improves(metrics,parent_metrics,native,parent_native),[]
    targets=[row for row in native['findings'] if row['type']=='unconnected_items' and row['severity']=='error' and row.get('excluded') is False
        and OUTSIDE_PAD in {item.get('uuid') for item in row['items']} and {INSIDE_PAD,ZONE_UUID}&{item.get('uuid') for item in row['items']}]
    return native['opens']>0 and not p.native_accepted(native) and bool(targets),targets


def validate(folder,source,basis,before_tree,remaining,steps):
    """Reuse production finalizer and pruning lineage checker on every witness."""
    original=p.preflight(source);hashes=inventory(source.parent);job=f.FloorJob(folder,30,remaining)
    candidate=folder/'candidate'/source.name;shutil.copytree(source.parent,candidate.parent);sx.write(candidate,before_tree)
    row={'candidate':str(candidate),'steps':job.steps,'accepted':False,'completed':False}
    try:
        digest,native=p.validate_candidate(job,original,candidate,hashes,[],guidance_contract=f.read_json(basis/'floor-policy.json'),guidance_basis=basis)
        job.native('metrics','metrics',candidate,folder/'metrics.json');metrics=f.read_json(folder/'metrics.json')
        row.update(completed=True,candidate_sha256=digest,native=native,native_report_sha256=p.sha(folder/'final-drc.json'),metrics=metrics)
        ps.check_candidate_stage(folder,row,original,hashes,basis,before_tree);return row
    except (Exception,KeyboardInterrupt) as exc:
        row.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc));raise
    finally:
        steps.extend(job.steps);p.save_json(folder/'witness.json',row)


def experiment(output,*,run_native=False,resume=None):
    if run_native is not True or HERE!=ROOT/'experiments/placement_pruning_controls_v1':raise p.Rejected('ROOT must promote/checkpoint reviewed helpers before --run-native')
    start=time.monotonic();cpu0=shared.cpu();prior_wall=prior_cpu=0.;remaining=lambda:max(0,min(SECONDS-prior_wall-(time.monotonic()-start),SECONDS-prior_cpu-(shared.cpu()-cpu0)))
    out=control_output(output);out.mkdir();protocol=f.read_json(HERE/'PROTOCOL.json');steps=[];completed={};sources={};arms={};arm_dirs={};frozen=None
    record={'schema':1,'status':'incomplete','accepted':False,'controls_passed':False,'observations_complete':False,'routing_quality_gain_claim':False,
        'production_support_extended':False,'family_comparison_eligible':False,'physical_electrical_validation':False,'budget_seconds':SECONDS,'cpu_budget_seconds':SECONDS,
        'output_ceiling_bytes':LIMIT,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protocol_sha256':p.sha(HERE/'PROTOCOL.json'),
        'arms':[],'cases':[],'scope':'Fresh engineered six-pad controls; actual search/C final readback and redundant/necessary GND deletion. No measured-board performance claim.'}
    def account():
        record.update(steps=steps,wall_seconds=prior_wall+time.monotonic()-start,total_cpu_seconds=prior_cpu+shared.cpu()-cpu0,child_step_cpu_seconds=sum(x.get('cpu_seconds') or 0 for x in steps),
            monitor_cpu_seconds=sum(x.get('monitor_cpu_seconds') or 0 for x in steps),native_executed=bool(steps))
        record['within_budget']=remaining()>0
        record['accounting_point']='Stored totals precede summary publication. Final freshness/readback and every parent/waited-child CPU are charged; observed limits, not OS aggregate quotas.'
        if not record['within_budget']:record.update(status='budget_exceeded',controls_passed=False,observations_complete=False)
        if record['status'] in ('invalidated','cancelled','budget_exceeded','failed'):record.update(controls_passed=False,observations_complete=False)
    def stable():
        if size(out)>LIMIT or remaining()<=0:raise p.Rejected('whole control resource cap')
        if frozen is None:return
        if p.tool_manifest()!=record['tools'] or inventory(out/'code')!=frozen:raise p.Rejected('runtime/code/HEAD changed')
        if p.sha(HERE/'PROTOCOL.json')!=record['protocol_sha256']:raise p.Rejected('protocol changed')
        if resume is not None:
            for rel,expected in protocol.get('preserved_prefixes',{}).items():
                if inventory(ROOT/rel)!=expected:raise p.Rejected('prior invocation changed')
        for rel,expected in protocol['input_trees'].items():
            if inventory(ROOT/rel)!=expected:raise p.Rejected('original control seed changed')
        for rel,sha in runtime.items():
            if p.sha(ROOT/rel)!=sha:raise p.Rejected('committed helper changed')
        for source,expected in sources.items():
            if inventory(Path(source).parent)!=expected:raise p.Rejected('derived immutable source changed')
        for folder,expected in completed.items():
            if inventory(Path(folder))!=expected:raise p.Rejected('completed control evidence changed')
    try:
        p.check_storage();tools=p.tool_manifest();record['tools']=tools
        for rel,expected in protocol['input_trees'].items():
            if inventory(ROOT/rel)!=expected:raise p.Rejected('original control seed pins differ')
        runtime=shared.snapshot(out,tools,remaining)
        selected=[*(HERE/name for name in HELPERS),BASE/'smoke.kicad_pcb',TEMPLATE/'fixture.kicad_pro',TEMPLATE/'PROVENANCE.md',*sorted((TEMPLATE/'_licenses').iterdir())]
        for path in selected:
            rel=str(path.relative_to(ROOT));raw=pc.read_bytes(path,LIMIT)
            blob=subprocess.run(['git','show',tools['git_head']+':'+rel],cwd=ROOT,capture_output=True,check=True,timeout=max(.001,min(3,remaining()))).stdout
            if raw!=blob:raise p.Rejected('commit exact control seed/helper first: '+rel)
            target=out/'code'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw);runtime[rel]=shared.sha_bytes(raw)
        if resume is not None:
            resume=shared.owned(resume);pin=protocol['resumable_prefix']
            if resume!=ROOT/pin['directory'] or inventory(resume)!=pin['inventory'] or p.sha(resume/'result.json')!=pin['result_sha256']:raise p.Rejected('resumed prefix differs')
            if p.sha(resume.parent/'execution.json')!=pin['execution_sha256']:raise p.Rejected('prefix execution changed')
            prior=f.read_json(resume/'result.json');execution=f.read_json(resume.parent/'execution.json')
            if prior['status']!='failed' or prior['controls_passed'] is not False or prior['observations_complete'] is not False:raise p.Rejected('resumed prefix state differs')
            prior_wall=execution['wall_seconds']+prior.get('resumed_prefix',{}).get('wall_seconds',0)
            prior_cpu=execution['full_cpu_seconds']+prior.get('resumed_prefix',{}).get('total_cpu_seconds',0)
            additional=pin.get('additional_prior_execution')
            if additional:
                old=ROOT/additional['path']
                if p.sha(old)!=additional['sha256']:raise p.Rejected('earlier setup failure changed')
                cost=f.read_json(old);prior_wall+=cost['wall_seconds'];prior_cpu+=cost['full_cpu_seconds']
            if not all(type(x) in (int,float) and 0<=x<SECONDS for x in (prior_wall,prior_cpu)):raise p.Rejected('invalid resumed cost')
            steps.extend(prior['steps']);completed[str(resume)]=pin['inventory']
            record['resumed_prefix']={'directory':str(resume),'result_sha256':pin['result_sha256'],'wall_seconds':prior_wall,'total_cpu_seconds':prior_cpu,'all_prior_failures_retained':True}
            for arm,arm_pin in pin['reused_arms'].items():
                folder=shared.owned(ROOT/arm_pin['directory'])
                if p.sha(folder/'result.json')!=arm_pin['result_sha256']:raise p.Rejected('completed arm changed')
                receipt=f.read_json(folder/'result.json');p.check_result(folder/'result.json')
                if receipt['accepted'] is not True or receipt['input_policy']!=f.SEARCH_POLICY or receipt['engine_profile']!=arm or receipt['scoring_variant']!='via_default':raise p.Rejected('resumed arm differs')
                arms[arm]=receipt;arm_dirs[arm]=folder;record['arms'].append({'arm':arm,'reused_completed_control':True,'receipt':str(folder/'result.json'),'result_sha256':p.sha(folder/'result.json'),'accepted':True,'status':receipt['status'],'native':receipt['native'],'metrics':receipt['metrics']})
        record['runtime_sources']=runtime;frozen=inventory(out/'code');record['code_inventory']=frozen
        for case in CASES:
            folder=out/'sources'/case;folder.mkdir(parents=True);source=folder/'fixture.kicad_pcb'
            source.write_bytes(derive(pc.read_bytes(BASE/'smoke.kicad_pcb'),case));shutil.copy2(TEMPLATE/'fixture.kicad_pro',folder/'fixture.kicad_pro')
            shutil.copytree(TEMPLATE/'_licenses',folder/'_licenses');(folder/'PROVENANCE.md').write_text(NOTICE)
            sources[str(source)]=inventory(folder);p.preflight(source);record.setdefault('source_hashes',{})[case]=sources[str(source)]
        for arm in ARMS:
            if arm in arms:continue
            stable();source=Path(next(key for key in sources if Path(key).parent.name==('necessary' if arm=='necessary_tuned' else 'redundant')))
            cap=protocol['arm_assignment_seconds'][arm]
            if remaining()<cap+15:raise p.Rejected('control next-stage reserve unavailable')
            folder=out/arm
            try:
                receipt=ps.prune(source,folder,cap) if arm=='C' else f.route(source,folder,cap,False,'both','standard' if arm=='standard' else 'tuned','via_default',guidance_policy=f.SEARCH_POLICY)
            finally:
                if (folder/'result.json').is_file():
                    actual=f.read_json(folder/'result.json');steps.extend(actual.get('steps',[]));record['arms'].append({'arm':arm,'receipt':str(folder/'result.json'),'result_sha256':p.sha(folder/'result.json'),'accepted':actual['accepted'],'status':actual['status'],'native':actual.get('native'),'metrics':actual.get('metrics')})
            if receipt['accepted'] is not True:raise p.Rejected('fresh '+arm+' rejected: '+str(receipt.get('reason',receipt['status'])))
            p.check_result(folder/'result.json');arms[arm]=receipt;arm_dirs[arm]=folder;completed[str(folder)]=inventory(folder);stable()
        for case,basis_arm in (('redundant','tuned'),('necessary','necessary_tuned')):
            stable();basis=arm_dirs[basis_arm];receipt=arms[basis_arm];source=Path(receipt['source']);tree=sx.read(Path(receipt['candidate']));nets=s.zone_net_ids(p.preflight(source))
            before,recipe=bridge_parent(tree,nets);row={'case':case,'passed':False,'parent_recipe':recipe};record['cases'].append(row)
            parent=validate(out/'controls'/case/'parent',source,basis,before,remaining,steps);row['parent']=parent
            if not p.native_accepted(parent['native']) or not ps.warnings(parent['native'])<=ps.warnings(receipt['native']):raise p.Rejected('engineered bridge parent rejected or adds warnings')
            parent_board=Path(parent['candidate']);proposal=s.proposals(sx.read(parent_board),nets,[],True)
            if len(proposal)!=1 or proposal[0]['net']!='"GND"' or len(proposal[0]['route_ids'])!=1:raise p.Rejected('exact authored GND bridge proposal required')
            row['proposal']=proposal[0];after=ps.deletion(parent_board,proposal[0],nets)
            deleted=validate(out/'controls'/case/'deletion',source,basis,after,remaining,steps);row['deletion']=deleted
            row['passed'],row['targeted_findings']=control_observation(case,parent['native'],deleted['native'],parent['metrics'],deleted['metrics'])
            p.save_json(out/'controls'/case/'case.json',row);completed[str(out/'controls'/case)]=inventory(out/'controls'/case)
            if not row['passed']:raise p.Rejected('native '+case+' deletion observation differs')
            stable()
        record.update(status='controls_passed',controls_passed=True,observations_complete=True,original_inputs_unchanged=True,completed_evidence=completed)
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,observations_complete=False,error=type(exc).__name__+': '+str(exc))
    # Use the existing fail-closed publication path. This diagnostic never sets
    # accepted=True or manufactures a production receipt for authored parents.
    return f.publish(out,record,stable,account,remaining)


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--run-native',action='store_true');ap.add_argument('--resume',type=Path);args=ap.parse_args(argv)
    if not args.run_native:ap.error('--run-native required after committed promotion')
    prior={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in prior:signal.signal(sig,interrupted)
        with shared.owned(ROOT/'.runs/quality-experiment.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=experiment(args.output,run_native=True,resume=args.resume)
    finally:
        for sig,handler in prior.items():signal.signal(sig,handler)
    print(json.dumps({key:result[key] for key in ('status','controls_passed','routing_quality_gain_claim')}))
    return 0 if result['controls_passed'] else 2
if __name__=='__main__':raise SystemExit(main())
