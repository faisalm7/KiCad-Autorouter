"""Finite shared-helper readback of legacy-zone-controls001; no native jobs."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,importlib.util,json,sys,time
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
HELPER=ROOT/'experiments/legacy_zone_controls_v1';RUN=ROOT/'.runs/legacy-zone-controls-001'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HELPER));sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('legacy_zone_review',HELPER/'driver.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
p=d.p;f=d.f;io=d.io;read=d.shared.read;checks=[]
def ck(value,name):
 checks.append({'check':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def entry(path):return {'bytes':path.stat().st_size,'sha256':p.sha(path)}
def main():
 start=time.monotonic();before=d.capture(RUN);r=read(RUN/'summary.json');protocol=read(HELPER/'PROTOCOL.json');base=ROOT/'fixtures/smoke';base_raw=io.inventory(base,contents=True);base_hashes=d.hashes(base_raw)
 ck(r['status']=='observations_complete' and r['observations_complete'] is True and r['original_inputs_unchanged'] is True and r['within_budget'] is True,'complete observation receipt')
 ck(all(r[x] is False for x in d.FALSE_FLAGS),'all routing/production/native-legacy/dependency/format admission flags false')
 ck(r['tools']['git_head']=='8f9ffeb68ab1e250163ae26214c8d7fd6894adf6' and len(r['steps'])==6,'exact run HEAD and six native stages')
 ck(r['base_sha256']==protocol['base_sha256']==base_hashes and r['protocol_sha256']==p.sha(HELPER/'PROTOCOL.json'),'base source and protocol exact')
 ck(d.capture(RUN/'code')==r['code_inventory'],'complete captured code snapshot')
 for name,digest in r['runtime_sources'].items():ck(p.sha(ROOT/name)==p.sha(RUN/'code'/name)==digest,'live/captured runtime '+name)
 for name,digest in r['tools']['files'].items():ck(p.sha(Path(name))==digest,'pinned tool '+Path(name).name)
 wrapper=Path(protocol['pcbnew_wrapper']['path']);ck(entry(wrapper)=={k:protocol['pcbnew_wrapper'][k] for k in ('bytes','sha256')},'live wrapper declaration pin')
 declaration=wrapper.read_text();ck('Build(CONNECTIVITY_DATA self, BOARD aBoard, PROGRESS_REPORTER * aReporter=None) -> bool' in declaration and 'CONNECTIVITY_DATA_GetPadCount' in declaration,'live connectivity declaration names')
 for pin in protocol['research']:ck(entry(Path(pin['path']))=={k:pin[k] for k in ('bytes','sha256')},'cached source/research '+Path(pin['path']).name)
 research=ROOT/'.runs/legacy-zone-severity-origin-001';source_pins={}
 for row in read(research/'fetch-receipt.json'):
  if row.get('status')==200:
   path=research/row['path'];ck(entry(path)=={k:row[k] for k in ('bytes','sha256')},'retained historical/modern source '+row['path']);source_pins[row['path']]={'url':row['url'],**entry(path)}
 facts=read(research/'facts.json')
 for row in facts['cache'].values():ck(entry(ROOT/row['local_path'])=={k:row[k] for k in ('bytes','sha256')},'current source registry/settings '+row['local_path'])
 ck([x['case'] for x in r['cases']]==list(d.controls.CASES),'exact three-case denominator')
 rows=[]
 for index,row in enumerate(r['cases']):
  case=row['case'];out=RUN/case;board,project=d.controls.derive(base_raw['smoke.kicad_pcb'],base_raw['smoke.kicad_pro'],case);expected=d.hashes(dict(base_raw,**{'smoke.kicad_pcb':board,'smoke.kicad_pro':project}))
  ck(row['source_hashes']==expected==d.capture(out/'observe-input'),'exact reversible fixture recipe '+case)
  actual_project=read(out/'observe-input/smoke.kicad_pro');ck(actual_project=={'meta':{'filename':'smoke.kicad_pro','version':1},'board':{'design_settings':{'rule_severities':{'zone_has_empty_net':'error'}}}},'only declared owned project severity delta '+case)
  case_steps=r['steps'][2*index:2*index+2];ck([s['name'] for s in case_steps]==['observe','drc'],'sequential export/DRC '+case)
  job=SimpleNamespace(out=out,steps=case_steps)
  f.process_check(out,{'steps':case_steps},'observe',f.SANDBOX+d.observer_argv(out))
  ck(d.bind_observation(out,expected,case)==row['predicate'],'same-BOARD source/context/zone/GetPadCount readback '+case)
  ck(d.bind_drc(job,expected)==row['drc'],'nonsaving native input/process/raw report readback '+case)
  ck(d.capture(out/'drc-input')==expected,'all three native input files unchanged '+case)
  for name,stage in row['stage_evidence'].items():
   ck(all(p.sha(out/path)==digest for path,digest in stage['artifacts'].items()),'captured pre-parse report/log/process hashes '+case+'/'+name)
   ck(stage['input']==expected,'captured stage input hashes '+case+'/'+name)
  for s in case_steps:ck(s['cleanup_complete'] is True and not s['log_truncated'] and Path(s['log']).stat().st_size==s['log_bytes'] and s['resource_guards']['max_workdir_bytes']==20*1024**2 and s['resource_guards']['max_group_rss_bytes']==2*1024**3,'actual bounded process cleanup/log '+case+'/'+s['name'])
  raw=read(out/'zones.json');obs=raw['observation_before_export'];zone=obs['zones'][0]
  ck(obs==raw['observation_after_export'] and raw['same_loaded_board'] is True and raw['board_saved'] is False and obs['connectivity_build_succeeded'] is True,'rebuilt direct connectivity same BOARD before/after export '+case)
  count=sum(pad['netcode']==zone['netcode'] for pad in obs['pads']) if zone['netcode']>0 else None;ck(count==zone['pad_count'],'reported count independently matches six exact pad identities '+case)
  native=row['drc']['native'];ck(row['drc']['raw_legacy_findings']==[] and not p.native_accepted(native),'no native legacy category; unrouted candidate never accepted '+case)
  ck((native['opens'],native['blocking'],native['warnings'],native['exclusions'])==[(2,0,0,0),(3,0,1,0),(3,0,1,0)][index],'all raw counters retained '+case)
  rows.append({'case':case,'net':zone['net'],'netcode':zone['netcode'],'native_pad_count':zone['pad_count'],'historical_violation':row['predicate']['historical_violation'],'historical_guard_accepts':row['predicate']['historical_guard_accepts'],'counts':{k:native[k] for k in ('opens','blocking','warnings','exclusions')},'findings':native['findings'],'ignored_checks':native['ignored_checks'],'raw_legacy_findings':[],'report_sha256':row['drc']['report_sha256']})
 outerpath=ROOT/'.runs/legacy-zone-controls-001-execution.json';outer=read(outerpath);log=ROOT/'.runs/legacy-zone-controls-001-command.log';launcher=ROOT/'.runs/run-legacy-zone-controls-001.py'
 ck(outer['git_head']==r['tools']['git_head'] and outer['exit_code']==0 and outer['cleanup_signals']==[] and outer['log_sha256']==p.sha(log) and outer['log_bytes']==log.stat().st_size and outer['wrapper_sha256']==p.sha(launcher),'outer wrapper/hash/cleanup bindings')
 ck(outer['argv']==['python3','-B','experiments/legacy_zone_controls_v1/driver.py','--run-native','--output','.runs/legacy-zone-controls-001'] and outer['cwd']==str(ROOT),'exact whole-run command')
 ck(0<r['wall_seconds']<outer['wall_seconds']<30 and 0<r['total_cpu_seconds']<outer['waited_child_cpu_seconds']<30 and d.shared.size(RUN)<20*1024**2,'full outer wall/CPU and retained output within caps')
 ck(d.capture(RUN)==before and d.capture(base)==base_hashes,'full raw run and original base unchanged during audit')
 result={'schema':1,'passed':True,'checks':checks,'cases':rows,'summary':entry(RUN/'summary.json'),'run_files':len(before),'run_bytes':d.shared.size(RUN),'run_inventory_sha256':d.shared.sha_bytes(json.dumps(before,sort_keys=True).encode()),'base_sha256':base_hashes,'runtime_sources':r['runtime_sources'],'source_pins':source_pins,'stored_seconds':{'wall':r['wall_seconds'],'cpu':r['total_cpu_seconds']},'outer':outer,'audit_seconds':time.monotonic()-start,'native_or_engine_executed_by_audit':False}
 (HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'checks':len(checks),'run_files':len(before),'run_bytes':result['run_bytes'],'audit_seconds':result['audit_seconds']}))
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  (HERE/'failure.json').write_text(json.dumps({'error':type(exc).__name__+': '+str(exc),'checks':checks},indent=2)+'\n');raise
