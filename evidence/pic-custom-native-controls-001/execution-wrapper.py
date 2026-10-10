"""One foreground invocation; preserve exact exit and outer accounting."""
from pathlib import Path
import datetime, hashlib, json, os, resource, signal, subprocess, sys, time
root=Path('/Users/faisal/Projects/KiCad-Autorouter-local')
name='pic-custom-native-controls-001'
assert Path.cwd()==root and not (root/'.runs'/name).exists()
log=root/'.runs'/(name+'-command.log');receipt=root/'.runs'/(name+'-execution.json')
assert not log.exists() and not receipt.exists()
argv=[sys.executable,'-B','experiments/pic_custom_native_controls_v1/driver.py','--run-native','--output','.runs/'+name]
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=root).strip()
start=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
record={'argv':argv,'cwd':str(root),'git_head':head,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'outer_wall_limit_seconds':210,'stdout_stderr':str(log.relative_to(root)),'outer_cleanup_signals':[]}
with log.open('xb') as stream:
 process=subprocess.Popen(argv,cwd=root,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=process.wait(timeout=210)
 except subprocess.TimeoutExpired:
  record['outer_cleanup_signals'].append('SIGTERM process group');os.killpg(process.pid,signal.SIGTERM)
  try:code=process.wait(timeout=5)
  except subprocess.TimeoutExpired:
   record['outer_cleanup_signals'].append('SIGKILL process group');os.killpg(process.pid,signal.SIGKILL);code=process.wait(timeout=5)
end=resource.getrusage(resource.RUSAGE_CHILDREN)
record.update(controller_exit_code=code,outer_wall_seconds=time.monotonic()-start,outer_waited_child_cpu_seconds=end.ru_utime+end.ru_stime-before.ru_utime-before.ru_stime,log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
receipt.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
print(log.read_text()[-3000:])
raise SystemExit(code if code>=0 else 128-code)
