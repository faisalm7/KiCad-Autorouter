"""Generate/freeze018 delivery from exact completed017 methods after full154.

Authoring source only until lead execution. No routing, Native board validation,
JVM, build, installation, dependency download or completed-evidence mutation.
"""
from pathlib import Path
import argparse,ast,hashlib,importlib.util,json,os,re,resource,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv,floor_route as f,handoff as h
from autorouter.runner import run
CASE=ROOT/'.runs/runtime-directory-018';RUNTIME=CASE/'runtime'
QUALIFIED='0754615776e38ea34ebc83f5b9a66c458538e1d2'
MAIN_PIN='969ee3f7143dee26a0fa328ebffd0ad355ebcfe74c09c8cd99f48cc778db3f45'
PIPELINE_PIN='bfc3f2388d73df7f5000ff35f86d3d72e4dd380ba52e13acfb0630ed7c2e9400'
SHARED=ROOT/'.runs/named-edge-installed-pair-001/run-installed-arm.py'
SHARED_PIN='c412dc76a66bea20b52a071ce6b0de255047d817f5c432a3dbc7d287dc81e12e'
PRIOR=ROOT/'.runs/runtime-directory-017/production-delivery-protocol-frozen-001.json'
PRIOR_PIN='8cd2e96a439ecf3e3dd78ad6e4d947a86e71ab6ef2eb58c4c07d3cf04e6e1176'
TEMPLATES={'qualify-runtime017-production-001.py':'efbc44db006baff9606dfc4d0e73ee564a2db218f333490f3e3c228ae200b0d9',
           'run-runtime017-production-001.py':'c8474903c6cbfd66b09965474383be8193b4b1156574cd7facdbb3664719a72f'}

def require(value,reason):
    if not value:raise p.Rejected(reason)
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
def write_new(path,raw):
    with path.open('xb')as stream:stream.write(raw)
def strict(raw):
    return json.loads(raw,object_pairs_hook=pv._strict_object,parse_constant=lambda value:(_ for _ in()).throw(ValueError('invalid JSON constant')))

