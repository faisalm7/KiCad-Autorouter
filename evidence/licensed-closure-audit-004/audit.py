"""Static source/rights/dependency census only. No native tool, network or data execution."""
from collections import Counter
import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
import time
import sexpr_snapshot as sx

HERE=Path(__file__).absolute().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/pipeline.py').is_file())
PROTOCOL_SHA='23239f00d5d249611d2403eec0e41d8d6db22881aa76dd3d76e94bd764b24427'
PARSER_SHA='c65b209def530fab9ca1481c67ed2d8217a294b73df8e5e41458e269f917b6dd'
MIB=1024**2
LIMIT=64*MIB
FALSE={'native_executed':False,'engine_executed':False,'routing_accepted':False,
       'dependency_closure_verified':False,'redistribution_approved':False,'independent_family_established':False}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def safe(value):
    if not isinstance(value,str) or not value or value.startswith('/') or '\\'in value or any(ord(c)<32 for c in value) or any(p in ('','.','..')for p in value.split('/')):raise ValueError('unsafe relative path')
    return Path(*PurePosixPath(value).parts)
def owned(root,path):
    path=path.absolute()
    if not path.is_relative_to(root.absolute()) or any(p.is_symlink()for p in (path,*path.parents)):raise ValueError('unsafe owned path')
    return path
def read_bytes(path,cap=10*MIB):
    if path.is_symlink()or not path.is_file()or path.stat().st_size>cap:raise ValueError('unsafe/oversized input')
    with path.open('rb')as stream:raw=stream.read(cap+1)
    if len(raw)>cap or len(raw)!=path.stat().st_size:raise ValueError('input grew/size changed')
    return raw
def decode(raw):
    def pairs(rows):
        out={}
        for k,v in rows:
            if k in out:raise ValueError('duplicate JSON key')
            out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def inventory(base):
    result={};dirs=[];stack=[owned(base,base)];count=total=0;folded=set()
    while stack:
        with os.scandir(stack.pop())as entries:
            for e in entries:
                count+=1
                if count>4096 or e.is_symlink():raise ValueError('entry ceiling/symlink')
                path=Path(e.path);name=path.relative_to(base).as_posix();safe(name)
                if name.casefold()in folded:raise ValueError('casefold collision')
                folded.add(name.casefold())
                if e.is_dir(follow_symlinks=False):dirs.append(name);stack.append(path)
                elif e.is_file(follow_symlinks=False):
                    if len(result)>=2048 or total+e.stat(follow_symlinks=False).st_size>LIMIT:raise ValueError('inventory cap')
                    raw=read_bytes(path);total+=len(raw);result[name]={'bytes':len(raw),'sha256':sha(raw)}
                else:raise ValueError('special input')
    return {'files':dict(sorted(result.items())),'directories':sorted(dirs),'file_count':len(result),'bytes':total,'schema':1}
def plan():
    raw=read_bytes(HERE/'protocol.json')
    if sha(raw)!=PROTOCOL_SHA or sha(read_bytes(HERE/'sexpr_snapshot.py'))!=PARSER_SHA:raise ValueError('protocol/parser changed')
    p=decode(raw);baseline=read_bytes(HERE/'existing-data-inventory.json')
    if sha(baseline)!=p['baseline_sha256']:raise ValueError('old data baseline changed')
    return p,decode(baseline)
def atom(node,key,default=None):
    value=sx.one(node,key)
    return sx.unquote(value[1])if value and len(value)>1 else default

def walk(node):
    stack=[node];count=0
    while stack:
        n=stack.pop();count+=1
        if count>500000:raise ValueError('AST node bound')
        if isinstance(n,list):yield n;stack.extend(reversed([x for x in n if isinstance(x,list)]))

