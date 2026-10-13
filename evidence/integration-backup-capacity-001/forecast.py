"""Read-only existing-backup capacity forecast; no snapshot/archive/Git/native."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
import copy,hashlib,json,os,signal,stat,subprocess,sys,time,shutil
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=next(x for x in HERE.parents if (x/'scripts/backup.py').is_file());sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from scripts import backup as b
start=time.monotonic();cutoff=datetime.now(timezone.utc).isoformat()
def forbidden(*args,**kwargs):raise RuntimeError('Capacity forecast prohibits subprocesses/Git/native/network')
def prescan():
 counts={}
 for scope in b.SCOPES:
  files=dirs=total=0
  for current,children,names in os.walk(ROOT/scope,followlinks=False):
   dirs+=1
   for name in names:
    st=(Path(current)/name).lstat();files+=1;total+=st.st_size
  counts[scope]={'files':files,'directories':dirs,'file_bytes':total}
 return counts
def encoded_size(value):return len((json.dumps(value,indent=2,sort_keys=True)+'\n').encode())
initial=prescan();original_caps={key:getattr(b,key) for key in ('LIMIT','MAX_FILES','MAX_RECEIPT_BYTES','MAX_CHAIN_RECEIPT_BYTES','MAX_CHAIN')};elevated=False
if max(sum(x['files'] for x in initial.values()),sum(x['directories'] for x in initial.values()))>b.MAX_FILES:b.MAX_FILES=140000;elevated=True
with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
 try:current=b.inventory(ROOT)
 except b.BackupError as exc:
  after_failure=prescan()
  if ('file-count ceiling' in str(exc) or 'directory-count ceiling' in str(exc)) and max(sum(x['files'] for x in after_failure.values()),sum(x['directories'] for x in after_failure.values()))>original_caps['MAX_FILES'] and not elevated:
   b.MAX_FILES=140000;elevated=True;current=b.inventory(ROOT)
  else:raise
counts={scope:{'files':0,'directories':0,'file_bytes':0} for scope in b.SCOPES}
for row in current['files']:
 scope=row['path'].split('/',1)[0];counts[scope]['files']+=1;counts[scope]['file_bytes']+=row['size']
for name in current['directories']:counts[name.split('/',1)[0]]['directories']+=1
prefix='.runs/installation-009';install_files=[row for row in current['files'] if row['path'].startswith(prefix+'/')];install_dirs=[name for name in current['directories'] if name==prefix or name.startswith(prefix+'/')]
require=lambda truth,message:truth or (_ for _ in ()).throw(ValueError(message))
require(install_files,'actual retained installation009 missing')
prior_path=ROOT/'.local-backups/checkpoint-20261012T094930Z-5027fbfe1fbf49639151d24e106d18fa/receipt.json'
prior,prior_hash,prior_bytes=b.read_json(prior_path);require(prior_bytes==29878286,'prior receipt byte context changed')
# Serialization forecast uses the existing exact receipt structure and complete
# inventory. No archive or certified source snapshot is created.
def receipt(current,parent=None):
 value={key:copy.deepcopy(prior[key]) for key in ('created_utc','source_root','git_head','git_refs','limitation','excluded','bundle','archive')}
 value.update(schema=1,inventory=current)
 if parent is not None:
  value.update(schema=2,kind='incremental',base_verification=copy.deepcopy(prior.get('base_verification')),
   parent={'name':str(prior_path.relative_to(ROOT/'.local-backups')),'sha256':prior_hash},delta=b.delta_inventory(parent,current))
 return value
current_full_size=encoded_size(receipt(current))
# b.delta_inventory validates actual current inventories with unchanged bounds.
current_incremental=receipt(current,prior['inventory']);current_incremental_size=encoded_size(current_incremental)
forecast_prefix='.runs/installation-010-forecast-only';future={**current,'files':[dict(x) for x in current['files']],'directories':list(current['directories'])}
future['files'] += [dict(row,path=forecast_prefix+row['path'][len(prefix):]) for row in install_files]
future['directories'] += [forecast_prefix+name[len(prefix):] for name in install_dirs]
future['files'].sort(key=lambda x:x['path']);future['directories'].sort();future['total_file_bytes']+=sum(x['size'] for x in install_files)
# Future arithmetic does not waive current backup guards. The exact added rows
# are installation009 shape; one future prefix is fictional, never written.
future_full_size=encoded_size(receipt(future))
# The future delta can be forecast from exact new rows without elevating any
# non-file bound or calling backup creation/extraction.
future_delta={'inventory':{**future,'files':[dict(x,path=forecast_prefix+x['path'][len(prefix):]) for x in install_files],
               'total_file_bytes':sum(x['size'] for x in install_files)},'deleted_files':[],'deleted_directories':[]}
future_incremental=receipt(future);future_incremental.update(schema=2,kind='incremental',base_verification=copy.deepcopy(prior.get('base_verification')),
 parent={'name':'checkpoint-FORECAST-'+('0'*32)+'/receipt.json','sha256':'0'*64},delta=future_delta)
future_incremental_size=encoded_size(future_incremental)
# Existing chain receipts are read-only: no load_chain (archives/Git/restore).
chain=[];path=prior_path;seen=set()
while True:
 require(path not in seen and len(chain)<b.MAX_CHAIN,'prior chain cycle/length');seen.add(path)
 data,hashed,size=b.read_json(path);chain.append({'receipt':str(path.relative_to(ROOT)), 'sha256':hashed,'bytes':size,'schema':data['schema'],'files':len(data['inventory']['files'])})
 if data['schema']==1:break
 path=ROOT/'.local-backups'/data['parent']['name']
 require(data['parent']['sha256']==b.digest(path),'prior parent receipt hash differs')
chain.reverse();disk=shutil.disk_usage(ROOT)
result={'schema':1,'status':'read_only_forecast_not_certified_snapshot','started_cutoff_utc':cutoff,'finished_utc':datetime.now(timezone.utc).isoformat(),'wall_seconds':time.monotonic()-start,
 'no_exclusions_added':True,'no_evidence_deleted':True,'native_git_network_or_subprocess_executed':False,'tracked_or_global_caps_changed':False,
 'existing_caps':original_caps,'in_memory_MAX_FILES':b.MAX_FILES,'in_memory_elevated_only_if_actual_count_exceeded':elevated,
 'pre_hash_stat_population':initial,'actual_shared_inventory_population':counts,'actual_inventory':{'files':len(current['files']),'directories':len(current['directories']),'file_bytes':current['total_file_bytes'],'absent_scopes':current['absent_scopes'],'canonical_sha256':hashlib.sha256(json.dumps(current,sort_keys=True,separators=(',',':')).encode()).hexdigest()},
 'prior_receipt':{'path':str(prior_path.relative_to(ROOT)),'sha256':prior_hash,'bytes':prior_bytes,'files':len(prior['inventory']['files']),'directories':len(prior['inventory']['directories']),'file_bytes':prior['inventory']['total_file_bytes']},
 'existing_chain_receipts':chain,'existing_chain_receipt_bytes':sum(x['bytes'] for x in chain),
 'retained_installation009':{'prefix':prefix,'files':len(install_files),'directories':len(install_dirs),'file_bytes':sum(x['size'] for x in install_files),'result_sha256':b.digest(ROOT/prefix/'result.json'),'result_fields':{k:json.loads((ROOT/prefix/'result.json').read_text()).get(k) for k in ('status','passed','accepted','head','git_head','tests')}},
 'one_installation009_shape_addition_forecast':{'prefix':forecast_prefix,'files':len(future['files']),'directories':len(future['directories']),'file_bytes':future['total_file_bytes'],'full_receipt_bytes':future_full_size,'incremental_from_current_receipt_bytes':future_incremental_size,'shape_assumption':'One extra complete retained installation009 tree, unchanged size/content distribution. Current source/evidence growth and different install behavior may increase it; not actual future installation proof.'},
 'receipt_serialization_forecast':{'current_full_bytes':current_full_size,'current_incremental_from_latest_bytes':current_incremental_size,'current_delta_files':len(current_incremental['delta']['inventory']['files']),'current_delta_file_bytes':current_incremental['delta']['inventory']['total_file_bytes'],'metadata_assumption':'Existing exact receipt metadata reused; unknown future bundle/archive hashes/sizes/head/time are small unmeasured metadata differences. Full inventories and actual path lengths preserved; forecast names explicitly fictional.'},
 'disk':{'free_bytes':disk.free,'total_bytes':disk.total,'note':'Filesystem capacity at cutoff, not a reservation. Archive compressed size and restored Git checkout/bundle must be measured by actual backup/restore.'},
 'concurrency_limit':'Other .runs writers may run during the inventory; per-file shared guard checks pass, but no second complete inventory equality or Git-state certification occurred. This is a cutoff forecast only, not a backup or completed restoration.'}
(HERE/'facts.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
