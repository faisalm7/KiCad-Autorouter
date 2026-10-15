"""Owned exposed full-schematic/effective-field toolchain diagnostic.

Uses existing Native/process/PRL/original-shell/publication helpers. This is
qualification evidence for this fixture, never production route admission.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,sys,time
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)];sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,handoff as h,schematic_field_evidence as fields
import fixture
BOARD=fixture.STEM+'.kicad_pcb'
PRL=fixture.STEM+'.kicad_prl'
SECONDS=180
VERSIONS=('10.0.0','10.0.7')
PREREQUISITES={'.runs/kicad-1007-bundle-qualification-001/result.json':'26564ecd90268e463760270902d302445d9b0e6859105d3ed06e5976a8989c73','.runs/native-rule-area-toolchain-001/result.json':'8705387a1089b30fce98d021eecf2617bde9adfb341c6859c2170945fe673efa','.runs/native-rule-area-toolchain-readback-001/execution.json':'714bb2314d9df89a6a14db32e3dc2457d0b23eaf6be558ca6a2061883aec88b3'}


def retained_case(directory,row,nt):
    """One shared retained-reader path for producer and later independent use."""
    directory=Path(directory);jobdir=directory/'native';source=directory/'source'/BOARD
    expected_source={name:hashlib.sha256(raw).hexdigest() for name,raw in fixture.files(row['case']).items()}
    if row['source_files']!=expected_source or p.tree_hash(source.parent)!=expected_source:raise p.Rejected('authored control source changed')
    candidate=jobdir/'candidate'/BOARD;filled=jobdir/'refill'/BOARD
    if p.sha(candidate)!=row['candidate_sha256']:raise p.Rejected('final candidate hash differs')
    p.verify_candidate_files(candidate,row['source_files'],row['candidate_sha256'])
    original=sx.read(source)
    if p.immutable(original)!=p.immutable(sx.read(candidate)) or p.routes(original)!=p.routes(sx.read(candidate)):
        raise p.Rejected('original-shell control geometry/routes changed')
    parity_options=dict(schematic_parity=True,native_toolchain=nt,experimental_schematic_parity=nt is not None)
    saved=f.check_drc_stage(jobdir,row,'refill-drc',filled,filled,True,expected_source,**parity_options)
    if p.transplant_fill(original,sx.read(filled))!=sx.read(candidate):raise p.Rejected('final original-shell candidate differs from saved Native refill reconstruction')
    final=f.check_drc_stage(jobdir,row,'final-drc',candidate,jobdir/'final-drc-input'/BOARD,False,row['candidate_files'],**parity_options)
    if saved!=row['saved_refill'] or final!=row['final_native']:raise p.Rejected('derived native summary differs')
    if p.sha(jobdir/'refill-drc.json')!=row['saved_refill_report_sha256'] or p.sha(jobdir/'final-drc.json')!=row['final_report_sha256']:
        raise p.Rejected('actual report bytes differ')
    for observed in (saved,final):
        proof=observed.get('field_parity',{});qualification=proof.get('qualification',{})
        if not fields.has_fields(observed['findings']):raise p.Rejected('control did not exercise actual native first field finding')
        if observed['opens'] or observed['blocking'] or observed['exclusions']:raise p.Rejected('control has unintended connectivity/blocking/excluded findings')
        if row['case']=='positive':
            if not p.native_accepted(observed) or qualification.get('qualified') is not True or qualification.get('component_count')!=4:
                raise p.Rejected('owned positive failed complete field qualification')
        elif row['case']=='hidden_later_custom_field':
            if p.native_accepted(observed) or qualification.get('qualified') is not False or fixture.FIELD not in qualification.get('reason',''):
                raise p.Rejected('hidden later field did not reject for its intended reason')
        else:raise p.Rejected('unknown control case')
    for project in (source.parent,candidate.parent,filled.parent,jobdir/'final-drc-input'):
        if p.sha(project/PRL)!=row['source_files'][PRL]:
            raise p.Rejected('preexisting local settings changed')
    if p.tree_hash(source.parent)!=row['source_files']:raise p.Rejected('source changed during control readback')
    return {'passed':True,'candidate_sha256':p.sha(candidate),'final_native_counts':{k:final[k] for k in ('opens','blocking','warnings','exclusions')},
        'complete_field_qualified':final['field_parity']['qualification']['qualified'],'native_accepted':p.native_accepted(final),'prl_preserved':True,
        'original_shell_and_routes_preserved':True,'actual_saved_refill_checked':True}


def experiment(output,proof_path):
    if output.parent.parent!=ROOT/'.runs' or output.exists() or output.is_symlink():raise p.Rejected('fresh output in a direct .runs execution folder required')
    start=time.monotonic();cpu=time.process_time()+f.child_cpu()
    if proof_path!=ROOT/'.runs/kicad-1007-bundle-qualification-001/result.json' or any(p.sha(ROOT/name)!=pin for name,pin in PREREQUISITES.items()):raise p.Rejected('fixed actual toolchain prerequisites differ')
    area=f.read_json(ROOT/'.runs/native-rule-area-toolchain-001/result.json')
    review=f.read_json(ROOT/'.runs/native-rule-area-toolchain-readback-001/execution.json')['process']
    if area.get('controls_passed') is not True or area.get('native_toolchain_qualified') is not True or review.get('status')!='success' or review.get('exit_code')!=0 or review.get('cleanup_complete') is not True or review.get('log_truncated') is not False:raise p.Rejected('prior actual area control qualification missing')
    proof=f.read_json(proof_path)
    if proof.get('status')!='signed_bundle_observed' or proof.get('signature_verified') is not True or proof.get('notarization_verified') is not True:
        raise p.Rejected('previous actual signed bundle observations required')
    nt=p.ExperimentalNativeToolchain.from_record(proof['experimental_native_toolchain'])
    proof_pin=p.sha(proof_path);tools=p.tool_manifest()
    code={str(x):p.sha(x) for x in Path(__file__).resolve().parent.glob('*.py')}
    output.mkdir();owner={};h.capture_destination(owner,output);rows=[];completed={}
    record=dict(schema=1,kind='owned_complete_schematic_toolchain_controls',status='incomplete',accepted=False,controls_passed=False,
        production_admitted=False,routing_scope_accepted=False,physical_electrical_validation=False,
        versions=list(VERSIONS),budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,tools=tools,code_sha256=code,
        signature_proof=str(proof_path),signature_proof_sha256=proof_pin,prerequisites_sha256=PREREQUISITES,experimental_native_toolchain=nt.record(),cases=rows,
        scope='Owned exposed four-terminal two-net source; literal fullSCH and hidden later custom-field control on10.0.0 and explicit10.0.7. Actual saved zone refill and original-shell final parity with unchanged original rules and preexisting PRL. No engine/GUI/production routing migration, benchmark gain, untouched-family, human/electrical/physical claim.')
    def remaining():return max(0,min(SECONDS-(time.monotonic()-start),SECONDS-(time.process_time()+f.child_cpu()-cpu)))
    def stable():
        h.owned_destination(owner);nt.check()
        if remaining()<=0:raise p.Rejected('whole diagnostic wall/fullCPU budget exhausted')
        if any(p.sha(ROOT/name)!=pin for name,pin in PREREQUISITES.items()):raise p.Rejected('fixed actual prerequisite changed')
        if p.sha(proof_path)!=proof_pin or p.tool_manifest()!=tools:raise p.Rejected('frozen source/tool/prerequisite changed')
        if any(p.sha(Path(name))!=pin for name,pin in code.items()):raise p.Rejected('diagnostic code changed')
        if any(p.tree_hash(Path(name))!=inventory for name,inventory in completed.items()):raise p.Rejected('completed control evidence changed')
        if remaining()<=0:raise p.Rejected('diagnostic budget exhausted during freshness checks')
    def account():
        record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu,within_budget=remaining()>0)
        if not record['within_budget'] or record['status']!='completed':record['controls_passed']=False
    try:
        stable()
        for version in VERSIONS:
            for case in fixture.CASES:
                stable();directory=output/(version+'-'+case);directory.mkdir();source=directory/'source'
                fixture.write_project(source,case);source_board=source/BOARD;before=p.tree_hash(source)
                current=nt if version=='10.0.7' else None
                job=f.FloorJob(directory/'native',remaining(),remaining,native_toolchain=current,protect_local_settings=True,experimental_schematic_parity=current is not None)
                shutil.copytree(source,job.out/'candidate');candidate=job.out/'candidate'/BOARD
                shutil.copytree(source,job.out/'refill');filled=job.out/'refill'/BOARD
                saved=job.drc('refill-drc',filled,save=True,schematic_parity=True)
                rebuilt=p.transplant_fill(sx.read(source_board),sx.read(filled));sx.write(candidate,rebuilt)
                candidate_files=p.tree_hash(candidate.parent)
                final=job.drc('final-drc',candidate,schematic_parity=True)
                row=dict(version=version,case=case,source_files=before,candidate_files=candidate_files,candidate_sha256=p.sha(candidate),saved_refill=saved,final_native=final,
                    saved_refill_report_sha256=p.sha(job.out/'refill-drc.json'),final_report_sha256=p.sha(job.out/'final-drc.json'),steps=job.steps)
                rows.append(row);row['checks']=retained_case(directory,row,current)
                completed[str(directory)]=p.tree_hash(directory);stable()
        for version in VERSIONS:
            pair=[r for r in rows if r['version']==version]
            if len(pair)!=2:raise p.Rejected('complete control population missing')
            first=[r for r in pair if r['case']=='positive'][0]['final_native']
            second=[r for r in pair if r['case']=='hidden_later_custom_field'][0]['final_native']
            if first['findings']!=second['findings'] or first['ignored_checks']!=second['ignored_checks']:
                raise p.Rejected('hidden later-field control changed first native findings')
        record.update(status='completed',controls_passed=True,completed_evidence=completed)
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
    f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    print(json.dumps({k:record.get(k) for k in ('status','controls_passed','wall_seconds','total_cpu_seconds','error')}))
    return record['status']=='completed' and record['controls_passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');parser.add_argument('--output',type=Path,required=True);parser.add_argument('--toolchain-proof',type=Path,required=True);args=parser.parse_args()
    if not args.run_native:parser.error('explicit --run-native required')
    raise SystemExit(0 if experiment(args.output,args.toolchain_proof) else 2)
