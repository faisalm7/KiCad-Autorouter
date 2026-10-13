"""Separate stored-evidence readback; preserve failed controller and raw reports."""
from pathlib import Path
from decimal import Decimal
import hashlib,json,re,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
from experiments.modern_semantics_controls_v1 import driver as d
out=ROOT/'.runs/modern-semantics-corrected-readback-001';out.mkdir();start=time.monotonic();cpu=time.process_time()+f.child_cpu()
run=ROOT/'.runs/modern-semantics-controls-001';before=io.inventory(run,max_bytes=d.LIMIT,max_files=3000,max_entries=6000);report=f.read_json(run/'result.json');execution=f.read_json(ROOT/'.runs/modern-semantics-controls-execution-001/execution.json')
assert report['status']=='failed' and report['controls_passed'] is False and report['error']=='Rejected: declared native predicate failed: hole_negative' and len(report['cases'])==6 and len(report['steps'])==10
facts_path=ROOT/'.runs/modern-semantics-actual-review-001/threshold-primary-source-001/facts.json';facts=f.read_json(facts_path)
assert facts['original_rule_mm']=='0.25' and facts['native_reported_effective_threshold_mm']=='0.2495' and facts['source_default_epsilon_mm']=='0.0005' and facts['raw_report_not_rewritten_or_rounded'] and not facts['runtime_epsilon_API_readback_recorded']
for path,digest in facts['source_bindings'].items():assert p.sha(ROOT/path)==digest
rows=[]
for row in report['cases']:
 case=row['case'];source=run/case/'original';candidate=run/case/'observe-input';board=next(candidate.glob('*.kicad_pcb'));hashes=io.inventory(source,max_bytes=d.LIMIT,max_files=3000,max_entries=6000)
 assert hashes==row['source_hashes'] and p.sha(board)==row['final_candidate_sha256'] and p.sha(board)==row['candidate_sha256'] and p.sha(board.with_suffix('.kicad_pro'))==row['project_sha256'];d.geometry(source/board.name,board,hashes)
 stage=case+'-drc';native=f.check_drc_stage(run,report,stage,board,run/(stage+'-input')/board.name,False,hashes)
 assert native==row['native'] and p.sha(run/(stage+'.json'))==row['report_sha256']
 if case!='hole_negative':assert row['control_passed']
 else:
  assert native['opens']==native['blocking']==native['exclusions']==0 and native['warnings']==1 and len(native['findings'])==1
  hit=native['findings'][0];assert hit['type']=='hole_to_hole' and hit['severity']=='warning' and len(hit['items'])==2 and {x['uuid'] for x in hit['items']}=={d.uid('pad0'),d.uid('pad1')}
  match=re.fullmatch(r'Drilled hole too close to other hole \(([^;\n]+) ([0-9]+\.[0-9]+) mm; actual ([0-9]+\.[0-9]+) mm\)',hit['description']);assert match and Decimal(match[2])==Decimal('0.2495') and Decimal(match[3])==Decimal('0.1')
  rules=f.read_json(board.with_suffix('.kicad_pro'))['board']['design_settings'];assert rules['rules']['min_hole_to_hole']==rules['rules']['min_hole_clearance']==.25 and rules['rule_severities']['hole_to_hole']=='warning'
  assert not p.native_accepted(native) and p.native_rejection_reasons(native)==['policy-critical native finding: hole_to_hole (warning)']
 rows.append({'case':case,'observed_behavior_verified':True,'native':native,'candidate_sha256':p.sha(board),'report_sha256':row['report_sha256']})
assert io.inventory(run,max_bytes=d.LIMIT,max_files=3000,max_entries=6000)==before
wall=time.monotonic()-start;full_cpu=time.process_time()+f.child_cpu()-cpu
value={'schema':1,'kind':'modern-semantics-stored-corrected-readback-v1','observed_semantics_verified':True,'original_controller_status_unchanged':'failed','original_protocol_predicate_passed':False,'native_reexecuted':False,'accepted':False,'physical_electrical_qualified':False,'actual_default_epsilon_api_measured':False,'source_default_agreement_only':True,'native_effective_minimum_mm':'0.2495','unchanged_nominal_original_minimum_mm':'0.25','actual_gap_mm':'0.1000','threshold_source_facts_sha256':p.sha(facts_path),'cases':rows,'readback_wall_seconds':wall,'readback_full_cpu_seconds':full_cpu,'prior_full_execution':execution,'cumulative_wall_seconds':execution['wall_seconds']+wall,'cumulative_full_cpu_seconds':execution['full_cpu_seconds']+full_cpu,'original_evidence_unchanged':True,'control_sha256':p.sha(Path(__file__)),'scope':'Six completed diagnostics read without native rerun. Explicit error text cases remain prior002; field/textbox/dimension parser refusals not native qualification. Original failure retained; native tolerance is reported exactly, not a changed rule or suppressed warning.'}
p.save_json(out/'readback.json',value);print(f.canonical({k:value[k] for k in ('observed_semantics_verified','original_controller_status_unchanged','cumulative_wall_seconds','cumulative_full_cpu_seconds')}))
