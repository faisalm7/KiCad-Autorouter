import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,adapter as dsn,sexpr as sx
from experiments.hfe_original_native_v1 import driver as shared
from experiments.placement_handoff_native_v1.driver import copy_bytes
HEAD='a5cf977974d00ebbf8711f28635e941e97743b77';shared.clean(HEAD)
OUT=ROOT/'.runs/free-angle-export-missing-probe-001';OUT.mkdir();tools=p.tool_manifest()
source=ROOT/'.runs/free-angle-native-enclosure-001/native/route/snapshot';before=p.tree_hash(source)
copy_bytes({q.name:q.read_bytes() for q in source.iterdir() if q.is_file()},OUT/'original')
board=OUT/'original/owned-free-angle.kicad_pcb'
job=shared.BoundJob(OUT/'job',45,lambda:min(43-(time.monotonic()-START),43-(cpu()-CPU0)),protect_local_settings=True)
copy_bytes({Path(n).name:(ROOT/n).read_bytes() for n in tools['implementation_sha256']},job.out/'code')
job.native('export-mapped','export',board,job.out/'mapped.dsn',job.out/'classes.json')
classes=f.read_json(job.out/'classes.json');audit=p.audit_candidate_netclasses(board,p.routes(sx.read(board)),classes)
old=ROOT/'.runs/free-angle-native-enclosure-001/native/route/native.dsn'
def rules(path):
 tree=dsn._parse_dsn(path.read_text());return dict(structure_rule=sx.children(sx.one(tree,'structure'),'rule'),classes=sx.children(sx.one(tree,'network'),'class'),vias=sx.children(sx.one(tree,'structure'),'via'))
record=dict(schema=1,kind='missing-only-mapped-versus-unmapped-native-export',accepted=False,tools=tools,source_sha256=before,source_unchanged=p.tree_hash(source)==before and p.tree_hash(board.parent)==before,steps=job.steps,original_unmapped_sha256=p.sha(old),mapped_sha256=p.sha(job.out/'mapped.dsn'),original_unmapped_rules=rules(old),mapped_rules=rules(job.out/'mapped.dsn'),native_classes=classes,source_target_audit=audit,scope='One missing-only original-task export with existing mapping flag, no engine/DRC/candidate rerun or source edits. Compare to retained original actual unmapped export; no Native-positive route qualification.',wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
assert record['source_unchanged'] and p.tool_manifest()==tools
p.save_json(OUT/'result.json',record);print(f.canonical({k:record[k] for k in ['wall_seconds','full_cpu_seconds','original_unmapped_rules','mapped_rules']}))