def reference(value,kind,file,files,project_dir):
    """Classify without opening or substituting an external path."""
    row={'kind':kind,'source_file':file,'original':value,'resolution':'unresolved','target':None}
    if kind in ('footprint_identifier','symbol_identifier','legacy_library'):
        row['reason']='library identifier requires authentic original table/library revision; embedded geometry is separate'
        row['alias']=value.split(':',1)[0]if ':'in value else None
        return row
    variables=re.findall(r'\$\{([^}]+)\}',value)
    if any(v!='KIPRJMOD'for v in variables)or '$('in value or re.search(r'\$[A-Za-z_]',value):
        row.update(reason='external or unknown environment variable; no invented alias',variables=variables);return row
    value=value.replace('${KIPRJMOD}',project_dir or '.')
    if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',value)or value.startswith(('/', '~'))or '\\'in value:
        row['reason']='absolute, external URI, or platform-specific path not followed';return row
    # A KIPRJMOD path already starts at project directory; other paths are relative to containing native file.
    parts=[]
    origin=''if '${KIPRJMOD}'in row['original']else str(PurePosixPath(file).parent)
    for part in (origin+'/'+value).split('/'):
        if part in ('','.'):continue
        if part=='..':
            if not parts:row['reason']='reference escapes acquired project';return row
            parts.pop()
        else:parts.append(part)
    target='/'.join(parts);row['target']=target
    if target in files:row.update(resolution='local_file_present',reason='exact original case/path present; content/version semantics remain unqualified')
    elif any(n.startswith(target.rstrip('/')+'/')for n in files):row.update(resolution='local_directory_present',reason='exact local directory exists; not proof all members/aliases are complete')
    else:row['reason']='missing exact original relative path'
    return row

def inspect_native(name,raw,files):
    text=raw.decode('utf-8');ext=Path(name).suffix.lower();project_dir=str(PurePosixPath(name).parent)
    result={'file':name,'syntax':'sexpr','observed':{},'references':[],'parse_error':None}
    if ext=='.kicad_pro':
        data=decode(raw);settings=data.get('board',{}).get('design_settings',{})
        result.update(syntax='modern_json',observed={'meta':data.get('meta'),'net_settings':data.get('net_settings'),'design_settings':settings,'unknown_top_level_keys':sorted(set(data)-{'board','boards','cvpcb','erc','libraries','meta','net_settings','pcbnew','schematic','sheets','text_variables'})})
        for key,value in data.get('libraries',{}).items():
            if isinstance(value,list):
                for v in value:
                    if isinstance(v,str):result['references'].append(reference(v,'project_library',name,files,project_dir))
        return result
    if ext=='.pro':
        cfg=configparser.ConfigParser(interpolation=None,strict=True);cfg.optionxform=str;cfg.read_string(text)
        sections={section:dict(cfg.items(section))for section in cfg.sections()}
        result.update(syntax='legacy_project_ini',observed={'sections':sections,'native_migration_performed':False})
        for section,values in sections.items():
            for key,value in values.items():
                if re.search('lib|path',key,re.I)and value:result['references'].append(reference(value,'legacy_library',name,files,project_dir))
        return result
    if ext=='.sch'and text.startswith('EESchema Schematic File'):
        result.update(syntax='legacy_schematic',observed={'header':text.splitlines()[0],'component_count':text.count('$Comp'),'sheet_count':text.count('$Sheet')})
        for line in text.splitlines():
            if line.startswith('LIBS:'):result['references'].append(reference(line[5:],'legacy_library',name,files,project_dir))
            if line.startswith('L '):result['references'].append(reference(line.split()[1],'symbol_identifier',name,files,project_dir))
            match=re.match(r'F\s+2\s+"([^"]+)"',line)
            if match:result['references'].append(reference(match.group(1),'footprint_identifier',name,files,project_dir))
            match=re.match(r'F1\s+"([^"]+)"',line)
            if match and match.group(1).lower().endswith('.sch'):result['references'].append(reference(match.group(1),'schematic_sheet',name,files,project_dir))
        return result
    tree=sx.parse(text);kind=tree[0];nodes=list(walk(tree))
    observed={'root':kind,'version':atom(tree,'version'),'generator':atom(tree,'generator'),'generator_version':atom(tree,'generator_version')}
    if kind=='kicad_pcb':
        fps=sx.children(tree,'footprint')+sx.children(tree,'module');pads=[p for fp in fps for p in sx.children(fp,'pad')]
        layers=sx.one(tree,'layers',[]);zones=sx.children(tree,'zone')
        observed.update(copper_layers=[row for row in layers[1:]if isinstance(row,list)and len(row)>2 and re.fullmatch(r'(F|B|In[0-9]+)\.Cu',sx.unquote(row[1]))],
            footprints=len(fps),legacy_module_count=len(sx.children(tree,'module')),pads=len(pads),pad_shapes=dict(Counter(p[3]for p in pads if len(p)>3)),
            root_net_declarations=sx.children(tree,'net'),net_references=sorted(set(sx.unquote(n[-1])for n in nodes if n and n[0]=='net'and len(n)>1)),
            route_counts={key:len(sx.children(tree,key))for key in ('segment','arc','via')},locked_route_count=sum(any(n=='locked'or isinstance(n,list)and n and n[0]=='locked'for n in r)for key in ('segment','arc','via')for r in sx.children(tree,key)),
            zones=[{k:sx.children(z,k)for k in ('uuid','tstamp','net','net_name','layer','layers','name','keepout','placement','attr','connect_pads','fill')}for z in zones],
            edges=[{'kind':n[0],'node':n}for n in tree if isinstance(n,list)and n and n[0].startswith('gr_')and atom(n,'layer')=='Edge.Cuts'],
            board_setup=sx.one(tree,'setup'),footprint_rulearea_count=sum(bool(sx.children(z,'keepout'))for fp in fps for z in sx.children(fp,'zone')),
            custom_pad_primitives=[sx.children(p,'primitives')for p in pads if len(p)>3 and p[3]=='custom'])
        for fp in fps:result['references'].append(reference(sx.unquote(fp[1]),'footprint_identifier',name,files,project_dir))
    for node in nodes:
        if len(node)<2:continue
        if node[0]=='model':result['references'].append(reference(sx.unquote(node[1]),'model',name,files,project_dir))
        if node[0]=='lib_id':result['references'].append(reference(sx.unquote(node[1]),'symbol_identifier',name,files,project_dir))
        if node[0]=='property'and len(node)>2 and sx.unquote(node[1])in ('Sheetfile','Sheet file','Footprint')and sx.unquote(node[2]):
            prop=sx.unquote(node[1]);result['references'].append(reference(sx.unquote(node[2]),'footprint_identifier'if prop=='Footprint'else 'schematic_sheet',name,files,project_dir))
        if node[0]=='uri':result['references'].append(reference(sx.unquote(node[1]),'library_table_uri',name,files,project_dir))
    if kind in ('fp_lib_table','sym_lib_table'):
        observed['table_entries']=[{'name':atom(n,'name'),'type':atom(n,'type'),'uri':atom(n,'uri')}for n in sx.children(tree,'lib')]
    result['observed']=observed
    return result

