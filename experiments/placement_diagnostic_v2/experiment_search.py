"""Prospective three-arm placement clearance/search diagnostic.

Requires a same-code full fixture diagnostic using margin20um/via_low before three sequential native runs.
Every arm pays the full measured shared overhead under equal120s wall/CPU caps.
"""
from __future__ import annotations
import argparse,copy,datetime,fcntl,math,os,shutil,signal,sys,time,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE))
import diagnostic_route as d
p=d.p;f=d.f;g=d.g;ROOT=d.ROOT
BUDGET=120.;RESERVE=5.


def selected_source():
    manifest=f.read_json(ROOT/'data/sources.json');rows=[x for x in manifest['projects']if x['project_id']=='kicad-multichannel']
    if len(rows)!=1 or rows[0]['split']!='development':raise p.Rejected('predeclared licensed development source missing')
    project=rows[0];base=d.owned(ROOT/'.data'/project['destination']);board=base/'multichannel_mixer.kicad_pcb'
    if ROOT/'.data/boards' not in base.parents:raise p.Rejected('source destination escaped corpus')
    expected={str(Path(x['destination']).relative_to(project['destination'])):x['sha256']for x in manifest['files']if x.get('project_id')==project['project_id']}
    entries=[x for x in project['boards']if Path(x['board']).name==board.name]
    if len(entries)!=1 or entries[0]['same_basename_project'] is not True or not expected or p.tree_hash(base)!=expected:raise p.Rejected('complete original licensed source identity differs')
    return board,project


def fixture_gate(path,frozen):
    path=d.owned(path);before=p.tree_hash(path.parent);value=d.check_result(path);receipt=f.read_json(path)
    if not value['routing_accepted'] or receipt['policy']!=d.POLICIES[2] or receipt['tools']!=frozen['tools']:
        raise p.Rejected('same-code accepted margin20um/via_low fixture required before search comparison')
    if receipt['freeze']['files_sha256']!=frozen['files_sha256'] or receipt['source_hashes']!=f.read_json(HERE/'protocol.json')['qualification_fixture']['source_hashes']:
        raise p.Rejected('fixture code/project pin differs')
    source=d.sx.read(Path(receipt['source']));rows=d.narrow_source(source)
    if len(d.sx.children(source,'footprint'))!=4 or len(rows)!=1 or receipt['native']['findings'] or receipt['metrics']['vias']<1:
        raise p.Rejected('expected required-via allowed-placement fixture not qualified')
    if p.tree_hash(path.parent)!=before:raise p.Rejected('fixture evidence changed during gate')
    return before


def compare_pair(first,last):
    if not all(row.get('diagnostic_verified') for row in (first,last)):return None
    value={'reference_policy':first['policy'],'variant_policy':last['policy'],
        'reference_accepted':first['accepted'],'variant_accepted':last['accepted'],
        'completion_difference':int(last['accepted'])-int(first['accepted']),
        'scope':'One exposed diagnostic planning/search comparison; no production/C/B2/generalized claim'}
    for key in ('opens','blocking','warnings','exclusions'):value[key+'_delta']=last[key]-first[key]
    if first['accepted'] and last['accepted']:value.update(length_delta_mm=last['length_mm']-first['length_mm'],via_delta=last['vias']-first['vias'])
    return value


def compare(rows):
    if len(rows)!=3 or not all(row.get('diagnostic_verified') for row in rows):return None
    return {'margin_effect':compare_pair(rows[0],rows[1]),'via_cost_effect':compare_pair(rows[1],rows[2]),
            'combined_effect':compare_pair(rows[0],rows[2])}


