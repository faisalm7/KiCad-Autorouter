"""Bounded owned named-edge Native controls; never run a routing engine.

SPDX-License-Identifier: GPL-3.0-or-later
Attempt006: source Native and all20 prepared files reused from failed005.
The failure was an experiment predicate bug, not a source-design conflict. Reuses
the existing jobs, candidate validation, stage/process/PRL replay and publisher.
"""
import time
START = time.monotonic()
import resource

def cpu():
    return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path
import argparse
import json
import sys
from types import SimpleNamespace
ROOT = next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,sexpr as sx,placement_clearance as pc,handoff as h,local_settings as ls
from autorouter.strategy import _warning_signatures
from autorouter.provenance import _git
from experiments.native_edge_named_v1 import driver as importer
from experiments.native_edge_named_v1.prospective_threshold_v1 import controller as previous
from experiments.placement_handoff_native_v1.driver import copy_bytes

HERE=Path(__file__).resolve().parent
BASE=importer.BASE/'threshold-prospective-006'
SETUP=previous.SETUP
PLAN=BASE/'plan-002.json'
PREVIOUS_PLAN_PIN='2b0f6e9f3719a5226b4b8e6b22fa5ffb486d09524cf645ee4bea6e4004a3f3f6'
PREVIOUS_RESULT_PIN='dc604d384ea96e64e0add4c4ed0b3941abc738101c11d68ce9cc371f82d0633f'
PREVIOUS_CONTROLLER_PIN='e67cf0954b6b12e4301521d2d78210d7a7705c4aca68f8a1d5ec60cabed7cba3'
PREVIOUS_PROTOCOL_PIN='c44d68b28855ff29d19023b42b0b6f874f3ffe527a7eb46727c8ae4e784fb54b'
OUT=BASE/'native-controls'
SOURCE=importer.BASE/'sources/literal300/owned-named-edge-literal300.kicad_pcb'
IMPORT_PIN='67766d0b978dc47ac1398bb3d0891125cfb83ef3b41d0855e6e8e972500920be'
IMPORT_RESULT_PIN='c73ce88b36c7efb11092db55f918f08c1aaaa638dbd4468a8678dd25cacb591a'
IMPORT_OBSERVATION_PIN='98103ab1c739aabaf191a97376077d9767b66ed0ae208f0e6e9bc083d953d076'
SECONDS=180.0
PUBLICATION_CHARGE=4.0
LIMIT=64*1024**2
CASES=(('track_allowed_035','track','6.55',True),('track_below_025','track','6.45',False),
       ('via_allowed_035','via','6.95',True),('via_below_025','via','6.85',False))

def require(value,reason):
    if not value:raise p.Rejected(reason)
