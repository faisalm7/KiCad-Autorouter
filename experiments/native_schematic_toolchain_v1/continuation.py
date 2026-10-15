"""Two genuinely later-field negatives; reuse all completed Native controls.

The earlier aggregate remains failed: its custom field was directly visible in
KiCad. No prior positive/negative worker is repeated to repair that hypothesis.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,sys,time
from collections import Counter
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path[:0]=[str(ROOT),str(Path(__file__).resolve().parent)];sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,handoff as h
from experiments.native_schematic_toolchain_v1 import driver as common
fixture=common.fixture
PREPARATION=ROOT/'.runs/native-schematic-hidden-followup-preparation-001/protocol.json'
PREPARATION_SHA='e1d2969b4ea454ce3e7182d8057ad619ea9cb1a87a22d1811ae9fbba8d291bcc'
FAILED_FIRST=ROOT/'.runs/native-schematic-toolchain-execution-001/result.json'
FAILED_FIRST_SHA='1859b17cd0e3d985b16153b243f420ca2a2269f27249786ca06c00b651d642ee'
REFERENCE=ROOT/'.runs/native-schematic-toolchain-execution-002'
SECONDS=120


def same_findings(first,second):
    """Exact complete finding multisets, including duplicates and every field."""
    return (Counter(f.canonical(row) for row in first['findings'])==Counter(f.canonical(row) for row in second['findings'])
            and first['ignored_checks']==second['ignored_checks'])


def reference_records():
    if p.sha(PREPARATION)!=PREPARATION_SHA or p.sha(FAILED_FIRST)!=FAILED_FIRST_SHA:raise p.Rejected('fixed failed/history preparation changed')
    frozen=f.read_json(PREPARATION)
    if p.tree_hash(REFERENCE)!=frozen['reference_inventory']:raise p.Rejected('fixed completed Native population changed')
    report=f.read_json(REFERENCE/'native/result.json');enclosure=f.read_json(REFERENCE/'result.json')
    if (report['status']!='failed' or report['controls_passed'] is not False
            or report.get('error')!='Rejected: hidden later-field control changed first native findings'
            or enclosure['passed'] is not False or len(report['cases'])!=4
            or any(row.get('checks',{}).get('passed') is not True for row in report['cases'])):
        raise p.Rejected('retain original failed aggregate and four completed individual controls')
    first=f.read_json(FAILED_FIRST)
    costs={key:sum(row[key]+row['publication_allowance_seconds'] for row in (first,enclosure))
           for key in ('wall_seconds','full_cpu_seconds')}
    return frozen,report,costs


def experiment(output):
    if output.parent.parent!=ROOT/'.runs' or output.exists() or output.is_symlink():raise p.Rejected('fresh nested .runs output required')
    start=time.monotonic();cpu=time.process_time()+f.child_cpu();frozen,old,previous=reference_records()
    if any(p.sha(ROOT/name)!=pin for name,pin in common.PREREQUISITES.items()):raise p.Rejected('actual pinned tool prerequisites differ')
    toolproof=f.read_json(ROOT/'.runs/kicad-1007-bundle-qualification-001/result.json')
    nt=p.ExperimentalNativeToolchain.from_record(toolproof['experimental_native_toolchain']);tools=p.tool_manifest()
    if tools['implementation_sha256']!=old['tools']['implementation_sha256'] or tools['files']!=old['tools']['files']:raise p.Rejected('reference/current core implementation or production tool bytes differ')
    code={str(x):p.sha(x) for x in Path(__file__).resolve().parent.glob('*.py')}
    # The original positive and visible-negative packet bytes are immutable.
    for row in old['cases']:
        expected={name:hashlib.sha256(raw).hexdigest() for name,raw in fixture.files(row['case']).items()}
        if expected!=row['source_files']:raise p.Rejected('completed source packet changed')
    output.mkdir();owner={};h.capture_destination(owner,output);rows=[];readback=[];completed={}
    record=dict(schema=1,kind='native_masked_later_field_missing_controls',status='incomplete',accepted=False,controls_passed=False,
        production_admitted=False,routing_scope_accepted=False,budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,
        cumulative_enclosure_wall_full_cpu_cap_seconds=190,prior_charged_enclosure_costs=previous,
        preparation_sha256=PREPARATION_SHA,failed_first_sha256=FAILED_FIRST_SHA,reference_source_head=old['tools']['git_head'],
        reference_result_sha256=p.sha(REFERENCE/'native/result.json'),reference_enclosure_sha256=p.sha(REFERENCE/'result.json'),
        experimental_native_toolchain=nt.record(),tools=tools,code_sha256=code,cases=rows,prior_individual_readback=readback,
        scope='Only two new later-Description negatives on1000/1007. Four completed Native002 controls are replayed without workers; its aggregate staysfailed because earliercustomfieldwasdirectlyreported. New negatives must retain exact full finding multisets of their priorpositive, yet complete fields reject Description. Original source/rules/zone/lockedroute/PRL/refill/hash/process/version checks staymandatory. No engine/normal1007routing/GUI/gain/human/release claim.')
    def remaining():return max(0,min(SECONDS-(time.monotonic()-start),SECONDS-(time.process_time()+f.child_cpu()-cpu)))
    def stable():
        h.owned_destination(owner);nt.check()
        if remaining()<=0:raise p.Rejected('missing-control budget exhausted')
        if p.tool_manifest()!=tools or any(p.sha(Path(name))!=pin for name,pin in code.items()):raise p.Rejected('frozen source/code changed')
        if any(p.sha(ROOT/name)!=pin for name,pin in common.PREREQUISITES.items()):raise p.Rejected('pinned actual prerequisite changed')
        if p.sha(PREPARATION)!=PREPARATION_SHA or p.sha(FAILED_FIRST)!=FAILED_FIRST_SHA or p.tree_hash(REFERENCE)!=frozen['reference_inventory']:
            raise p.Rejected('retained failed/completed experiment changed')
        if any(p.tree_hash(Path(name))!=files for name,files in completed.items()):raise p.Rejected('new completed Native evidence changed')
        if remaining()<=0:raise p.Rejected('budget exhausted during final readback')
    def account():
        record.update(wall_seconds=time.monotonic()-start,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu)
        if record['status']!='completed' or remaining()<=0:record['controls_passed']=False
    try:
        stable()
        for row in old['cases']:
            current=nt if row['version']=='10.0.7' else None
            checks=common.retained_case(REFERENCE/'native'/(row['version']+'-'+row['case']),row,current)
            readback.append(dict(version=row['version'],case=row['case'],checks=checks))
        for version in common.VERSIONS:
            stable();case=fixture.MASKED_CASE;directory=output/(version+'-'+case);directory.mkdir();source=directory/'source'
            fixture.write_project(source,case);before=p.tree_hash(source);current=nt if version=='10.0.7' else None
            job=f.FloorJob(directory/'native',remaining(),remaining,native_toolchain=current,protect_local_settings=True,experimental_schematic_parity=current is not None)
            shutil.copytree(source,job.out/'candidate');candidate=job.out/'candidate'/common.BOARD
            shutil.copytree(source,job.out/'refill');filled=job.out/'refill'/common.BOARD
            saved=job.drc('refill-drc',filled,save=True,schematic_parity=True)
            sx.write(candidate,p.transplant_fill(sx.read(source/common.BOARD),sx.read(filled)));candidate_files=p.tree_hash(candidate.parent)
            final=job.drc('final-drc',candidate,schematic_parity=True)
            row=dict(version=version,case=case,source_files=before,candidate_files=candidate_files,candidate_sha256=p.sha(candidate),saved_refill=saved,final_native=final,
                saved_refill_report_sha256=p.sha(job.out/'refill-drc.json'),final_report_sha256=p.sha(job.out/'final-drc.json'),steps=job.steps)
            rows.append(row);row['checks']=common.retained_case(directory,row,current)
            positive=next(r for r in old['cases'] if r['version']==version and r['case']=='positive')
            for name in ('saved_refill','final_native'):
                if not same_findings(positive[name],row[name]):raise p.Rejected('new negative did not preserve complete first-finding population')
            row['same_actual_findings_as_prior_positive']=True;completed[str(directory)]=p.tree_hash(directory);stable()
        record.update(status='completed',controls_passed=len(rows)==2 and len(readback)==4,completed_evidence=completed)
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',controls_passed=False,error=type(exc).__name__+': '+str(exc))
    f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    print(json.dumps({k:record.get(k) for k in ('status','controls_passed','wall_seconds','total_cpu_seconds','error')}))
    return record['status']=='completed' and record['controls_passed']

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if not args.run_native:parser.error('explicit --run-native required')
    raise SystemExit(0 if experiment(args.output) else 2)
