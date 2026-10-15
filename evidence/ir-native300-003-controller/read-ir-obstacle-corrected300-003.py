"""Pure missing-stage300 reader; no old001 semantic reader or Native calls."""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json,copy,importlib.util
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx,config as c,handoff as h
from experiments.native_paired_v1 import readback as shared
from scripts import experiment_quality as q,experiment_paired as paired
# Shared readers may only recheck the current checkpoint, never execute routing.
import subprocess
_ORIGINAL_POPEN=subprocess.Popen
def _read_only_popen(argv,*args,**kwargs):
 if type(argv) not in (list,tuple) or list(argv)!=['git','rev-parse','HEAD'] or Path(kwargs.get('cwd','')).resolve()!=ROOT or kwargs.get('shell'):
  raise p.Rejected('pure reader forbidden subprocess')
 return _ORIGINAL_POPEN(argv,*args,**kwargs)
subprocess.Popen=_read_only_popen

def main():
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--prospective',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args();spec=f.read_json(args.prospective)
 require=lambda ok,why:None if ok else (_ for _ in ()).throw(p.Rejected(why))
 require(p.sha(Path(spec['wrapper_source']))==spec['wrapper_sha256'],'wrapper changed')
 mod=importlib.util.spec_from_file_location('ir_missing_stage_contract',spec['wrapper_source']);w=importlib.util.module_from_spec(mod);mod.loader.exec_module(w)
 prior,control=w.contract(spec);base=Path(spec['output']);outer=f.read_json(base/'execution.json');worker=f.read_json(base/'worker-result.json');pair=f.read_json(base/'feedback/paired-summary.json');pp=f.read_json(base/'feedback/protocol.json')
 require(p.sha(args.prospective)==outer['prospective_sha256'] and outer['wrapper_sha256']==spec['wrapper_sha256'] and outer['reader_sha256']==spec['reader_sha256'],'outer protocol/code differs')
 require(outer['process']['argv']==[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',spec['wrapper_source'],'--prospective',str(args.prospective),'--worker'] and outer['process']['cwd']==str(base),'outer argv/cwd differs')
 require(outer['process']['cleanup_complete'] is True and outer['process']['log_truncated'] is False,'outer cleanup/log incomplete')
 require(pp['source']==spec['source'] and pp['arm_order']==['B2_portfolio','C_feedback'] and pp['wall_budget_per_arm_seconds']==pp['cpu_budget_per_arm_seconds']==120 and pp['freeze']==spec['freeze'],'actual feedback pair contract differs')
 require(pair['protocol_sha256']==p.sha(base/'feedback/protocol.json') and [r['id'] for r in pair['results']]==['B2_portfolio','C_feedback'],'actual two-arm population differs')
 board=Path(spec['source']);original=p.preflight(board);hashes=spec['source_hashes'];baseline=p.parse_report(base/'original-baseline.json',board.name)
 require(p.sha(base/'original-baseline.json')==spec['raw_baseline_sha256'] and baseline==spec['raw_baseline_summary'],'raw42-warning baseline differs')
 material=w.inv(base);stored=outer['material'];require({k:v for k,v in material[0].items() if k!='execution.json'}==stored[0] and f.canonical(material[1])==f.canonical(stored[1]),'outer actual material differs')
 oldbase=ROOT/spec['prior_matrix'];oldouter=f.read_json(oldbase/'execution.json');oldmaterial=w.inv(oldbase/'run');require(oldmaterial[0]==oldouter['paired_material'],'old matrix bytes changed')
 pins={str(args.prospective):p.sha(args.prospective),str(Path(__file__)):p.sha(Path(__file__))}
 args.output.mkdir();owner={};h.capture_destination(owner,args.output)
 result=dict(schema=1,status='incomplete',accepted=False,comparison_eligible=False,new_native_execution=False,new_engine_execution=False,prior_rows=prior,control_charge=list(control),failed_continuation_common_charge=spec['failed_continuation_common_charge'],results=[],final_candidates=[],workers=[],raw_B1=worker['B1'],raw_feedback=pair,scope='Exposed IR cumulative300; old001 allfalse retained. New B1/actual two-arm feedback only; no native-all relabel or independent-family/PCB claim.')
 def remaining():return 60-max(time.monotonic()-START,cpu()-CPU0)
 def stable():
  w.stable(spec)  # ALL tool callbacks first, then byte/source/proof witnesses.
  w.contract(spec);h.owned_destination(owner)
  require(w.inv(base)==material and w.inv(oldbase/'run')==oldmaterial,'old/new material changed')
  for name,pin in pins.items():require(p.sha(Path(name))==pin,'reader/protocol changed')
  require(p.sha(base/'wrapper.py')==spec['wrapper_sha256'] and p.sha(base/'reader.py')==spec['reader_sha256'],'captured code changed')
  for name,pin in spec['dependencies_sha256'].items():require(p.sha(base/'reader-dependencies'/name)==pin,'captured dependency changed')
  require(remaining()>0,'reader60 budget exhausted')
 def observed(path,parent=None):
  d=f.read_json(path);folder=path.parent
  lineage=d if parent is None else parent
  require(lineage['source']==str(board) and lineage['source_hashes']==hashes and lineage['tools']==spec['tools'],'new receipt source/producer differs')
  if parent is None and d.get('accepted') is True:p.check_result(path)
  resource_error=None
  try:
   if parent is None:p.check_resource_accounting(d)
   else:shared.inherited_trial_accounting(folder,d,parent)
  except p.Rejected as exc:
   require(d.get('accepted') is False or (parent is not None and parent.get('accepted') is False),'accepted resource failure');resource_error=str(exc)
  declared=set()
  for row in d.get('steps',[]):
   cwd=Path(row['cwd']);name=row['name'];require(Path(name).name==name,'unsafe worker name');require((cwd==folder or folder in cwd.parents) and cwd==cwd.resolve(),'worker escaped receipt')
   key=(str(cwd),name);require(key not in declared,'duplicate worker');declared.add(key)
   process=f.read_json(cwd/(name+'-process.json'));require(all(f.canonical(row.get(k))==f.canonical(v) for k,v in process.items()),'process differs from history');require(process['cleanup_complete'] is True,'worker cleanup incomplete')
   require(process['log']==str(cwd/(name+'.log')),'worker log escaped');pc.read_bytes(Path(process['log']),16*1024**2)
   done=process['status'] in ('success','nonzero_exit') and type(process.get('exit_code')) is int
   if done:f.process_check(cwd,d,name,process['argv'],allowed=(process['exit_code'],))
   binding=cwd/(name+'-binding.json');native=None
   if binding.is_file() and done and str(c.CLI) in process['argv']:
    b=f.read_json(binding);source=Path(b['source']);inp=Path(b['input']);require(folder in source.parents and folder in inp.parents,'native input escaped')
    before=dict(hashes)
    if name=='refill-drc':before[board.name]=p.sha(cwd/'pre-refill.kicad_pcb')
    elif name=='final-drc':before[board.name]=p.sha(source)
    else:require(name=='source-drc','unknown DRC stage')
    native=f.check_drc_stage(cwd,d,name,source,inp,b['saved'],before,schematic_parity='--schematic-parity' in process['argv'],sandboxed=process['argv'][:len(f.SANDBOX)]==f.SANDBOX)
   result['workers'].append(dict(receipt=str(path),cwd=str(cwd),name=name,status=process['status'],native=native,process_sha256=p.sha(cwd/(name+'-process.json'))))
  actual={(str((folder/n).parent),Path(n).name[:-13]) for n in w.inv(folder)[0] if n.endswith('-process.json')}
  require(actual==declared,'retained worker census differs')
  if d.get('candidate_sha256') and d.get('native_report_sha256'):
   candidate=folder/'candidate'/board.name;p.verify_candidate_files(candidate,hashes,d['candidate_sha256']);tree=sx.read(candidate);require(p.immutable(tree)==p.immutable(original),'original geometry/rules changed')
   protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original);require(all(x in p.routes(tree) for x in protected),'protected source changed')
   proof=None
   if resource_error is None:proof=shared.final_candidate_readback(folder,d,board,original,hashes,resource_parent=parent)
   pre=sx.read(folder/'pre-refill.kicad_pcb');saved=sx.read(folder/'refill'/board.name);require((sx.dump(p.transplant_fill(pre,saved))+'\n').encode()==pc.read_bytes(candidate),'saved refill differs from final')
   require(d['native']['ignored_checks']==baseline['ignored_checks'],'ignored checks differ')
   warnings=lambda n:sorted(f.canonical(x) for x in n['findings'] if x['severity']=='warning')
   if d.get('accepted') is True:require(warnings(d['native'])==warnings(baseline),'accepted candidate changed original42 warnings')
   if 'metrics' in d:
    require(f.read_json(folder/'metrics.json')==d['metrics'] and d['metrics']['version']=='10.0.0','actual metrics mismatch')
    f.process_check(folder,d,'metrics',[str(c.PYTHON),str(ROOT/'autorouter/native.py'),'metrics',str(candidate),str(folder/'metrics.json')])
   result['final_candidates'].append(dict(receipt=str(path),accepted=d['accepted'],candidate_sha256=p.sha(candidate),native_report_sha256=p.sha(folder/'final-drc.json'),native=d['native'],metrics=d.get('metrics'),full_shared_proof=proof,resource_failure=resource_error))
  else:result.setdefault('unqualified',[]).append(dict(receipt=str(path),status=d['status'],reason=d.get('reason')))
  return d
 def bind(raw,authoritative):
  require(not raw['accepted'] or authoritative['accepted'],'raw accepted unqualified receipt')
  for k,v in authoritative.items():
   if k=='accepted' or (raw.get('status')=='invocation_error' and (k in ('status','reason') or k not in raw)):continue
   require(k in raw and f.canonical(raw[k])==f.canonical(v),'raw summary differs: '+k)
 def account():
  wall=time.monotonic()-START;full=cpu()-CPU0;new=[worker['B1'],*pair['results']]
  overhead=[num(outer['wall_seconds'])-sum(num(x['invocation_wall_seconds']) for x in new),num(outer['full_cpu_seconds'])-sum(num(x['invocation_cpu_seconds']) for x in new)]
  require(min(overhead)>=0,'nested invocation costs exceed whole outer')
  overhead=[overhead[i]+num(spec['failed_continuation_common_charge'][i]) for i in range(2)]
  valid=result['status']=='completed' and outer['source_current'] is True and outer['whole_delivery_within_budget'] is True and outer['status']=='completed' and outer['process']['status']=='success' and outer['process']['exit_code']==0
  result['results']=[]
  for old in prior:
   raw=next((x for x in new if x['id']==old['id']),None);row=copy.deepcopy(raw if raw is not None else old);row['prior_row']=old
   costw=old['charged_wall_seconds']+control[0]+(raw['invocation_wall_seconds'] if raw else 0)+overhead[0]+2+wall+1+2
   costc=old['charged_cpu_seconds']+control[1]+(raw['invocation_cpu_seconds'] if raw else 0)+overhead[1]+2+full+1+2
   row.update(charged_wall_seconds=costw,charged_cpu_seconds=costc,accepted=bool(valid and raw and raw['accepted'] and max(costw,costc)<=300));result['results'].append(row)
  result.update(comparison_eligible=valid,replacement_shared_cost=overhead,reader_wall_seconds=wall,reader_full_cpu_seconds=full,comparisons=paired.comparisons(result['results']) if valid else [])
 num=w.num
 try:
  with p.validation_readback_session():
   stable()
   if (base/'B1/result.json').is_file():
    b1=f.read_json(base/'B1/result.json');bind(worker['B1'],q.summarize(dict(id='B1',adapter='both',engine_profile='standard',operation='route'),base/'B1',b1,worker['B1']['invocation_wall_seconds'],worker['B1']['invocation_cpu_seconds']));observed(base/'B1/result.json')
   else:require(worker['B1']['accepted'] is False,'accepted B1 missingreceipt');result.setdefault('unqualified',[]).append(dict(id='B1',reason='no finalreceipt, original partial material retained'))
   port=f.read_json(base/'feedback/B2_portfolio/portfolio-summary.json');bind(pair['results'][0],paired.verify_portfolio(base/'feedback/B2_portfolio',port,board,pp['freeze']));result['portfolio_coverage']={k:port.get(k) for k in ('attempted_variants','unattempted_variants','skipped_variants','all_variants_attempted','pareto_frontier')}
   for trial in port['trials']:
    if trial.get('result'):observed(Path(trial['result']))
   cp=base/'feedback/C_feedback/result.json';parent=f.read_json(cp);bind(pair['results'][1],q.summarize(paired.C_ARM,cp.parent,parent,pair['results'][1]['invocation_wall_seconds'],pair['results'][1]['invocation_cpu_seconds']));observed(cp)
   if parent.get('incumbent'):
    inc=cp.parent/'incumbent/result.json';data=observed(inc);mark=parent['incumbent'];require(mark['receipt']==str(inc) and all(mark[k]==data[k] for k in ('status','accepted','metrics','wall_seconds')),'C own incumbent marker differs')
    require([dict(x,phase='incumbent') for x in data['steps']]==[x for x in parent['steps'] if x.get('phase')=='incumbent'],'C own incumbent history differs')
    if data.get('candidate_sha256') and data.get('native_report_sha256'):shared.pruning_incumbent_readback(cp.parent,parent,board,original,hashes)
   for trial in parent.get('trials',[]):
    path=Path(trial['receipt']);require(path==cp.parent/'trials'/trial['id']/'result.json','trial escaped parent');observed(path,parent)
   result['status']='completed'
 except (Exception,KeyboardInterrupt) as exc:result.update(status='failed',reason=type(exc).__name__+': '+str(exc))
 def final_check():
  stable()
  for row in result['results']:
   bound=max(row['charged_wall_seconds']-result['reader_wall_seconds'],row['charged_cpu_seconds']-result['reader_full_cpu_seconds'])+60
   require(not row['accepted'] or bound<=300,'remaining reader publication could exceed300')
 f.publish(args.output,result,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final_check)
 published=args.output/'result.json'
 require(f.canonical(f.read_json(published))==f.canonical(result),'published reader receipt differs')
 result_pin=p.sha(published)
 stable();account()
 require(p.sha(published)==result_pin,'published reader receipt changed during final callbacks')
 p.save_json(args.output/'execution.json',dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,final_charged_results=result['results'],result_sha256=result_pin,scope='Reader firstline/self+children plus all callbacks; startup1/finalpublication2 conservatively charged, old original/readback costs already in exact priorrow.'))
 require(p.sha(published)==result_pin and f.read_json(args.output/'execution.json')['result_sha256']==result_pin,'final reader receipt binding differs')
 print(f.canonical({k:result[k] for k in ('status','comparison_eligible')}));return 0 if result['status']=='completed' else 2
if __name__=='__main__':raise SystemExit(main())
