"""Retain an explicit metadata/owned-draft list; never run validation or routing.

The public reporter already checked stored custody. This copies bounded safe
metadata only. All unique CAD/DSN/SES/raw findings remain on this Mac outside010.
"""
from pathlib import Path
import datetime, hashlib, json, os, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from scripts import report_current_comparison as q

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):
    with path.open('x') as stream:json.dump(data,stream,indent=2);stream.write('\n')
def retain(name,paths):
    notes=ROOT/'evidence'/(name+'-notes');packet=ROOT/'evidence'/(name+'.json')
    assert not os.path.lexists(notes) and not os.path.lexists(packet)
    rows=[];pending=[];total=0
    assert len(paths)==len(set(paths)) and len(paths)<100
    for source in paths:
        assert source.is_file() and not source.is_symlink() and source.is_relative_to(ROOT/'.runs')
        raw=q.pv.read_bytes(source,4*1024**2);raw.decode('utf8');assert b'\0' not in raw
        relative=source.relative_to(ROOT/'.runs');target=notes/relative
        total+=len(raw);assert total<8*1024**2
        pending.append((source,target,raw,sha(source)))
    notes.mkdir()
    for source,target,raw,pin in pending:
        assert sha(source)==pin;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(raw)
        assert sha(target)==pin
        rows.append(dict(source=str(source.relative_to(ROOT)),path=str(target.relative_to(ROOT)),sha256=pin,bytes=len(raw)))
    return packet,rows

base=ROOT/'.runs/runtime043-ir-support-followup-001'
report_path=ROOT/'.runs/runtime043-ir-support-facts-001/report.json'
assert sha(report_path)=='46f57d6e2001e059776fc89ffa978930d755dd8b3b5721420eb3cc16058b1498'
report=q.read(report_path)
assert len(report['rows'])==6 and [r['arm'] for r in report['rows']]==list(q.frozen.ARM_ORDER)
assert [r['evidence_classification'] for r in report['rows']].count('validated_delivery')==5
assert report['complete_external_totals']==dict(wall_seconds=565.27,CPU_seconds=545.06)
paths=[report_path,report_path.with_name('files.json'),ROOT/'.runs/runtime043-ir-support-facts-001.log',ROOT/'.runs/runtime043-ir-support-facts-001-time.log',
    ROOT/'.runs/freeze-runtime043-ir-followup-001.py',ROOT/'.runs/freeze-runtime043-ir-followup-001.log',ROOT/'.runs/freeze-runtime043-ir-followup-001-time.log',
    ROOT/'.runs/current-comparison-report-targeted-001.log',ROOT/'.runs/current-comparison-report-targeted-001-time.log',Path(__file__)]
paths += [base/name for name in ('population.json','frozen-children.json','sources.json','native-only-prerequisites.json','tools-defaults.json','tools-defaults-process.json')]
for arm in report['planned_arm_order']:
    paths += [base/'ir-obstacle'/arm/name for name in ('protocol.json','outer.log','outer-time.log','enclosure/result.json','enclosure/process.json','enclosure/command.log')]
