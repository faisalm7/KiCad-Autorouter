"""Offline independent audit of failed LiPo native diagnostic001. Never launches native tools."""
from pathlib import Path
from collections import Counter
import hashlib, json, math, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RUN=ROOT/'.runs/lipo-native-diagnostic-001'
SOURCE=ROOT/'.data/expansion003/lipo-disconnector'
RECEIPT=ROOT/'.runs/licensed-acquisition-003/lipo-disconnector-001/receipt.json'
HEAD='7ecc1b3004831aea614fbc8c7d42babd1571bdbd'
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, sexpr as sx, floor_route as f, placement_clearance as io
checks=[]
def ck(value,name):
    checks.append({'check':name,'passed':bool(value)})
    if not value:raise AssertionError(name)
def raw(path,limit=20*1024*1024):return io.read_bytes(path,limit)
def sha(path):return hashlib.sha256(raw(path,128*1024*1024)).hexdigest()
def read(path):return f.read_json(path)
def inventory(path):return io.inventory(path,max_bytes=20*1024*1024,max_files=512,max_entries=1024)
def git(*args):
    return subprocess.run(['git','-c','core.hooksPath=/dev/null',*args],cwd=ROOT,check=True,capture_output=True,timeout=3).stdout
def main():
    if (HERE/'audit.json').exists():raise ValueError('refuse output collision')
    started=time.monotonic();before=inventory(RUN);source_before=inventory(SOURCE)
    d=read(RUN/'summary.json');s=read(RUN/'observe-process.json');r=read(RECEIPT)
    ck(d['schema']==1 and d['status']=='failed' and d['error']=='Rejected: observe: nonzero_exit','honest first-stage native failure')
    for key in ['observations_complete','routing_accepted','dependency_complete','format_support_qualified','semantic_migration_performed','board_saved','new_engine_execution']:
        ck(d[key] is False,key+' remains false')
    ck(d['native_executed'] is True and d['steps']==[s] and s['name']=='observe','exactly one native stage attempted')
    absent=['observation.json','native.dsn','original-drc.json','original-drc-input','original-drc-process.json','original-drc-binding.json']
    ck(all(not (RUN/name).exists() for name in absent),'no raw observation/DSN or later DRC artifacts exist')
    ck(not any(key in d for key in ['native','native_effective_floors_nm','native_effective_nets','native_original_pad_route_identities_match','stage_one_evidence','stage_two_evidence','completed_evidence','settings_observation']),'no unobserved native result invented')
    ck(sha(RECEIPT)==d['acquisition_receipt_sha256']=='b57bc2ce29d7c5e45939fbf917896d02536b357e8b5a08c04828dd8305107c27','original acquisition receipt exact')
    ck(r['status']=='acquired_unqualified' and r['project']=='lipo-disconnector' and r['split']=='development','acquisition remains development unqualified')
    expected={};total=0
    for row in r['files']:
        path=ROOT/row['local_path'];ck(path.is_relative_to(SOURCE),'acquired path scoped '+path.name)
        payload=raw(path);relative=str(path.relative_to(SOURCE));ck(relative not in expected,'unique acquired path '+relative)
        ck(len(payload)==row['bytes'] and sha(path)==row['sha256'] and hashlib.sha1(b'blob '+str(len(payload)).encode()+b'\0'+payload).hexdigest()==row['git_blob_sha1'],'original SHA/size/Git blob '+relative)
        expected[relative]=row['sha256'];total+=len(payload)
    ck(len(expected)==26 and total==4194990 and expected==source_before==d['source_hashes']==inventory(RUN/'observe-input'),'all 26 files complete and original copy unchanged')
    ck(d['source_file_count']==26 and d['source_bytes']==4194990 and d['planned_project_copy_bytes']==8389980,'planned versus actual project copies distinguished')
    board=SOURCE/'lipo_disconnector.kicad_pcb';project=read(board.with_suffix('.kicad_pro'));tree=sx.read(board)
    ck(sha(board)=='3ef2141230ce971115381107486892bdf06a724c5d31d9ef2103622e113cf4e0' and sha(board.with_suffix('.kicad_pro'))=='8bc2dc577fb98404f317730b10ba2945f213a14e212b7a0b3e7fba7943a8d95e','exact original board/project')
    ck(sx.one(tree,'version')==['version','20220621'],'original legacy version unchanged')
    try:p.preflight(board)
    except p.Rejected as exc:gate=str(exc)
    else:raise AssertionError('original unexpectedly admitted')
    ck(gate==d['production_gate_rejection']=='unsupported: unqualified board format version','actual production format gate still rejects')
    notes=d['source_notes'];netnames={int(n[1]):sx.unquote(n[2]) for n in sx.children(tree,'net')};pads=[];footprints=[]
    for fp in sx.children(tree,'footprint'):
        references=[sx.unquote(n[2]) for n in sx.children(fp,'fp_text') if n[1]=='reference'];ck(len(references)==1,'single original reference')
        footprint={'reference':references[0],'uuid':sx.unquote(sx.one(fp,'tstamp')[1]),'pad_count':len(sx.children(fp,'pad'))};footprints.append(footprint)
        for pad in sx.children(fp,'pad'):
            net=sx.one(pad,'net');pads.append({'uuid':sx.unquote(sx.one(pad,'tstamp')[1]),'reference':references[0],'number':sx.unquote(pad[1]),'net':netnames.get(int(net[1]) if net else 0,'')})
    ck(pads==notes['source_pads_identity'] and len(pads)==10,'static ten terminal identities exact, not native observation')
    ck(sorted(n for n in netnames.values() if n)==notes['source_nonempty_nets'],'static original three nonempty nets exact')
    route_ids=sorted(sx.unquote(sx.one(route,'tstamp')[1]) for route in p.routes(tree));ck(route_ids==notes['source_route_ids'] and len(route_ids)==8,'static original eight route IDs exact')
    zones=[[x for x in z if not isinstance(x,list) or not x or x[0] not in p.DERIVED_ZONE] for z in sx.children(tree,'zone')]
    ck(zones==notes['source_zone_intent_ast'] and len(zones)==3,'static original three zone intentions exact, native reinterpretation unobserved')
    ck(notes['source_design_settings']==project['board']['design_settings'] and notes['source_net_settings']==project['net_settings'] and notes['source_meta']==project['meta'],'static source settings and misleading metadata preserved exactly')
    ck(d['tools']['git_head']==HEAD and git('rev-parse','HEAD').decode().strip()==HEAD,'frozen current HEAD exact')
    ck(d['runtime_sources']==d['code_inventory']==inventory(RUN/'code'),'complete copied runtime source inventory')
    ck(set(d['runtime_sources'])==set(d['tools']['implementation_sha256'])|{'toolchain.lock.json','experiments/lipo_native_diagnostic_v1/driver.py','experiments/lipo_native_diagnostic_v1/test_driver.py'},'exact helper/core/lock population')
    for name,digest in d['runtime_sources'].items():
        ck(sha(ROOT/name)==sha(RUN/'code'/name)==digest and hashlib.sha256(git('show',HEAD+':'+name)).hexdigest()==digest,'exact committed and runtime source '+name)
    for path,digest in d['tools']['files'].items():ck(sha(Path(path))==digest,'actual pinned tool '+Path(path).name)
    expected_argv=f.context_argv('export',RUN/'observe-input'/board.name,RUN/'observation.json',RUN/'native.dsn')
    ck(s['argv']==expected_argv and s['cwd']==str(RUN),'only exact nonsaving same-load export argv with OS network denial')
    ck(s['status']=='nonzero_exit' and s['exit_code']==1 and s['cleanup_complete'] is True and s['log_truncated'] is False,'native failure/cleanup/untruncated log preserved')
    log=raw(RUN/'observe.log').decode();ck(s['log']==str(RUN/'observe.log') and s['log_bytes']==len(log.encode())==868,'raw failed log bound and retained')
    ck(log.count('PCB_VIA::GetWidth called without a layer argument')==2 and 'ValueError: DSN export failed' in log and 'ExportSpecctraDSN(native,str(dsn))' in log,'actual warnings and export traceback distinguished')
    ck(s['resource_guards']['max_group_rss_bytes']==2*1024**3 and s['resource_guards']['max_workdir_bytes']==20*1024**2,'unchanged bounded native resource guards')
    for key in ['wall_seconds','cpu_seconds','supervisor_cpu_seconds','monitor_cpu_seconds']:ck(type(s[key]) in (int,float) and math.isfinite(s[key]) and s[key]>=0,'finite process '+key)
    ck(d['budget_seconds']==d['cpu_budget_seconds']==30 and d['within_budget'] is True and 0<d['wall_seconds']<30 and 0<d['total_cpu_seconds']<30,'failed diagnostic stayed within sampled whole-run wall/CPU budgets')
    ck(d['child_step_cpu_seconds']==s['cpu_seconds'] and d['monitor_cpu_seconds']==s['monitor_cpu_seconds'] and d['total_cpu_seconds']>=s['cpu_seconds'],'CPU aggregate retains failed native step without false completion')
    ck(d['output_ceiling_bytes']==20*1024**2 and sum((RUN/name).stat().st_size for name in before)<20*1024**2,'complete failed output below 20 MiB')
    source_receipt=ROOT/'.runs/placement-area-export-review-001/source-receipt.json';primary=read(source_receipt);key='pcbnew/specctra_import_export/specctra_export.cpp';src=ROOT/'.runs/placement-area-export-review-001/source'/key;row=next(x for x in primary['files'] if x['path']==key)
    ck(primary['commit']=='0feeca2a807f428ad2b3fa7c1e39625cb769f02c' and sha(src)==row['sha256'],'cached pinned KiCad exporter source binding')
    duplicates={k:v for k,v in Counter(fp['reference'] for fp in footprints).items() if v>1};ck(duplicates=={'kibuzzard-62E1C2B7':4} and all(fp['pad_count']==0 for fp in footprints if fp['reference'] in duplicates),'exact four duplicate padless references: static export blocker hypothesis')
    ck(inventory(RUN)==before and inventory(SOURCE)==source_before and sha(RECEIPT)==d['acquisition_receipt_sha256'],'full original/run/acquisition unchanged throughout audit')
    ck(git('rev-parse','HEAD').decode().strip()==HEAD and all(sha(ROOT/name)==digest for name,digest in d['runtime_sources'].items()),'final HEAD and helper/core material unchanged')
    result={'schema':1,'audit_passed':True,'actual_diagnostic_status':d['status'],'observations_complete':False,'source_and_run_unchanged':True,'checks':checks,'run':str(RUN),'summary_sha256':sha(RUN/'summary.json'),'process_sha256':sha(RUN/'observe-process.json'),'log_sha256':sha(RUN/'observe.log'),'git_head':HEAD,'source_files':26,'source_bytes':total,'source_inventory':source_before,'retained_run_files':len(before),'retained_run_bytes':sum((RUN/name).stat().st_size for name in before),'native_stages_attempted':['observe'],'unattempted':['original-drc'],'absent_native_outputs':absent,'static_footprints':footprints,'native_settings_and_identities_qualified':False,'duplicate_reference_hypothesis':{'static_duplicates':duplicates,'pinned_primary_commit':primary['commit'],'source_sha256':sha(src),'source_url':row['url'],'lines':'1074–1095','interpretation':'All-footprint duplicate-reference guard would reject the original if native references are preserved; raw diagnostic emits only Boolean failure, so actual error cause/native reference census is not proven.'},'stored_wall_seconds':d['wall_seconds'],'stored_total_cpu_seconds':d['total_cpu_seconds'],'native_process_wall_seconds':s['wall_seconds'],'native_process_cpu_seconds':s['cpu_seconds'],'accounting_limit':'Stored totals precede final publication checks. No independent outer elapsed or post-final CPU invented. This was already a failed diagnostic, not accepted native evidence.','audit_wall_seconds':time.monotonic()-started,'reviewer_native_jobs':0,'reviewer_engine_jobs':0}
    (HERE/'run-inventory.json').write_text(json.dumps(before,indent=2,sort_keys=True)+'\n');(HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['audit_passed','actual_diagnostic_status','source_and_run_unchanged','retained_run_files','retained_run_bytes','native_stages_attempted','stored_wall_seconds','stored_total_cpu_seconds','audit_wall_seconds']},indent=2))
if __name__=='__main__':main()
