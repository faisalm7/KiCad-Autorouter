"""Exact selected public/raw byte comparison; no native or network."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
rows=[];seen=set();total=0
for name in ('pic-custom-observation-001','pic-core-placement-regression-001'):
    directory=ROOT/'evidence'/name;manifest=json.loads((directory/'public-copy.json').read_text());listed=set()
    for entry in manifest['files']:
        a,b=ROOT/entry['source'],ROOT/entry['public']
        assert b.is_relative_to(directory) and entry['public'] not in seen and not a.is_symlink() and not b.is_symlink()
        seen.add(entry['public']);listed.add(str(b.relative_to(directory)))
        assert a.stat().st_size==b.stat().st_size==entry['bytes']<32*1024*1024
        aa,bb=a.read_bytes(),b.read_bytes();digest=hashlib.sha256(aa).hexdigest()
        assert aa==bb and digest==entry['sha256'];total+=len(bb)
        rows.append({'source':entry['source'],'public':entry['public'],'bytes':len(bb),'sha256':digest,'exact':True})
    actual={str(x.relative_to(directory)) for x in directory.rglob('*') if x.is_file()}
    assert actual==listed|{'PUBLIC_SCOPE.md','public-copy.json'}
    for license in ('LICENSE.README','LICENSE.CC-BY-SA-4.0'):
        assert '_licenses/'+license in listed
    text=(directory/'PUBLIC_SCOPE.md').read_text()
    assert 'CC BY-SA4.0' in text and 'complete raw' in text
receipt=json.loads((ROOT/'.runs/pic-custom-observation-001-execution.json').read_text())
assert receipt['controller_exit_code_measured'] is None and receipt['tool_shell_exit_code']==0
assert receipt['command_log_sha256']==hashlib.sha256((ROOT/'.runs/pic-custom-observation-001-command.log').read_bytes()).hexdigest()
assert receipt['git_head']=='9300c75a4e70b29a3f919edc5cb3ed0ee3566e3e'
result={'schema':1,'status':'passed','files':rows,'file_count':len(rows),'bytes':total,'execution_wrapper_bound':True,'rights_scope':'Both original notices and exact upstream demo commit retained. Original LICENSE.README explicitly assigns demos/* CC BY-SA4.0. These selected files are native observations/settings/DSN or owned-fixture evidence; complete project copies, installed tools and source snapshots remain local. This is a byte/provenance scope audit, not a new license opinion or self-contained restoration test.','native_or_engine_executed':False}
(HERE/'public-copy-audit-001.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','file_count','bytes')}))
