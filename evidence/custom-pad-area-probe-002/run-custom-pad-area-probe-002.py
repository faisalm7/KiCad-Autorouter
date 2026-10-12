from pathlib import Path
import datetime, hashlib, json, os, resource, signal, subprocess, time
root=Path(__file__).resolve().parents[1]
argv=['python3','-B','experiments/custom_pad_area_probe_v1/driver.py','--run-import','--output','.runs/custom-pad-area-probe-002']
log=root/'.runs/custom-pad-area-probe-002-command.log';execution=root/'.runs/custom-pad-area-probe-002-execution.json'
assert not log.exists() and not execution.exists()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
started=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN);cleanup=[]
with log.open('xb') as output:
 p=subprocess.Popen(argv,cwd=root,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=p.wait(timeout=75)
 except (subprocess.TimeoutExpired,KeyboardInterrupt):
  cleanup.append('SIGTERM process group');os.killpg(p.pid,signal.SIGTERM)
  try:code=p.wait(timeout=5)
  except subprocess.TimeoutExpired:
   cleanup.append('SIGKILL process group');os.killpg(p.pid,signal.SIGKILL);code=p.wait(timeout=5)
after=resource.getrusage(resource.RUSAGE_CHILDREN);raw=log.read_bytes()
record={'argv':argv,'cwd':str(root),'git_head':head,'started_utc':started,'exit_code':code,'wall_seconds':time.monotonic()-t,'waited_child_cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,'cleanup_signals':cleanup,'log_sha256':hashlib.sha256(raw).hexdigest(),'log_bytes':len(raw),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Six fixed actual pinned-JAR whole-DSN area/contact import cases only; no router or native KiCad run and no support change.'}
execution.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));raise SystemExit(code)
