"""DRAFT: retain completed INA2XX data/static facts only; no acquisition/Native.

The Teensy owned-facts schema is reused with the existing bounded030 retain
function and public complete-exit cost parser. Detailed foreign source inspection
is a hash-only witness; no CAD, model, README, licence body or findings is copied.
"""
from pathlib import Path
import ast,hashlib,json,math,os,re,stat,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,provenance as pv
from experiments.licensed_acquisition_v1 import fetch as acquisition
H=ROOT/'.runs/development-ina2xx-001'
DATA=ROOT/'.data/development-ina2xx-001'
OUTPUT=ROOT/'evidence/development-ina2xx-001.json'
notes=ROOT/'evidence/development-ina2xx-001-notes'
RESULT_SHA='ecfbcd7e6407c7d737ae8e8b7edd0314f7d43d8f44570848cf41031794ee1cee'
PROTOCOL_SHA='4b7d4d57a52b3db148ada5f230e284b48a6774232633174547010e6a0589fc38'
SHARED=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
SHARED_SHA='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
COST_SOURCE=ROOT/'scripts/report_current_comparison.py'
COST_SHA='0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e'
TEENSY=ROOT/'evidence/development-teensy-ethernet-001.json'
TEENSY_SHA='c0804b94d8a2a5cb769c696059bb3965d11696bf223a0e64f463b2e5394acbb1'

def read(q):return acquisition.decode(io.read_bytes(q,4*1024**2))
def write(q,value):
    with q.open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')

assert not OUTPUT.exists() and not OUTPUT.is_symlink() and not notes.exists() and not notes.is_symlink()
assert p.sha(SHARED)==SHARED_SHA and p.sha(COST_SOURCE)==COST_SHA and p.sha(TEENSY)==TEENSY_SHA
for path in (H,DATA):
    acquisition.contained(ROOT,path);s=path.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==os.getuid()
original_owner={path:(path.stat().st_dev,path.stat().st_ino,path.stat().st_uid) for path in (H,DATA)}
result=read(H/'result.json');plan=read(H/'protocol.json');freeze=read(H/'execution-freeze.json');acquired=read(H/'acquisition.json')
assert p.sha(H/'result.json')==RESULT_SHA and p.sha(H/'protocol.json')==PROTOCOL_SHA
assert result['kind']=='finite-ina2xx-development-data-acquisition-and-static-defer-v1'
assert result['decision']=='defer_no_installed_preflight_or_comparison' and type(result['eligible_family_count']) is int and result['eligible_family_count']==0
assert all(result[key] is False for key in ('Native','engine','GUI','accepted','comparison_ready','holdout','human_review','independent_family_established'))
assert result['source_originals_exact'] is result['source_originals_unchanged'] is True
assert (plan['repository'],plan['commit'],plan['expected_files'],plan['expected_bytes'])==('sparkfun/SparkFun_Qwiic_Current_Sensor_INA2XX','313d3e2c03218f00eb5fb051d5594f05c95abecf',5,871730)
assert acquired['status']=='acquired_unqualified' and acquired['source_exact'] is True
assert acquired['requests_actual']==5 and acquired['received_bytes']==871730
assert all(row['http_status']==200 and row['status']=='response_received' and row['url']==row['final_url'] for row in acquired['requests'])
assert acquired['protocol_sha256']==freeze['protocol_sha256']==PROTOCOL_SHA
source_inventory=acquisition.inventory(DATA,acquired['source_inventory'],cap=1024**2)
selected=[H/name for name in ('result.json','protocol.json','execution-freeze.json','acquisition.json','authoring-failure-001.json','worker.py','acquire-process.json','inspect-process.json','acquire-time.log','inspect-time.log','acquire-controller.log','inspect-controller.log','acquire.log','inspect.log')]
selected += [ROOT/'.runs/acquire-development-ina2xx-001.py',Path(__file__).resolve()]
witness={q:p.sha(q) for q in selected}
omitted=[dict(path=str((H/'inspection.json').relative_to(ROOT)),bytes=(H/'inspection.json').stat().st_size,sha256=result['evidence']['inspection.json'],reason='Detailed source exclusions/coordinates/model paths stay local; public scalar facts only.')]
for row in plan['rows']:
    q=DATA/acquisition.safe(row['source_path']);s=q.lstat()
    assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_uid==os.getuid() and not s.st_mode&0o222
    assert acquisition.payload(row,io.read_bytes(q,1024**2))==acquired['files'][row['source_path']]
    omitted.append(dict(path=str(q.relative_to(ROOT)),bytes=row['bytes'],sha256=acquired['files'][row['source_path']]['sha256'],reason='Foreign CAD or full creator README/licence body: metadata/hash only.'))

