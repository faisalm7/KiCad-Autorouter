"""Retain owned administration sources/controls, never foreign board payloads."""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io

HELPER=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
HELPER_SHA='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
notes=ROOT/'evidence/current-comparison-improve-administration-001-notes'
summary_path=ROOT/'evidence/current-comparison-improve-administration-001.json'
assert not notes.exists() and not summary_path.exists()
refs={};files=[];material=[];total=0
raw=io.read_bytes(HELPER,4*1024**2)
assert hashlib.sha256(raw).hexdigest()==HELPER_SHA
parsed=ast.parse(raw)
selected=[node for node in parsed.body if isinstance(node,ast.FunctionDef) and node.name in {'retain','cost'}]
assert {node.name for node in selected}=={'retain','cost'}
exec(compile(ast.Module(body=selected,type_ignores=[]),str(HELPER)+'::retain-cost','exec'),globals())

def read(name):
    return json.loads(io.read_bytes(ROOT/name,4*1024**2))

def pin(name,expected=None):
    raw=io.read_bytes(ROOT/name,4*1024**2)
    value=dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    assert expected is None or value['sha256']==expected
    return value

cutoff_names=[
 ('.runs/current-comparison-improve-administration-001.json','6bf65bb86e7de485bb191d27e8ae61315328099ba0c40b4a40cb1de7b735d9b5'),
 ('.runs/current-comparison-native-policy-correction-001.json','f50eb353c6157f6e26f9ec2e7ef06785afae4df3c5eb265210f3d653fd647878'),
 ('.runs/current-comparison-no-field-correction-001.json','48b5cf44831818caba268410d527ec76f8f4eccf3c40e27c2740e0853148ecbb')]
cutoff_pins=[pin(name,sha) for name,sha in cutoff_names]
cutoffs=[read(name) for name,_ in cutoff_names]
latest=cutoffs[-1]
for row in latest['source_pins']:assert pin(row['path'])==row
intent_name='.runs/runtime050-optional-improve-development-intent-001.json'
intent_pin=pin(intent_name,'1b4a03b06819e4a983b04d06baa27ed1006b406de8825ec8f307e2efb19906eb')
schema_base='.runs/runtime050-improve-report-schema-review-001/'
schema_pin=pin(schema_base+'result.json','9649e7836ab71c9e789d79a0686d2c8b5c0c2bf0e072c55c271f576feefddadd')
schema=read(schema_base+'result.json')
assert schema['Native_executed'] is False and schema['central_readers_executed'] is False
assert schema['source_sha256_before']==schema['source_sha256_after']=='0e4cbed10b1ee09f3613dd2aadcd3d0f94c632bc700691334a0dcd7004bfcfba'
assert schema['all_helpers_passed'] is True and len(schema['actual_completed_roles'])==4 and len(schema['in_memory_fault_controls'])==7
dependencies=[pin('evidence/runtime050-install-existing-001.json','27ec36c6c6b23c631499b986656c2a4181305bca2443019be0c83ddb21807185'),
 pin('evidence/runtime050-native-milestone-002.json','1d0d2019d5505f1fad0134cc2163b3337ce227e1b8d841c8c3c8a81e21a94934')]

selection=[]
def select(name,target,expected=None):
    record=pin(name,expected);selection.append((record,target))

for item in cutoff_pins:select(item['path'],Path('cutoffs')/Path(item['path']).name,item['sha256'])
select(intent_name,Path('prospective-intent')/Path(intent_name).name,intent_pin['sha256'])
for row in latest['source_pins']:select(row['path'],Path('source')/row['path'],row['sha256'])
for row in latest['preserved_pre_correction_sources']:
    select(row['path'],Path('prior-policy-correction-source')/Path(row['path']).relative_to('.runs/current-comparison-no-field-pre-correction-001'),row['sha256'])
tests=[]
for index,cutoff in enumerate(cutoffs):
    for event in cutoff['tests']:
        row=dict(event,source_cutoff_sha256=cutoff_pins[index]['sha256'])
        for label in ('stdout','stderr_and_external_time'):
            item=event[label];select(item['path'],Path('targeted-controls')/Path(item['path']).name,item['sha256'])
        measured=cost(ROOT/event['stderr_and_external_time']['path'])
        assert measured['wall_seconds']==event['wall_seconds'] and measured['CPU_seconds']==event['full_CPU_seconds']
        tests.append(row)
for name in ('result.json','execution.json','check.py','run.log','time.log'):
    select(schema_base+name,Path('earlier-schema-helper')/name,schema_pin['sha256'] if name=='result.json' else None)
schema_cost=cost(ROOT/(schema_base+'time.log'))
assert schema_cost==dict(wall_seconds=.32,CPU_seconds=.21)
select('LICENSE',Path('rights/LICENSE'))
select(str(HELPER.relative_to(ROOT)),Path('curation/retention-helper.py'),HELPER_SHA)
select(str(Path(__file__).relative_to(ROOT)),Path('curation')/Path(__file__).name)
# Exact finite population, UTF8 text only. Preflight before exclusive writes.
assert len(selection)<2000 and sum(row['bytes'] for row,_ in selection)<16*1024**2
for row,_ in selection:
    raw=io.read_bytes(ROOT/row['path'],4*1024**2)
    assert b'\0' not in raw;raw.decode('utf8')
