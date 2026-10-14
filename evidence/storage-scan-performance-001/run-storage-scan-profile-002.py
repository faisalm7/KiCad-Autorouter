from pathlib import Path
import ast,json,subprocess,time,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
out=ROOT/'.runs/storage-scan-performance-002';out.mkdir()
raw=subprocess.check_output(['git','show','19a42ed2d12d2a2bbab3d866d69ad93b0497ebf2:autorouter/pipeline.py'],cwd=ROOT).decode()
function=next(node for node in ast.parse(raw).body if isinstance(node,ast.FunctionDef) and node.name=='check_storage')
namespace={'c':p.c,'shutil':p.shutil,'Rejected':p.Rejected}
exec(compile(ast.Module(body=[function],type_ignores=[]),'stored-legacy-counter','exec'),namespace)
observations=[]
for name,call in [('legacy',namespace['check_storage']),('descriptor',p.check_storage)]:
 wall=time.monotonic();cpu=time.process_time();count=call()
 observations.append({'kind':name,'logical_bytes':count,'wall_seconds':time.monotonic()-wall,'parent_cpu_seconds':time.process_time()-cpu})
record={'schema':1,'kind':'same-root fresh full storage scan comparison','observations':observations,'same_logical_count':observations[0]['logical_bytes']==observations[1]['logical_bytes'],'git_head':p.tool_manifest()['git_head'],'runner_sha256':p.sha(ROOT/'autorouter/runner.py'),'pipeline_sha256':p.sha(ROOT/'autorouter/pipeline.py'),'legacy_git_head':'19a42ed2d12d2a2bbab3d866d69ad93b0497ebf2','controller_sha256':p.sha(Path(__file__)),'scope':'Two fresh full .data/.tools/.runs scans, no cached totals/omissions; first legacy then descriptor, same retainedpopulation, noNative/JAR. Filesystem caching may affect timing; one local performance observation, not routing speedup. Existing ceilings/headroom retained. Investigation outside alreadyfrozen002 methods; everyfuture routing call paysitsactualscan CPU/wall.'}
with (out/'result.json').open('x') as stream:stream.write(json.dumps(record,indent=2)+'\n')
print(json.dumps(record));raise SystemExit(0 if record['same_logical_count'] else 2)
