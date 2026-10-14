"""Stored installation/workflow readback in actual installed Python/root context."""
import time
START=time.monotonic()
from pathlib import Path
import sys
sys.dont_write_bytecode=True
SOURCE=Path(__file__).resolve().parents[2]
CLONE=SOURCE/'.runs/installation-019/checkout'
assert Path(sys.prefix)==CLONE/'.venv'
import ast,copy,hashlib,json,re,subprocess,traceback,xml.etree.ElementTree as ET
from unittest.mock import patch
from autorouter import pipeline as p,config as c,floor_route as f,placement_clearance as pc,sexpr as sx,handoff as h,review_export as e,review_view as v
from scripts import install_smoke as install,fetch_led_demo as demo
assert c.ROOT==CLONE and Path(p.__file__).resolve()==CLONE/'autorouter/pipeline.py'
D=Path(__file__).resolve().parent;I=SOURCE/'.runs/installation-019';W=SOURCE/'.runs/installation-019-review-export'
def no_process(*a,**k):raise AssertionError('readback forbids subprocess/native/JVM/Git/HTTP')
def witness(root):return pc.inventory(root,max_bytes=256*1024**2,max_files=12000,max_entries=24000,with_directories=True)
def hashed(value):return hashlib.sha256(f.canonical(value).encode()).hexdigest()
def warnings(native):return hashed([x for x in native['findings']if x['severity']=='warning'])
def counts(native):return {k:native[k]for k in ('opens','blocking','warnings','exclusions')}
def native_argv(action,board,out,*extra):return [str(c.PYTHON),str(c.ROOT/'autorouter/native.py'),action,str(board),str(out),*[str(x)for x in extra]]
def stage_material(folder,data,before_refill,source_hashes,parity):
    candidate=Path(data['candidate']);expected=dict(source_hashes);expected[candidate.name]=hashlib.sha256((sx.dump(before_refill)+'\n').encode()).hexdigest()
    refill=folder/'refill'/candidate.name
    f.check_drc_stage(folder,data,'refill-drc',refill,refill,True,expected,sandboxed=False)
    assert(sx.dump(p.transplant_fill(before_refill,sx.read(refill)))+'\n').encode()==candidate.read_bytes()
    expected[candidate.name]=data['candidate_sha256']
    native=f.check_drc_stage(folder,data,'final-drc',candidate,folder/'final-drc-input'/candidate.name,False,expected,schematic_parity=parity,sandboxed=False)
    assert native==data['native']and p.sha(folder/'final-drc.json')==data['native_report_sha256']
    return native

