"""Small facts-only readback using retained shared reporters; no Native or admission."""
from pathlib import Path
from collections import Counter
import ast,datetime,hashlib,json,math,os,re,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
HEAD='82aaa3b750007ef2ffaafd367ffcb718aa93865e';MANIFEST='0fa1f13c4a43385d2d0b513c7c84fb89bb6370eb9962531018f0d1ccbfd6f039';keys=('opens','blocking','warnings','exclusions')
helpers=[('.runs/curate-runtime030-native-workflow-qualification-001.py','b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',['cost']),('.runs/curate-runtime042-current-comparison-001.py','d6d99941d9afe8d6a81e862d406d66b72f39fdf1c5241dc6cb7403154a61d974',['complete_cost','inventory','custody','counts','delivered_proof']),('.runs/curate-gui-runtime042-081-recovery-deliveries-001.py','340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',['read','own_final'])]
for name,pin,names in helpers:
 source=ROOT/name;assert p.sha(source)==pin
 selected=[n for n in ast.parse(source.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names];assert [n.name for n in selected]==names
 exec(compile(ast.Module(body=selected,type_ignores=[]),str(source),'exec'),globals())
base=ROOT/'.runs/runtime042-default-target-followup-001';plan=f.read_json(base/'protocol.json');outer=f.read_json(base/'enclosure/result.json');out=Path(plan['output']);child=f.read_json(out/'result.json');allowed=[out,*custody(out,plan,outer,'B2_portfolio')]
assert outer['passed'] and child['controls_passed'] and child['workflow_delivered'] and child['outcome']=='validated_winner_delivery'
assert plan['administration_head']=='6ec7ad2344ed060d5e0971965ef05bd9de68925d' and io.inventory(Path(plan['source']).parent)==plan['source_hashes']
summary=f.read_json(Path(plan['portfolio_output'])/'portfolio-summary.json');assert summary['status']=='completed' and summary['all_variants_attempted'] is True and p.sha(Path(plan['portfolio_output'])/'portfolio-summary.json')==child['portfolio_summary_sha256']
trials=[]
for row in summary['trials']:
 receipt=Path(row['result']);data=f.read_json(receipt);assert p.sha(receipt)==row['result_sha256'] and row['eligible'] is True
 proof=delivered_proof(receipt,export=False,source_hashes=plan['source_hashes'],allowed=allowed);proof['own_final']=own_final(data,receipt.parent,receipt.parent,plan['source_hashes'],data['candidate'])
 assert data['engine_budget']['strict_class_targets'] is True
 for arg in ['--router.automatic_neckdown=false','--router.fanout.enabled=false','--router.neck_width_um=0']:assert arg in data['engine_budget']['argv']
 trials.append({'variant':row['id'],'proof':proof,'strict_profile':data['engine_budget'],'metrics':data['metrics']})
proofs={}
for label,key,export in [('route','selected_route_receipt',False),('export','export_receipt',True)]:
 receipt=Path(child[key]);data=f.read_json(receipt);proof=delivered_proof(receipt,export=export,source_hashes=plan['source_hashes'],allowed=allowed);folder=receipt.parent/'validation' if export else receipt.parent
 proof['own_final']=own_final(data,folder,folder,plan['source_hashes'],data['candidate']);proof['finding_types']=dict(Counter(str(v['severity'])+':'+str(v['type']) for v in data['native']['findings']));proofs[label]=proof
assert proofs['route']['candidate_sha256']==proofs['export']['candidate_sha256']
followup={'classification':'labelled_followup_validated_winner_delivery','first_attempt':False,'unattended_batch':False,'protocol_sha256':p.sha(base/'protocol.json'),'outer_sha256':p.sha(base/'enclosure/result.json'),'child_sha256':p.sha(out/'result.json'),'summary_sha256':child['portfolio_summary_sha256'],'complete_cost':complete_cost(base/'outer-time.log'),'method_wall_seconds':child['method_wall_seconds'],'method_full_CPU_seconds':child['method_full_CPU_seconds'],'source_unchanged':True,'source_hashes':plan['source_hashes'],'trials':trials,'delivered':proofs,'metrics':child['metrics'],'selected_variant':summary['selected']['id'],'ordinary_production_admitted':False,'scope':'Measurement-corrected B2, unchanged042runtime/input/constraints/budgets. NewNative7 fractional core not used. Original failed firsttrial and cost remain in042cohort.'}
assert max(followup['complete_cost']['wall_seconds'],followup['complete_cost']['CPU_seconds'])<=600 and max(child['method_wall_seconds'],child['method_full_CPU_seconds'])<=450
native={}
for number in ('001','002'):
 folder=ROOT/('.runs/native7-fractional-edge-controls-'+number);enclosure=ROOT/('.runs/native7-fractional-edge-controls-execution-'+number);r=f.read_json(folder/'result.json');e=f.read_json(enclosure/'execution.json');rows=[]
 assert e['source_current'] and e['process']['cleanup_complete'] and not e['process']['log_truncated']
 for row in r['controls']:
  small={'case':row['case'],'passed':row['passed'],'accepted':row['accepted'],'Native_counts':counts(row.get('native')),'reason':row.get('reason'),'candidate_sha256':row.get('candidate_sha256'),'steps':[]}
  for step in row['steps']:
   assert step['cleanup_complete'] and not step['log_truncated'];assert 'kicad-10.0.7-local-001' in ' '.join(step['argv'])
   small['steps'].append({k:step.get(k) for k in ['name','argv','cwd','status','exit_code','validated_input_sha256']})
  rows.append(small)
 native[number]={'passed':e['passed'],'all_controls_passed':r['all_passed'],'complete_cost':complete_cost(ROOT/('.runs/native7-fractional-edge-controls-'+number+'-time.log')),'execution_sha256':p.sha(enclosure/'execution.json'),'result_sha256':p.sha(folder/'result.json'),'transport_passed':r['transport']['passed'],'transport_native_host_version':r['transport']['data']['native_edge_correction']['inward_boundary']['native_host_version'],'rows':rows,'scope':'Owned diagnostic only, noSCH, engine, fullproduct, electrical or routing-quality claim.'}
assert not native['001']['passed'] and native['002']['passed'] and [x['Native_counts'] for x in native['002']['rows'][:2]]==[[0,0,0,0],[0,1,0,0]]
assert native['002']['rows'][2]['accepted'] is False
notes=ROOT/'evidence/runtime043-general-corrections-native-001-notes';output=ROOT/'evidence/runtime043-general-corrections-native-001.json';assert not notes.exists() and not output.exists();notes.mkdir()
paths=[Path(__file__),base/'preregistration.json',*[base/n for n in ['protocol.json','outer.log','outer-time.log','enclosure/result.json','enclosure/process.json','enclosure/command.log']],ROOT/'.runs/native7-edge-control-base-001-creation.json']
for number in ('001','002'):
 paths += [ROOT/('.runs/run-native7-fractional-edge-controls-'+number+'.py'),ROOT/('.runs/native7-fractional-edge-controls-'+number+'-controller.log'),ROOT/('.runs/native7-fractional-edge-controls-'+number+'-time.log')]
 paths += [ROOT/('.runs/native7-fractional-edge-controls-execution-'+number)/n for n in ['protocol.json','execution.json','command.log']]
 paths += [ROOT/('.runs/native7-fractional-edge-controls-'+number)/'protocol.json']
files=[]
for path in paths:
 raw=io.read_bytes(path,4*1024**2);raw.decode('utf8');assert b'\0' not in raw
 target=notes/Path(*path.relative_to(ROOT).parts[1:]);target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as stream:stream.write(raw)
 files.append({'source':str(path.relative_to(ROOT)),'path':str(target.relative_to(ROOT)),'sha256':p.sha(path),'bytes':len(raw)})
custody(out,plan,outer,'B2_portfolio')
record={'schema':1,'kind':'general-corrections-actual-native-diagnostics-and-restart-followup-facts-v1','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'accepted':False,'project_complete':False,'new_product_qualified':False,'actual_GUI':False,'human_review':False,'source_checkpoint':'6ec7ad2344ed060d5e0971965ef05bd9de68925d','restart_followup':followup,'Native_diagnostics':native,'interpretation':['General verifier correction now passes all3actualNative trials and freshwinnerdelivery; not a new algorithmic improvement.','Exact7fractionalguard has actualexport/purepriorpacket plus Native positive/edge-negative/rule-tamper controls; selectednewproduct/nativefullSCH/GUI stillpending.','001ran refill DRC then classfloor refusal before final DRC for positive/edge; no false finalNativepass. Fresh002authored explicitfloors at creation and uses identical sharedvalidator.','Different publisher priorcohort notrewritten, no stitched unattended firstattempt.','No copied third-party CAD/DSN/SES/plots/rawfindings; unique rawMac-only/outside010.'],'review':'Native002 independent AI spotbindingreview windows005_gate no materialdiscrepancy, not human or allraw/centralreplay. Restart artifact review pending.','files':files,'retained_bytes':sum(x['bytes'] for x in files)}
p.save_json(output,record);print(json.dumps({'retained_files':len(files),'retained_bytes':record['retained_bytes'],'restart_Native_counts':proofs['export']['Native_counts'],'metrics':child['metrics']}))
