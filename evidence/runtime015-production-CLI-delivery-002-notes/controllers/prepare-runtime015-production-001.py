"""Freeze one fresh default-production workflow; reuse prepared015 unchanged."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-015/runtime'
sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,preferences as pref
tools=p.tool_manifest();assert tools['git_head']=='73de3151b4ca81319a537595e68dc461b73b1664'
prior=f.read_json(ROOT/'.runs/runtime-directory-014/setup.json');item=prior['sources']['matching'];source=Path(item['board']).parent
assert p.tree_hash(source)==item['source_hashes']
child=runtime/'.runs/qualify-runtime015-production-001.py';assert not child.exists();shutil.copyfile(ROOT/'.runs/qualify-runtime015-production-001.py',child)
plan=dict(schema=1,kind='fresh-installed015-default-production-workflow',source_head=tools['git_head'],runtime_tools=tools,
 runtime_manifest_sha256=p.sha(runtime/'runtime-distribution.json'),child_sha256=p.sha(child),board_name=Path(item['board']).name,
 fixture_files={n:(source/n).read_text()for n in item['source_hashes']},fixture_sha256=item['source_hashes'],settings={**pref.DEFAULTS,'seconds':90},
 whole_child_wall_full_cpu_seconds=240,outer_cooperative_watchdog_seconds=245,outer_acceptance_seconds=260,
 scope='One fresh shipped production10.0.0 CLI workflow through unchanged GUI model: preview/protected4Cu Route/render/test intent/fresh Native export/check. No actual GUI rerun, new family, quality advantage, human/physical approval or experimental1007 promotion. Preparation is separate cold research setup, no repeated runtime build; every actual CLI/Native/readback/delivery step is counted.')
path=runtime.parent/'production-delivery-protocol-001.json';assert not path.exists();p.save_json(path,plan)
print(json.dumps(dict(protocol=str(path),protocol_sha256=p.sha(path),Native_executed=False)))
