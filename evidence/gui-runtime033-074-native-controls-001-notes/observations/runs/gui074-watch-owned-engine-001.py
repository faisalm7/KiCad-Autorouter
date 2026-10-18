"""Finite read-only test oracle; GUI/production runner alone owns cancellation."""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys, time

workspace=Path(sys.argv[1]).resolve(strict=True)
output=Path(sys.argv[2])
assert workspace.parent.name=='jobs' and workspace.name.startswith('autorouter-gui-')
assert not output.exists()
start=time.monotonic();cpu=time.process_time();result=None;polls=0
while time.monotonic()-start<45:
    raw=subprocess.check_output(['/bin/ps','-axo','pid=,ppid=,pgid=,command='],timeout=2)
    assert len(raw)<=1024**2
    processes={}
    for line in raw.decode().splitlines():
        parts=line.strip().split(None,3)
        if len(parts)==4:processes[int(parts[0])]=(int(parts[1]),int(parts[2]),parts[3])
    polls+=1
    owners={pid for pid,(parent,group,cmd) in processes.items() if cmd.endswith('Python -B -m autorouter.gui') and '/Users/faisal/Projects/KiCad-Autorouter-local/.tools/kicad-10.0.7-local-001/KiCad.app/' in cmd and parent in processes and processes[parent][2]=='/Users/faisal/Projects/KiCad-Autorouter-local/.tools/kicad-10.0.7-local-001/KiCad.app/Contents/MacOS/kicad'}
    assert owners, 'No current owned KiCad GUI ancestry found'
    for pid,(parent,group,command) in processes.items():
        if str(workspace) not in command or 'java' not in command or '-jar' not in command:continue
        chain=[];current=pid
        while current in processes and len(chain)<16:
            chain.append(current)
            if current in owners:break
            current=processes[current][0]
        if chain[-1] not in owners:continue
        result=dict(schema=1,actual_engine_observed=True,PID=pid,PPID=parent,PGID=group,
                    owned_ancestry=chain,argv_text=command,argv_text_sha256=hashlib.sha256(command.encode()).hexdigest(),
                    workspace=str(workspace),observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    scope='Read-only phase observation. No signal/GUI action/cleanup assertion by this oracle.')
        break
    if result is not None:break
    time.sleep(.05)
if result is None:result=dict(schema=1,actual_engine_observed=False,workspace=str(workspace),scope='No engine observed within finite45second bound; no cancellation-phase claim.')
result.update(observer_wall_seconds=time.monotonic()-start,observer_parent_CPU_seconds=time.process_time()-cpu,polls=polls,
              ps_child_CPU_seconds=None,accounting='Test-oracle overhead separate; ps child CPU not instrumented, not zero. No routing speed claim.')
with output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps(result),flush=True)
