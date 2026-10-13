"""Executable historical/current shared-validator parity comparison.
Every native call is a fabricated step seam; no real tool executes.
Historical code is read from the actual diagnostic's preserved source snapshot.
"""
from pathlib import Path
import hashlib,importlib.util,json,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as current,sexpr as sx,floor_route as f
OWN=Path(__file__).resolve().parent;history=ROOT/'.runs/ardujoy-original-native-001/code/autorouter/pipeline.py'
spec=importlib.util.spec_from_file_location('autorouter.ardujoy_frozen_pipeline',history);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
source_sha=lambda:current.sha(ROOT/'autorouter/pipeline.py');before=source_sha();results=[]
for label,module,explicit in [('historical-default',old,False),('current-default',current,False),('current-forced-false',current,False),('current-explicit-true',current,True)]:
 folder=OWN/label;folder.mkdir();candidate=folder/'candidate';candidate.mkdir();board=candidate/'probe.kicad_pcb';tree=sx.parse('(kicad_pcb (version 20260206) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)))');sx.write(board,tree);board.with_suffix('.kicad_pro').write_text('{}');board.with_suffix('.kicad_sch').write_text('captured native-schematic path; fabricated native seam ONLY\n');hashes=module.tree_hash(candidate)
 job=object.__new__(module.Job);job.out=folder/'job';job.out.mkdir();job.steps=[];calls=[]
 def fake_step(name,argv,allowed):
  report=Path(argv[argv.index('--output')+1]);native={'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':Path(argv[-1]).name,'included_severities':['error','warning','exclusion'],'ignored_checks':[],'violations':[],'unconnected_items':[],'schematic_parity':[]};module.save_json(report,native);process={'name':name,'argv':[str(x) for x in argv],'status':'success','exit_code':0,'cleanup_complete':True};job.steps.append(process);module.save_json(job.out/(name+'-process.json'),process);calls.append(process);return process
 job.step=fake_step
 with patch('subprocess.run',side_effect=AssertionError('forbidden subprocess')),patch('subprocess.Popen',side_effect=AssertionError('forbidden subprocess')):
  kwargs={} if label.endswith('default') else {'schematic_parity':explicit};digest,native=module.validate_candidate(job,tree,board,hashes,[],**kwargs)
 final=next(x for x in calls if x['name']=='final-drc');binding=f.read_json(job.out/'final-drc-binding.json');results.append({'case':label,'pipeline_sha256':module.sha(history if module is old else ROOT/'autorouter/pipeline.py'),'schematic_captured':board.with_suffix('.kicad_sch').name in hashes,'explicit_kwargs':kwargs,'final_argv':final['argv'],'parity_requested':'--schematic-parity' in final['argv'],'complete_project_same_in_final_copy':module.tree_hash(Path(binding['input']).parent)==hashes,'candidate_preserved':module.tree_hash(candidate)==hashes,'candidate_sha256':digest,'native_validation_performed':False})
# Existing raw native parity warnings remain warnings; policy application is new.
actual=current.parse_report(ROOT/'.runs/ardujoy-original-native-001/job/parity-drc.json','Ardujoy_HW.kicad_pcb');conflicts=[x for x in actual['findings'] if x['type']=='net_conflict'];only={'opens':0,'blocking':0,'warnings':len(conflicts),'exclusions':0,'ignored_checks':[],'findings':conflicts};results.append({'case':'same actual four net_conflict warnings isolated for application-policy comparison','historical_accepted':old.native_accepted(only),'current_accepted':current.native_accepted(only),'original_severities_preserved':all(x['severity']=='warning' for x in conflicts),'count':len(conflicts),'current_rejection_reasons':current.native_rejection_reasons(only),'no_new_native':True})
record={'native_validation_performed':False,'subprocesses_executed':0,'historical_pipeline_sha256':current.sha(history),'current_pipeline_sha256_before':before,'current_pipeline_sha256_after':source_sha(),'results':results};current.save_json(OWN/'parity-probe-results.json',record);assert before==source_sha();assert results[0]['parity_requested'] is False;assert all(x['parity_requested'] for x in results[1:4]);assert all(x['complete_project_same_in_final_copy'] and x['candidate_preserved'] for x in results[:4]);assert results[-1]['historical_accepted'] is True and results[-1]['current_accepted'] is False;print(json.dumps({'historical_parity_requested':results[0]['parity_requested'],'current_three_modes_parity_requested':[x['parity_requested'] for x in results[1:4]],'same_actual_warning_policy':results[-1]},sort_keys=True))