def prepare(full154_pin,setup_pin,manifest_pin):
    started=time.monotonic();cpu0=cpu();self_pin=p.sha(Path(__file__))
    for pin in(full154_pin,setup_pin,manifest_pin):require(type(pin)is str and re.fullmatch('[0-9a-f]{64}',pin),'explicit actual154/setup/manifest SHA256 pins required')
    require(p.sha(PRIOR)==PRIOR_PIN and p.sha(SHARED)==SHARED_PIN,'completed017 protocol/shared helper changed')
    old=f.read_json(PRIOR);full_path=ROOT/'.runs/full-integration-154/execution.json';full=f.read_json(full_path)
    require(p.sha(full_path)==full154_pin and full['process']['status']=='success'and full['process']['exit_code']==0
        and full['process']['cleanup_complete']is True and full['process']['log_truncated']is False
        and p.sha(full_path.parent/'command.log')==full['log_sha256'],'actual completed full154PASS/log required before generation or freeze')
    setup_path=CASE/'setup.json';manifest_path=RUNTIME/pv.MANIFEST
    require(p.sha(setup_path)==setup_pin and p.sha(manifest_path)==manifest_pin,'actual018 setup/manifest pins differ')
    setup=f.read_json(setup_path);manifest=f.read_json(manifest_path)
    require(setup.get('prepared')is True and setup.get('status')=='prepared'and setup['manifest_sha256']==manifest_pin
        and setup['qualified_source_commit']==QUALIFIED and setup['changed_runtime_modules']==['autorouter/__main__.py']
        and setup['unchanged_runtime_modules']==43,'actual qualified018 preparation required')
    require(manifest['build_source']['git_head']==setup['source_head'],'actual018 setup/build source identity differs')
    spec=importlib.util.spec_from_file_location('retained_pair_018_metadata',SHARED);shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
    require(p.sha(SHARED)==SHARED_PIN,'shared helper changed during import')
    current=p.tool_manifest();implementation=current['implementation_sha256'];prior_impl=old['runtime_tools']['implementation_sha256']
    require(len(implementation)==44 and set(implementation)==set(prior_impl)
        and sorted(name for name in implementation if implementation[name]!=prior_impl[name])==['autorouter/__main__.py']
        and implementation['autorouter/__main__.py']==MAIN_PIN and implementation['autorouter/pipeline.py']==PIPELINE_PIN
        and full['tools']['implementation_sha256']==implementation,'exact tested01844module population required')
    require(hashlib.sha256(pv._git(ROOT,'show',QUALIFIED+':autorouter/__main__.py',limit=pv.MAX_FILE_BYTES)).hexdigest()==MAIN_PIN,'qualified doctor source differs')
    selected=('autorouter',*sorted(pv.FIXED_FILES))
    for head in(setup['source_head'],current['git_head']):
        pv._git(ROOT,'merge-base','--is-ancestor',QUALIFIED,head)
        require(not pv._git(ROOT,'diff','--name-only',QUALIFIED,head,'--',*selected),'later checkpoint changed selected018 product bytes')
    for name,digest in manifest['build_source']['files_sha256'].items():require(p.sha(ROOT/name)==p.sha(RUNTIME/name)==digest,'exact installed/root selected product differs: '+name)
    # Match017's controllers byte-for-byte except the case labels/paths. The
    # retained pair hash and every other64hex literal must remain unchanged.
    generated={}
    for name,digest in TEMPLATES.items():
        source=ROOT/'.runs'/name;raw=pv.read_bytes(source);require(hashlib.sha256(raw).hexdigest()==digest,'completed017 controller changed: '+name)
        text=raw.decode();converted=text.replace('017','018')
        require(re.findall(r'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])',text)==re.findall(r'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])',converted),'label substitution changed a64hex literal')
        compile(ast.parse(converted,name),name,'exec');generated[name.replace('017','018')]=converted.encode()
    out=CASE/'delivery-preparation-001';out.mkdir();owner={};h.capture_destination(owner,out)
    child_name='qualify-runtime018-production-001.py';outer_name='run-runtime018-production-001.py'
    for name,raw in generated.items():write_new(ROOT/'.runs'/name,raw)
    write_new(RUNTIME/'.runs'/child_name,generated[child_name])
    metadata=out/'metadata';metadata.mkdir();processes=[]
    coordinator_python=shared.coordinator_python_context();installed_file=shared.python_file_context(RUNTIME/'.venv/bin/python')
    require(coordinator_python['version'][:2]==[3,11]and coordinator_python['implementation']=='cpython'
        and installed_file['sha256']==coordinator_python['sha256'],'exact actual regular root/installed Python3.11 bytes required')
    env={key:value for key,value in os.environ.items()if key not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}}
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
    observations={}
    for label,python,source in [('coordinator',coordinator_python['path'],ROOT),('runtime',str(RUNTIME/'.venv/bin/python'),RUNTIME)]:
        query=("import sys,json,importlib.util;sys.dont_write_bytecode=True;sys.path.insert(0,"+repr(str(source))+");"
            "from autorouter import pipeline as p;spec=importlib.util.spec_from_file_location('retained_pair_metadata',"+repr(str(SHARED))+");"
            "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
            "print(json.dumps(dict(tools=p.tool_manifest(),python=m.coordinator_python_context()),sort_keys=True))")
        log=metadata/(label+'.json');proc=run([*f.SANDBOX,python,'-B','-c',query],cwd=metadata,log=log,timeout=30,
            max_log_bytes=256*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=1024**3,env=env)
        processes.append(proc);p.save_json(metadata/(label+'-process.json'),proc)
        require(proc['status']=='success'and proc['exit_code']==0 and proc['cleanup_complete']is True and not proc['log_truncated'],'bounded actual metadata query failed: '+label)
        observations[label]=strict(pv.read_bytes(log,256*1024))
    root_observed=observations['coordinator'];runtime_observed=observations['runtime']
    require(root_observed['tools']==current and root_observed['python']==coordinator_python,'observed root tools/Python changed')
    runtime_python=runtime_observed['python'];runtime_tools=runtime_observed['tools']
    require({key:runtime_python[key]for key in('path','resolved_path','sha256','bytes')}==installed_file
        and runtime_python['version']==coordinator_python['version']and runtime_python['implementation']==coordinator_python['implementation'],'observed installed Python3.11 differs')
    require({key:value for key,value in shared.selected_tools(current).items()if key!='files'}==
        {key:value for key,value in shared.selected_tools(runtime_tools).items()if key!='files'}
        and sorted(current['files'].values())==sorted(runtime_tools['files'].values())
        and runtime_tools['source_provenance']['manifest_sha256']==manifest_pin,'observed root/installed44module/version/network/policy/tool bytes differ')
    plan=json.loads(json.dumps(old));plan.update(kind='runtime018-four-cu-production-protocol-v1',runtime=str(RUNTIME),source_head=setup['source_head'],qualified_source_commit=QUALIFIED,
        runtime_manifest_sha256=manifest_pin,runtime_tools=runtime_tools,runtime_python=runtime_python,coordinator_tools=current,coordinator_python=coordinator_python,
        installed_child_name=child_name,child_sha256=hashlib.sha256(generated[child_name]).hexdigest(),outer_controller_sha256=hashlib.sha256(generated[outer_name]).hexdigest(),
        scope='Fresh018 six-stage installed4Cu CLI delivery qualification after doctor readiness fix only; exact017 methods/owned fixture/settings/Native warning/ignored/class/protected/original acceptance and260s whole envelope.43othermodules unchanged. No negative017 rerun, newfamily, routing-quality/GUI/human/physical approval or release claim.',
        source_review={'inherited017_methods_only':old.get('source_review'),'new_source_review':'Lead/skeptic review required before execution; no new review fabricated.'},
        metadata_reuse='All fixture/settings/warning/ignored/limits/CRITICALskip values are exact017 values.018root/runtime/Python metadata were freshly observed with bounded shared runner in this small preparation directory.',
        execution_gate='Actual full154PASS and018setup/manifest were mandatory before this freeze. Lead checkpoint/readback and source review remain required before one sequential fresh six-stage execution.',
        future_lead_command=[coordinator_python['path'],'-B',str(ROOT/'.runs'/outer_name),'--protocol',str(CASE/'production-delivery-protocol-frozen-001.json'),'--protocol-sha256','<actual-frozen-sha256>'])
    extra=[PRIOR,SHARED,Path(__file__),full_path,full_path.parent/'command.log',setup_path,manifest_path,*[metadata/(label+suffix)for label in('coordinator','runtime')for suffix in('.json','-process.json')]]
    plan['prerequisite_sha256'].update({str(path):p.sha(path)for path in extra})
    require(plan['status']=='frozen'and all(plan[key]==old[key]for key in('fixture_files','fixture_sha256','board_name','settings','expected_warning_rows','expected_ignored_checks','limits','expected_native_edge_observation','required_receipt_policy')),'original017 acceptance/input values changed')
    for name,row in setup['sources'].items():
        require(p.tree_hash(Path(row['board']).parent)==row['source_hashes'],'reused018 fixture changed: '+name)
    require(p.sha(Path(__file__))==self_pin and p.sha(PRIOR)==PRIOR_PIN and p.sha(SHARED)==SHARED_PIN
        and p.sha(full_path)==full154_pin and p.sha(setup_path)==setup_pin and p.sha(manifest_path)==manifest_pin and p.tool_manifest()==current,'preparation source/tool/proof freshness failed')
    h.owned_destination(owner)
    plan['preparation_costs']=dict(runtime_setup_wall_seconds=setup['wall_seconds'],runtime_setup_full_CPU_seconds=setup['full_CPU_seconds'],
        delivery_freeze_inner_wall_seconds=time.monotonic()-started,delivery_freeze_inner_full_CPU_seconds=cpu()-cpu0,
        qualification='Inner source/metadata preparation samples only; complete externally reaped preparation costs and full154/review costs remain separate from the260s routing workflow.')
    target=CASE/'production-delivery-protocol-frozen-001.json';write_new(target,(json.dumps(plan,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
    p.save_json(out/'result.json',dict(schema=1,prepared=True,accepted=False,Native_board_jobs=0,JVM_jobs=0,protocol=str(target),protocol_sha256=p.sha(target),
        processes=processes,source_sha256={name:hashlib.sha256(raw).hexdigest()for name,raw in generated.items()},preparation_costs=plan['preparation_costs']))
    print(json.dumps(dict(prepared=True,protocol=str(target),protocol_sha256=p.sha(target),Native_board_jobs=0,JVM_jobs=0)))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--full154-sha256',required=True);parser.add_argument('--setup-sha256',required=True);parser.add_argument('--manifest-sha256',required=True)
    args=parser.parse_args();prepare(args.full154_sha256,args.setup_sha256,args.manifest_sha256)