packet,files=retain('runtime043-ir-support-followup-001',paths)
save(packet,dict(schema=1,kind='runtime043-labelled-IR-support-followup-facts-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    accepted=False,project_complete=False,actual_GUI=False,human_review=False,source_head=report['source_head'],runtime_manifest_sha256=report['runtime_manifest_sha256'],
    administration_head=report['administration_head'],report=report,files=files,preparation_complete_cost=q.complete_cost(ROOT/'.runs/freeze-runtime043-ir-followup-001-time.log'),
    report_complete_cost=q.complete_cost(ROOT/'.runs/runtime043-ir-support-facts-001-time.log'),targeted_complete_cost=q.complete_cost(ROOT/'.runs/current-comparison-report-targeted-001-time.log'),
    targeted_tests=dict(passed=True,tests=11,Native=False),AI_spot_review=dict(reviewer='/root/preset_picker_review',human=False,findings=[],
        scope='Read-only current reporter/tests and actual six-row artifacts. Own final candidate/report/process/binding/input/source/tool/fullSCH/exit5/cleanup and sealed containment checked; source five files unchanged. No new Native or central readers.'),
    disposition='Integrate narrow actual7 fractional rectangle support. Corrected standard/B1 stays default. IR default now delivers, but B1/tuned/restart also deliver and thermal returns the unchanged incumbent; no new gain beyond B1/B2. Source warnings/ignored checks and all old042 failures remain.',
    interpretation='One exposed circuit-family label, not independent ancestry, untouched confirmation, general superiority, cleanup, electrical, GUI or standalone qualification. All five deliveries retain42warnings/seven ignored; protected0 gives no protection positive. Portfolio fixed via_high winner trades length175.6898mm/0vias against other valid167.4251mm/2vias.',
    prior_original=dict(path='evidence/runtime042-unrelated-development-comparison-001.json',sha256='a9aaf1edeedb224e046cbf3fb69c2e3b73e60993fe0caaaa8e5b945c737b2f60',unchanged=True),
    rights='IR source Ahmed Osama Metwally creator MIT grant at AhmedOsama21998/IR-Obstacle-Avoidance-Sensor-PCB@6399dfd3bd8d2f48878a9a7c5b2f2e7a76a2b899. Local cached research use; CAD/artwork/model title closure remains unqualified. Own metadata/hash facts only, no CAD/DSN/SES/plots/raw findings redistributed.',
    accounting='Six complete external exits565.27wall/545.06CPU; nested samples included once. Setup/report/targeted/research/authoring/AI review/retention/whole-interactive costs additional; unmetered notzero. CLI/API authority workloads and desktop contention limit speed inference. This retention exit is separately metered after publication.',
    backup='Metadata Git-backed only after verified checkpoint. All new unique raw remains on this Mac outside010; current full restoration capacity blocked.'))

session=ROOT/'.runs/runtime-directory-043/runtime/.runs/gui-session083'
access=ROOT/'.runs/gui083-access-001.json';observed=q.read(access)
assert observed['actual_GUI_qualified'] is False and not list((session/'jobs').iterdir())
packet,files=retain('gui-runtime043-083-access-001',[access,session/'prepared-state.json',session/'protocol-required-001.json',session/'prepare-launcher-process.json',
    ROOT/'.runs/prepare-runtime043-gui083.py',ROOT/'.runs/prepare-runtime043-gui083.log',ROOT/'.runs/prepare-runtime043-gui083-time.log',ROOT/'.runs/gui083-boundary-via-shared081-001.py'])
save(packet,dict(schema=1,kind='runtime043-GUI083-prepared-and-picker-input-gate-v1',source_head=observed['source_head'],runtime_manifest_sha256=observed['runtime_manifest_sha256'],
    project_complete=False,actual_GUI_qualified=False,human_review=False,observed=observed,files=files,
    scope='Actual manager launch/setup and picker observed; no toolbar/route/review/choice/cancellation/export/open roles qualified. One minimum owner action requested, no lock or security setting change. Prepared sources and unfinished jobs preserved; current processes must be rechecked before reuse.'))

names=['native7-improve-single-draft-001.patch','native7-improve-single-draft-001-notes.json','native7-improve-single-draft-001-pre-review.patch','native7-improve-single-draft-001-notes-pre-review.json',
    'native7-improve-child-context-draft-001.patch','native7-improve-child-context-draft-001-notes.json']
packet,files=retain('native7-improve-integration-drafts-001',[ROOT/'.runs'/name for name in names])
save(packet,dict(schema=1,kind='unapplied-native7-Improve-integration-prerequisite-drafts-v1',source_head='6ec7ad2344ed060d5e0971965ef05bd9de68925d',
    project_complete=False,production_modified=False,admission_ready=False,Native_executed=False,tests_run=False,files=files,
    status='Partial unapplied drafts, AST-only. Selection replay prerequisite has7 constructed tests; private child-context seam has8. Parent/Preview/export admission remains closed; standalone tuned Route still refuses.',
    review='Lead caught unused guard_key in first selection draft; original preserved, corrected dispatch and focused guard regression authored but not executed. No partial permissive admission integrated.',
    next='Review/test the three-file child-context seam and selection replay, then integrate exact source-derived parent/producer/cache/export/final-root PRL lineage with current native positive/invalid/reserve/stale/cancel/full/install/GUI qualification. No old native or GUI proof transfers to changed production code.'))
print(json.dumps(dict(packets=3,Native_executed=False,raw_backup=False)))
