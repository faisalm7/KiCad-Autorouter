"""Offline comparison of retained GUI/CLI reports; no KiCad, GUI, or subprocess calls."""
from pathlib import Path
import collections, hashlib, json, os, sys, time
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT)); sys.dont_write_bytecode=True
from autorouter import sexpr as sx
LIMIT=8*1024*1024

def read(p):
    p=Path(p)
    if p.is_symlink() or not p.is_file(): raise ValueError('not a regular input: '+str(p))
    with p.open('rb') as f: b=f.read(LIMIT+1)
    if len(b)>LIMIT: raise ValueError('input cap')
    return b

def sha(p): return hashlib.sha256(read(p)).hexdigest()
def unique(pairs):
    d={}
    for k,v in pairs:
        if k in d: raise ValueError('duplicate JSON key')
        d[k]=v
    return d

def js(p): return json.loads(read(p),object_pairs_hook=unique,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
def inventory(path):
    found={}; size=entries=0
    for base,dirs,files in os.walk(path,followlinks=False):
        entries+=len(dirs)+len(files)
        if entries>4000: raise ValueError('entry cap')
        for n in dirs:
            if (Path(base)/n).is_symlink(): raise ValueError('directory symlink')
        for n in files:
            p=Path(base)/n;b=read(p);size+=len(b)
            if size>64*1024*1024: raise ValueError('aggregate cap')
            found[p.relative_to(path).as_posix()]=hashlib.sha256(b).hexdigest()
    return dict(sorted(found.items()))

def delta(a,b,path=''):
    if type(a) is dict and type(b) is dict:
        rows=[]
        for k in sorted(set(a)|set(b)):
            q=path+'/'+k
            if k not in a: rows.append({'path':q,'change':'added','after':b[k]})
            elif k not in b: rows.append({'path':q,'change':'removed','before':a[k]})
            else: rows.extend(delta(a[k],b[k],q))
        return rows
    return [] if canonical(a)==canonical(b) else [{'path':path,'change':'changed','before':a,'after':b}]

def main():
    started=time.monotonic(); checks=[]
    def check(label,condition):
        checks.append({'check':label,'passed':bool(condition)})
        if not condition: raise AssertionError(label)
    run=ROOT/'.runs/placement-production-multichannel-001'; pub=ROOT/'evidence/placement-gui-observations-002'
    handoff=ROOT/'.runs/placement-gui-multichannel-001'; project=handoff/'project'
    result=js(run/'result.json'); review=js(handoff/'review.json'); observation=js(pub/'multichannel-observation.json')
    source=Path(result['source']).parent
    before={str(p.relative_to(ROOT)):inventory(p) for p in [source,run,project]}
    check('complete original project equals receipt and handoff', before[str(source.relative_to(ROOT))]==result['source_hashes']==review['source_project_hashes'])
    check('complete accepted run equals original handoff inventory',before[str(run.relative_to(ROOT))]==review['routing_evidence_hashes'])
    check('complete disposable GUI project equals retained postclose inventory',before[str(project.relative_to(ROOT))]==observation['prepared_project_after'])
    check('same prepared complete project',review['initial_project_hashes']==observation['prepared_project_before'])
    cli=js(run/'final-drc.json');gui=js(pub/'multichannel-gui-drc.json');binding=js(run/'final-drc-binding.json');process=js(run/'final-drc-process.json')
    check('CLI report receipt digest',sha(run/'final-drc.json')==result['native_report_sha256'])
    check('GUI report observation digest',sha(pub/'multichannel-gui-drc.json')==observation['native_report_sha256'])
    check('handoff exact routing receipt',sha(run/'result.json')==review['receipt_sha256'])
    candidate=Path(result['candidate']); board_hash=sha(candidate)
    check('GUI and CLI final saved board exact',board_hash==result['candidate_sha256']==observation['board_sha256']==sha(project/candidate.name)==review['candidate_sha256'])
    check('CLI exact candidate/input binding',binding['source']==str(candidate) and binding['before']==inventory(candidate.parent) and binding['after']==inventory(Path(binding['input']).parent) and binding['saved'] is False)
    check('CLI original rules at final DRC',all(binding['before'].get(k)==v for k,v in result['source_hashes'].items() if k!=candidate.name))
    expected_argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)','/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(run/'final-drc.json'),binding['input']]
    check('CLI exact final DRC command and cleanup',process['argv']==expected_argv and process['cwd']==str(run) and process['exit_code']==5 and process['status']=='nonzero_exit' and process['cleanup_complete'] is True and process['log_truncated'] is False)
    check('CLI native log count',read(run/'final-drc.log').decode().startswith('Found 96 violations\nFound 0 unconnected items\n'))
    for key in ['$schema','coordinate_units','kicad_version','source','included_severities','ignored_checks','unconnected_items','schematic_parity']:
        check('report metadata exact: '+key,cli[key]==gui[key])
    check('both have only warning violations',all(r['severity']=='warning' for report in [cli,gui] for r in report['violations']))
    LIB={'lib_footprint_mismatch','lib_footprint_issues'}
    noncli=[x for x in cli['violations'] if x['type'] not in LIB]; nongui=[x for x in gui['violations'] if x['type'] not in LIB]
    check('all fifteen complete nonlibrary records equal with multiplicity',collections.Counter(map(canonical,noncli))==collections.Counter(map(canonical,nongui)) and len(noncli)==15)
    connection=[x for x in noncli if x['type']=='connection_width']; other=[x for x in noncli if x['type']!='connection_width']
    check('nine connection widths and six other',len(connection)==9 and len(other)==6)
    libcli=[x for x in cli['violations'] if x['type'] in LIB];libgui=[x for x in gui['violations'] if x['type'] in LIB]
    check('exact library conditions',len(libcli)==81 and all(x['type']=='lib_footprint_mismatch' for x in libcli) and len(libgui)==114 and all(x['type']=='lib_footprint_issues' and x['description']=="The footprint library 'multichannel_mixer' is not enabled in the current configuration" for x in libgui))
    board=sx.parse(read(candidate).decode()); fps=sx.children(board,'footprint')
    fp_by_uuid={sx.unquote(sx.one(fp,'uuid')[1]):sx.unquote(fp[1]) for fp in fps}
    uuids=lambda rows: [x['items'][0]['uuid'] for x in rows if len(x['items'])==1]
    check('GUI library records cover each of 114 footprint identities once',len(fp_by_uuid)==114 and collections.Counter(uuids(libgui))==collections.Counter(fp_by_uuid.keys()))
    check('all CLI library identities included in GUI set once',len(uuids(libcli))==81 and len(set(uuids(libcli)))==81 and set(uuids(libcli))<=set(uuids(libgui)))
    pro_before=js(candidate.with_suffix('.kicad_pro'));pro_after=js(project/candidate.with_suffix('.kicad_pro').name)
    changes=delta(pro_before,pro_after)
    check('all sixteen project JSON differences match saved report',changes==js(pub/'multichannel-project-changes.json') and len(changes)==16)
    check('no existing DRC severity change',all(pro_after['board']['design_settings']['rule_severities'][k]==v for k,v in pro_before['board']['design_settings']['rule_severities'].items()))
    check('all original hard-rule values unchanged',pro_before['board']['design_settings']['rules']==pro_after['board']['design_settings']['rules'])
    cls_before=pro_before['net_settings']['classes'];cls_after=pro_after['net_settings']['classes']
    check('Default dimensions unchanged plus empty tuning profile only',cls_after==[dict(x,tuning_profile='') for x in cls_before])
    check('library table/files and all original project files except pro unchanged', [k for k,v in observation['prepared_project_before'].items() if observation['prepared_project_after'].get(k)!=v]==[candidate.with_suffix('.kicad_pro').name])
    source_pins=[]
    desired={'pcbnew/drc/drc_test_provider_library_parity.cpp','pcbnew/board_design_settings.cpp','pcbnew/drc/drc_item.cpp','common/project/net_settings.cpp'}
    for folder in ['support-scope-review-001','pic-severity-scope-review-001']:
        receipt_path=ROOT/'.runs'/folder/'source-receipt.json';receipt=js(receipt_path)
        for row in receipt['files']:
            if row['path'] in desired:
                path=receipt_path.parent/'source'/row['path'];check('cached primary source pin '+row['path'],sha(path)==row['sha256'])
                source_pins.append(dict(path=str(path.relative_to(ROOT)),receipt=str(receipt_path.relative_to(ROOT)),receipt_sha256=sha(receipt_path),commit=receipt['commit'],url=row['url'],sha256=row['sha256']))
    check('four cached primary sources pinned',len(source_pins)==4)
    freeze=js(run/'placement-source-freeze.json')
    check('source-freeze digest',sha(run/'placement-source-freeze.json')==result['placement_source_freeze']['sha256'])
    for name in ['pipeline.py','floor_route.py']:
        check('frozen runtime environment code '+name,sha(run/'code'/name)==freeze['files_sha256']['autorouter/'+name])
    saved_summary=sha(pub/'summary.json')
    check('historical wrong summary preserved',saved_summary=='b032a68d9b6adcca87069697e5fc52e883d91e4ef14be296b95bd6f1fd94f5b2')
    after={str(p.relative_to(ROOT)):inventory(p) for p in [source,run,project]}
    check('all originals/run/disposable evidence unchanged by this audit',before==after)
    inputs=[run/'result.json',run/'final-drc.json',run/'final-drc-process.json',run/'final-drc-binding.json',run/'final-drc.log',run/'placement-source-freeze.json',run/'code'/'pipeline.py',run/'code'/'floor_route.py',handoff/'review.json',pub/'multichannel-gui-drc.json',pub/'multichannel-observation.json',pub/'multichannel-project-changes.json',pub/'summary.json',candidate,candidate.with_suffix('.kicad_pro'),project/candidate.with_suffix('.kicad_pro').name,project/'fp-lib-table']
    output={'schema':1,'scope':'Offline retained-evidence comparison; no native/GUI/engine/network execution or rule changes','status':'completed','checks':checks,'input_pins':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in inputs},'frozen_routing_code_head':freeze['git_head'],'candidate_sha256':board_hash,'counts':{'cli':dict(collections.Counter(x['type'] for x in cli['violations'])),'gui':dict(collections.Counter(x['type'] for x in gui['violations']))},'nonlibrary_full_record_multisets_equal':True,'connection_width_records':connection,'other_nonlibrary_records':other,'ignored_checks':cli['ignored_checks'],'library_delta':33,'cli_library_mismatch_by_footprint_name':dict(collections.Counter(fp_by_uuid[x] for x in uuids(libcli))),'gui_library_issue_all_footprints':114,'cli_process':process,'project_changes':changes,'source_pins':source_pins,'inventories':{k:{'files':len(v),'sha256_of_canonical_inventory':hashlib.sha256(canonical(v).encode()).hexdigest()} for k,v in before.items()},'all_inputs_unchanged':True,'library_runtime_root_cause_established':False,'gui_qualified':False,'new_validation_performed':False,'wall_seconds':time.monotonic()-started}
    (OUT/'audit.json').write_text(json.dumps(output,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({'status':output['status'],'checks':len(checks),'counts':output['counts'],'wall_seconds':output['wall_seconds']}))
if __name__=='__main__':main()
