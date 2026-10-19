"""Finite owned Native hierarchy controls using shared Jobs and proof readers."""
import argparse,copy,json,resource,shutil,sys,time
from pathlib import Path
START=time.monotonic()
def cpu():return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,handoff as h,local_settings as local,schematic_class_evidence as classes,sexpr as sx
ap=argparse.ArgumentParser();ap.add_argument('--protocol',required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
protocol=Path(a.protocol);plan=f.read_json(protocol);assert p.sha(protocol)==a.protocol_sha256
assert plan['kind']=='hierarchy-owned-native-identity-controls-v1' and plan['whole_wall_full_cpu_seconds']==180
assert c.ROOT==ROOT==Path(plan['runtime']) and c.NATIVE_VERSION=='10.0.7' and Path(sys.prefix).resolve()==ROOT/'.venv'
assert Path(__file__)==Path(plan['controller']) and p.sha(Path(__file__))==plan['controller_sha256']
assert p.sha(ROOT/'runtime-distribution.json')==plan['runtime_manifest_sha256']
tools=p.tool_manifest();assert tools==plan['tools'] and tools['git_head']==plan['source_head']
source=Path(plan['source']);original=p.tree_hash(source.parent);assert original==plan['source_hashes']
out=Path(plan['output']);assert not out.exists();out.mkdir();owner={};h.capture_destination(owner,out)
report=dict(schema=1,kind=plan['kind'],status='failed',control_passed=False,accepted=False,production_admitted=False,project_complete=False,actual_GUI=False,human_review=False,Native_executed=False,source_head=plan['source_head'],protocol_sha256=a.protocol_sha256,source=str(source),source_hashes=original,tools=tools,cases=[])
jobs=[]
def fresh():
 assert p.sha(protocol)==a.protocol_sha256 and p.sha(Path(__file__))==plan['controller_sha256'] and p.tool_manifest()==tools
 assert p.tree_hash(source.parent)==original and h.owned_destination(owner)==out
 assert max(time.monotonic()-START,cpu()-CPU0)<175
def case(label):
 fresh();job=p.Job(out/label,120,protect_local_settings=True);jobs.append(job)
 board=job.out/'candidate'/source.name;shutil.copytree(source.parent,board.parent)
 assert p.tree_hash(board.parent)==original
 return job,board
def mutate_child(board,change):
 child=board.parent/plan['child_name'];tree=sx.read(child);change(tree);sx.write(child,tree)
def classes_for(job,board):
 mapping=job.out/'export-netclasses.json'
 job.native('export','export',board,job.out/'task.dsn',mapping,'--task-copper-fixed')
 return mapping
def source_drc(job,board):
 before=p.tree_hash(board.parent)
 value=job.drc('source-drc',board,schematic_parity=True)
 data=dict(steps=job.steps,source_hashes=before,tools=tools)
 actual=f.check_drc_stage(job.out,data,'source-drc',board,job.out/'source-drc-input'/board.name,False,before,schematic_parity=True,sandboxed=False)
 assert actual==value and p.tree_hash(board.parent)==before
 return value
try:
 job,board=case('positive');mapping=classes_for(job,board)
 metadata=classes.collect(job,'task',board,mapping)
 data=dict(steps=job.steps,source_hashes=original,schematic_class_task=metadata)
 proof=classes.check(job.out,data,'task',board_raw=board.read_bytes(),source=str(board),project_raw=board.with_suffix('.kicad_pro').read_bytes(),schematic_raw=board.with_suffix('.kicad_sch').read_bytes(),native_map=mapping)
 q=proof['qualification'];assert (q['components'],q['terminals'],q['nets'],q['instances'],len(q['unconnected_pads']))==(5,11,5,3,4)
 native=source_drc(job,board);assert native['blocking']==0 and native['opens']==6
 report['cases'].append(dict(case='positive',passed=True,Native=native,proof_sha256=p.sha(classes.paths(job.out,'task')['proof']),class_metadata=metadata,steps=job.steps))
 fresh()
 job,board=case('net-partition-mismatch')
 def change_net(tree):
  labels=[r for r in sx.children(tree,'label') if sx.unquote(r[1])=='SIG_A'];assert len(labels)==2
  # Move only unit1's local label to SIG_B. All names/counts/classes stay;
  # actual Native export must expose the changed terminal partition.
  labels[0][1]='"SIG_B"'
 mutate_child(board,change_net);mutant=p.tree_hash(board.parent);mapping=classes_for(job,board)
 rejection=None
 try:classes.collect(job,'task',board,mapping)
 except ValueError as exc:rejection=str(exc)
 assert rejection is not None and 'terminal partitions differ' in rejection
 assert not classes.paths(job.out,'task')['proof'].exists()
 native=source_drc(job,board);assert native['blocking']>0
 assert p.tree_hash(board.parent)==mutant
 report['cases'].append(dict(case='actual-Native-net-partition-mismatch',passed=True,rejection=rejection,Native=native,source_hashes=mutant,steps=job.steps))
 fresh()
 job,board=case('wrong-instance-path');tree=sx.read(board)
 fps=sx.children(tree,'footprint');target=next(row for row in fps if classes.q._properties(row)['Reference']=='U1')
 other=next(row for row in fps if classes.q._properties(row)['Reference']=='U2')
 sx.one(target,'path')[1]=sx.one(other,'path')[1];sx.write(board,tree)
 rejection=None
 try:classes.requirement(board)
 except ValueError as exc:rejection=str(exc)
 assert rejection is not None and 'primary unit path differs' in rejection
 native=source_drc(job,board)
 report['cases'].append(dict(case='instance-path-refusal-with-actual-Native-observation',passed=True,rejection=rejection,Native=native,source_hashes=p.tree_hash(board.parent),steps=job.steps,scope='Identity refusal is required whether NativeDRC independently reports this path defect or not.'))
 fresh()
 job,board=case('unsupported-class-directive')
 project=json.loads(board.with_suffix('.kicad_pro').read_bytes());diag=copy.deepcopy(project['net_settings']['classes'][0]);diag.update(name='DIAG',priority=0);project['net_settings']['classes'].append(diag)
 p.save_json(board.with_suffix('.kicad_pro'),project)
 def class_flag(tree):
  tree.append(['netclass_flag','""',['length','2.54'],['shape','round'],['at','43.18','40.64','90'],['effects',['font',['size','1.27','1.27']]],['uuid','"16869780-9de6-40af-a305-545e8d0f5efa"'],['property','"Netclass"','"DIAG"',['at','43.18','40.64','90'],['hide','yes'],['effects',['font',['size','1.27','1.27']]]]])
 mutate_child(board,class_flag);before=p.tree_hash(board.parent);work=job.out/'class-input';shutil.copytree(board.parent,work)
 netlist=job.out/'class-control.net';state={'complete':False};start=len(job.steps)
 with local.preserve(work/board.with_suffix('.kicad_prl').name,job.out,job._local_settings_owner,cleanup_complete=lambda:state['complete']) as protection:
  try:job.step('class-control-export',[str(c.CLI),'sch','export','netlist','--format','kicadsexpr','--output',str(netlist),str(work/board.with_suffix('.kicad_sch').name)])
  finally:
   rows=job.steps[start:];state['complete']=len(rows)==1 and rows[0].get('cleanup_complete') is True
 after=p.tree_hash(work);p.check_drc_project(before,after,board.name,saved=False);local.check_preserved(work/board.with_suffix('.kicad_prl').name,before,protection)
 net_tree=sx.read(netlist);identities=sorted({classes.q._single(row,'class') for row in sx.children(sx.one(net_tree,'nets'),'net')})
 assert any(value!='Default' for value in identities)
 rejection=None
 try:classes.requirement(board)
 except ValueError as exc:rejection=str(exc)
 assert rejection is not None
 assert p.tree_hash(board.parent)==before
 p.save_json(job.out/'class-control-binding.json',dict(before=before,after=after,protection=protection,netlist_sha256=p.sha(netlist)))
 report['cases'].append(dict(case='actual-Native-class-identity-and-unsupported-refusal',passed=True,Native_class_identities=identities,rejection=rejection,source_hashes=before,steps=job.steps,scope='Deliberately unsupported nonDefault/childflag control; not a routing failure or supportedclass admission.'))
 fresh();report.update(status='completed',control_passed=True,Native_executed=True)
except (Exception,KeyboardInterrupt) as exc:
 report.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',control_passed=False,error=type(exc).__name__+': '+str(exc),Native_executed=any(job.steps for job in jobs))
try:fresh()
except BaseException as exc:report.update(status='freshness_or_budget_failed',control_passed=False,error=str(exc))
report.update(all_steps=[dict(job=str(job.out),steps=job.steps) for job in jobs],sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,external_exit_required=True,scope='Four finite actual selected7 owned Native identity controls; no candidate accepted, routing/GUI/platform breadth/electrical/human claim. Original source remains exact. All failures retained.')
p.save_json(out/'result.json',report);raise SystemExit(0 if report['control_passed'] else 2)