def resolve_local_identifiers(refs,analyses,available):
    """Resolve only original explicit local tables; never invent stock aliases."""
    tables=[r for r in analyses if r.get('observed',{}).get('table_entries')]
    for ref in refs:
        if ref['kind']not in ('footprint_identifier','symbol_identifier')or ':'not in ref['original']:continue
        alias,member=ref['original'].split(':',1)
        if not alias or not member or '/'in member or '\\'in member:continue
        table_name='fp-lib-table'if ref['kind']=='footprint_identifier'else 'sym-lib-table'
        directory=PurePosixPath(ref['source_file']).parent;selected=None
        for parent in (directory,*directory.parents):
            name=(parent/table_name).as_posix()
            selected=next((r for r in tables if r['file']==name),None)
            if selected:break
        if not selected:continue
        entries=[r for r in selected['observed']['table_entries']if r['name']==alias]
        if len(entries)!=1:
            ref['reason']='missing or duplicate original local alias';continue
        uri=entries[0]['uri']
        if not isinstance(uri,str):continue
        target=reference(uri,'library_table_uri',selected['file'],set(available),str(directory))
        if not target['resolution'].startswith('local_'):continue
        library=target['target']
        if ref['kind']=='footprint_identifier':
            leaf=library.rstrip('/')+'/'+member+'.kicad_mod'
            exists=leaf in available
        else:
            leaf=library;exists=False
            if leaf in available:
                try:
                    lib=sx.parse(available[leaf].decode('utf-8'))
                    exists=len([n for n in sx.children(lib,'symbol')if len(n)>1 and sx.unquote(n[1])==member])==1
                except (ValueError,UnicodeError):pass
        if exists:ref.update(resolution='explicit_local_member_present',target=leaf,reason='member found through exact original table URI; external/version/native semantics remain unqualified',table=selected['file'])


