from pathlib import Path
import datetime, hashlib, json, os, resource, signal, subprocess, time
root=Path(__file__).resolve().parents[1]
import sys
protocol=root/'.runs/protected-lock-position-protocol-001.json'
assert hashlib.sha256(protocol.read_bytes()).hexdigest()=='1081a5276126fc60f744b6c1391e2547915080ffdf4da2fd5f22fe8d2866ca75'
cases=json.loads(protocol.read_text())['cases']
case=next(x for x in cases if x['id']==sys.argv[1])
argv=['python3','-B','-m','autorouter','route',case['board'],'--settings',case['settings'],'--output',case['output'],*case['overrides']]
log=Path(case['output']+'-command.log');execution=Path(case['output']+'-execution.json')
assert not Path(case['output']).exists()
assert not log.exists() and not execution.exists()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
started=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN);cleanup=[]
with log.open('xb') as output:
 p=subprocess.Popen(argv,cwd=root,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=p.wait(timeout=case['wall_cpu_seconds']+15)
 except (subprocess.TimeoutExpired,KeyboardInterrupt):
  cleanup.append('SIGTERM process group');os.killpg(p.pid,signal.SIGTERM)
  try:code=p.wait(timeout=5)
  except subprocess.TimeoutExpired:
   cleanup.append('SIGKILL process group');os.killpg(p.pid,signal.SIGKILL);code=p.wait(timeout=5)
after=resource.getrusage(resource.RUSAGE_CHILDREN);raw=log.read_bytes()
record={'argv':argv,'cwd':str(root),'git_head':head,'started_utc':started,'exit_code':code,'wall_seconds':time.monotonic()-t,'waited_child_cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,'cleanup_signals':cleanup,'log_sha256':hashlib.sha256(raw).hexdigest(),'log_bytes':len(raw),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Prospectively frozen protected identity restoration and locked-scope qualification; not a comparative routing gain.'}
execution.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));raise SystemExit(code)
