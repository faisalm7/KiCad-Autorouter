"""Prospective four-case saved-refill/original-shell rule-area qualification.

Uses shared process, native binding, parsing and publication helpers. This is
an experimental toolchain diagnostic; production admission remains false.
"""
from pathlib import Path
import argparse,importlib.util,json,shutil,sys,time
ROOT=next(parent for parent in Path(__file__).resolve().parents if (parent/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).resolve().parent));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,handoff as h
import fixture_recipe as recipe
import native_areas as worker
from native_expected import native_expected
BASE=ROOT/'evidence/placement-area-native-001'
SUMMARY_SHA='c61d54b5508f0508528e1236ead7bf97ad21ef336e32448994c6239db56b058f'
SECONDS=120

def experiment(output,proof_path):
    if output.parent!=ROOT/'.runs' or output.exists() or output.is_symlink():raise p.Rejected('fresh direct .runs output required')
    started=time.monotonic();cpu=time.process_time()+f.child_cpu()
    proof=f.read_json(proof_path)
    if (proof.get('status')!='signed_bundle_observed' or proof.get('signature_verified') is not True
            or proof.get('notarization_verified') is not True):raise p.Rejected('actual normally assessed signed bundle proof required')
    nt=p.ExperimentalNativeToolchain.from_record(proof['experimental_native_toolchain'])
    summary=BASE/'summary.json'
    if p.sha(summary)!=SUMMARY_SHA:raise p.Rejected('original control expectation summary pin differs')
    old=f.read_json(summary)
    if p.sha(summary)!=SUMMARY_SHA:raise p.Rejected('original control expectation summary changed during capture')
    output.mkdir();owner={};h.capture_destination(owner,output)
    tools=p.tool_manifest();proof_pin=p.sha(proof_path)
    sources={case:p.tree_hash(BASE/case/'candidate') for case in recipe.CASES}
    code={str(x):p.sha(x) for x in Path(__file__).resolve().parent.glob('*.py')}
    completed={};rows=[]
    record=dict(schema=1,kind='explicit_1007_native_rule_area_controls',status='incomplete',accepted=False,
        production_admitted=False,routing_scope_accepted=False,controls_passed=False,native_toolchain_qualified=False,
        budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,experimental_native_toolchain=nt.record(),
        signature_proof=str(proof_path),signature_proof_sha256=proof_pin,tools=tools,source_inputs=sources,code_sha256=code,cases=rows,
        original_controls_summary={'path':str(summary),'sha256':SUMMARY_SHA},
        scope='Four owned exposed fixtures; allowed placement positive and deliberately prohibited track/via/mixed negatives. Actual saved refill and final original-shell Native checks. No engine, source repair, production migration, schematic/GUI or physical/electrical qualification.')
    def remaining():return max(0,min(SECONDS-(time.monotonic()-started),SECONDS-(time.process_time()+f.child_cpu()-cpu)))
    def owned():h.owned_destination(owner)
    def stable():
        owned();nt.check()
        if remaining()<=0:raise p.Rejected('whole diagnostic wall/fullCPU budget exhausted')
        if p.tool_manifest()!=tools or p.sha(proof_path)!=proof_pin:raise p.Rejected('source/tool/signature proof changed')
        if p.sha(summary)!=SUMMARY_SHA:raise p.Rejected('original control expectation summary changed')
        if sources!={case:p.tree_hash(BASE/case/'candidate') for case in recipe.CASES}:raise p.Rejected('original control input changed')
        if any(p.sha(Path(name))!=pin for name,pin in code.items()):raise p.Rejected('control code changed')
        for name,files in completed.items():
            if p.tree_hash(Path(name))!=files:raise p.Rejected('completed native evidence changed')
        if remaining()<=0:raise p.Rejected('diagnostic budget exhausted during freshness checks')
    def account():
        record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu)
        record['within_budget']=remaining()>0
        if not record['within_budget'] or record['status']!='completed':record.update(controls_passed=False,native_toolchain_qualified=False)
    try:
        stable()
        for case in recipe.CASES:
            stable();source=BASE/case/'candidate/fixture.kicad_pcb'
            prior=next(row for row in old['cases'] if row['case']==case);expected=prior['expected']
            if p.sha(source)!=expected['board_sha256']:raise p.Rejected('original recipe board pin differs')
            job=f.FloorJob(output/case,remaining(),remaining,native_toolchain=nt)
            shutil.copytree(source.parent,job.out/'candidate');candidate=job.out/'candidate'/source.name
            before=p.tree_hash(candidate.parent)
            area_argv=[nt.python,'-B',Path(__file__).parent/'native_areas.py',candidate,job.out/'areas.json',job.out/'native.dsn',nt.expected_version]
            job.step('area-export',area_argv)
            f.process_check(job.out,{'steps':job.steps},'area-export',[*f.SANDBOX,*map(str,area_argv)])
            observed=f.read_json(job.out/'areas.json')
            if (observed['native_python']!=str(nt.python.resolve()) or observed['loaded_pcbnew']!=str(nt.pcbnew.resolve())
                    or observed['input_hashes_before']!=before or observed['input_hashes_after']!=before
                    or observed['source']!=str(candidate) or observed['board_sha256']!=p.sha(candidate)
                    or observed['project_sha256']!=p.sha(candidate.with_suffix('.kicad_pro'))
                    or observed['dsn_sha256']!=p.sha(job.out/'native.dsn')
                    or observed.get('limits')!=worker.LIMITS):raise p.Rejected('actual loaded native observer/input differs')
            context=recipe.verify_observation(observed,expected,expected_version=nt.expected_version)
            transport=recipe.verify_dsn((job.out/'native.dsn').read_bytes(),expected)
            shutil.copytree(candidate.parent,job.out/'refill');filled=job.out/'refill'/source.name
            refill_before=p.tree_hash(filled.parent);native_refill=job.drc('refill-drc',filled,save=True)
            if f.check_drc_stage(job.out,{'steps':job.steps},'refill-drc',filled,filled,True,refill_before,native_toolchain=nt)!=native_refill:raise p.Rejected('saved refill readback differs')
            rebuilt=p.transplant_fill(sx.read(source),sx.read(filled));sx.write(candidate,rebuilt)
            if p.immutable(rebuilt)!=p.immutable(sx.read(source)) or p.routes(rebuilt)!=p.routes(sx.read(source)):raise p.Rejected('original geometry/routes changed')
            p.verify_candidate_files(candidate,sources[case],p.sha(candidate))
            final_before=p.tree_hash(candidate.parent);native=job.drc('final-drc',candidate)
            if f.check_drc_stage(job.out,{'steps':job.steps},'final-drc',candidate,job.out/'final-drc-input'/source.name,False,final_before,native_toolchain=nt)!=native:raise p.Rejected('final candidate native readback differs')
            expected_ignored=prior['native']['ignored_checks']
            refill_ok,refill_hits=native_expected(case,native_refill,expected,expected_ignored)
            final_ok,final_hits=native_expected(case,native,expected,expected_ignored)
            rows.append(dict(case=case,passed=refill_ok and final_ok,source_sha256=p.sha(source),candidate_sha256=p.sha(candidate),
                original_constraints_unchanged=True,source_files=sources[case],native_context=context,dsn_transport=transport,
                saved_refill=native_refill,saved_refill_targets=refill_hits,final_native=native,final_targets=final_hits,
                saved_refill_report_sha256=p.sha(job.out/'refill-drc.json'),final_report_sha256=p.sha(job.out/'final-drc.json'),steps=job.steps))
            completed[str(job.out)]=p.tree_hash(job.out);stable()
        passed=len(rows)==4 and all(row['passed'] for row in rows)
        record.update(status='completed',controls_passed=passed,native_toolchain_qualified=passed,completed_evidence=completed)
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,native_toolchain_qualified=False,error=type(exc).__name__+': '+str(exc))
    f.publish(output,record,stable,account,remaining,owned=owned,final_check=stable)
    print(json.dumps({'status':record['status'],'controls_passed':record['controls_passed'],'wall_seconds':time.monotonic()-started,'full_cpu_seconds':time.process_time()+f.child_cpu()-cpu}))
    return record['status']=='completed' and record['controls_passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');parser.add_argument('--output',type=Path,required=True);parser.add_argument('--toolchain-proof',type=Path,required=True);args=parser.parse_args()
    if not args.run_native:parser.error('explicit --run-native required')
    raise SystemExit(0 if experiment(args.output,args.toolchain_proof) else 2)