def run():
    installed=f.read_json(I/'result.json');workflow=f.read_json(W/'result.json');head=installed['git_head']
    assert installed['passed']is True and installed['status']=='passed'and workflow['controls_passed']is True and workflow['status']=='completed'and workflow['accepted']is False
    assert installed['source_installation_mode']=='distribution'and installed['installed_tracked_files']==479 and installed['complete_source_tracked_files']==19345
    original=f.read_json(I/'source-tracked.json');listing='\0'.join(original)+'\0';selected=install.distribution_listing(listing)
    installed_files={n:original[n]for n in selected.split('\0')if n}
    assert len(installed_files)==479 and install.tracked_inventory(SOURCE,listing)==original and install.tracked_inventory(CLONE,selected)==installed_files
    assert p.sha(I/'source-tracked.json')==installed['source_inventory_sha256']
    identities={str(root):install.git_identity(root,head,branch)for root,branch in [(SOURCE,installed['source_branch']),(CLONE,None)]}
    assert identities==installed['git_identity_witnesses']
    # Execute unchanged actual tool_manifest body; only the forbidden Git child
    # HEAD observation is replaced by the exact detached-HEAD filesystem witness.
    tree=ast.parse((CLONE/'autorouter/pipeline.py').read_text());fn=copy.deepcopy(next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='tool_manifest'))
    replacement_count=0
    for node in fn.body:
        if isinstance(node,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='git_head'for x in node.targets):node.value=ast.Name(id='_review_bound_detached_head',ctx=ast.Load());replacement_count+=1
    assert replacement_count==1
    space=dict(vars(p));space['_review_bound_detached_head']=head
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(CLONE/'autorouter/pipeline.py')+' [only Git HEAD observation substituted]','exec'),space)
    observed_tools=space['tool_manifest']()
    smoke_path=Path(installed['native_receipt']['path']);smoke=f.read_json(smoke_path);assert p.sha(smoke_path)==installed['native_receipt']['sha256']
    p.check_result(smoke_path);assert counts(smoke['native'])=={'opens':0,'blocking':0,'warnings':0,'exclusions':0}and smoke['metrics']['track_length_mm']==60.0 and smoke['metrics']['vias']==0
    assert smoke['tools']==observed_tools
    journals=[]
    for rec,label in [(installed,'installation'),(workflow,'workflow')]:
        for item in rec['commands']:
            process=item['process']if'process'in item else item;log=Path(process['log'])
            assert process['status']=='success'and process['exit_code']==0 and process['cleanup_complete']is True and process['log_truncated']is False
            assert log.stat().st_size==process['log_bytes']and p.sha(log)==item['log_sha256']
            journals.append({'scope':label,'name':item['name'],'log_sha256':p.sha(log),'process_cpu_seconds':process['cpu_seconds'],'process_wall_seconds':process['wall_seconds']})
    assert len(installed['commands'])==22 and[item['name']for item in workflow['commands']]==['preview','route','check-route','review-copy','accept-intent','export','check','reject-intent']
    test_step=next(x for x in installed['commands']if x['name']=='tests');test_log=Path(test_step['log']).read_text();match=re.search(r'Ran (\d+) tests in ([0-9.]+)s\s+OK\s*$',test_log);assert match and int(match[1])==65
    packet=CLONE/'.data/arcdice-demo-001';raw=demo.verify_project(packet/'project',profile_id='arcdice');native_packet=demo.verify_project(packet/'native-project',profile_id='arcdice',native_packet=True)
    assert raw['file_count']==5 and native_packet['file_count']==7
    fetch=f.read_json(packet/'result.json');assert fetch['status']=='acquired_unqualified'and fetch['source_files_exact']is True and fetch['native_accepted']is False and fetch['new_network_requests']==5 and fetch['received_bytes']==595341
    for request,row in zip(fetch['requests'],demo.fixed_profile('arcdice')['rows']):assert request['http_status']==200 and request['url']==row['raw_url']==request['final_url']and request['response_sha256']==row['sha256']and request['received_bytes']==row['bytes']
    source=packet/'native-project/hardware/ArcDice.kicad_pcb';receipt=CLONE/'.runs/install-arcdice-route-019/result.json';report=f.read_json(receipt)
    review_path=CLONE/'.runs/install-review-export-019/review.json';review=f.read_json(review_path);intent=CLONE/'.runs/install-intent-019/choice.json';reject=CLONE/'.runs/install-reject-019/choice.json';rejection=f.read_json(reject)
    export_path=CLONE/'.runs/install-export-019/export.json';proof=f.read_json(export_path)
    roots=(packet,smoke_path.parent,receipt.parent,review_path.parent,intent.parent,reject.parent,export_path.parent,W)
    inputs={str(x.relative_to(SOURCE)):witness(x)for x in roots}
    assert p.sha(export_path)==workflow['export_proof_sha256']and proof['tools']==observed_tools
    with patch.object(p,'tool_manifest',space['tool_manifest']):export_checked=e._check_export(export_path,lambda:None)
    p.check_result(receipt);binding,bound_report=e.bind(intent);assert bound_report==report and binding==proof['inputs']
    assert counts(report['native'])=={'opens':0,'blocking':0,'warnings':26,'exclusions':0}and report['schematic_parity']=='checked by final native DRC'and proof['schematic_parity']==report['schematic_parity']
    assert counts(proof['native'])==counts(report['native'])and warnings(proof['native'])==warnings(report['native'])and proof['metrics']==report['metrics']==workflow['metrics']
    assert report['metrics']['track_length_mm']==636.9890979739067 and report['metrics']['vias']==0 and proof['whole_project_drc_clean']is False
    original_tree=p.preflight(source);task=copy.deepcopy(original_tree);task[:]=[n for n in task if not isinstance(n,list)or not n or n[0]not in p.ROUTES or p.locked(n)]
    for z in sx.children(task,'zone'):z[:]=[n for n in z if not isinstance(n,list)or not n or n[0]not in p.DERIVED_ZONE]
    protected=p.protected_for_record(report,original_tree);assert not protected
    folder=receipt.parent;candidate=Path(report['candidate'])
    before=p.transplant_routes(task,sx.read(folder/'imported.kicad_pcb'),protected=protected,policy='exact_non_uuid_lock_position_v2');stage_material(folder,report,before,report['source_hashes'],True)
    assert f.check_drc_stage(folder,report,'source-drc',folder/'snapshot'/source.name,folder/'source-drc-input'/source.name,False,report['source_hashes'],sandboxed=False)==report['source_drc']
    for name,action,out,extra in [('export','export',folder/'task.dsn',(folder/'export-netclasses.json',)),('obstacles','obstacles',folder/'obstacles.json',()),('import','import',folder/'imported.kicad_pcb',(folder/'routes.ses',)),('metrics','metrics',folder/'metrics.json',()),('final-netclasses','netclasses',folder/'final-netclasses.json',())]:f.process_check(folder,report,name,native_argv(action,candidate,out,*extra))
    f.process_check(folder,report,'engine',p.engine_argv(folder,report['engine_budget']['argv']));classes=p.audit_candidate_netclasses(candidate,protected,f.read_json(folder/'final-netclasses.json'))
    plots=[];preview=review['preview'];assert preview['layers']==['F.Cu','B.Cu']and preview['native_validation_performed']is False
    for step in preview['steps']:
        name=step['name'];label,layer=name.split('-',1);board=source if label=='before'else candidate;work=review_path.parent/'plot-work'/(name+'-input');target=review_path.parent/'plot-work/native-plots'/(name+'.svg')
        expected=[*f.SANDBOX,str(c.CLI),'pcb','export','svg','--mode-single','--layers',layer+',Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','--output',str(target),str(work/source.name)]
        f.process_check(review_path.parent/'plot-work',{'steps':preview['steps']},name,expected)
        b=f.read_json(review_path.parent/'plot-work'/(name+'-input-binding.json'));before_hash=p.tree_hash(board.parent);assert b['source']==str(board)and b['before']==before_hash and b['input']==str(work/source.name)
        p.check_drc_project(b['before'],b['after'],source.name);assert p.tree_hash(work)==b['after']
        raw_svg=v.svg_bytes(target);display=review_path.parent/'plot-work/plots'/target.name;assert display.read_bytes()==v.display_svg(raw_svg)
        assert ET.fromstring(v.display_svg(raw_svg)).find('.//{http://www.w3.org/2000/svg}path')is not None
        plots.append({'name':name,'raw_sha256':p.sha(target),'display_sha256':p.sha(display),'bound_input_board_sha256':before_hash[source.name],'native_process_bound':True})
    assert len(plots)==4 and all(p.sha(review_path.parent/name)==digest for name,digest in preview['files'].items())
    assert rejection['choice']=='reject'and rejection['choice_recorded']is True and rejection['routing_accepted']is False and rejection['applied']is False and rejection['native_validation_performed']is False
    assert rejection['review_sha256']==p.sha(review_path)and rejection['receipt_sha256']==p.sha(receipt)and rejection['saved_native_findings']==report['native']
    assert rejection['original_source_hashes']==report['source_hashes']and h.evidence_witness(receipt.parent)==rejection['routing_evidence_hashes']
    executions={}
    for name in ('installation-019-execution','installation-019-arcdice-fetch-execution','installation-019-workflow-execution'):
        ext=f.read_json(SOURCE/'.runs'/name/'execution.json');process=ext['process'];assert process['status']=='success'and process['exit_code']==0 and process['cleanup_complete']is True and process['log_truncated']is False
        assert p.sha(Path(process['log']))==ext['log_sha256'];executions[name]={k:ext[k]for k in ('wall_seconds','full_cpu_seconds','charged_wall_seconds','lifetime_full_cpu_seconds')if k in ext}
    assert install.tracked_inventory(SOURCE,listing)==original and install.tracked_inventory(CLONE,selected)==installed_files
    assert {str(x.relative_to(SOURCE)):witness(x)for x in roots}==inputs
    assert {str(root):install.git_identity(root,head,branch)for root,branch in [(SOURCE,installed['source_branch']),(CLONE,None)]}==identities
    assert demo.verify_project(packet/'project',profile_id='arcdice')==raw and demo.verify_project(packet/'native-project',profile_id='arcdice',native_packet=True)==native_packet
    return dict(status='passed',same_installed_python=str(Path(sys.executable)),same_module_root=str(c.ROOT),tool_manifest_scope='Exact installed function body and actual native/code hashing; only forbidden Git HEAD subprocess replaced by verified detached-HEAD filesystem witness. No Native/Solver mock.',head=head,installation_commands=22,installed_test_count=65,installed_test_seconds=float(match[2]),installed_test_scope=installed['installed_test_scope'],source_complete_files=19345,installed_distribution_files=479,source_inventory_sha256=p.sha(I/'source-tracked.json'),source_and_installed_tracked_unchanged=True,raw_source_files=5,native_packet_files=7,source_packet_exact=True,actual_source_gets=5,actual_source_bytes=595341,smoke_native=counts(smoke['native']),smoke_metrics=smoke['metrics'],smoke_receipt_sha256=p.sha(smoke_path),workflow_commands=8,workflow_route_native=counts(report['native']),workflow_export_native=counts(proof['native']),full_warning_signature_sha256=warnings(report['native']),workflow_metrics=report['metrics'],class_dimensions=classes['route_dimensions'],source_protected_routes=len(protected),plots=plots,export_proof_sha256=p.sha(export_path),export_current=export_checked['current'],export_candidate_sha256=proof['candidate_sha256'],export_native_report_sha256=proof['native_report_sha256'],accept_intent_only=True,rejection_recorded=True,no_live_apply=True,no_human_approval=True,no_physical_electrical_battery_qualification=True,new_native_execution=False,new_gets=False,new_suite_execution=False,new_git_processes=False,executions=executions,journal_hashes=journals,input_inventory_sha256=hashed(inputs),input_evidence_unchanged=True,thin_workflow_tail_publication_limit='Actual completed successful019 metadata is bound to stored controllerSHA. Source review identifies final save/tracked checks outside try; late error can leave positive controls metadata; fix/regression belongs future controller and requires no native repeat.',workflow_controller_sha256=workflow['controller_sha256'],installation_receipt_sha256=p.sha(I/'result.json'),workflow_receipt_sha256=p.sha(W/'result.json'),claim_scope='Fresh local distribution/venv with installed65test subset and genuine native smoke+Arc workflow; separate from completed comparative experiments and leadfull981 suite. Not freshOS/fullinstalledsuite/physicalGUI qualification.')
try:
    with patch.object(subprocess,'run',no_process),patch.object(subprocess,'Popen',no_process):record=run()
except BaseException as exc:record={'status':'failed','error':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc(),'new_native_execution':False}
record.update(review_wall_seconds=time.monotonic()-START,review_lifetime_self_cpu_seconds=time.process_time(),review_children=0)
(D/('actual-readback.json'if record['status']=='passed'else'audit-failure-001.json')).write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:record.get(k)for k in ('status','error','message','review_wall_seconds','review_lifetime_self_cpu_seconds')}))
raise SystemExit(0 if record['status']=='passed'else 1)