def stable():
    assert p.sha(H/'result.json')==RESULT_SHA and p.sha(H/'protocol.json')==PROTOCOL_SHA
    assert all(p.sha(q)==pin for q,pin in witness.items())
    assert all(p.sha(H/name)==pin for name,pin in result['evidence'].items())
    assert all(p.sha(ROOT/name)==pin for name,pin in freeze['material_sha256'].items())
    assert p.sha(SHARED)==SHARED_SHA and p.sha(COST_SOURCE)==COST_SHA and p.sha(TEENSY)==TEENSY_SHA
    for path,owner in original_owner.items():
        s=path.lstat();assert stat.S_ISDIR(s.st_mode) and not path.is_symlink() and (s.st_dev,s.st_ino,s.st_uid)==owner
    acquisition.inventory(DATA,source_inventory,cap=1024**2)
    for row in omitted:assert p.sha(ROOT/row['path'])==row['sha256']

# Unchanged bounded writer and complete external timing parser; no tree walk.
module=ast.parse(SHARED.read_text());nodes=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='retain'];assert len(nodes)==1
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SHARED),'exec'),globals())
module=ast.parse(COST_SOURCE.read_text());nodes=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in ('require','digest','complete_cost')];assert len(nodes)==3
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(COST_SOURCE),'exec'),globals())
costs={}
for phase in ('acquire','inspect'):
    process=read(H/(phase+'-process.json'));cost=complete_cost(H/(phase+'-time.log'))
    assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False
    assert cost['wall_seconds']==result['costs'][phase]['wall_seconds'] and cost['CPU_seconds']==result['costs'][phase]['CPU_seconds']
    costs[phase]=dict(complete_external_wall_seconds=cost['wall_seconds'],complete_external_CPU_seconds=cost['CPU_seconds'],time_log_sha256=cost['time_log_sha256'],process_sha256=p.sha(H/(phase+'-process.json')),process_cleanup_complete=True,process_exit_code=0,process_log_truncated=False,scope='Complete external phase exit; nested worker/runner samples overlap and are not added.')
# Preflight the exact allowlist before any public output. No raw input tree copier.
assert len(selected)<2000 and sum(q.stat().st_size for q in selected)<16*1024**2
for q in selected:
    s=q.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1
    raw=io.read_bytes(q,4*1024**2);assert b'\0' not in raw;raw.decode('utf8')
stable();notes.mkdir(mode=0o755)
refs={};files=[];material=[];total=0
for q in selected:
    retain(q,Path('retained-run')/q.name)
