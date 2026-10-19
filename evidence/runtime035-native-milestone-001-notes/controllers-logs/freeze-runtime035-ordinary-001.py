"""Fresh current-source regressions using unchanged ordinary workflow helper."""
from pathlib import Path
import sys,json,datetime,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
runtime=ROOT/'.runs/runtime-directory-035/runtime';manifest=runtime/'runtime-distribution.json';data=json.loads(manifest.read_bytes())
assert json.loads((ROOT/'.runs/full-integration-178/execution.json').read_bytes())['passed']
assert json.loads((ROOT/'.runs/install-distribution-native-008/execution.json').read_bytes())['passed']
assert data['build_source']['git_head']=='7edc7229ea905e6734bf6cec8ff926a92e6a8613' and data['native_version']=='10.0.7'
assert p.sha(manifest)=='8f0c455d7db2beb64e23283081fe788cfc26ee4d49cd95c8fd152b8e45ccb677'
assert data['immutable_files_sha256']['autorouter/gui.py']=='93963f6a68d3269042298b6a2d374ffbfa18a86315c2ee30cb9cf02d7caf709e'
assert shutil.disk_usage(ROOT).free>2*1024**3
for label in ('whole4Cu','partial2Cu'):
 old=ROOT/('.runs/runtime033-ordinary-'+label+'-001');plan=json.loads((old/'protocol.json').read_bytes());source=Path(plan['source']);assert p.tree_hash(source.parent)==plan['source_hashes']
 assert p.sha(ROOT/'.runs/enclose-runtime030-ordinary-workflow-001.py')==plan['enclosure_sha256']
 assert p.sha(ROOT/'scripts/qualify_runtime_workflow.py')==plan['driver_sha256']
 base=ROOT/('.runs/runtime035-ordinary-'+label+'-001');base.mkdir();raw=(old/'settings.json').read_bytes()
 with (base/'settings.json').open('xb') as stream:stream.write(raw)
 assert p.sha(base/'settings.json')==plan['settings_sha256']
 output=runtime/('.runs/production-'+label+'-delivery-001');assert not output.exists()
 plan.update(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=data['build_source']['git_head'],runtime=str(runtime),runtime_manifest_sha256=p.sha(manifest),output=str(output),scope='Fresh035 actual ordinary Request/Workflow/CliJob six-stage Native/full-schematic/original/protected regression after presentation-only captured recovery-budget correction; same explicit constraints/settings/expected warnings. No GUI/recovery/comparative/breadth/cleanOS/release claim. Existing unchanged enclosure030 kind label is historical helper name; actual runtime/provenance035 is mandatory.')
 with (base/'protocol.json').open('x') as stream:json.dump(plan,stream,indent=2);stream.write('\n')
 print(json.dumps(dict(label=label,protocol=str(base/'protocol.json'),sha256=p.sha(base/'protocol.json'),freeze_only=True)))
