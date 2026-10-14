"""Bounded fresh incumbent experiment; no baseline candidate is a solver input."""
from pathlib import Path
import time
START=time.monotonic();CPU0=time.process_time()
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,strategy as s,handoff as h
from autorouter.runner import run
from scripts import experiment_quality as q
CPU0+=f.child_cpu()

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--inner',action='store_true')
 args=parser.parse_args();protocol=args.protocol.resolve(strict=True);spec=f.read_json(protocol);out=h.real_path(args.output,existing=args.inner)
 board=Path(spec['source']);q.verify_freeze(spec['freeze'],board)
 if p.sha(Path(__file__))!=spec['controller_sha256']:raise p.Rejected('experiment controller changed')
 for name,pin in spec['artifacts'].items():
  if p.sha(Path(name))!=pin:raise p.Rejected('original/baseline evidence changed')
 if args.inner:
  result=s.prune(board,out/'run',spec['inner_seconds'],proposal_policy='feedback',incumbent_scoring='via_high')
  print(json.dumps({k:result.get(k) for k in ('status','accepted','reason','metrics')}))
  return 0 if result.get('accepted') else 2
 out.mkdir();owner={};h.capture_destination(owner,out)
 argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--protocol',str(protocol),'--output',str(out),'--inner']
 process=run(argv,cwd=out,log=out/'command.log',timeout=spec['outer_wall_seconds']-(time.monotonic()-START),max_log_bytes=256*1024,max_workdir_bytes=64*1024**2,max_group_rss_bytes=2*1024**3)
 h.owned_destination(owner);q.verify_freeze(spec['freeze'],board)
 record={'schema':1,'process':process,'wall_seconds':time.monotonic()-START,'full_cpu_seconds':time.process_time()+f.child_cpu()-CPU0,'protocol_sha256':p.sha(protocol),'controller_sha256':p.sha(Path(__file__)),'log_sha256':p.sha(out/'command.log'),'fresh_own_high_solve':True,'baseline_candidate_used_as_input':False,'native_executions_sequential':True,'cost_scope':'Module entry before imports through final checks; separate1startup/publication allowance charged in prospective protocol; source18+audit15 also charged. This is a separately frozen exposed hypothesis, not a <=120 continuation of prior defaultC. Total exploration costs must retain both methods.'}
 p.save_json(out/'execution.json',record);print(json.dumps({k:record[k] for k in ('wall_seconds','full_cpu_seconds')}))
 return 0 if process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] else 2

if __name__=='__main__':raise SystemExit(main())