def notices(name,raw,declared,license_files):
    ext=Path(name).suffix.lower();binary=ext in ('.pdf','.ods','.png','.jpg','.zip')
    text=''if binary else raw.decode('utf-8',errors='replace')
    lines=[{'line':i+1,'text':line[:400]}for i,line in enumerate(text.splitlines())if re.search(r'copyright|SPDX-License-Identifier|licensed? under|creativecommons\.org|Apache License|MIT License|CERN|All Rights Reserved',line,re.I)]
    result={'source_file':name,'declared_repository_basis':declared,'root_grant_evidence':license_files,
        'notice_matches':lines[:32],'notice_matches_truncated':len(lines)>32,'binary_document_not_parsed':binary,
        'file_level_redistribution_review':'pending; root grant is evidence, not automatic clearance of third-party exceptions','redistribution_approved':False}
    if ext in ('.step','.stp'):
        end=text.find('ENDSEC;');header=text[:end+7]if end>=0 else text[:16384]
        result['model_header']={key:re.findall(key+r'\s*\((.*?)\)\s*;',header,re.S)[:2]for key in ('FILE_DESCRIPTION','FILE_NAME','FILE_SCHEMA')}
        result['model_authorship_or_vendor_rights']='unresolved pending human-readable header/adjacent original notice review; no blanket root assumption'
    return result

LINEAGE={
 'ideal-diode':'Four repeated diode-channel circuits and SparkFun template lineage; structural dedup pending.',
 'hstx-pth':'Passive connector breakout/SparkFun template; compare shared connector patterns with prior acquired PMOD, no repository-name independence.',
 'olimex-ice40-dio':'iCE40-HX1K/HX8K extension circuitry lineage; related parent designs and legacy templates require structural comparison.'}

def analyze_project(project,available,expected):
    """Every planned board survives missing/parse-failed sources; no support gate waiver."""
    files=set(available);slug=project['slug'];grant_files=[{'path':n,'sha256':sha(value)}for n,value in available.items()if Path(n).name.upper().startswith(('LICENSE','COPYING','NOTICE'))]
    rights=[notices(n,raw,project['license'],grant_files)for n,raw in sorted(available.items())]
    analyses=[];allrefs=[]
    interesting={'.kicad_pcb','.kicad_pro','.kicad_sch','.pro','.sch','.kicad_dru','.net'}
    for name,raw in sorted(available.items()):
        if Path(name).suffix.lower()not in interesting and Path(name).name not in ('fp-lib-table','sym-lib-table'):continue
        try:info=inspect_native(name,raw,files)
        except (ValueError,UnicodeError,IndexError,TypeError,configparser.Error,RecursionError)as exc:info={'file':name,'parse_error':type(exc).__name__+': '+str(exc),'references':[],'observed':{}}
        analyses.append(info);allrefs.extend(info['references'])
    # Deduplicate references with full original file/kind/URI identity. Never erase their originals.
    unique={json.dumps(r,sort_keys=True):r for r in allrefs};refs=[unique[k]for k in sorted(unique)]
    planned_boards=[row['source_path']for row in expected if row['source_path'].lower().endswith('.kicad_pcb')]
    boards=[]
    for name in planned_boards:
        stem=str(PurePosixPath(name).with_suffix(''));matched_project=next((stem+ext for ext in ('.kicad_pro','.pro')if stem+ext in files),None)
        schematic=next((stem+ext for ext in ('.kicad_sch','.sch')if stem+ext in files),None)
        info=next((x for x in analyses if x['file']==name),None)
        boards.append({'source_file':name,'source_sha256':sha(available[name])if name in files else None,'acquisition_state':'present_verified'if name in files else 'missing_or_invalid',
            'matched_project':matched_project,'matched_schematic':schematic,'rule_file':stem+'.kicad_dru'if stem+'.kicad_dru'in files else None,
            'board_syntax_observation':info,'support_status':'unqualified; current production preflight not run',
            'format_gate':'legacy project observation/migration remains separate'if matched_project and matched_project.endswith('.pro')else 'modern matched syntax is not native compatibility',**FALSE})
    resolve_local_identifiers(refs,analyses,available)
    unresolved=[r for r in refs if r['resolution']=='unresolved']
    repeat=slug in ('ideal-diode','hstx-pth')and any(r['kind']in ('footprint_identifier','symbol_identifier','model')for r in unresolved)
    return {'slug':slug,'repository':project['repository'],'commit':project['commit'],'split':'development','planned_file_count':len(expected),'verified_file_count':len(available),
        'missing_or_invalid_files':[r['source_path']for r in expected if r['source_path']not in files],
        'boards':boards,'native_file_observations':analyses,'file_rights':rights,'references':refs,'unresolved_reference_count':len(unresolved),
        'closure_state':'unresolved'if unresolved or len(available)!=len(expected)else 'static references only; native/version/asset semantics unqualified',
        'stop_repeated_alias_branch':repeat,'stop_reason':'Unresolved library/model identities: preserve authentic URI/version gap; no alias creation or broad crawl.'if repeat else None,
        'lineage_caveat':LINEAGE[slug],'metadata_omission_scope':project['omission_scope'],**FALSE}

