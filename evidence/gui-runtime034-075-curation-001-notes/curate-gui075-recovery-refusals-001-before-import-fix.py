"""Retain existing075 refusal controls using the shared bounded copier."""
from pathlib import Path
import ast, datetime, json, sys
ROOT=Path(__file__).resolve().parents[1]
runtime=ROOT/'.runs/runtime-directory-034/runtime'
sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io,local_settings as local
base=runtime/'.runs/gui-session075'
notes=ROOT/'evidence/gui-runtime034-075-recovery-refusals-001-notes'
packet=ROOT/'evidence/gui-runtime034-075-recovery-refusals-001.json'
assert not notes.exists() and not packet.exists()
refs,files,material,total={},[],[],0
prior=f.read_json(ROOT/'evidence/runtime034-ordinary-install-001.json')
idx=ROOT/prior['files_index']['path'];assert p.sha(idx)==prior['files_index']['sha256']
for row in f.read_json(idx)['files']+f.read_json(idx)['material']:
    refs.setdefault(row['sha256'],row.get('path',row.get('retained')))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
nodes=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree','cost')]
assert len(nodes)==3
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper),'exec'))
prepared=f.read_json(base/'prepared-state.json');tools=p.tool_manifest()
assert tools==prepared['tools'] and tools['git_head']=='d64e5f1c9e35552eb2eeca93c71c5683fd09c37c'
assert p.sha(runtime/'runtime-distribution.json')==prepared['runtime_manifest_sha256']=='65aa2eb27ac5c61ce96a771bb6d8a65f923220e464886fb43d789377e4c61d5b'
rows=[]
for index in ('001','002'):
    admin=ROOT/'.runs'/('gui075-direct-four-copper-'+index)
    plan=f.read_json(admin/'protocol.json');out=Path(plan['output'])
    result=f.read_json(out/'result.json');enclosed=f.read_json(admin/'enclosure/result.json')
    assert result['accepted'] is False and result['actual_GUI'] is False
    assert enclosed['child_sha256']==p.sha(out/'result.json') and enclosed['protocol_sha256']==p.sha(admin/'protocol.json')
    assert enclosed['process']['cleanup_complete'] is True and enclosed['process']['log_truncated'] is False
    assert result['source_hashes']==p.tree_hash(Path(result['source']).parent)
    assert result['tools']==tools and result['runtime_manifest_sha256']==prepared['runtime_manifest_sha256']
    assert f.evidence_inventory(out)==result['evidence_sha256']==enclosed['completed_evidence']
    if index=='001':
        assert result['control_passed'] is False and result['error']=='Rejected: original project/rules/schematic/PRL bytes changed'
        assert enclosed['passed'] is False
    else:
        assert result['control_passed'] is True and enclosed['passed'] is True
        assert result['copied_project_rules_schematic_PRL_unchanged'] is True
        assert result['refusal']=='Experimental thermal recovery supports two source copper layers only; no layers were changed.'
        assert p.tree_hash(Path(result['fixture']).parent)==result['fixture_hashes']
        assert p.tree_hash(Path(result['authoring_project']))==result['authoring_after_hashes']
        native=result['source_native_diagnostic'];fixture=Path(result['fixture']);validation=out/'validation'
        assert [native[k] for k in ('opens','blocking','warnings','exclusions')]==[2,0,1,0]
        assert f.check_drc_stage(validation,result,'fixture-full-drc',fixture,
            validation/'fixture-full-drc-input'/fixture.name,False,result['fixture_hashes'],schematic_parity=True,sandboxed=False)==native
        final_packet=(validation,dict(steps=result['steps'],native=native))
    tree(admin,Path('controls')/index/'enclosure')
    tree(out,Path('controls')/index/'raw')
    for suffix in ('-controller.log','-time.log'):
        path=ROOT/'.runs'/('gui075-direct-four-copper-'+index+suffix);retain(path,Path('controllers-logs')/path.name)
    controller=ROOT/'.runs'/('qualify-gui075-direct-four-copper-'+index+'.py')
    assert p.sha(controller)==plan['controller_sha256'];retain(controller,Path('controllers-logs')/controller.name)
    rows.append(dict(control=index,passed=enclosed['passed'],receipt_sha256=p.sha(out/'result.json'),
        complete_cost=cost(ROOT/'.runs'/('gui075-direct-four-copper-'+index+'-time.log')),error=result.get('error'),
        scope='Native source authoring/static Request only; actual GUI refusal is a separate observation.'))
refusals=f.read_json(base/'recovery-controls-001/no-workspace-refusals-001.json')
direct=f.read_json(base/'recovery-controls-001/direct-layer-GUI-refusal-002.json')
assert refusals['no_workspace_created'] is True and refusals['layer_guard_directly_observed'] is False
assert direct['no_workspace_created'] is True and direct['actual_GUI_refusal'] is True
assert direct['native_diagnostic_sha256']==p.sha(Path(direct['native_diagnostic_receipt']))
for name in ('no-workspace-refusals-001.json','direct-layer-GUI-refusal-002.json','before-no-workspace-refusals-001.json'):
    retain(base/'recovery-controls-001'/name,Path('observations')/name)
for name in ('061-recovery-partial-settings-selected-AX.txt','062-recovery-incompatible-refused-AX.txt',
    '063-recovery-four-copper-selected-AX.txt','064-recovery-four-copper-refused-AX.txt',
    '073-direct-four-copper-selected-AX.txt','074-direct-four-copper-refused-AX.txt'):
    retain(base/'actual-GUI-observations-001'/name,Path('observations')/name)
retain(Path(__file__),Path('controllers-logs')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='runtime034-GUI075-actual-recovery-preworkspace-refusals',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    project_complete=False,accepted=False,recovery_delivery_qualified=False,actual_GUI_refusals=True,
    source_head=prepared['source_head'],runtime_manifest_sha256=prepared['runtime_manifest_sha256'],controls=rows,
    incompatible_settings_and_flagged_class_refusal=refusals,direct_layer_refusal=direct,
    distinction='First4Cu class-preflight refusal did not reach the layerguard. New unflagged owned synthetic4Cu reached it in static Request and actual GUI. Both refused beforeworkspace. Native source diagnostic2opens/0blocking/1danglingwarning/0exclusions is retained, not source cleanliness or routing success.',
    authoring_failure='001 SaveBoard normalized its new clone PRO/PRL and exact companion preservation failed before DRC/Request.002 retains changed authoring companions separately and builds a new fixture from generated PCB plus pristine original companions. No001 artifact or original source was restored, discarded or weakened.',
    limits='Functional support refusals only. No new routing completion, recovery repair/no-repair/cancel delivery, electrical/human/Windows/restoration or general performance claim. Raw later artifacts remain Mac-only outside008/010.',
    source_rights='Project-owned synthetic geometry/controller GPL; original demo project/settings retain prior CC-BY-SA-4.0 notices/provenance. No engine/app/venv/private/browser capture copied.',
    accounting='Complete external exits include all child work: failed0011.53wall/1.38CPU, corrected0023.02wall/2.39CPU. Authoring/AI review/curation/UI costs are additional, unknown interactive CPU is not zero.',
    files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
assert p.tool_manifest()==tools
for item in material:assert p.sha(ROOT/item['original'])==item['sha256']
local.check_final_events([final_packet],p.c.CLI)
p.save_json(packet,record)
print(json.dumps(dict(files=len(files),bytes=total,actual_GUI_refusals=True,routing_gain=False)))
