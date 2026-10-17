"""Prepare019 using the exact018 builder/runner and retained owned inputs.

Source-only until the lead supplies the actual audited GUI-fix checkpoint. No
Native/JVM/GUI, downloads, pip, global install, tool changes or release occurs.
This helper deliberately does not acquire the Native benchmark lane.
"""
from pathlib import Path
import argparse,hashlib,json,os,resource,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv,sexpr as sx,placement_clearance as pc,handoff as h
from autorouter.runner import run
from experiments.placement_handoff_native_v1.driver import copy_bytes

GUI_PIN='f448a08206ead70025fcefd886a1775157e86ccb139e974102e709d0cb80a844'
MAIN_PIN='969ee3f7143dee26a0fa328ebffd0ad355ebcfe74c09c8cd99f48cc778db3f45'
PIPELINE_PIN='bfc3f2388d73df7f5000ff35f86d3d72e4dd380ba52e13acfb0630ed7c2e9400'
BUILDER_PIN='560b7512be6d22af628822b2f8b9fc512e2e4bb8625ebb3fcf64780befaea6e6'
COPY_HELPER_PIN='a84176cbab44199c5d10c80860f391d56f624b2624da2d157eb8810266796f8c'
PRIOR_SETUP_PIN='3a4bfe3598b2c1cd4c475992650432406f52a19fbda3eedb91e0e0271fc4f69d'
PRIOR_MANIFEST_PIN='ba65f0ed8356d148b3ac811e18496be0a9d15670f762dbba543bb20e59ea2e1b'
PRIOR=ROOT/'.runs/runtime-directory-018'
CASE=ROOT/'.runs/runtime-directory-019'

def require(value,reason):
    if not value:raise p.Rejected(reason)
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))