def verify_file(row,raw,receipt_row):
    if (type(row['bytes'])is not int or len(raw)!=row['bytes'] or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=row['git_blob_sha1']):raise ValueError('protocol Git blob/size mismatch')
    if row.get('sha256')and sha(raw)!=row['sha256']:raise ValueError('protocol SHA mismatch')
    if not receipt_row:raise ValueError('missing acquired receipt row')
    for key in ('destination','repository','commit','mode','source_path','bytes','git_blob_sha1'):
        if receipt_row.get(key)!=row[key]:raise ValueError('receipt/protocol identity differs: '+key)
    if receipt_row.get('sha256')!=sha(raw):raise ValueError('receipt/source SHA mismatch')

def execute(root,receipt_path,out):
    """Called only after lead announces immutable acquisition, never in default mode."""
    started=time.monotonic();material={n:sha(read_bytes(HERE/n))for n in ('audit.py','sexpr_snapshot.py','protocol.json','existing-data-inventory.json')}
    evidence={}
    p,baseline=plan();receipt_path=owned(root,receipt_path);out=owned(root,out)
    if (receipt_path.name!='receipt.json' or receipt_path.parent.parent!=root/'.runs' or not re.fullmatch(r'licensed-acquisition-004-run-[0-9]{3}',receipt_path.parent.name)):
        raise ValueError('canonical acquisition receipt required')
    if out.parent not in (root/'.runs',HERE)or out.exists():raise ValueError('fresh owned audit output required')
    receipt_raw=read_bytes(receipt_path);receipt=decode(receipt_raw);before=inventory(root/'.data')
    outside={k:v for k,v in before['files'].items()if not k.startswith('expansion004/')}
    if outside!=baseline['files']:raise ValueError('preexisting acquired files changed or extra unrecorded acquisition')
    if receipt.get('protocol_sha256')!=PROTOCOL_SHA or receipt.get('preexisting_inventory_sha256')!=p['baseline_sha256']:raise ValueError('acquisition protocol/baseline differs')
    if any(receipt.get(k)is not False for k in ('native_executed','engine_executed','dependency_closure_verified','redistribution_approved','independent_families_established')):raise ValueError('acquisition scope differs')
    runtime=receipt['runtime'];head=runtime['head'];helper_names=('fetch.py','test_fetch.py','protocol.json','existing-data-inventory.json','README.md','STATIC_AUDIT.md')
    if not re.fullmatch('[0-9a-f]{40}',head)or set(runtime['files'])!=set(helper_names):raise ValueError('helper provenance schema')
    for name in helper_names:
        blob=subprocess.run(['git','show',head+':experiments/licensed_acquisition_v1/'+name],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=3).stdout
        if len(blob)>10*MIB or sha(blob)!=runtime['files'][name]:raise ValueError('committed acquisition helper hash differs')
    requests=receipt.get('requests',[])
    if len(requests)>33 or len({q.get('index')for q in requests})!=len(requests)or len({q.get('destination')for q in requests})!=len(requests):raise ValueError('duplicate/extra request identity')
    receipt_rows={};errors=[]
    for row in receipt.get('files',[]):
        name=row['destination'];safe(name)
        if name in receipt_rows:raise ValueError('duplicate receipt file')
        receipt_rows[name]=row
    planned={r['destination']:r for project in p['projects']for r in project['files']}
    if set(receipt_rows)-set(planned):raise ValueError('extra acquired receipt file')
    actual={k[len('expansion004/'):]:v for k,v in before['files'].items()if k.startswith('expansion004/')}
    if set(actual)-set(planned):raise ValueError('unexpected acquired source path')
    projects=[]
    for project in p['projects']:
        available={}
        for row in project['files']:
            dest=row['destination'];safe(dest)
            try:
                path=owned(root,root/'.data/expansion004'/dest);value=read_bytes(path);verify_file(row,value,receipt_rows.get(dest))
                request=next((q for q in receipt['requests']if q.get('destination')==dest),None)
                if request is None or request.get('url')!=row['raw_url']or request.get('http_status')!=200 or request.get('response_sha256')!=sha(value)or request.get('received_bytes')!=len(value):raise ValueError('network response receipt differs')
                index=request['index']
                if type(index)is not int or not 0<=index<33:raise ValueError('request index')
                response=owned(root,receipt_path.parent/f'response-{index:03}.bin')
                captured_response=read_bytes(response);evidence[response]=sha(captured_response)
                if captured_response!=value:raise ValueError('retained response/source bytes differ')
                available[row['source_path']]=value
            except (ValueError,OSError,KeyError)as exc:errors.append({'destination':dest,'error':type(exc).__name__+': '+str(exc)})
        projects.append(analyze_project(project,available,project['files']))
    complete=(receipt.get('status')=='acquired_unqualified'and not errors and len(actual)==33 and receipt.get('acquired_files')==33 and receipt.get('acquired_bytes')==5016162 and receipt.get('aggregate_data_bytes')==37408570 and receipt.get('aggregate_data_files')==345 and receipt.get('original_inputs_unchanged')is True)
    record={'schema':1,'status':'static_audit_complete'if complete else 'acquisition_incomplete_or_inconsistent_retained','scope':'static original source/notice/reference audit; not support or rights clearance','source_receipt':str(receipt_path),'source_receipt_sha256':sha(receipt_raw),'protocol_sha256':PROTOCOL_SHA,'acquisition_code_head':head,'projects':projects,'acquisition_errors':errors,'acquisition_complete_verified':complete,'considered_projects':3,'planned_boards':sum(len(x['boards'])for x in projects),'actual_verified_boards':sum(b['source_sha256']is not None for x in projects for b in x['boards']),'prior_population_count':16,'new_boards_must_remain_in_population_even_if_unsupported':True,'preexisting_file_count':baseline['file_count'],'preexisting_bytes':baseline['bytes'],'source_files_unchanged':False,'network_requests_by_audit':0,**FALSE}
    # Publication is invalidated if any captured source/receipt/runtime helper changes.
    def stable():
        if inventory(root/'.data')!=before or read_bytes(receipt_path)!=receipt_raw or any(sha(read_bytes(HERE/n))!=h for n,h in material.items()) or any(sha(read_bytes(path))!=h for path,h in evidence.items()):raise ValueError('audit source/receipt/helper changed')
        if time.monotonic()-started>60:raise TimeoutError('60-second audit bound')
    stable();record['source_files_unchanged']=True;record['wall_seconds_sample_before_publication']=time.monotonic()-started
    out.mkdir();target=out/'audit.json'
    try:
        emitted=(json.dumps(record,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()
        if len(emitted)>10*MIB:raise ValueError('audit output cap')
        target.write_bytes(emitted);stable()
        if read_bytes(target)!=emitted:raise ValueError('audit publication changed')
        if time.monotonic()-started>60:raise TimeoutError('final audit bound')
    except BaseException:
        if target.exists():target.rename(out/'audit.invalidated.json')
        raise
    return record

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--audit-acquired',action='store_true');ap.add_argument('--receipt',type=Path);ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    if not args.audit_acquired:
        p,baseline=plan();print(json.dumps({'status':'draft_plan_only','planned_projects':[x['slug']for x in p['projects']],'planned_files':p['planned_files'],'planned_bytes':p['planned_bytes'],'no_expansion004_read':True,'network_requests':0,**FALSE}));return
    if args.receipt is None or args.output is None:ap.error('--receipt and --output required after completed acquisition announcement')
    previous={s:signal.getsignal(s)for s in (signal.SIGINT,signal.SIGTERM)}
    def cancel(*_):raise KeyboardInterrupt
    try:
        for s in previous:signal.signal(s,cancel)
        result=execute(ROOT,args.receipt.absolute(),args.output.absolute());print(json.dumps({k:result[k]for k in ('status','planned_boards','actual_verified_boards','acquisition_complete_verified')}))
    finally:
        for s,h in previous.items():signal.signal(s,h)
if __name__=='__main__':main()
