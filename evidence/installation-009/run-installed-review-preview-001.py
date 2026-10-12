from pathlib import Path
import datetime, hashlib, json, os, resource, signal, subprocess, time
root=Path(__file__).resolve().parents[1]
installation=root/'.runs/installation-009/result.json'
installation_raw=installation.read_bytes();installed=json.loads(installation_raw);assert installed['passed'] is True and installed['git_head']=='339e539600798a221f423a7e70b53242f17a062f'
checkout=root/'.runs/installation-009/checkout';python=checkout/'.venv/bin/python'
assert installed['venv']['prefix']==str(checkout/'.venv')
argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(python),'-B','-m','autorouter','review-copy',installed['native_receipt']['path'],'--render','--output','.runs/install-review-preview-001']
log=root/'.runs/installed-review-preview-001-command.log';execution=root/'.runs/installed-review-preview-001-execution.json'
assert not log.exists() and not execution.exists()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip()
started=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN);cleanup=[]
with log.open('xb') as output:
 p=subprocess.Popen(argv,cwd=checkout,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=p.wait(timeout=45)
 except (subprocess.TimeoutExpired,KeyboardInterrupt):
  cleanup.append('SIGTERM process group');os.killpg(p.pid,signal.SIGTERM)
  try:code=p.wait(timeout=5)
  except subprocess.TimeoutExpired:
   cleanup.append('SIGKILL process group');os.killpg(p.pid,signal.SIGKILL);code=p.wait(timeout=5)
after=resource.getrusage(resource.RUSAGE_CHILDREN);raw=log.read_bytes()
assert installation.read_bytes()==installation_raw
record={'argv':argv,'cwd':str(checkout),'git_head':head,'started_utc':started,'exit_code':code,'wall_seconds':time.monotonic()-t,'waited_child_cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,'cleanup_signals':cleanup,'log_sha256':hashlib.sha256(raw).hexdigest(),'log_bytes':len(raw),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'installation_sha256':hashlib.sha256(installation_raw).hexdigest(),'installed_python':str(python),'scope':'Installed clone/venv optional native copper plotting of an already accepted owned fixture through existing review-copy transaction; no engine, new DRC, source apply or GUI claim.'}
execution.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));raise SystemExit(code)