def read(path):return pc.read_bytes(path,LIMIT)
def inventory(path,*,contents=False):return pc.inventory(path,contents=contents,max_bytes=LIMIT,max_files=2048,max_entries=4096)
def save(path,data):
    with path.open('x') as stream:json.dump(data,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
def remaining():return min(SECONDS-(time.monotonic()-START),SECONDS-(cpu()-CPU0))
def own_code():
    files=[Path(__file__),HERE/'PROTOCOL006.json',ROOT/'experiments/placement_handoff_native_v1/driver.py']
    return {str(path.relative_to(ROOT)):p.sha(path) for path in files}

def prerequisite(receipt_pin):
    require(receipt_pin==IMPORT_RESULT_PIN,'explicit reviewed importer004 receipt pin required')
    data=importer.frozen(importer.IMPORT_EXECUTION/'result.json',receipt_pin)
    protocol=importer.frozen(importer.IMPORT_PROTOCOL,IMPORT_PIN)
    plan=importer.frozen(importer.PLAN,protocol['source_plan_sha256']);importer.check_source_plan(plan)
    require(data.get('passed') is True and data.get('status')=='completed' and data.get('actual_imports')==9
            and data.get('protocol_sha256')==IMPORT_PIN and data.get('accepted') is False
            and data.get('production_admitted') is False and data.get('routing_executed') is False
            and data.get('native_executed') is False,'actual qualified nine-load importer004 required')
    expected=[*f.SANDBOX,str(c.JAVA),'-Xmx512m','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true',
              '--class-path',str(c.JAR),str(importer.HERE/'NamedEdgeManagerProbe.java'),
              str(importer.BASE/'import-inputs'),str(importer.IMPORT_EXECUTION/'observation.json')]
    f.process_check(importer.IMPORT_EXECUTION,data,'importer',expected)
    require(p.sha(importer.IMPORT_EXECUTION/'observation.json')==data['observation_sha256']==IMPORT_OBSERVATION_PIN
            and p.sha(importer.IMPORT_EXECUTION/'command.log')==data['log_sha256'], 'qualified importer outputs changed')
    return dict(receipt_sha256=receipt_pin,import_protocol_sha256=IMPORT_PIN,
                material_sha256=inventory(importer.IMPORT_EXECUTION))

def source_predicate(native):
    require(native['opens']==2 and native['blocking']==0 and native['exclusions']==0,
            'original source differs from exactly two expected unrouted pairs')
    errors=[row for row in native['findings'] if row['severity']=='error']
    require(len(errors)==2 and all(row['type']=='unconnected_items' for row in errors),
            'original source has errors beyond exactly two expected unconnected_items')
    require(p.native_rejection_reasons(native)==[
                'native error finding: unconnected_items','native opens=2',
                'policy-critical native finding: unconnected_items (error)'],
            'original source has policy conflicts beyond expected unrouted pairs')

def previous_source():
    require(p.sha(Path(previous.__file__))==PREVIOUS_CONTROLLER_PIN
            and p.sha(HERE/'PROTOCOL.json')==PREVIOUS_PROTOCOL_PIN,'failed005 source/protocol changed')
    old_plan=importer.frozen(SETUP/'plan.json',PREVIOUS_PLAN_PIN);previous.check_plan(old_plan)
    data=importer.frozen(previous.OUT/'result.json',PREVIOUS_RESULT_PIN)
    require(data.get('passed') is False and data.get('status')=='failed' and data.get('cases')==[]
            and data.get('plan_sha256')==PREVIOUS_PLAN_PIN
            and data.get('first_failure')==dict(type='Rejected',message='original source has conflicts beyond expected unrouted pairs'),
            'failed005 must remain the exact source-predicate controller failure with no candidates')
    now=p.tool_manifest();old=data['tools']
    require(all(now[key]==old[key] for key in ('implementation_sha256','files','kicad','freerouting','network',
                'normal_drc_local_settings_policy','normal_selected_proposal_import_policy','normal_native_export_alias_policy')),
            'source Native tool/runtime pins changed')
    job=SimpleNamespace(out=previous.OUT/'source-job',steps=data['source_steps'])
    native=f.check_drc_stage(job.out,{'steps':job.steps},'source-drc',SETUP/'original'/SOURCE.name,
            job.out/'source-drc-input'/SOURCE.name,False,old_plan['source_sha256'],schematic_parity=True)
    require(native==data['source_native'],'retained005 source Native proof changed');source_predicate(native)
    proof=dict(frozen_plan_sha256=PREVIOUS_PLAN_PIN,failed_result_sha256=PREVIOUS_RESULT_PIN,
               failed_controller_sha256=PREVIOUS_CONTROLLER_PIN,failed_protocol_sha256=PREVIOUS_PROTOCOL_PIN,
               prepared_material_sha256=inventory(SETUP),failed_material_sha256=inventory(previous.OUT),
               source_job_material_sha256=inventory(job.out),source_job=str(job.out),
               historical_inner_sample_costs={key:data[key] for key in ('inner_sample_wall_seconds','inner_sample_full_cpu_seconds',
                    'charged_wall_seconds','charged_full_cpu_seconds')},
               failure_classification='experiment-source-predicate-bug; source Native completed; no candidate Native executed')
    return old_plan,job,native,proof

def freeze(receipt_pin):
    require(not PLAN.exists() and not OUT.exists(),'fresh006 plan/output required')
    old_plan,job,native,reuse=previous_source();proof=prerequisite(receipt_pin)
    record=dict(schema=1,kind='named-edge-native-threshold-plan-v1',accepted=False,production_admitted=False,
                routing_executed=False,source=str(SOURCE),source_sha256=old_plan['source_sha256'],qualification=proof,
                cases=old_plan['cases'],reused005=reuse,prepared_root=str(SETUP),
                code_sha256=own_code(),runtime_sha256=importer.code_pins(),tools_sha256=importer.tools_pins(),
                protocol_sha256=p.sha(HERE/'PROTOCOL006.json'),budget_seconds=SECONDS,
                preparation_wall_seconds=time.monotonic()-START,preparation_full_cpu_seconds=cpu()-CPU0)
    BASE.mkdir(exist_ok=True);save(PLAN,record)
    return dict(plan=str(PLAN),sha256=p.sha(PLAN),workers_executed=False)

def check_plan(plan):
    require(plan.get('schema')==1 and plan.get('kind')=='named-edge-native-threshold-plan-v1'
            and plan.get('accepted') is False and plan.get('production_admitted') is False
            and plan.get('routing_executed') is False and plan.get('budget_seconds')==SECONDS
            and plan.get('prepared_root')==str(SETUP),'threshold006 plan scope changed')
    require(own_code()==plan['code_sha256'] and importer.code_pins()==plan['runtime_sha256']
            and importer.tools_pins()==plan['tools_sha256'],'threshold006 source/tools changed')
    require(prerequisite(plan['qualification']['receipt_sha256'])==plan['qualification'],'qualified importer changed')
    old_plan,job,native,reuse=previous_source()
    require(reuse==plan['reused005'] and old_plan['source_sha256']==plan['source_sha256']
            and old_plan['cases']==plan['cases'],'retained005 prepared/source proof changed')
    return job,native

def result_predicate(native,source_native,positive):
    require(native['opens']==0 and native['exclusions']==0,'control is open/excluded')
    require(_warning_signatures(native)==_warning_signatures(source_native)
            and native['ignored_checks']==source_native['ignored_checks'],'warnings or ignored checks changed')
    if positive:
        require(p.native_accepted(native),'allowed original-rule threshold rejected')
    else:
        errors=[row for row in native['findings'] if row['severity']=='error']
        require(errors and all(row['type']=='copper_edge_clearance' for row in errors)
                and native['blocking']==len(errors) and not p.native_accepted(native),
                'below-threshold control lacks only intended Native edge errors')
        require(set(p.native_rejection_reasons(native))=={'native blocking='+str(len(errors)),
                    'native error finding: copper_edge_clearance',
                    'policy-critical native finding: copper_edge_clearance (error)'},'negative rejected for unrelated policy failure')

def case_readback(row,source_hashes,original,source_native):
    folder=OUT/row['case'];job=folder/'job';board=folder/'candidate'/SOURCE.name;data={'steps':row['steps']}
    require(p.sha(board)==row['candidate_sha256'],'candidate changed after Native validation')
    p.verify_candidate_files(board,source_hashes,row['candidate_sha256'])
    require(p.immutable(sx.read(board))==p.immutable(original)
            and all(route in p.routes(sx.read(board)) for route in p.routes(original)), 'original/protected design changed')
    require(read(job/'pre-refill.kicad_pcb')==read(SETUP/row['case']/SOURCE.name),'actual Native preimage differs from frozen candidate')
    before={**source_hashes,SOURCE.name:p.sha(job/'pre-refill.kicad_pcb')};refill=job/'refill'/SOURCE.name
    f.check_drc_stage(job,data,'refill-drc',refill,refill,True,before)
    require((sx.dump(p.transplant_fill(sx.read(job/'pre-refill.kicad_pcb'),sx.read(refill)))+'\n').encode()==read(board),
            'candidate differs from its actual saved refill')
    native=f.check_drc_stage(job,data,'final-drc',board,job/'final-drc-input'/SOURCE.name,False,
                             {**source_hashes,SOURCE.name:row['candidate_sha256']},schematic_parity=True)
    require(native==row['native'],'final Native report changed')
    mapping=f.read_json(job/'final-netclasses.json')
    f.process_check(job,data,'final-netclasses', [*f.SANDBOX,str(c.PYTHON),str(ROOT/'autorouter/native.py'),
                                                'netclasses',str(board),str(job/'final-netclasses.json')])
    audited=p.audit_candidate_netclasses(board,p.routes(original),mapping);audited['native_map_file_sha256']=p.sha(job/'final-netclasses.json')
    require(audited==f.read_json(job/'final-netclass-audit.json')==row['class_audit'],'fresh class/dimension proof changed')
    require(audited['route_dimensions']['checked']==dict(segments=5,arcs=0,vias=int(row['kind']=='via'),protected=1),
            'control missed exact generated route/dimension coverage')
    result_predicate(native,source_native,row['positive'])

@importer.cancellable_phase
def native_controls(plan_pin):
    plan=importer.frozen(PLAN,plan_pin);source_job,source_native=check_plan(plan)
    require(not OUT.exists(),'fresh threshold Native output required');OUT.mkdir();owner={};h.capture_destination(owner,OUT)
    tools=p.tool_manifest()
    # Reuse the existing exact Git reader: no uncommitted controller/protocol is
    # allowed to start real workers. A later checkpoint may change HEAD only.
    for name,pin in plan['code_sha256'].items():
        raw=_git(ROOT,'show',tools['git_head']+':'+name,limit=2*1024**2)
        require(importer.digest(raw)==pin,'checkpoint exact threshold source before Native execution')
    original=sx.read(SETUP/'original'/SOURCE.name);source_hashes=plan['source_sha256'];rows=[];witness=None
    # Initial complete qualification has already run above. Retain byte witnesses
    # of its finite dependencies, not another complete semantic replay per case.
    engine_plan=f.read_json(importer.PLAN)
    input_trees={SETUP:plan['reused005']['prepared_material_sha256'],previous.OUT:plan['reused005']['failed_material_sha256'],importer.IMPORT_EXECUTION:plan['qualification']['material_sha256'],
                 importer.BASE/'native-preparation':engine_plan['reused_native_preparation']['native_preparation_material_sha256'],
                 importer.BASE/'import-inputs':engine_plan['reused_import_inputs_after_failed001']['prior_inputs_sha256'],
                 importer.BASE/'import-execution':engine_plan['reused_import_inputs_after_failed001']['failed001_material_sha256']}
    input_trees.update({importer.BASE/'sources'/name:hashes for name,hashes in engine_plan['sources'].items()})
    input_files=dict(engine_plan['retained_sha256'])
    input_files.update({str(Path(previous.__file__).relative_to(ROOT)):PREVIOUS_CONTROLLER_PIN,
                        str((HERE/'PROTOCOL.json').relative_to(ROOT)):PREVIOUS_PROTOCOL_PIN})
    for path in (importer.PLAN,importer.PRIOR_PLAN,importer.IMPORT_PROTOCOL,importer.BASE/'source-plan-003.json',importer.BASE/'import-protocol.json'):
        input_files[str(path.relative_to(ROOT))]=p.sha(path)
    input_files.update({str((importer.BASE/name).relative_to(ROOT)):pin for name,pin in importer.OUTLINE_PROOF_PINS.items()})
    completed_trees={}
    record=dict(schema=1,kind='named-edge-native-threshold-controls-v1',accepted=False,passed=False,status='incomplete',
                whole_project_drc_clean=False,production_admitted=False,routing_executed=False,budget_seconds=SECONDS,
                plan_sha256=plan_pin,tools=tools,reused005=plan['reused005'],source_native=source_native,source_steps=source_job.steps,preparation_costs={k:plan[k] for k in ('preparation_wall_seconds','preparation_full_cpu_seconds')},cases=rows,
                publication_charge_seconds=PUBLICATION_CHARGE,
                accounting_point='Inner pre-final-replay sample plus conservative4s publication charge; not whole process lifetime. Actual final remaining gate and lead whole-process wall/CPU acceptance<=180s remain mandatory.')
    def late_prls():
        pairs=[] if source_native is None else [(source_job.out,'source-drc')]
        pairs += [(OUT/row['case']/'job',stage) for row in rows for stage in ('refill-drc','final-drc')]
        for directory,stage in pairs:ls.check_event(directory,f.read_json(directory/(stage+'-binding.json')),f.read_json(directory/(stage+'-process.json')))
    def stable():
        h.owned_destination(owner);importer.frozen(PLAN,plan_pin)
        require(p.tool_manifest()==tools,'Native control tool/runtime context changed')
        require(own_code()==plan['code_sha256'] and importer.code_pins()==plan['runtime_sha256'],'prepared code changed')
        importer.checked_pins(input_files)
        for path,expected in (*input_trees.items(),*completed_trees.items()):
            require(inventory(path)==expected,'prepared/source/importer/completed evidence changed: '+str(path))
        if witness is not None:require({k:v for k,v in inventory(OUT).items() if k!='result.json'}==witness,'completed Native evidence changed')
        late_prls()
    def final_replay():
        # One complete semantic replay after publication, then final byte/PRL
        # freshness and deadline. No semantic validators run in stable().
        replay_job,replay_native=check_plan(plan)
        require(replay_job.out==source_job.out and replay_job.steps==source_job.steps and replay_native==source_native,
                'retained source proof differs during final replay')
        for row in rows:case_readback(row,source_hashes,original,source_native)
        stable()
        require(remaining()>0,'whole Native deadline exhausted during final replay')
    def account():
        wall,full_cpu=time.monotonic()-START,cpu()-CPU0
        record.update(inner_sample_wall_seconds=wall,inner_sample_full_cpu_seconds=full_cpu,
                      charged_wall_seconds=wall+PUBLICATION_CHARGE,charged_full_cpu_seconds=full_cpu+PUBLICATION_CHARGE)
        if remaining()<=0 or max(wall,full_cpu)+PUBLICATION_CHARGE>=SECONDS:record.update(passed=False,status='budget_exceeded')
        elif record['status'] in ('failed','invalidated','cancelled'):record['passed']=False
    with importer.lane():
        try:
            p.preflight(SETUP/'original'/SOURCE.name)
            require(p.check_schematic_class_support(SETUP/'original'/SOURCE.name) is None,'unexpected schematic class directives')
            # Source006 is the exact completed005 Native/field/process/PRL proof.
            # check_plan already replayed it fully; no Native source worker is repeated.
            for prepared in plan['cases']:
                stable();folder=OUT/prepared['case'];folder.mkdir();copy_bytes(inventory(SETUP/prepared['case'],contents=True),folder/'candidate')
                candidate=folder/'candidate'/SOURCE.name
                job=f.FloorJob(folder/'job',SECONDS,remaining,protect_local_settings=True)
                digest,native=p.validate_candidate(job,original,candidate,source_hashes,p.routes(original),schematic_parity=True)
                row={**{k:prepared[k] for k in ('case','kind','x_mm','positive')},'candidate_sha256':digest,
                     'native':native,'steps':job.steps,'class_audit':f.read_json(job.out/'final-netclass-audit.json')}
                rows.append(row);case_readback(row,source_hashes,original,source_native)
                completed_trees[folder]=inventory(folder)
            require(remaining()>PUBLICATION_CHARGE,'Native control publication reserve exhausted')
            witness=inventory(OUT);record.update(passed=True,status='completed')
        except (Exception,KeyboardInterrupt) as exc:
            record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',reason=type(exc).__name__+': '+str(exc))
            record['first_failure']=dict(type=type(exc).__name__,message=str(exc))
        f.publish(OUT,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final_replay)
    return record

def main():
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument('phase',choices=('freeze','run-native'));args.add_argument('--sha256');args.add_argument('--allow-native',action='store_true')
    options=args.parse_args()
    if options.phase=='freeze':result=freeze(options.sha256)
    else:
        require(options.allow_native,'explicit --allow-native required; lead owns foreground lane');result=native_controls(options.sha256)
    print(json.dumps({k:v for k,v in result.items() if k in ('plan','sha256','workers_executed','passed','status','reason','wall_seconds','full_cpu_seconds')}))
    return 0 if result.get('passed',True) else 2
if __name__=='__main__':raise SystemExit(main())