index=notes/'files.json';write(index,dict(schema=1,files=files,material=material,omitted_hash_only=omitted))
rights=dict(observed_hardware_grant='CC-BY-SA-4.0',license_notice_path='LICENSE.md',license_notice_sha256=acquired['files']['LICENSE.md']['sha256'],basis='Pinned creator hardware grant; MIT code separate. No foreign code executed.',limitations='Per-asset title/environment and raw redistribution remain unqualified; no legal certification.')
originals=[dict(source_path=row['source_path'],source_url='https://github.com/'+plan['repository']+'/blob/'+plan['commit']+'/'+row['source_path'],git_blob_sha1=row['git_blob_sha1'],sha256=acquired['files'][row['source_path']]['sha256'],bytes=row['bytes'],mode=row['mode'],rights=rights) for row in plan['rows']]
summary=dict(schema=1,kind='finite-licensed-development-data-acquisition-static-defer-owned-facts-v1',repository=plan['repository'],source_revision=plan['commit'],source_url='https://github.com/'+plan['repository']+'/tree/'+plan['commit'],split='development-exposed',status='acquired_exact_originals_then_statically_deferred',decision='DEFER; no installed preflight, Native or comparison follows',eligible_family_count=0,claims=dict(Native=False,routing=False,engine=False,GUI=False,accepted=False,comparison_ready=False,eligible_routing_family_claim=False,independent_family_claim=False,unrelated_family_established=False,holdout=False,human_review=False,electrical_or_physical_validation=False,product_quality_or_superiority=False),originals=originals,acquisition=dict(actual_requests=5,all_response_HTTP_statuses=[row['http_status'] for row in acquired['requests']],original_bytes=871730,original_files=5,network_bytes_cap=1024**2,output_bytes_cap=1024**2,redirects_or_retries=False,scripts_hooks_models_firmware_executed_or_acquired=False,source_bytes_unchanged=True,source_files_exact=True,source_constraints_modified=False),static_source_counts=result['static'],deferred_reasons=result['blockers'],actual_pure_static_refusals=result['pure_static_preflight'],source_declaration_limit=result['source_declarations'],ancestry_screen=dict(compared_exposed_families=[row['family'] for row in result['ancestry']['comparisons']],exact_reference_pad_net_partition_matches=sum(row['exact_partition_match'] for row in result['ancestry']['comparisons']),shared_footprint_UUIDs=sum(row['shared_footprint_UUIDs'] for row in result['ancestry']['comparisons']),independent_ancestry_established=False,limit=result['ancestry']['limit']),costs=costs,measured_phase_totals=result['complete_external_totals'],additional_costs=dict(authoring_and_AI_review='unknown, not zero',metadata_preparation_readback_and_retention='additional; measured retention complete-exit logs must be recorded separately by invoker, not zero',prior_metadata_screen='separate historical cost, not free'),authoring_failure=dict(preserved=True,record_sha256=result['evidence']['authoring-failure-001.json'],scope='Incorrect prospective material filename detected before protocol/worker/payload creation; zero HTTP or Native; cost unknown, not zero.'),local_receipt_pins=dict(result_sha256=RESULT_SHA,protocol_sha256=PROTOCOL_SHA,inspection_sha256=result['evidence']['inspection.json'],all_evidence=result['evidence']),preservation=dict(public_payload='Owned sanitized facts, controller/source and small execution records only; no foreign CAD/geometry/models/README/licence body/findings.',raw_sources=str(DATA.relative_to(ROOT)),raw_receipts=str(H.relative_to(ROOT)),backup_limit='Raw Mac-only outside010; hashes/facts are not a raw backup.',previous_closed_acquisitions_unchanged=True),review_scope='Author static readback/retention of stored facts, AI not independent author review or human PCB review; no validation rerun.',next_action=result['further_action'],curator=dict(path=str(Path(__file__).resolve().relative_to(ROOT)),sha256=witness[Path(__file__).resolve()],shared030_sha256=SHARED_SHA,complete_cost_source_sha256=COST_SHA,teensy_facts_pattern_sha256=TEENSY_SHA),files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
stable();write(OUTPUT,summary);output_pin=p.sha(OUTPUT);index_pin=p.sha(index)
# A late refusal preserves the partial new namespace; no overwrites or cleanup.
stable();assert p.sha(OUTPUT)==output_pin and p.sha(index)==index_pin
for row in files:assert p.sha(ROOT/row['path'])==row['sha256']
print(json.dumps(dict(packet=str(OUTPUT.relative_to(ROOT)),sha256=output_pin,index_sha256=index_pin,new_files=len(files),new_bytes=total,material_rows=len(material),decision='DEFER',eligible_family_count=0,Native=False)))