for row,target in selection:retain(ROOT/row['path'],target)
scope=('Owned administration source/control evidence only. No board/CAD/DSN/SES, raw foreign findings, plots, binaries, venvs, caches, private inputs or credentials were selected. '
       'The schema-helper result refers only to already stored owned050 Native facts at an earlier reporter pin; no Native or central reader was run by that check or this curation. '
       'Earlier source cutoffs remain byte-exact records; only the final source population and preserved pre-no-field correction source files are copied, so a cutoff hash alone is not a claim that every earlier source snapshot is present.')
scope_path=notes/'SCOPE.md'
with scope_path.open('x') as out:out.write('# Scope and rights\n\n'+scope+'\n\nProject-owned GPL-3.0 source/tests, authored receipts and logs; retained LICENSE applies. Existing installation/Native packets are dependency references, not revalidated here. AI review is not human PCB review.\n')
scope_raw=scope_path.read_bytes();files.append(dict(path=str(scope_path.relative_to(ROOT)),bytes=len(scope_raw),sha256=hashlib.sha256(scope_raw).hexdigest()));total+=len(scope_raw)
index=notes/'files.json'
with index.open('x') as out:json.dump(dict(schema=1,files=files,material=material),out,indent=2);out.write('\n')
for row in files:assert pin(row['path'])==row
for row in material:assert pin(row['original'])['sha256']==pin(row['retained'])['sha256']==row['sha256']
for row in latest['source_pins']:assert pin(row['path'])==row
summary=dict(schema=1,kind='current-comparison-versioned-Cimprove-administration-controls-with-corrections-v1',
 recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,production_admitted=False,
 Native_executed=False,GUI_executed=False,comparison_executed=False,full_suite_executed=False,human_review=False,
 producer050_changed=False,source_cutoffs=cutoff_pins,final_source_pins=latest['source_pins'],dependencies=dependencies,
 implementation='Explicit versioned six-arm Cimprove administration extension. Legacy042/six-arm Cthermal contracts remain. New050 qualification is installed CLI/prepared GUI only, not full GUI. No runtime/router/engine policy or source board changed.',
 corrections=[dict(cutoff_sha256=cutoff_pins[1]['sha256'],scope='Stored own-final classification reuses the hash-bound product Native policy: warning-only/disabled-critical-check negatives stay distinct from Native-valid quality-rejected trials. Field qualification false alone adds no new policy rejection.'),
              dict(cutoff_sha256=cutoff_pins[2]['sha256'],scope='Field observations are conditional on exact hash-bound raw field findings. No-field facts require field artifacts/journals/own-root field steps/field_parity absent and report not_applicable; present findings retain the complete bridge.')],
 targeted_controls=tests,targeted_complete_exit_totals=dict(wall_seconds=round(sum(row['wall_seconds'] for row in tests),2),CPU_seconds=round(sum(row['full_CPU_seconds'] for row in tests),2),scope='All eight actual offline invocations, including two intentional REDs and one failing test-fixture invocation. Earlier sources/test populations are distinct; no sum is a final test count.'),
 final_targeted=dict(passed=True,tests=38,wall_seconds=.73,CPU_seconds=.65,scope='Two affected reporter/Improve modules; constructed offline guards only. Earlier freezer tests remain in their own cutoff; no full-suite pass from this work.'),
 earlier_schema_check=dict(result=schema_pin,reporter_sha256=schema['source_sha256_before'],stored_owned_roots=4,in_memory_controls=7,complete_cost=schema_cost,scope='Earlier source pin, not rerun after corrections. Existing owned receipts inspected only; no full420 Improve facts, Native or central revalidation.'),
 prospective_intent=dict(receipt=intent_pin,not_executed=True,families=['ds18b20','ir-obstacle'],exposure='Already exposed development families; no new or untouched family claim.',planned_arms=12,route_seconds=420,method_seconds=450,complete_seconds=600,export_seconds=120),
 accounting='Complete external test and stored-schema-helper exits are separate. Curation external exit is recorded in the adjacent local curator -time.log after this summary is emitted. Authoring/review cost remains unknown additional, not zero; no speed/comparative claim.',
 rights='Owned GPL source/tests and authored logs/metadata only; LICENSE retained. Third-party CAD/raw finding payload not selected.',
 public_safety_audit=dict(scope='Exact selected UTF8/NUL-free owned metadata/source/control files inspected; no archive scan or automatic publication. Local source/evidence paths remain as provenance.',foreign_geometry_payload=False),
 retained=dict(unique_payload_files=len(files),payload_bytes=total,material_rows=len(material),caps=dict(per_file_bytes=4*1024**2,total_bytes=16*1024**2,files=2000)),
 limitations=['No Native/engine/GUI/comparison/full-suite execution from this administration work.','No optional-Improve gain, broad superiority, electrical, human, holdout or family-independence claim.','Lead integration/audit/checkpoint and exact fresh protocol freeze remain prerequisites for any sequential comparison runs.','Local raw outside010 remains Mac-only; this is a small public evidence packet, not full backup/restoration.'],
 files_index=pin(str(index.relative_to(ROOT))))
with summary_path.open('x') as out:json.dump(summary,out,indent=2);out.write('\n')
print(json.dumps(dict(summary=pin(str(summary_path.relative_to(ROOT))),index=pin(str(index.relative_to(ROOT))),files=len(files),bytes=total,material=len(material))))
