"""Finite existing-runner enclosure; preserve all attempts and output."""
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'.runs/development-ina2xx-001'
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter.runner import run
ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['acquire','inspect']);a=ap.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((HERE/'execution-freeze.json').read_bytes())
for name,pin in freeze['material_sha256'].items():
 if sha(ROOT/name)!=pin:raise ValueError('frozen helper changed')
if sha(HERE/'protocol.json')!=freeze['protocol_sha256']:raise ValueError('protocol changed')
start=time.monotonic();receipt=run([sys.executable,'-B',str(HERE/'worker.py'),a.phase,'--protocol-sha256',freeze['protocol_sha256']],cwd=HERE,log=HERE/(a.phase+'.log'),timeout=90 if a.phase=='acquire' else 30,max_log_bytes=65536,max_group_rss_bytes=512*1024**2,max_workdir_bytes=16*1024**2)
with (HERE/(a.phase+'-process.json')).open('x') as stream:json.dump(receipt,stream,indent=2,sort_keys=True);stream.write('\n')
for name,pin in freeze['material_sha256'].items():
 if sha(ROOT/name)!=pin:raise ValueError('frozen helper changed after child')
print(json.dumps(dict(phase=a.phase,status=receipt['status'],exit_code=receipt['exit_code'],wall_seconds=receipt['wall_seconds'],cpu_seconds=receipt['cpu_seconds'],cleanup_complete=receipt['cleanup_complete'],complete_outer_wall_seconds=time.monotonic()-start)))
raise SystemExit(0 if receipt['status']=='success' and receipt['cleanup_complete'] and not receipt['log_truncated'] else 2)