def prepare(qualified_head):
    start=time.monotonic();cpu0=cpu()
    require(type(qualified_head)is str and pv._HEAD.fullmatch(qualified_head)is not None,'explicit full audited GUI-fix checkpoint SHA required')
    require(sys.version_info[:2]==(3,11),'prepare with the existing Python3.11 environment')
    tools=p.tool_manifest()
    prior_setup=PRIOR/'setup.json';prior_manifest=PRIOR/'runtime/runtime-distribution.json'
    require(p.sha(prior_setup)==PRIOR_SETUP_PIN and p.sha(prior_manifest)==PRIOR_MANIFEST_PIN,'retained018 setup/manifest changed')
    old=json.loads(pc.read_bytes(prior_manifest).decode());retained=json.loads(pc.read_bytes(prior_setup).decode())
    old_files=old['build_source']['files_sha256'];old_modules={name:digest for name,digest in old_files.items()if name.startswith('autorouter/')}
    modules=tools['implementation_sha256']
    require(set(modules)==set(old_modules)and len(modules)==44,'exact44-module runtime population required')
    require(sorted(name for name in modules if modules[name]!=old_modules[name])==['autorouter/gui.py']
        and modules['autorouter/gui.py']==GUI_PIN and modules['autorouter/__main__.py']==MAIN_PIN
        and modules['autorouter/pipeline.py']==PIPELINE_PIN,
        'only the exact queued-open GUI fix may differ from018; main/pipeline and43modules must match')
    require(pv._git(ROOT,'rev-parse','--verify',qualified_head+'^{commit}').decode().strip()==qualified_head,
        'qualified GUI-fix checkpoint must identify an actual exact commit')
    require(hashlib.sha256(pv._git(ROOT,'show',qualified_head+':autorouter/gui.py',limit=pv.MAX_FILE_BYTES)).hexdigest()==GUI_PIN,
        'audited checkpoint GUI bytes differ')
    selected=('autorouter',*sorted(pv.FIXED_FILES))
    changed=pv._git(ROOT,'diff','--name-only',old['build_source']['git_head'],qualified_head,'--',*selected).decode().splitlines()
    require(changed==['autorouter/gui.py'],'audited checkpoint changes other selected product bytes from018')
    require(not pv._git(ROOT,'diff','--name-only',qualified_head,tools['git_head'],'--',*selected),
        'current HEAD product bytes differ from qualified GUI-fix checkpoint')
    pv._git(ROOT,'merge-base','--is-ancestor',qualified_head,tools['git_head'])
    require(p.sha(ROOT/'scripts/prepare_runtime.py')==BUILDER_PIN
        and p.sha(ROOT/'experiments/placement_handoff_native_v1/driver.py')==COPY_HELPER_PIN,'curated builder/shared copier changed')
    # The unchanged builder requires complete selected source committed at HEAD.
    # Later evidence-only checkpoints must retain the qualified product bytes.
    for name,digest in old_files.items():
        if name!='autorouter/gui.py':require(p.sha(ROOT/name)==digest,'unchanged selected product file differs: '+name)
    CASE.mkdir();owner={};h.capture_destination(owner,CASE);runtime=CASE/'runtime';processes=[];sources={}
    record=dict(schema=1,prepared=False,status='preparing',native_or_JVM=False,actual_GUI=False,
        qualified_source_commit=qualified_head,source_head=tools['git_head'],tools=tools,runtime=str(runtime),
        prior_setup_sha256=PRIOR_SETUP_PIN,prior_manifest_sha256=PRIOR_MANIFEST_PIN,builder_sha256=BUILDER_PIN,
        copy_helper_sha256=COPY_HELPER_PIN,changed_runtime_modules=['autorouter/gui.py'],unchanged_runtime_modules=43,
        source_fixtures_reused=True,sources=sources,processes=processes,
        qualification='Curated path-bound Mac runtime preparation only. Only the audited queued-open GUI fix differs from018; all43other modules including doctor main/pipeline and other selected product files match. Owned matching/clean-fields/mismatch4Cu and plain sources copied byte-exact from018 with no Native regeneration. Same exposed families. Fresh no-pip copied interpreter and cachedJAR; no downloads, Native/JVM/GUI execution, global install, release or binary redistribution claim. Fresh installed Native/GUI qualification remains pending.')
    env={key:value for key,value in os.environ.items()if key not in {'PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN'}}
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
    try:
        for name,argv in [('build',[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/prepare_runtime.py'),'--output',str(runtime),'--copy-local-engine']),
                          ('venv',[str(ROOT/'.venv/bin/python'),'-B','-m','venv','--copies','--without-pip',str(runtime/'.venv')])]:
            proc=run(argv,cwd=CASE,log=CASE/(name+'.log'),timeout=90,max_log_bytes=64*1024,
                max_workdir_bytes=256*1024**2,max_group_rss_bytes=1024**3,env=env)
            processes.append(proc);p.save_json(CASE/(name+'-process.json'),proc)
            require(proc['status']=='success'and proc['exit_code']==0 and proc['cleanup_complete']is True,
                name+' failed; preserve this attempt and its logs')
        require(set(retained['sources'])=={'matching','clean-fields','mismatch','plain'},'exact existing owned input population required')
        for name in ('matching','clean-fields','mismatch','plain'):
            old_source=retained['sources'][name];before=Path(old_source['board']);expected=old_source['source_hashes']
            captured=pc.inventory(before.parent,contents=True)
            require({key:hashlib.sha256(raw).hexdigest()for key,raw in captured.items()}==expected,'retained018 source changed: '+name)
            folder=CASE/('source-'+name);copy_bytes(captured,folder,expected_parent_owner=owner)
            board=folder/before.name;require(pc.inventory(folder)==expected and pc.inventory(before.parent)==expected,'source copy/binding changed: '+name)
            tree=sx.read(board);protected=p.routes(tree)
            require(len(protected)==old_source['protected_routes']and all(p.locked(row)for row in protected),'retained protected copper differs: '+name)
            if name=='plain':p.preflight(board)
            else:p.preflight(board,class_context='native-route-flat-classes-v1')
            sources[name]=dict(board=str(board),source_hashes=expected,options=old_source['options'],protected_routes=old_source['protected_routes'],
                copied_from=str(before),native_validation='not executed; static preflight only, mismatch remains a deliberate Native negative')
        manifest=json.loads(pc.read_bytes(runtime/pv.MANIFEST).decode());new_files=manifest['build_source']['files_sha256']
        require(set(new_files)==set(old_files),'curated selected file population changed')
        require(sorted(name for name in new_files if new_files[name]!=old_files[name])==['autorouter/gui.py']
            and new_files['autorouter/gui.py']==GUI_PIN and new_files['autorouter/__main__.py']==MAIN_PIN
            and new_files['autorouter/pipeline.py']==PIPELINE_PIN,
            'built product differs beyond audited queued-open GUI fix')
        require(manifest['build_source']['git_head']==tools['git_head'],'builder source checkpoint differs')
        (runtime/'.runs').mkdir()
        require(p.sha(prior_setup)==PRIOR_SETUP_PIN and p.sha(prior_manifest)==PRIOR_MANIFEST_PIN and p.tool_manifest()==tools,
            'source/tools/prior preparation changed')
        record.update(prepared=True,status='prepared',manifest_sha256=p.sha(runtime/pv.MANIFEST))
    except(Exception,KeyboardInterrupt)as exc:
        record.update(prepared=False,status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',reason=type(exc).__name__+': '+str(exc))
    record.update(wall_seconds=time.monotonic()-start,full_CPU_seconds=cpu()-cpu0)
    h.owned_destination(owner);p.save_json(CASE/'setup.json',record)
    print(json.dumps({key:record.get(key)for key in('prepared','status','source_head','wall_seconds','full_CPU_seconds','reason')}))
    return 0 if record['prepared']and record['status']=='prepared'else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qualified-head',required=True,help='Exact audited GUI-fix checkpoint SHA; no prospective/default commit.')
    args=parser.parse_args();raise SystemExit(prepare(args.qualified_head))