def experiment(out,fixture):
    started=time.monotonic();cpu0=d.cpu();out=d.owned(out)
    if out.parent!=ROOT/'.runs' or out.exists():raise p.Rejected('fresh direct .runs output required')
    out.mkdir();rows=[{'policy':x,'accepted':False,'verified_native_accepted':False,'status':'not_attempted'}for x in d.POLICIES]
    summary={'schema':2,'kind':'diagnostic_placement_search_three_arm','status':'incomplete','production_qualified':False,'comparison_eligible':False,'comparison':None,'results':rows}
    frozen=None;trees={};bound={}
    def stable():
        if frozen is not None:
            d.verify_freeze(frozen)
            if p.tree_hash(board.parent)!=source_hashes:raise p.Rejected('paired original source changed')
        for name,digest in bound.items():
            if p.sha(d.owned(name))!=digest:raise p.Rejected('pair protocol/index/manifest changed')
        for name,hashes in trees.items():
            if p.tree_hash(d.owned(name))!=hashes:raise p.Rejected('paired source/fixture/code/completed evidence changed')
    def account():
        wall=time.monotonic()-started;cpu=d.cpu()-cpu0
        sw=wall-sum(row.get('invocation_wall_seconds',0)for row in rows);sc=cpu-sum(row.get('invocation_cpu_seconds',0)for row in rows)
        if any(not math.isfinite(x) or x<0 for x in (wall,cpu,sw,sc)):raise p.Rejected('invalid shared resource arithmetic')
        summary.update(batch_wall_seconds=wall,batch_cpu_seconds=cpu,shared_wall_seconds=sw,shared_cpu_seconds=sc)
        for row in rows:
            w=row.get('invocation_wall_seconds',0)+sw;c=row.get('invocation_cpu_seconds',0)+sc
            row.update(charged_wall_seconds=w,charged_cpu_seconds=c,within_charged_caps=w<=BUDGET and c<=BUDGET)
            row['accepted']=summary['status']=='completed' and row.get('verified_native_accepted',False) and row['within_charged_caps']
        summary['comparison_eligible']=summary['status']=='completed' and summary.get('raw_tasks_equivalent') is True and all(row.get('diagnostic_verified') and row['within_charged_caps']for row in rows)
        summary['comparison']=compare(rows) if summary['comparison_eligible'] else None
    def invalidate(exc):
        def archive():
            for name in ('summary.json','summary.json.partial'):
                path=out/name
                if path.exists():path.rename(out/('invalidated-'+uuid.uuid4().hex+'-'+name))
        archive();summary['completed_trees']=copy.deepcopy(trees);summary.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',reason=type(exc).__name__+': '+str(exc),comparison=None,comparison_eligible=False)
        for row in rows:row.update(accepted=False,verified_native_accepted=False)
        try:account();p.save_json(out/'summary.json',summary)
        except (Exception,KeyboardInterrupt):archive()
    try:
        p.check_storage();board,project=selected_source();original=p.preflight(board);d.narrow_source(original);source_hashes=p.tree_hash(board.parent)
        frozen=d.freeze();fixture=d.owned(fixture);trees[str(fixture.parent)]=fixture_gate(fixture,frozen)
        qualified_fixture=f.read_json(fixture);qualified_source=d.owned(qualified_fixture['source']).parent
        trees[str(qualified_source)]=qualified_fixture['source_hashes']
        stable()
        bound[str(ROOT/'data/sources.json')]=p.sha(ROOT/'data/sources.json')
        shutil.copytree(board.parent,out/'source-project');trees[str(out/'source-project')]=source_hashes
        for name,digest in frozen['files_sha256'].items():
            dest=out/'code'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
            if p.sha(dest)!=digest:raise p.Rejected('pair code changed during copy')
        trees[str(out/'code')]=p.tree_hash(out/'code')
        shared_wall=time.monotonic()-started;shared_cpu=d.cpu()-cpu0;assigned=math.floor((BUDGET-max(shared_wall,shared_cpu)-RESERVE)*1000)/1000
        if assigned<50:raise p.Rejected('pair setup exhausted equal route allowance')
        protocol={'frozen':frozen,'source':str(board),'source_hashes':source_hashes,'fixture_receipt':str(fixture),'fixture_sha256':p.sha(fixture),
            'protocol':f.read_json(HERE/'protocol.json'),'identical_assigned_seconds':assigned,'shared_wall_at_assignment':shared_wall,'shared_cpu_at_assignment':shared_cpu,
            'fixed_order':True,'desktop_background_contention':'uncontrolled; one project heavy worker; desktop application activity not measured','family':project['family'],'exposure':'development exposed, not independent family or confirmatory test'}
        p.save_json(out/'protocol.json',protocol);bound[str(out/'protocol.json')]=p.sha(out/'protocol.json');summary['protocol_sha256']=bound[str(out/'protocol.json')]
        for index,policy in enumerate(d.POLICIES):
            row=rows[index];directory=out/('arm-'+str(index));wall0=time.monotonic();cpu_start=d.cpu();row['host_load_begin']=list(os.getloadavg())
            try:
                stable();value=d.route(board,directory,assigned,policy)
                saved=f.read_json(directory/'result.json')
                if f.canonical(saved)!=f.canonical(value):raise p.Rejected('returned diagnostic differs from saved receipt')
                if value['status']=='cancelled':raise KeyboardInterrupt
                if value.get('tools')!=frozen['tools'] or value.get('source_hashes')!=source_hashes or value.get('budget_seconds')!=assigned or value.get('policy')!=policy:
                    raise p.Rejected('paired invocation contract differs')
                verdict=d.check_result(directory/'result.json') if 'native' in value else {'diagnostic_verified':False,'routing_accepted':False}
                row.update(status=value['status'],diagnostic_verified=verdict['diagnostic_verified'],verified_native_accepted=verdict['routing_accepted'],receipt_sha256=p.sha(directory/'result.json'))
                if 'native' in value:
                    row.update({key:value['native'][key]for key in ('opens','blocking','warnings','exclusions')});row.update(length_mm=value['metrics']['track_length_mm'],vias=value['metrics']['vias'])
                    row.update(peak_child_rss_bytes=value['peak_child_rss_bytes'],chain=value['chain'])
                trees[str(directory)]=p.tree_hash(directory);stable()
            finally:
                if directory.is_dir() and str(directory) not in trees:trees[str(directory)]=p.tree_hash(directory)
                row.update(invocation_wall_seconds=time.monotonic()-wall0,invocation_cpu_seconds=d.cpu()-cpu_start,host_load_end=list(os.getloadavg()))
                index_path=out/('arm-'+str(index)+'-invocation.json');p.save_json(index_path,row);bound[str(index_path)]=p.sha(index_path)
        raw=[]
        for index in range(len(d.POLICIES)):
            tree=g._parse_dsn((out/('arm-'+str(index))/'native.dsn').read_text());tree[1]='"display-name-only"';raw.append(tree)
        if any(tree!=raw[0] for tree in raw[1:]):raise p.Rejected('paired native raw tasks differ beyond displayed name')
        summary.update(raw_tasks_equivalent=True,status='completed',completed_trees=copy.deepcopy(trees))
    except (Exception,KeyboardInterrupt) as exc:invalidate(exc);return summary
    summary['accounting_point']='Stored totals precede final publication/freshness/readback; charged caps rechecked after all checks. Corrective rejection can finish outside cap.'
    try:
        stable();account();expected=f.canonical(summary);p.save_json(out/'summary.json',summary)
        if f.canonical(f.read_json(out/'summary.json'))!=expected:raise p.Rejected('pair summary changed after write')
        for index,row in enumerate(rows):
            if row.get('diagnostic_verified'):d.check_result(out/('arm-'+str(index))/'result.json')
        stable()
        if f.canonical(f.read_json(out/'summary.json'))!=expected:raise p.Rejected('pair summary changed during final checks')
        sw=time.monotonic()-started-sum(row['invocation_wall_seconds']for row in rows);sc=d.cpu()-cpu0-sum(row['invocation_cpu_seconds']for row in rows)
        if any(row['invocation_wall_seconds']+sw>BUDGET or row['invocation_cpu_seconds']+sc>BUDGET for row in rows):raise p.Rejected('pair charged cap exceeded at publication')
    except (Exception,KeyboardInterrupt) as exc:invalidate(exc)
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--fixture-result',required=True,type=Path);parser.add_argument('--run-search',action='store_true');args=parser.parse_args(argv)
    if not args.run_search:parser.error('--run-search required; no native work executed')
    handlers={sig:signal.getsignal(sig)for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in handlers:signal.signal(sig,interrupted)
        with d.owned(ROOT/'.runs/quality-experiment.lock').open('a')as stream:
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);value=experiment(args.output,args.fixture_result)
    finally:
        for sig,handler in handlers.items():signal.signal(sig,handler)
    print(f.canonical({'status':value['status'],'comparison_eligible':value['comparison_eligible']}))
    return 0 if value['status']=='completed' else 1
if __name__=='__main__':raise SystemExit(main())
