"""Exact packaging/backup diff review and one isolated existing basis test."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,shutil,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));OUT=Path(__file__).resolve().parent
j=lambda path:json.loads(path.read_text());sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
checks=[]
def require(name,ok):checks.append({'check':name,'passed':bool(ok)});assert ok,name
basis=ROOT/'evidence/layer-mask-basis-001';meta=j(basis/'provenance.json')
old=ROOT/'.runs/installation-005/checkout/scripts/probe_engine_profiles.py';new=ROOT/'scripts/probe_engine_profiles.py'
def assignment(path,key):
 for n in ast.parse(path.read_text()).body:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==key for t in n.targets):return ast.literal_eval(n.value)
 raise AssertionError(key)
oldpins=assignment(old,'LAYER_BASIS');newpins=assignment(new,'LAYER_BASIS')
def omit_basis(path):
 tree=ast.parse(path.read_text());tree.body=[n for n in tree.body if not(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='LAYER_BASIS' for t in n.targets))];return ast.dump(tree)
require('probe runtime AST unchanged except basis constants',omit_basis(old)==omit_basis(new))
require('14 old records plus3 notices',len(meta['files'])==14 and len(oldpins)==15 and len(newpins)==18)
source_records=[]
for rec in (ROOT/'.runs/optimizer-budget-research-001/sources.json',ROOT/'.runs/baseline-strength-review-001/sources.json',ROOT/'.runs/baseline-strength-review-001/additional-sources.json'):source_records.extend(j(rec))
java=[]
for entry in meta['files']:
 original=ROOT/entry['original_local_path'];public=ROOT/entry['public_path']
 require('exact original/public '+public.name,original.read_bytes()==public.read_bytes() and sha(public)==entry['sha256']==oldpins[entry['original_local_path']]==newpins[entry['public_path']] and public.stat().st_size==entry['bytes'])
 if entry['kind']=='unmodified upstream source':
  prior=[r for r in source_records if r.get('local',r.get('path'))==entry['original_local_path']]
  require('upstream original acquisition pin '+public.name,len(prior)==1 and prior[0]['url']==entry['url'] and prior[0]['sha256']==entry['sha256'] and '/'+meta['commit']+'/' in entry['url'])
  require('Java source text no binary '+public.name,public.suffix=='.java' and '\x00' not in public.read_text())
  java.append(entry['public_path'])
require('seven unmodified Java source files',len(java)==7)
license=meta['license'];raw=(basis/license['file']).read_bytes()
require('GPL3 license pin',hashlib.sha256(raw).hexdigest()==license['sha256']==newpins[str((basis/license['file']).relative_to(ROOT))] and len(raw)==license['bytes']==35121 and b'Version 3, 29 June 2007' in raw and b'4. Conveying Verbatim Copies.' in raw and license['url'].endswith('/'+meta['commit']+'/LICENSE'))
require('new notice/provenance pins',all(sha(ROOT/name)==want for name,want in newpins.items()) and meta['engine_binary_included'] is False and meta['source_modified'] is False)
# Reuse exact test against evidence-only copies: no private .runs basis is available.
spec=importlib.util.spec_from_file_location('review_existing_basis_test',ROOT/'tests/test_layer_mask_probe.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
variants=[]
for variant in ('complete','missing-javap'):
 dest=OUT/('isolated-'+variant);dest.mkdir(exist_ok=False)
 for name in newpins:
  if variant=='missing-javap' and name.endswith('/javap.log'):continue
  target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
 require(variant+' no private research directory',not(dest/'.runs').exists())
 with patch.object(t,'ROOT',dest):
  try:t.Layers('test_exact_retained_dsn_and_basis').debug();outcome='passed'
  except FileNotFoundError:outcome='missing-file rejected'
 require(variant+' existing strict test outcome',outcome==('passed' if variant=='complete' else 'missing-file rejected'));variants.append({'variant':variant,'result':outcome})
# Compare all prior backup AST, changing only the intended constant/messages.
backup=ROOT/'scripts/backup.py';oldbackup=ROOT/'.runs/installation-005/checkout/scripts/backup.py'
a=ast.parse(oldbackup.read_text());b=ast.parse(backup.read_text())
class Normalize(ast.NodeTransformer):
 def visit_Assign(self,node):
  if any(isinstance(x,ast.Name) and x.id=='LIMIT' for x in node.targets):node.value=ast.Constant(0)
  return self.generic_visit(node)
 def visit_Constant(self,node):
  if isinstance(node.value,str):node.value=node.value.replace('2 GiB','CAP GiB').replace('3 GiB','CAP GiB')
  return node
require('backup only cap/messages AST change',ast.dump(Normalize().visit(a))==ast.dump(Normalize().visit(b)))
limits={n.targets[0].id:ast.unparse(n.value) for n in ast.parse(backup.read_text()).body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('LIMIT','MAX_FILES','MAX_CHAIN','MAX_RECEIPT_BYTES','MAX_CHAIN_RECEIPT_BYTES')}
require('finite 3GiB and unchangedotherbounds',limits=={'LIMIT':'3 * 1024 ** 3','MAX_FILES':'100000','MAX_CHAIN':'16','MAX_RECEIPT_BYTES':'32 * 1024 ** 2','MAX_CHAIN_RECEIPT_BYTES':'128 * 1024 ** 2'})
failed=j(ROOT/'.runs/installation-005/result.json');log=ROOT/'.runs/installation-005/13-tests.log'
require('failed005 retained no native',failed['passed'] is False and failed['status']=='failed' and len(failed['commands'])==14 and failed['reason']=='RuntimeError: tests: nonzero_exit exit=1' and not(ROOT/'.runs/installation-005/native').exists())
require('608test actual missingignoredfile',"Ran 608 tests" in log.read_text() and 'FileNotFoundError' in log.read_text() and '/checkout/.runs/layer-mask-api-001/javap.log' in log.read_text() and 'FAILED (errors=1)' in log.read_text())
v=os.statvfs(ROOT);available=v.f_bavail*v.f_frsize
result={'all_passed':True,'checks':checks,'source_pins':{str(p.relative_to(ROOT)):sha(p) for p in (new,backup,ROOT/'tests/test_layer_mask_probe.py',basis/'provenance.json',basis/'NOTICE.md',basis/'LICENSE.freerouting')},'isolated_existing_test':variants,'license_scope':'Exact seven unmodified upstream source files, pinned repository GPL3 text and local source acquisition records; original files preserved including all existing notices. No engine binary shipped. No new legal or native qualification claim.','backup_limits':limits,'available_project_volume_bytes':available,'failed_install005':{'receipt_sha256':sha(ROOT/'.runs/installation-005/result.json'),'tests_log_sha256':sha(log),'scratch_bytes':failed['scratch_bytes'],'passed':False,'native_run_reached':False},'native_executed':False,'jvm_executed':False,'network_executed':False,'full_suite_executed':False}
(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'all_passed':True,'checks':len(checks),'isolated_test':variants,'available_project_volume_bytes':available,'source_pins':result['source_pins']}))
