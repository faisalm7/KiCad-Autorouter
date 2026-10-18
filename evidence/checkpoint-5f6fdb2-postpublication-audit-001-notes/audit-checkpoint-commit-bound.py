import hashlib,json,re,subprocess,sys
from pathlib import Path
label=sys.argv[1]
def git(*args):return subprocess.check_output(['git',*args])
postpublication='--committed-parent' in sys.argv[2:]
commit=git('rev-parse','HEAD').decode().strip()
files=git('diff','--name-only',commit+'^',commit,'-z').decode().strip('\0').split('\0') if postpublication else git('diff','--cached','--name-only','-z').decode().strip('\0').split('\0')
assert files and files!=['']
rows=[]
for name in files:
 assert not any(v in Path(name).parts for v in ('.runs','.data','.tools','.local-reference','.local-backups','.private','secrets','.venv'))
 assert Path(name).suffix not in ('.jar','.zip','.gz','.bundle','.pem','.key','.p12','.pfx')
 entry=(git('ls-tree',commit,'--',name) if postpublication else git('ls-files','-s','--',name)).decode().split()
 if not entry:
  previous=git('show',(commit+'^:' if postpublication else 'HEAD:')+name);rows.append({'path':name,'action':'delete public duplicate only','previous_sha256':hashlib.sha256(previous).hexdigest(),'bytes':0});continue
 mode=entry[0];assert mode in ('100644','100755')
 raw=git('show',(commit+':' if postpublication else ':')+name);assert len(raw)<4*1024*1024
 if b'\0' in raw:
  assert name=='evidence/runtime022-thermal-export-control-001-notes/export/validation/candidate/tux.bmp'
  manifest=json.loads(git('show',(commit+':' if postpublication else ':')+'data/sources.json'));fixture=next(x for x in manifest['files'] if x['destination']=='boards/kicad-interf-u/tux.bmp')
  assert fixture['sha256']=='89a17e4b73847e9afddfa1ce25619b4d7e12b61063a9ebe972e9351ccbd181a4' and fixture['bytes']==185814
  assert hashlib.sha256(raw).hexdigest()==fixture['sha256'] and len(raw)==fixture['bytes'] and raw[:2]==b'BM'
  assert fixture['license']=='CC-BY-SA-4.0' and fixture['additional_attribution']=='Tux artwork: Larry Ewing and The GIMP; retain this attribution with artwork and native conversions.'
  assert 'Larry Ewing and The GIMP' in git('show',(commit+':' if postpublication else ':')+'evidence/runtime022-thermal-export-control-001-notes/SCOPE.md').decode()
  rows.append({'path':name,'sha256':fixture['sha256'],'bytes':len(raw),'binary_exception':'Exact public KiCad demo Tux asset, not runtime binary; source license and artwork attribution retained.'});continue
 text=raw.decode('utf-8')
 for pat in (r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'gh[pousr]_[A-Za-z0-9]{30,}',r'github_pat_[A-Za-z0-9_]{30,}',r'AKIA[A-Z0-9]{16}',r'sk-[A-Za-z0-9]{40,}'):
  assert not re.search(pat,text),('sensitive-pattern',name)
 rows.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
branch=git('branch','--show-current').decode().strip();assert branch=='rebuild/local-20261010-015447'
assert git('remote','get-url','origin').decode().strip()=='https://github.com/faisalm7/KiCad-Autorouter.git'
history=git('log','--format=%H','origin/'+branch+'..HEAD').decode().splitlines()
assert not history,history
result={'passed':True,'postpublication_audit':postpublication,'git_head':commit,'files':rows,'rights':'Manually reviewed project-owned source/tests/docs and small diagnostic evidence; official copied demo settings CC BY-SA4.0 with source/notices recorded. Reviewed layer-mask basis includes seven unchanged upstream GPL3 source files with exact revision provenance and complete license/notices. No bulk datasets, private inputs, downloaded engine binaries or credentials.','new_history':history}
Path('.runs/staged-audit-'+label+'.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':True,'files':len(rows),'bytes':sum(r['bytes'] for r in rows)}))
