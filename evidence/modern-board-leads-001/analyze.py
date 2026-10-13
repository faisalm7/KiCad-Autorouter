"""Static original-rule observations; no native validation or source promotion."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx
receipt=json.loads((OUT/'fetch-receipt.json').read_text())
previous=json.loads((ROOT/'evidence/corpus-next-001/source-ledger-draft.json').read_text())
prior={r['repository'] for r in previous['repositories']}
repos=['siderakb/pmw3610-pcb','XavierBerger/RotaryEncoderDebounced','nushackers/hsp-pcb-intro']
results=[]
for repo in repos:
    assert repo not in prior
    metadata=json.loads((OUT/(repo.replace('/','__')+'.json')).read_text())
    tree={r['path']:r for r in metadata['tree']}
    raw={r['label'][len(repo)+1:]:r for r in receipt['requests'] if r['url'].startswith('https://raw.githubusercontent.com/'+repo+'/') and 'file' in r}
    base=OUT/'inputs'/repo.replace('/','__');base.mkdir(parents=True,exist_ok=False)
    for path,row in raw.items():
        data=(OUT/row['file']).read_bytes();entry=tree[path]
        assert hashlib.sha256(data).hexdigest()==row['sha256']
        assert len(data)==entry['size'] and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==entry['sha']
        target=base/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    board=next(path for path in raw if path.endswith('.kicad_pcb'));pcb=base/board
    before=p.tree_hash(base)
    try:p.preflight(pcb);rejection=None
    except p.Rejected as exc:rejection=str(exc)
    assert p.tree_hash(base)==before
    t=sx.read(pcb);pro=json.loads(pcb.with_suffix('.kicad_pro').read_text())
    fps=sx.children(t,'footprint');pads=[pad for fp in fps for pad in sx.children(fp,'pad')]
    layers=[sx.unquote(l[1]) for l in sx.one(t,'layers')[1:] if isinstance(l,list) and len(l)>1 and re.fullmatch(r'(?:F|B|In[0-9]+)\.Cu',sx.unquote(l[1]))]
    ds=pro.get('board',{}).get('design_settings',{});sev=ds.get('rule_severities',{})
    history=next(r for r in receipt['requests'] if r['label']==repo+' pinned path history '+board)
    commits=json.loads((OUT/history['file']).read_text())
    history_sanitized=[{'sha':r['sha'],'author_name':r['commit']['author']['name'],'author_date':r['commit']['author']['date'],'message':r['commit']['message']} for r in commits]
    models=sorted({sx.unquote(m[1]) for fp in fps for m in sx.children(fp,'model')})
    tables={path:(base/path).read_text() for path in raw if path.endswith(('fp-lib-table','sym-lib-table'))}
    symbols=[]
    sch=sx.read(pcb.with_suffix('.kicad_sch'))
    for symbol in sx.children(sch,'lib_symbols'):
        symbols.extend(sx.unquote(n[1]) for n in sx.children(symbol,'symbol'))
    notices={path:row['sha256'] for path,row in raw.items() if path.lower() in {'license','licence.txt','license.md','readme.md','codeowners'}}
    results.append({'repository':repo,'source_commit':metadata['commit'],'fork':metadata['fork'],'declared_creator':metadata['creator'],
        'board':board,'board_sha256':raw[board]['sha256'],'source_primary_url':'https://github.com/'+repo+'/tree/'+metadata['commit'],
        'format':sx.one(t,'version')[1],'copper_layers':layers,'footprints':len(fps),'pads':len(pads),
        'custom_pads':sum(pad[3]=='custom' for pad in pads),'zones':len(sx.children(t,'zone')),
        'native_preflight':{'eligible':rejection is None,'exact_rejection':rejection,'native_validation_performed':False},
        'source_title':sx.children(t,'title_block'),'native_net_names':[sx.unquote(n[2]) for n in sx.children(t,'net')],
        'classes':pro.get('net_settings'),'unknown_severity_keys':sorted(set(sev)-p.KNOWN_CHECKS),
        'nonblocking_critical_original_severities':{k:v for k,v in sev.items() if k in p.CRITICAL_CHECKS and v!='error'},
        'drc_exclusions':ds.get('drc_exclusions',[]),'library_tables':tables,'embedded_schematic_library_ids':symbols,
        'embedded_board_footprint_ids':sorted({sx.unquote(fp[1]) for fp in fps}),'model_references':models,
        'custom_rule_paths_in_pinned_tree':[path for path in tree if path.endswith('.kicad_dru')],
        'submodules':[r['path'] for r in tree.values() if r['mode']=='160000'],
        'notice_hashes':notices,'pinned_board_path_history':history_sanitized,'history_first_page_100_only':True,
        'inspected_original_file_hashes':before,'originals_unchanged_during_guard':True,
        'acquisition_promoted':False,'functional_or_independent_ancestry_certification':False})

dependency=json.loads((OUT/'MaloufSleep__ME-ESP8266.json').read_text())
modelpath='3D_Models/Button_Switch_SMD.3dShapes/TS-1187A-B-A-B.step'
depmodel=next(r for r in dependency['tree'] if r['path']==modelpath)
nusmeta=json.loads((OUT/'nushackers__hsp-pcb-intro.json').read_text())
nusmodel=next(r for r in nusmeta['tree'] if r['path'].endswith('/TS-1187A-B-A-B.step'))
assert depmodel['sha']==nusmodel['sha'] and depmodel['size']==nusmodel['size']
result={'schema':1,'scope':'At most three new primary creator project leads; all development-exposed by this static research, not acquired production corpus members',
 'original_population_unchanged':{'acquired':20,'statically_eligible':3,'unsupported':17,'untouched_holdout':False},
 'prior48_ledger_sha256':p.sha(ROOT/'evidence/corpus-next-001/source-ledger-draft.json'),
 'actual_allowed_formats':['20241229','20260206'],'requested20260101_is_not_production_admitted':True,
 'live_guard_sha256':p.sha(ROOT/'autorouter/pipeline.py'),'sexpr_sha256':p.sha(ROOT/'autorouter/sexpr.py'),
 'new_raw_response_bytes':receipt['new_raw_response_bytes'],'max_new_raw_response_bytes':receipt['max_raw_response_bytes'],
 'network_requests':len(receipt['requests']),'failed_requests':[r for r in receipt['requests'] if 'error' in r],
 'raw_board_payloads_read':3,'new_native_jobs':0,'new_engine_jobs':0,'git_subprocesses':0,'new_external_spending':0,
 'leads':results,'button_model_origin':{'creator_repository':dependency['repository'],'commit':dependency['commit'],
 'source_path':modelpath,'original_copy_path':nusmodel['path'],'same_git_blob_sha1':depmodel['sha'],'bytes':depmodel['size'],
 'payload_downloaded':False,'limit':'Exact copied object and publisher root MIT notice observed; asset-specific original authorship remains unproved. Preserve MIT attribution with any permitted future acquisition; no model redistribution authorized by this audit.'}}
(OUT/'facts.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'raw_bytes':receipt['new_raw_response_bytes'],'requests':len(receipt['requests']),
 'leads':[{'repository':r['repository'],'format':r['format'],'layers':r['copper_layers'],'preflight':r['native_preflight']} for r in results]},indent=2))
