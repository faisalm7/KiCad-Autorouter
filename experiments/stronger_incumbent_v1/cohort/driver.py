"""Fresh exposed stronger-stock cohort B2 versus existing C/chains; no general gain claim.
SPDX-License-Identifier: GPL-3.0-or-later
One command per arm; read/report are pure and never rerun a solver or Native.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
from decimal import Decimal
import importlib.util
import argparse,contextlib,fcntl,hashlib,json,os,re,signal,stat,subprocess,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,strategy as s,handoff as h,placement_clearance as io,sexpr as sx,local_settings as ls,engine_angle
from autorouter.runner import run
from scripts import experiment_quality as q
from autorouter import schematic_field_evidence as fields,adapter as dsn
from experiments.original_project_native_v1.driver import route_records
from experiments.native_paired_v1 import observations as obs,readback as rb
from experiments.hfe_original_native_v1 import driver as shared
from experiments.stronger_incumbent_v1 import native_control as owned
PREP=ROOT/'.runs/stronger-incumbent-cohort-preparation-001';PROTOCOL=PREP/'protocol.json'
OUT=ROOT/'.runs/stronger-incumbent-cohort-command-001';TIMING=ROOT/'.runs/stronger-incumbent-cohort-timing-001'
READ=ROOT/'.runs/stronger-incumbent-cohort-read-001';REPORT=ROOT/'.runs/stronger-incumbent-cohort-report-001'
TABLE=Path(__file__).with_name('case-table.json')
CASE_CONFIG=Path(__file__).with_name('case_config.py')
TABLE_SHA='deaf8731e4697666dbf6a9919763cf9e92bad3993b46a48a8b7e7c94598007e0'
CASES=f.read_json(TABLE)['cases']
PROJECTS=('sonde','nus-usb-led','push-button-led','ds18b20','arcdice')
ARMS=('B2_stronger','C_stronger')
METHODS=ARMS
KIND='fresh-stronger-stock-cohort-v1'
ORDER=[(project,name) for project in PROJECTS if CASES[project]['scope']['private_policy'] is not None for name in ARMS]
POPULATION=[(project,name) for project in PROJECTS for name in ARMS]
STAGES={project+'--'+name:(project,name) for project,name in ORDER}
GATE_PUBLIC=ROOT/'evidence/stronger-cohort-original-gates-001.json'
GATE_MODULE=ROOT/'.runs/stronger-cohort-original-gates-support-001/driver.py'
GATE_HEAD='70412262cae51c2933f9fe48757dae05452a613f'
GATE_MODULE_SHA='202c0d675b7194752244a4a6b3d8f28946d5dbde8c4f162cf026df34db5a943b'
CONTROL_PUBLIC=ROOT/'evidence/global-min-width-native-qualified-001.json'
CONTROL_PUBLIC_SHA='2192a306569e5f42d8a640d7d58ceaca48dcbb7ba6e282ce576c8442de851cc5'
LIMITS=dict(route=120,worker=180,delivered=240,output=128*1024**2,rss=4*1024**3,log=256*1024,publication=2,reader=90,report=30)
COMMAND=Path(__file__).with_name('command.py')
ENCLOSURES=ROOT/'.runs/stronger-incumbent-cohort-enclosures-001'

HELPERS=[str(COMMAND.relative_to(ROOT)),str(TABLE.relative_to(ROOT)),str(CASE_CONFIG.relative_to(ROOT)),'scripts/experiment_quality.py','scripts/fetch_led_demo.py','experiments/native_paired_v1/observations.py','experiments/native_paired_v1/readback.py',
 'experiments/hfe_original_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py','experiments/stronger_incumbent_v1/native_control.py',
 'experiments/stronger_incumbent_v1/matched_ir/driver.py','experiments/fanout_baseline_v1/clearance_control.py','experiments/fanout_baseline_v1/clearance_fixture.py','experiments/fanout_baseline_v1/fixture.py',
 'experiments/free_angle_baseline_v1/fixture.py','experiments/native_schematic_transport_v1/fixture.py']

def control(pin):
 # Reuse the completed owned controls. Only the explicitly named producer
 # Git metadata differs; all current core and binary bytes must match v2.
 from experiments.stronger_incumbent_v1 import global_width_control as width
 def require(ok,msg):
  if not ok:raise p.Rejected(msg)
 require(pin==CONTROL_PUBLIC_SHA and p.sha(CONTROL_PUBLIC)==pin,'fixed qualified width receipt differs')
 public=f.read_json(CONTROL_PUBLIC);files={};literals={};materials={};prl=[]
 def retain(path,digest=None):
  path=Path(path);actual=p.sha(path);require(digest is None or actual==digest,'retained prerequisite bytes differ: '+str(path))
  name=str(path.relative_to(ROOT));files[name]=actual
  if path.suffix=='.json':literals[name]=f.canonical(f.read_json(path))
  return f.read_json(path) if path.suffix=='.json' else None
 retain(CONTROL_PUBLIC,pin)
 require(public['whole_qualification_passed'] is True and public['all_prior_failed_aggregates_retained'] is True
  and public['positive_git_head']=='0c3bc8424258d01ec9b7d2da8ec0a9921b4160d7'
  and public['negative_git_head']=='5949f6be17dbf31be7bf69e8805739138b35c69b','qualified producer identities differ')
 for name,digest in public['files_sha256'].items():retain(ROOT/name,digest)
 positive_plan=retain(width.PROTOCOL,'38f1eeeff584938961b1cbb517adad28114850cc28fec55f83cfaf697dd82159')
 negative_path=ROOT/'.runs/global-min-width-native-preparation-002/protocol.json'
 negative_plan=retain(negative_path,'f3d6f7f4fff6f15e46768826d69b00eb04532c31726d2593a4ef55071308afbb')
 control_name='experiments/stronger_incumbent_v1/global_width_control.py'
 require(p.sha(ROOT/control_name)=='bb0a2ae9e9362734f7ba5733d6c1b8edb05f9d24cbb94f3cb0433b066a258f5c','reviewed current width checker differs')
 for plan,head in ((positive_plan,public['positive_git_head']),(negative_plan,public['negative_git_head'])):
  current=p.tool_manifest()
  require(plan['git_head']==head and dict(plan['tools'],git_head=current['git_head'])==current,'only exact historical Git metadata may differ; core/binaries must match')
  require(p.tree_hash(width.PREP/'source')==positive_plan['source_sha256'],'owned original source changed')
  for name,digest in plan['code_sha256'].items():
   if name==control_name:
    expected='273a0823f440fd5e0c94d0d439408872c4b299c506e7c62f222d884482252a88' if plan is positive_plan else '14c369271a89c5734c9cb46a63577113139245ac94391b77a72c456694fb59c9'
    require(digest==expected,'unknown historical diagnostic code')
    retain(ROOT/name,'bb0a2ae9e9362734f7ba5733d6c1b8edb05f9d24cbb94f3cb0433b066a258f5c')
   else:retain(ROOT/name,digest)
 for name,digest in negative_plan['prior']['files_sha256'].items():
  if name==control_name:
   require(digest=='14c369271a89c5734c9cb46a63577113139245ac94391b77a72c456694fb59c9','unknown pre-correction source')
  else:retain(ROOT/name,digest)
 # Explicit fixed snapshots and reviewed controller-only corrections. Native
 # and core methods are unchanged; no old context/clean-HEAD waiver is called.
 retain(ROOT/'.runs/global-min-width-negative-warning-correction-001/global_width_control-before-warningfix.py','14c369271a89c5734c9cb46a63577113139245ac94391b77a72c456694fb59c9')
 delta=retain(ROOT/'.runs/global-min-width-negative-warning-source-delta-001.json','388429e960b6c60260f333045403960728b3d882c7ec0e6aec5e8781da8d4f81')
 require(all(delta['unchanged_functions_AST'].values()) and delta['changed_functions']==['check_negative']
  and delta['added_functions']==['negative_warning_population'],'reviewed negative-only correction differs')
 for number in ('001','002'):
  directory=ROOT/('.runs/global-min-width-native-'+number);raw=retain(directory/'result.json')
  require(raw['accepted'] is False and raw['passed'] is False and raw['status']=='failed'
   and raw['completed_evidence']==shared.material(directory),'failed control aggregate/material changed')
  materials[str(directory.relative_to(ROOT))]=raw['completed_evidence']
 positive=width.check_positive(positive_plan)
 require(p.sha(width.OUT/'route/result.json')==negative_plan['prior']['positive_receipt_sha256'],'historical positive receipt changed')
 width.check_settings(positive_plan,negative_plan['prior']['getter'])
 complete=retain(ROOT/public['readback']['path'],public['readback']['receipt_sha256'])
 require(complete['passed'] is True and complete['status']=='completed' and complete['native_executed'] is False
  and complete['jvm_executed'] is False and complete['engine_executed'] is False
  and complete['positive_git_head']==positive_plan['git_head'] and complete['negative_git_head']==negative_plan['git_head'], 'actual pure completion differs')
 negative=complete['negative'];negplan=dict(positive_plan,git_head=negative_plan['git_head'],tools=negative_plan['tools'])
 width.check_negative(negplan,negative,output=ROOT/'.runs/global-min-width-native-002')
 prl.extend([dict(directory=str((width.OUT/'route').relative_to(ROOT)),data=positive),
  dict(directory='.runs/global-min-width-native-002/undersized-job',data=dict(schema=1,steps=negative['steps'],source_hashes=negative['before'],tools=negplan['tools']))])
 require(max(public['readback']['total_including_all_failures_and_curation'].values())<180,'historical complete control costs exceed180')
 # The older v1 control is retained historical evidence, not recertified as a
 # current whole-route result after the explicitly versioned v2 core addition.
 # Replay its actual Native original-rule checks and complete raw witnesses;
 # current v1/no-width behavior also has regression controls and is measured
 # prospectively by DS18 in this cohort, never borrowed as a free incumbent.
 v1=retain(ROOT/'evidence/stronger-incumbent-native-001.json','301515fe9c017cadb9819b40c71d5fa4e1a8c72fe38b4e9fee7d204dbc22993a')
 for name,digest in v1['raw_evidence_sha256'].items():retain(ROOT/name,digest)
 v1plan=f.read_json(owned.PROTOCOL);v1raw=f.read_json(owned.OUT/'result.json')
 from experiments.stronger_incumbent_v1.matched_ir import driver as old_pair
 external=old_pair.control_external(v1plan,p.sha(owned.OUT/'result.json'),v1raw)
 for name,digest in external['files_sha256'].items():retain(ROOT/name,digest)
 require(v1plan['tools']['files']==current['files'],'historical v1 binaries/JAR differ from current pinned files')
 require(v1raw['passed'] is True and v1raw['status']=='completed' and v1raw['git_head']==v1plan['git_head']==v1['producer_git_head']
  and v1plan['policy']==s.STRONG_INCUMBENT_POLICY and shared.material(owned.OUT)==v1raw['completed_evidence'],'historical v1 control/material differs')
 materials[str(owned.OUT.relative_to(ROOT))]=v1raw['completed_evidence']
 old=f.read_json(owned.OUT/'route/result.json');board=Path(old['candidate'])
 checked=f.check_drc_stage(owned.OUT/'route',old,'final-drc',board,owned.OUT/'route/final-drc-input'/board.name,False,p.tree_hash(board.parent),schematic_parity=True,sandboxed=False)
 require(checked==old['native'] and p.native_accepted(checked),'historical v1 actual final Native differs')
 owned.check_negative(v1plan,v1raw['physical_short'])
 require(s._incumbent_route_options(s.STRONG_INCUMBENT_POLICY,'via_default')==dict(_fanout_enabled=False,_optimizer_enabled=False,_engine_clearance_margin_nm=20000),'current v1 option defaults changed')
 prl.extend([dict(directory=str((owned.OUT/'route').relative_to(ROOT)),data=old),
  dict(directory=str((owned.OUT/'invalid-job').relative_to(ROOT)),data=dict(schema=1,steps=v1raw['physical_short']['steps'],source_hashes=v1raw['physical_short']['before'],tools=v1plan['tools']))])
 binding=dict(receipt_sha256=pin,files_sha256=files,literals=literals,materials=materials,prl=prl,
  v1_scope='Historical actual Native controls only; current complete-route replay not asserted. Fresh DS18 arm measures current unchanged v1 defaults.',
  historical_complete_costs=public['readback'],v1_complete_costs=v1['complete_external_costs'])
 control_prl(binding)
 return dict(git_head=current['git_head'],tools=current),binding

def control_prl(binding):
 if (any(p.sha(ROOT/name)!=digest for name,digest in binding['files_sha256'].items())
     or any(shared.material(ROOT/name)!=witness for name,witness in binding['materials'].items())
     or any(f.canonical(f.read_json(ROOT/name))!=literal for name,literal in binding['literals'].items())):
  raise p.Rejected('owned prerequisite complete immutable witnesses changed')
 for row in binding['prl']:
  ls.check_normal_policy(ROOT/row['directory'],row['data'],max_bytes=LIMITS['output'],max_files=2048)

def same_transport(historical,current):
 if historical.get('git_head')!=GATE_HEAD or dict(historical,git_head=current['git_head'])!=current:
  raise p.Rejected('historical/current Native/core/tool bytes differ; only named producer metadata may differ')

def original_gate(project,public_pin):
 case=CASES[project];board=Path(case['source']);files={};literals={};materials={}
 def remember(path):
  path=Path(path);files[str(path.relative_to(ROOT))]=p.sha(path)
  if path.suffix=='.json':literals[str(path.relative_to(ROOT))]=f.canonical(f.read_json(path))
 if project in ('sonde','nus-usb-led'):
  if p.sha(GATE_PUBLIC)!=public_pin or p.sha(GATE_MODULE)!=GATE_MODULE_SHA:raise p.Rejected('fixed public source gate/helper pin differs')
  public=f.read_json(GATE_PUBLIC);entry=public['cases'][project]
  if (public['kind']!='qualified-missing-original-source-gates' or public['whole_external_cost_qualified'] is not True
      or public['producer_git_head']!=GATE_HEAD or entry['producer_git_head']!=GATE_HEAD or entry['gate_passed'] is not True):
   raise p.Rejected('exact704 qualified original gate required')
  remember(GATE_PUBLIC)
  for name,digest in public['files_sha256'].items():
   if p.sha(ROOT/name)!=digest:raise p.Rejected('public original process/log/timing/source witness differs')
   files[name]=digest
  protocol=ROOT/entry['protocol'];plan=f.read_json(protocol);path=ROOT/entry['producer_receipt'];record=f.read_json(path)
  readerpath=ROOT/entry['pure_receipt'];reader=f.read_json(readerpath)
  for file in (protocol,path,readerpath):remember(file)
  if (p.sha(protocol)!=entry['protocol_sha256'] or p.sha(path)!=entry['producer_receipt_sha256']
      or p.sha(readerpath)!=entry['pure_receipt_sha256'] or plan['git_head']!=GATE_HEAD or plan['case']!=project
      or record['git_head']!=GATE_HEAD or record['protocol_sha256']!=p.sha(protocol)
      or record['passed'] is not True or record['status']!='completed' or record['gate_passed'] is not True or record['accepted'] is not False
      or record['completed_evidence']!=shared.material(path.parent) or reader['passed'] is not True or reader['status']!='completed'
      or reader['gate_passed'] is not True or reader['git_head']!=GATE_HEAD or reader['protocol_sha256']!=p.sha(protocol)
      or reader['producer_receipt_sha256']!=p.sha(path) or reader['producer_literal']!=f.canonical(record)
      or reader['producer_material']!=shared.material(path.parent) or reader['completed_evidence']!=shared.material(readerpath.parent)
      or plan['source']!=str(board) or plan['freeze']['source_hashes']!=case['source_sha256']
      or entry['source']!=str(board) or entry['source_sha256']!=case['source_sha256']):
   raise p.Rejected('completed original producer/readback/source binding differs before adoption')
  same_transport(plan['tools'],p.tool_manifest())
  if entry['code_sha256']!=plan['code_sha256'] or any(p.sha(ROOT/n)!=v for n,v in plan['code_sha256'].items()):
   raise p.Rejected('named original-gate source/core/helper changed')
  spec=importlib.util.spec_from_file_location('retained_cohort_original_gate',GATE_MODULE);gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
  if project=='nus-usb-led' and gate.old_nus(plan['tools'])!=plan['old_drc_reference']:
   raise p.Rejected('original NUS raw DRC/process/input/material differs from stored reference')
  gate.check_worker(plan,record) # Deliberately no old context/shared.clean.
  native=json.loads(f.canonical(record['native'] if project=='sonde' else plan['old_drc_reference']['raw_native']))
  if project=='nus-usb-led':
   native['field_parity']=dict(schema=1,policy=fields.POLICY,qualification=record['supplement']['qualification'])
   # Comparison view of actual old DRC + new retained original field proof.
   # No old file or receipt is rewritten/relabelled.
  if not p.native_accepted(native) or {k:native[k] for k in ('opens','blocking','warnings','exclusions')}!=entry['native_counts']:
   raise p.Rejected('qualified original native findings/counts differ')
  for stage in ('prepare','run','read'):
   folder=ROOT/'.runs/stronger-cohort-original-gates-001'/project/stage
   materials[str(folder.relative_to(ROOT))]=shared.material(folder)
  if project=='nus-usb-led':
   old=case['original_aggregate'];remember(ROOT/old['path']);raw=f.read_json(ROOT/old['path'])
   if p.sha(ROOT/old['path'])!=old['sha256'] or raw['status']!='failed' or raw['accepted'] is not False:
    raise p.Rejected('old failed NUS aggregate was replaced')
   materials[str(Path(old['path']).parent)]=shared.material((ROOT/old['path']).parent)
  gate.prl_last(plan,record)
 else:
  aggregate=case['original_aggregate'];path=ROOT/aggregate['path'];record=f.read_json(path);remember(path)
  if p.sha(path)!=aggregate['sha256'] or record['status']!=aggregate['status'] or record['accepted'] is not False:
   raise p.Rejected('literal original aggregate disposition changed')
  materials[str(path.parent.relative_to(ROOT))]=shared.material(path.parent);native=None
  for stage in case['original_individual_stages']:
   for key,digestkey in (('report','report_sha256'),('binding','binding_sha256'),('process','process_sha256'),('log','log_sha256')):
    file=ROOT/stage[key];remember(file)
    if p.sha(file)!=stage[digestkey]:raise p.Rejected('exact original stage material differs')
   native=f.check_drc_stage(ROOT/stage['directory'],record,stage['stage'],Path(stage['source']),Path(stage['input']),stage['saved'],stage['before'],schematic_parity=stage['schematic_parity'])
   if stage['schematic_parity']:
    if p.immutable(sx.read(Path(stage['source'])))!=p.immutable(sx.read(board)) or route_records(sx.read(Path(stage['source'])))!=route_records(sx.read(board)):
     raise p.Rejected('original shell/complete route census differs')
  if native is None or not p.native_accepted(native):raise p.Rejected('original fullSCH Native proof unavailable')
  if (native['findings']!=case['baseline_reference']['exact_native_findings']
      or native['ignored_checks']!=case['baseline_reference']['ignored_checks_exact_array']):
   raise p.Rejected('original full warning/ignored population differs')
  original_legacy_prl(project)
 binding=dict(files_sha256=files,literals=literals,materials=materials)
 if (any(p.sha(ROOT/n)!=v for n,v in files.items()) or any(f.canonical(f.read_json(ROOT/n))!=v for n,v in literals.items())
     or any(shared.material(ROOT/n)!=v for n,v in materials.items())):raise p.Rejected('original gate changed after readback')
 return native,binding

def original_legacy_prl(project):
 # Exact original diagnostic layout is code/autorouter, unlike normal route
 # code/*.py. Replay its own captured producer and actual preserve events;
 # never manufacture modern markers for genuinely older unguarded jobs.
 case=CASES[project];path=ROOT/case['original_aggregate']['path'];record=f.read_json(path)
 if p.sha(path)!=case['original_aggregate']['sha256']:raise p.Rejected('fixed historical original aggregate changed')
 captured=path.parent/'code/autorouter/pipeline.py'
 captured_raw=io.read_bytes(captured,1024**2)
 if hashlib.sha256(captured_raw).hexdigest()!=record['tools']['implementation_sha256']['autorouter/pipeline.py']:raise p.Rejected('captured original Native producer differs')
 policy=ls.policy_declaration(captured_raw)
 diagnostic=path.parent/'code/experiments/original_project_native_v1/driver.py'
 guarded=record.get('protect_local_settings') is True
 if guarded and p.sha(diagnostic)!=record['helper_sha256']:raise p.Rejected('captured guarded original diagnostic producer differs')
 if guarded is not (project=='ds18b20') or (not guarded and (policy is not None or 'normal_drc_local_settings_policy' in record['tools'])):
  raise p.Rejected('specific legacy original protection scope differs')
 checked_stages=[]
 for stage in case['original_individual_stages']:
  documents=[]
  for key in ('binding','process'):
   raw=io.read_bytes(ROOT/stage[key],LIMITS['output'])
   if hashlib.sha256(raw).hexdigest()!=stage[key+'_sha256']:raise p.Rejected('fixed original '+key+' changed before final PRL check')
   documents.append(json.loads(raw))
  checked_stages.append(documents)
 # All producer/stage reads precede the final PRL bytes/flags replay.
 for binding,process in checked_stages:
  input_path=Path(binding['input']);prl=input_path.with_suffix('.kicad_prl')
  if guarded:
   ls.check_preserved(prl,binding['before'],process.get('local_settings_protection'))
  else:
   if process.get('local_settings_protection') is not None or binding.get('local_settings_policy') is not None or process.get('local_settings_policy') is not None:
    raise p.Rejected('legacy original unexpectedly declares a protection event')
   # Original LED/Arc packets contain no PRL. Any Native-created local file
   # must still have its exact retained after bytes and ordinary flags.
   if prl.name in binding['before']:raise p.Rejected('legacy original unexpectedly contains source PRL')
   if prl.is_symlink() or prl.exists() is not (prl.name in binding['after']):raise p.Rejected('legacy original retained PRL presence differs')
   if prl.exists():
    info=prl.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_flags!=0 or p.sha(prl)!=binding['after'].get(prl.name):raise p.Rejected('legacy original retained PRL bytes/flags differ')

def original_prl(plan):
 # Keep prerequisite flags current after all other source/material/context reads.
 for project in ('sonde','nus-usb-led'):
  entry=f.read_json(GATE_PUBLIC)['cases'][project];old=f.read_json(ROOT/entry['protocol']);record=f.read_json(ROOT/entry['producer_receipt'])
  spec=importlib.util.spec_from_file_location('retained_cohort_original_prl',GATE_MODULE);gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
  gate.prl_last(old,record)
 for project in ('push-button-led','ds18b20','arcdice'):
  case=CASES[project];record=f.read_json(ROOT/case['original_aggregate']['path'])
  original_legacy_prl(project)


def arm_spec(case, name):
    if name not in METHODS or case['scope']['private_policy'] is None:
        raise p.Rejected('declared supported case and method required')
    arm = dict(id=name, adapter='both', operation='route', engine_profile='tuned-free-angle')
    if name == 'C_stronger':
        arm.update(operation='prune', engine_profile='tuned', proposal_policy='chains',
                   incumbent_policy=case['scope']['private_policy'])
    return arm


def select_source(case):
    # Registry already uses the correct distinct capture machinery for all five.
    # Never call capture_native_source on a registry id it does not implement.
    board, family = q.selected_source(case['selected_source_id'])
    files = p.tree_hash(board.parent)
    if (str(board) != case['source'] or family != case['family']
            or files != case['source_sha256']):
        raise p.Rejected('complete pinned original/notice packet differs')
    return board, family, dict(packet=str(board.parent), files=files)


def eligibility(board, case):
    policy = p.netclass_policy(board)
    width = p.minimum_width_guard(board, 'both')
    expected = case['scope']['private_policy']
    if expected is None:
        if policy is None:
            raise p.Rejected('frozen unsupported named-class disposition changed')
        return dict(execution_eligible=False, derived_strict_class_targets=True,
                    netclass_policy=policy, minimum_width_guard=width,
                    refusal='unsupported: named-class policy remains outside this private cohort')
    strict = policy is not None or width is not None
    if policy is not None or expected not in s.STRONG_INCUMBENT_POLICIES:
        raise p.Rejected('single Default private policy required')
    v2 = expected == s.STRONG_WIDTH_INCUMBENT_POLICY
    if (v2 is not (width is not None) or
            (v2 and Decimal(str(width['min_track_width_mm'])) !=
             Decimal(str(case['Default']['min_track_width_mm'])))):
        raise p.Rejected('literal original minimum/private policy differs')
    return dict(execution_eligible=True, derived_strict_class_targets=strict,
                netclass_policy=policy, minimum_width_guard=width, refusal=None)


def invoke(board, folder, case, name):
    # Exact current method allowances/reserve and current acceptance are inherited.
    if name == 'C_stronger':
        return s.prune(board, folder, 120, proposal_policy='chains',
                       incumbent_scoring='via_default',
                       _incumbent_policy=case['scope']['private_policy'])
    if name != 'B2_stronger':
        raise p.Rejected('declared method required')
    extra = {}
    if case['scope']['engine_global_width_policy'] is not None:
        extra['_engine_global_width_policy'] = case['scope']['engine_global_width_policy']
    return p.route(board, folder, 120, False, 'both', 'tuned-free-angle',
                   scoring_variant='via_default', _fanout_enabled=False,
                   _optimizer_enabled=False, _engine_clearance_margin_nm=20000, **extra)


def check_planning(folder, data, case):
    p.check_engine_profile_record(data, folder)
    engine_angle.check_scope(data, 'native')
    proof = engine_angle.check(folder, data)
    changes = proof.get('planning_clearance', {}).get('changes', [])
    expected_width_policy = case['scope']['engine_global_width_policy']
    if (data.get('engine_profile') != 'tuned-free-angle'
            or data.get('scoring_variant') != 'via_default'
            or data.get('engine_fanout_override') is not False
            or data.get('engine_optimizer_override') is not False
            or type(data.get('engine_planning_clearance_margin_nm')) is not int
            or data['engine_planning_clearance_margin_nm'] != 20000
            or p.check_engine_global_width_policy(data) != expected_width_policy
            or len(changes) != 2
            or any(Decimal(row['before']) != Decimal(case['Default']['planning_clearance_before_um'])
                   or Decimal(row['after']) != Decimal(case['Default']['planning_clearance_after_um'])
                   for row in changes)):
        raise p.Rejected('case-specific exact strong stock planning differs')
    return proof


def check_field_census(native,baseline):
 has_fields=fields.has_fields(native['findings']);proof=native.get('field_parity')
 if not has_fields:
  if proof:raise p.Rejected('stray field proof without actual finding')
  return
 expected=baseline.get('field_parity',{}).get('qualification')
 actual=(proof or {}).get('qualification',{})
 if (expected is None or actual.get('qualified') is not True or actual.get('component_count')!=expected['component_count']
     or actual.get('compared_field_count')!=expected['compared_field_count']):
  raise p.Rejected('actual complete original effective-field census differs')

def stage_id(project,name):
 if (project,name) not in ORDER:raise p.Rejected('declared eligible stage required')
 return project+'--'+name

def source(project):
 return select_source(CASES[project])



def prepare(head,control_pin,gate_pin):
 shared.clean(head)
 if p.sha(TABLE)!=TABLE_SHA or tuple(CASES)!=PROJECTS or len(POPULATION)!=10 or len(ORDER)!=8:raise p.Rejected('exact five-case table/population required')
 if control_pin!=CONTROL_PUBLIC_SHA or p.sha(CONTROL_PUBLIC)!=CONTROL_PUBLIC_SHA:raise p.Rejected('fixed public owned qualification changed')
 qualified,binding=control(control_pin)
 if qualified['git_head']!=head or qualified['tools']!=p.tool_manifest() or p.sha(GATE_PUBLIC)!=gate_pin:raise p.Rejected('current owned/original prerequisite binding required')
 projects={}
 for project in PROJECTS:
  board,family,packet=source(project);frozen=q.freeze(board);p.preflight(board);state=eligibility(board,CASES[project]);baseline,gates=original_gate(project,gate_pin)
  if state['execution_eligible'] is not (project!='arcdice'):raise p.Rejected('frozen eligibility changed')
  projects[project]=dict(case_id=project,source=str(board),family=family,packet=packet,freeze=frozen,gate_binding=gates,baseline=baseline,eligibility=state,arms={name:arm_spec(CASES[project],name) for name in ARMS} if state['execution_eligible'] else {})
 plan=dict(schema=1,kind=KIND,status='frozen',git_head=head,tools=qualified['tools'],projects=projects,arms=list(ARMS),case_table_sha256=TABLE_SHA,case_table_literal=f.canonical(f.read_json(TABLE)),original_gate_public_sha256=gate_pin,
  arm_order=[list(x) for x in ORDER],population=[list(x) for x in POPULATION],control_binding=binding,helper_sha256={name:p.sha(ROOT/name) for name in HELPERS},controller_sha256=p.sha(Path(__file__)),limits=LIMITS,planned_external_timing_directory=str(TIMING),
  scope='Exposed Sonde/NUS/LED/DS18 fresh B2 versus existing C/chains; Arc2unsupported. Three positive-global-min v2 cases on both methods; DS18 unchanged v1/zerozones.120parent/180worker/240delivered including full preparation+ENTIRE cohort reader+rounding+30report. Own fresh C remaining-minus25 incumbent. Historic prerequisites retain failed-inclusive costs separately; every new pure replay is charged. No family/pedigree/novelty/default/broad quality claim.')
 context(plan);plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
 if max(plan['preparation_costs']['wall_seconds'],plan['preparation_costs']['full_cpu_seconds'])+2>=58:raise p.Rejected('preparation exhausted delivery margin')
 PREP.mkdir();p.save_json(PROTOCOL,plan);print(f.canonical(dict(prepared=True,protocol_sha256=p.sha(PROTOCOL),new_native_or_engine_execution=False)))


def context(plan,pin=None):
 shared.clean(plan['git_head'])
 if (plan.get('kind')!=KIND or plan.get('status')!='frozen' or plan.get('arms')!=list(ARMS) or plan.get('arm_order')!=[list(x) for x in ORDER] or plan.get('population')!=[list(x) for x in POPULATION] or plan.get('limits')!=LIMITS
     or set(plan.get('projects',{}))!=set(PROJECTS) or plan.get('planned_external_timing_directory')!=str(TIMING) or p.sha(Path(__file__))!=plan['controller_sha256'] or p.tool_manifest()!=plan['tools']
     or p.sha(TABLE)!=TABLE_SHA or plan.get('case_table_sha256')!=TABLE_SHA or f.canonical(f.read_json(TABLE))!=plan['case_table_literal']):raise p.Rejected('cohort protocol/controller/table/tools changed')
 if any(p.sha(ROOT/n)!=v for n,v in plan['helper_sha256'].items()):raise p.Rejected('frozen helper changed')
 qualified,binding=control(plan['control_binding']['receipt_sha256'])
 if binding!=plan['control_binding'] or qualified['git_head']!=plan['git_head'] or qualified['tools']!=plan['tools']:raise p.Rejected('owned prerequisite changed')
 for project,spec in plan['projects'].items():
  board,family,packet=source(project);q.verify_freeze(spec['freeze'],board)
  if str(board)!=spec['source'] or family!=spec['family'] or packet!=spec['packet'] or eligibility(board,CASES[project])!=spec['eligibility']:raise p.Rejected('source/eligibility changed')
  expected={name:arm_spec(CASES[project],name) for name in ARMS} if spec['eligibility']['execution_eligible'] else {}
  baseline,gates=original_gate(project,plan['original_gate_public_sha256'])
  if expected!=spec['arms'] or baseline!=spec['baseline'] or gates!=spec['gate_binding']:raise p.Rejected('case/original gate changed')
 if pin is not None and (p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan)):raise p.Rejected('protocol changed')
 original_prl(plan);control_prl(plan['control_binding'])


def planning(folder,data,case):
 proof=check_planning(folder,data,case)
 if data['engine_budget']['strict_class_targets'] is not (case['scope']['engine_global_width_policy'] is not None):raise p.Rejected('original derived strictness differs')
 def widths(parent):return [v for rule in sx.children(parent,'rule') for v in rule[1:] if isinstance(v,list) and v and v[0]=='width']
 for name in ('native.dsn','task.dsn',engine_angle.INPUT):
  tree=dsn._parse_dsn(io.read_bytes(folder/name).decode());classes=sx.children(sx.one(tree,'network'),'class')
  values=widths(sx.one(tree,'structure'))+(widths(classes[0]) if len(classes)==1 else [])
  if sx.one(tree,'unit')!=['unit','um'] or len(classes)!=1 or len(values)!=2 or any(len(v)!=2 or Decimal(v[1])!=Decimal(case['Default']['task_width_um']) for v in values):raise p.Rejected('original Default native/task/engine width differs')
 return dict(assigned_seconds=data['budget_seconds'],cpu_assigned_seconds=data['cpu_budget_seconds'],engine_process_sha256=p.sha(folder/'engine-process.json'),engine_angle_proof_sha256=p.sha(folder/'engine-angle.json'),planning_proof=proof)


def observations(folder,data,spec,arm):
 board=Path(spec['source']);original=sx.read(board);hashes=spec['freeze']['source_hashes'];finals=[];errors=[]
 workers=obs.workers(folder,data,board,hashes,original);resource_error=obs.resource_failure(folder,data)
 def final(directory,record,label,parent=None):
  if not (directory/'final-drc.json').is_file():return dict(id=label,status=record.get('status'),final_native_available=False)
  try:
   error=obs.resource_failure(directory,record,parent)
   proof=obs.candidate(directory,record,board,original,hashes,spec['baseline'],parent=parent,resource_error=error)
   check_field_census(record['native'],spec['baseline'])
   return dict(id=label,status=record.get('status'),accepted_in_receipt=record.get('accepted') is True,native=record['native'],proof=proof,field_parity=record['native'].get('field_parity'))
  except Exception as exc:
   errors.append(dict(id=label,error=type(exc).__name__+': '+str(exc)));return dict(id=label,status=record.get('status'),final_native_available=True,qualified=False,candidate_sha256=record.get('candidate_sha256'),native_report_sha256=record.get('native_report_sha256'),native=record.get('native'))
 finals.append(final(folder,data,'final'))
 child=folder/'incumbent/result.json' if arm['operation']=='prune' else folder/'result.json'
 incumbent=f.read_json(child) if child.is_file() else None;planproof=None
 if incumbent is not None:
  try:
   planproof=planning(child.parent,incumbent,CASES[spec['case_id']])
   if arm['operation']=='prune' and (child.parent/'final-drc.json').is_file():
    rb.pruning_incumbent_readback(folder,data,board,original,hashes)
  except Exception as exc:errors.append(dict(id='incumbent' if arm['operation']=='prune' else 'planning',error=type(exc).__name__+': '+str(exc)))
  if arm['operation']=='prune':finals.append(final(child.parent,incumbent,'incumbent'))
 if arm['operation']=='prune':
  for trial in data.get('trials',[]):
   path=Path(trial['receipt']);expected=folder/'trials'/trial['id']/'result.json'
   if path!=expected or path.is_symlink():raise p.Rejected('trial receipt escaped its declared arm')
   record=f.read_json(path)
   if any(record.get(k)!=trial.get(k) for k in ('id','status','accepted')):raise p.Rejected('trial summary differs from retained receipt')
   finals.append(final(path.parent,record,trial['id'],data))
 return dict(workers=workers,finals=finals,errors=errors,resource_failure=resource_error,planning=planproof)

def arm_prl(folder,data):ls.check_normal_policy(folder,data,max_bytes=LIMITS['output'],max_files=2048)

def worker(plan,pin,project,name):
 context(plan,pin);spec=plan['projects'][project];arm=spec['arms'][name];board=Path(spec['source']);folder=OUT/project/name/'child'
 if spec['eligibility']['execution_eligible'] is not True:raise p.Rejected(spec['eligibility']['refusal'])
 folder.mkdir();owner={};h.capture_destination(owner,folder);data=None
 record=dict(schema=1,accepted=False,passed=False,status='failed',project=project,arm=name,protocol_sha256=pin,git_head=plan['git_head'],tools=plan['tools'])
 try:
  with p.validation_readback_session():
   began,initial=time.monotonic(),cpu()
   data=invoke(board,folder/'route',CASES[project],name)
   wall,full=time.monotonic()-began,cpu()-initial;stored=f.read_json(folder/'route/result.json')
   if f.canonical(data)!=f.canonical(stored) or data['tools']!=plan['tools'] or data['source_hashes']!=spec['freeze']['source_hashes']:raise p.Rejected('returned/stored source/tool lineage differs')
   record['route_receipt_sha256']=p.sha(folder/'route/result.json');row=q.summarize(arm,folder/'route',data,wall,full)
   record['row']=row;record['observations']=observations(folder/'route',data,spec,arm);row['observations']=q.observations(folder/'route',data,row)
   row['accepted']=bool(row['accepted'] and not record['observations']['errors'] and record['observations']['resource_failure'] is None)
   record.update(passed=row['accepted'],status='completed' if row['accepted'] else 'failed')
 except (Exception,KeyboardInterrupt) as exc:record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) or data and q.cancelled(data) else 'failed',error=type(exc).__name__+': '+str(exc))
 witness=shared.material(folder);record['completed_evidence']=witness
 def remaining():return min(178-(time.monotonic()-START),178-(cpu()-CPU0))
 def stable():
  h.owned_destination(owner);context(plan,pin)
  if shared.material(folder)!=witness:raise p.Rejected('child material changed')
  if data is not None and data.get('accepted') is True:p.check_result(folder/'route/result.json')
  if shared.material(folder)!=witness:raise p.Rejected('child material changed late')
  original_prl(plan);control_prl(plan['control_binding'])
  if data is not None:arm_prl(folder/'route',data)
 def account():
  record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
  if remaining()<=0 and record['status']!='cancelled':record['status']='budget_exceeded'
  if record['status']!='completed':record['passed']=False
 f.publish(folder,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
 return 0 if record['passed'] and record['status']=='completed' else 130 if record['status']=='cancelled' else 2

def execute(plan,pin,project,name):
 context(plan,pin)
 for prior_project,prior_name in ORDER[:ORDER.index((project,name))]:
  old=f.read_json(OUT/prior_project/prior_name/'result.json')
  if old.get('protocol_sha256')!=pin or old.get('status')=='cancelled' or old.get('process',{}).get('cleanup_complete') is not True:raise p.Rejected('prior arm absent/cancelled or cleanup incomplete; second arm not attempted')
 folder=OUT/project/name;folder.parent.mkdir(parents=True,exist_ok=True);folder.mkdir();owner={};h.capture_destination(owner,folder)
 costs=plan['preparation_costs']
 if costs.get('publication_allowance_seconds')!=2 or any(not q.finite_nonnegative(costs.get(k)) for k in ('wall_seconds','full_cpu_seconds')):raise p.Rejected('finite preparation costs required')
 prewall,precpu=costs['wall_seconds']+2,costs['full_cpu_seconds']+2
 def remaining():return min(238-prewall-(time.monotonic()-START),238-precpu-(cpu()-CPU0))
 fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
 with os.fdopen(fd,'r+') as lock:
  info=os.fstat(lock.fileno())
  if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary existing shared lane required')
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__)),'--mode','worker','--source-head',plan['git_head'],'--protocol-sha256',pin,'--project',project,'--arm',name]
  env={key:value for key,value in os.environ.items() if key not in {'PYTHONPATH','PYTHONHOME'}};env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',LANG='C',LC_ALL='C')
  process=run(argv,cwd=folder,env=env,log=folder/'command.log',timeout=max(.001,min(180,remaining())),max_log_bytes=LIMITS['log'],max_workdir_bytes=LIMITS['output'],max_group_rss_bytes=LIMITS['rss'])
  path=folder/'child/result.json';child=f.read_json(path) if path.is_file() else None;childpin=p.sha(path) if child else None;literal=f.canonical(child)
  bound=bool(child and child.get('completed_evidence')==shared.material(folder/'child') and p.sha(path)==childpin and f.canonical(f.read_json(path))==literal)
  witness=shared.material(folder);passed=bool(bound and child.get('passed') is True and child.get('status')=='completed' and child.get('accepted') is False and child.get('project')==project and child.get('arm')==name
   and child.get('protocol_sha256')==pin and child.get('git_head')==plan['git_head'] and child.get('tools')==plan['tools'] and process['status']=='success' and type(process['exit_code'])is int and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
  record=dict(schema=1,accepted=False,passed=passed,status='completed' if passed else 'cancelled' if process['status']=='cancelled' or child and child.get('status')=='cancelled' else 'failed',project=project,arm=name,
   protocol_sha256=pin,git_head=plan['git_head'],controller_sha256=plan['controller_sha256'],process=process,child_receipt_sha256=childpin,child_literal=literal,child_material_bound=bound,completed_evidence=witness,
   preparation_costs=costs,delivered_qualification_pending=True,scope=plan['scope'])
  def stable():
   h.owned_destination(owner);context(plan,pin)
   if shared.material(folder)!=witness or child is not None and (not bound or p.sha(path)!=childpin or f.canonical(f.read_json(path))!=literal or shared.material(folder/'child')!=child['completed_evidence']):raise p.Rejected('outer/child complete material changed')
   original_prl(plan);control_prl(plan['control_binding'])
   route=folder/'child/route/result.json'
   if route.is_file():arm_prl(route.parent,f.read_json(route))
  def account():
   record.update(wall_seconds=prewall+time.monotonic()-START,full_cpu_seconds=precpu+cpu()-CPU0,publication_allowance_seconds=2)
   if remaining()<=0 and record['status']!='cancelled':record['status']='budget_exceeded'
   if record['status']!='completed':record['passed']=False
  f.publish(folder,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
  print(f.canonical({k:record.get(k) for k in ('project','arm','passed','status','wall_seconds','full_cpu_seconds')}))
  return 0 if record['passed'] and record['status']=='completed' else 130 if record['status']=='cancelled' else 2

@contextlib.contextmanager
def pure_process_guard():
 old_run,old_popen=subprocess.run,subprocess.Popen;active=False
 prefix=['git','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null'];allowed=[['git','rev-parse','HEAD'],[*prefix,'rev-parse','HEAD'],[*prefix,'status','--porcelain=v1','--untracked-files=normal']]
 def check(argv,kw):
  if type(argv)is not list or argv not in allowed or Path(kw.get('cwd','')).resolve()!=ROOT or kw.get('shell') or kw.get('executable')is not None:raise p.Rejected('pure reader allows only exact read-only source Git observations')
 def run_git(argv,*a,**kw):
  nonlocal active
  check(argv,kw)
  if a or active:raise p.Rejected('unexpected nested pure process call')
  active=True
  try:return old_run(argv,**kw)
  finally:active=False
 def popen_git(argv,*a,**kw):
  check(argv,kw)
  if a or not active:raise p.Rejected('unqualified pure process launch')
  return old_popen(argv,**kw)
 subprocess.run,subprocess.Popen=run_git,popen_git
 try:yield
 finally:subprocess.run,subprocess.Popen=old_run,old_popen

def dispositions(plan,pin):
 rows=[]
 for project,name in POPULATION:
  spec=plan['projects'][project];path=OUT/project/name/'result.json'
  if spec['eligibility']['execution_eligible'] is not True:
   if path.parent.exists() or path.parent.is_symlink():raise p.Rejected('unsupported case unexpectedly has runtime output')
   rows.append(dict(project=project,arm=name,status='unsupported',accepted=False,attempted=False,reason=spec['eligibility']['refusal']));continue
  if not path.is_file():
   rows.append(dict(project=project,arm=name,status='not_attempted' if not path.parent.exists() else 'missing_receipt',accepted=False,attempted=path.parent.exists(),reason='Frozen arm absent or incomplete; consult retained enclosing command logs. No candidate or pass synthesized.'));continue
  outer=f.read_json(path)
  if outer.get('protocol_sha256')!=pin or outer.get('project')!=project or outer.get('arm')!=name:raise p.Rejected('arm identity differs')
  rows.append(dict(project=project,arm=name,status=outer['status'],accepted=False,attempted=True,result=str(path),result_sha256=p.sha(path)))
 return rows

def read(plan,pin):
 READ.mkdir();owner={};h.capture_destination(owner,READ)
 with pure_process_guard(),p.validation_readback_session():
  context(plan,pin);rows=dispositions(plan,pin);witnesses={};errors=[]
  for row in rows:
   if not row.get('result'):continue
   project,name=row['project'],row['arm'];folder=OUT/project/name;outer=f.read_json(folder/'result.json');process=outer['process'];childpath=folder/'child/result.json'
   witnesses[str(folder)]=dict(material=shared.material(folder),result_sha256=p.sha(folder/'result.json'),literal=f.canonical(outer))
   try:
    expected=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__)),'--mode','worker','--source-head',plan['git_head'],'--protocol-sha256',pin,'--project',project,'--arm',name]
    if process['argv']!=expected or process['cwd']!=str(folder) or process['log']!=str(folder/'command.log') or process['cleanup_complete'] is not True or process['log_truncated'] is not False or Path(process['log']).stat().st_size!=process['log_bytes'] or process['resource_guards']['max_group_rss_bytes']!=LIMITS['rss'] or process['resource_guards']['max_workdir_bytes']!=LIMITS['output']:raise p.Rejected('actual enclosing worker process differs')
    if (shared.material(folder)!=outer['completed_evidence'] or outer.get('git_head')!=plan['git_head'] or outer.get('controller_sha256')!=plan['controller_sha256'] or outer.get('preparation_costs')!=plan['preparation_costs']):raise p.Rejected('outer complete witness/source/provenance changed')
    child=f.read_json(childpath)
    if (outer.get('child_material_bound') is not True or p.sha(childpath)!=outer['child_receipt_sha256'] or f.canonical(child)!=outer['child_literal'] or shared.material(childpath.parent)!=child['completed_evidence'] or child['protocol_sha256']!=pin or child.get('project')!=project or child.get('arm')!=name or child.get('git_head')!=plan['git_head'] or child.get('tools')!=plan['tools']):raise p.Rejected('child literal/prepublication witness differs')
    route=folder/'child/route';data=f.read_json(route/'result.json')
    if (p.sha(route/'result.json')!=child['route_receipt_sha256'] or data.get('source')!=plan['projects'][project]['source'] or data.get('source_hashes')!=plan['projects'][project]['freeze']['source_hashes'] or data.get('tools')!=plan['tools']):raise p.Rejected('route receipt/source/tool binding differs')
    observed=observations(route,data,plan['projects'][project],plan['projects'][project]['arms'][name])
    raw=q.summarize(plan['projects'][project]['arms'][name],route,data,child['row']['invocation_wall_seconds'],child['row']['invocation_cpu_seconds']);raw['observations']=q.observations(route,data,raw)
    raw['accepted']=bool(raw['accepted'] and not observed['errors'] and observed['resource_failure'] is None)
    if raw!=child['row'] or observed!=child['observations']:raise p.Rejected('retained summary/whole-final observations differ')
    if data.get('accepted') is True:p.check_result(route/'result.json')
    enclosure=(outer.get('passed') is True and outer.get('status')=='completed' and child.get('passed') is True and child.get('status')=='completed' and child.get('accepted') is False and process.get('status')=='success' and type(process.get('exit_code'))is int and process['exit_code']==0
     and all(q.finite_nonnegative(outer.get(key)) and outer[key]+2<=240 for key in ('wall_seconds','full_cpu_seconds')) and all(q.finite_nonnegative(child.get(key)) and child[key]+2<=180 for key in ('wall_seconds','full_cpu_seconds')))
    row.update(native_result_accepted=raw['accepted'],arm_enclosure_completed=enclosure,row=raw,observations=observed,outcome_evidence_qualified=True)
   except Exception as exc:errors.append(dict(project=project,arm=name,error=type(exc).__name__+': '+str(exc)));row.update(outcome_evidence_qualified=False,error=errors[-1]['error'])
  record=dict(schema=1,accepted=False,passed=not errors,status='completed' if not errors else 'failed',git_head=plan['git_head'],protocol_sha256=pin,rows=rows,errors=errors,arm_complete_trees=witnesses,new_native_execution=False,new_JVM_execution=False)
  own=shared.material(READ);record['completed_evidence']=own
  def remaining():return min(88-(time.monotonic()-START),88-(cpu()-CPU0))
  def stable():
   h.owned_destination(owner);context(plan,pin)
   if shared.material(READ)!=own or any(shared.material(Path(folder))!=tree['material'] or p.sha(Path(folder)/'result.json')!=tree['result_sha256'] or f.canonical(f.read_json(Path(folder)/'result.json'))!=tree['literal'] for folder,tree in witnesses.items()):raise p.Rejected('pure reader retained material changed')
   original_prl(plan);control_prl(plan['control_binding'])
   for project,name in ORDER:
    path=OUT/project/name/'child/route/result.json'
    if path.is_file():arm_prl(path.parent,f.read_json(path))
  def account():
   record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
   if remaining()<=0:record.update(passed=False,status='budget_exceeded')
   if record['status']!='completed':record['passed']=False
  f.publish(READ,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
  print(f.canonical(dict(passed=record['passed'],status=record['status'],errors=errors)))
  return 0 if record['passed'] and record['status']=='completed' else 130 if record['status']=='cancelled' else 2

def timing(stage,plan,pin):
 files={suffix:TIMING/(stage+'-'+suffix) for suffix in ('time.log','command.log')};text=io.read_bytes(files['time.log'],64*1024).decode()
 pairs=re.findall(r'(?m)^(real|user|sys) ([0-9.]+)$',text);values={key:float(value) for key,value in pairs}
 if len(pairs)!=3 or set(values)!={'real','user','sys'} or any(not q.finite_nonnegative(value) for value in values.values()):raise p.Rejected('unique complete external process-exit timing required')
 mode='run' if stage in STAGES else stage
 expected=[str(Path(__file__).resolve()),'--mode',mode,'--source-head',plan['git_head']]
 if mode=='prepare':expected+=['--control-sha256',plan['control_binding']['receipt_sha256'],'--source-gates-sha256',plan['original_gate_public_sha256']]
 else:expected+=['--protocol-sha256',pin]
 if mode=='run':
  project,name=STAGES[stage];expected+=['--project',project,'--arm',name]
 cwd=ENCLOSURES/stage;enclosure=cwd/'execution.json';e=f.read_json(enclosure);process=e['process'];log=cwd/'command.log'
 success=process.get('status')=='success' and type(process.get('exit_code'))is int and process['exit_code']==0
 completed=success or (stage in STAGES and process.get('status')=='nonzero_exit' and type(process.get('exit_code'))is int and process['exit_code']!=0)
 if (e.get('stage')!=stage or e.get('source_head')!=plan['git_head'] or e.get('driver_sha256')!=plan['controller_sha256']
     or e.get('wrapper_sha256')!=plan['helper_sha256'].get(str(COMMAND.relative_to(ROOT))) or p.sha(COMMAND)!=e['wrapper_sha256']
     or process.get('argv')!=[str(ROOT/'.venv/bin/python'),'-B',*expected] or process.get('cwd')!=str(cwd)
     or process.get('log')!=str(log) or not completed
     or process.get('cleanup_complete') is not True or process.get('log_truncated') is not False
     or e.get('log_sha256')!=p.sha(log) or log.stat().st_size!=process.get('log_bytes')
     or process['resource_guards']['max_workdir_bytes']!=8*1024**2 or process['resource_guards']['max_group_rss_bytes']!=LIMITS['rss']):
  raise p.Rejected('actual complete stage process/argv/cwd/log/source/cleanup differs')
 lines=io.read_bytes(files['command.log'],LIMITS['log']).decode().splitlines()
 if not lines:raise p.Rejected('actual external invocation journal missing')
 invocation=json.loads(lines[0]).get('invocation')
 if invocation!=dict(argv=expected,cwd=str(cwd),executable=str(ROOT/'.venv/bin/python'),controller_sha256=plan['controller_sha256']):raise p.Rejected('external timing log is not bound to exact actual invocation')
 lower_wall=process['wall_seconds'];lower_cpu=sum(process.get(k) or 0 for k in ('cpu_seconds','monitor_cpu_seconds','supervisor_cpu_seconds'))
 if stage=='prepare':sample=plan['preparation_costs'];sample_wall=sample['wall_seconds'];sample_cpu=sample['full_cpu_seconds']
 elif stage in STAGES:
  project,name=STAGES[stage];path=OUT/project/name/'result.json';outer=f.read_json(path) if path.is_file() else None;prep=plan['preparation_costs']
  sample_wall=max(0,outer['wall_seconds']-prep['wall_seconds']-2) if outer else 0;sample_cpu=max(0,outer['full_cpu_seconds']-prep['full_cpu_seconds']-2) if outer else 0
 else:
  sample=f.read_json(READ/'result.json');sample_wall=sample['wall_seconds'];sample_cpu=sample['full_cpu_seconds']
 if (any(not q.finite_nonnegative(x) for x in (lower_wall,lower_cpu,sample_wall,sample_cpu))
     or values['real']+.01<max(lower_wall,sample_wall) or values['user']+values['sys']+.02<max(lower_cpu,sample_cpu)):
  raise p.Rejected('external complete cost below retained actual process/stage lower bound')
 files.update(execution=enclosure,worker_log=log)
 return dict(wall_seconds=values['real'],full_cpu_seconds=values['user']+values['sys'],complete_process_success=success,actual_process_status=process['status'],actual_exit_code=process['exit_code'],files_sha256={str(path.relative_to(ROOT)):p.sha(path) for path in files.values()},rounding_allowance_seconds=.02)


def report(plan,pin):
 REPORT.mkdir();owner={};h.capture_destination(owner,REPORT)
 with pure_process_guard():
  context(plan,pin);reader=f.read_json(READ/'result.json');readpin=p.sha(READ/'result.json');readliteral=f.canonical(reader)
  if reader.get('passed') is not True or reader.get('status')!='completed' or reader.get('protocol_sha256')!=pin or reader.get('completed_evidence')!=shared.material(READ):raise p.Rejected('completed current whole pure reader required')
  costs={stage:timing(stage,plan,pin) for stage in ('prepare',*STAGES,'read')};rows=json.loads(f.canonical(reader['rows']))
  for row in rows:
   if not plan['projects'][row['project']]['eligibility']['execution_eligible']:continue
   key=stage_id(row['project'],row['arm']);selected=[costs['prepare'],costs[key],costs['read']]
   row['charged_wall_seconds']=sum(x['wall_seconds']+x['rounding_allowance_seconds'] for x in selected)+LIMITS['report']
   row['charged_full_cpu_seconds']=sum(x['full_cpu_seconds']+x['rounding_allowance_seconds'] for x in selected)+LIMITS['report']
   row['delivered_within_240']=max(row['charged_wall_seconds'],row['charged_full_cpu_seconds'])<=240
   row['accepted']=bool(row.get('native_result_accepted') and row.get('arm_enclosure_completed') and row.get('outcome_evidence_qualified') and row['delivered_within_240'] and costs[key]['complete_process_success'])
  record=dict(schema=1,accepted=False,passed=True,status='completed',git_head=plan['git_head'],protocol_sha256=pin,reader_sha256=readpin,external_costs=costs,rows=rows,
   common_report_wall_full_cpu_upper_allowance_seconds=LIMITS['report'],scope=plan['scope'],cost_scope='Each eligible case/method pays full external preparation + own full external arm + ENTIRE current external pure reader +.02perroundedlog +30s bounded report allowance. No failed or publication tails removed; actual report process-exit log retained separately. No historical quality comparison.')
  material=shared.material(REPORT);record['completed_evidence']=material
  def remaining():return min(28-(time.monotonic()-START),28-(cpu()-CPU0))
  def stable():
   h.owned_destination(owner);context(plan,pin)
   if p.sha(READ/'result.json')!=readpin or f.canonical(f.read_json(READ/'result.json'))!=readliteral or reader['completed_evidence']!=shared.material(READ) or shared.material(REPORT)!=material:raise p.Rejected('reader/report material changed')
   if any(timing(stage,plan,pin)!=old for stage,old in costs.items()) or any(shared.material(Path(folder))!=tree['material'] or p.sha(Path(folder)/'result.json')!=tree['result_sha256'] or f.canonical(f.read_json(Path(folder)/'result.json'))!=tree['literal'] for folder,tree in reader['arm_complete_trees'].items()):raise p.Rejected('actual command timing or arm material changed')
   original_prl(plan);control_prl(plan['control_binding'])
   for project,name in ORDER:
    path=OUT/project/name/'child/route/result.json'
    if path.is_file():arm_prl(path.parent,f.read_json(path))
  def account():
   record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
   if remaining()<=0:record.update(passed=False,status='budget_exceeded')
   if record['status']!='completed':
    record['passed']=False
    for row in rows:row['accepted']=False
  f.publish(REPORT,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
  print(f.canonical(dict(passed=record['passed'],status=record['status'],rows=[{key:row.get(key) for key in ('project','arm','status','accepted','charged_wall_seconds','charged_full_cpu_seconds')} for row in rows])));return 0 if record['passed'] and record['status']=='completed' else 130 if record['status']=='cancelled' else 2

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['prepare','worker','run','read','report'],required=True);ap.add_argument('--source-head',required=True);ap.add_argument('--protocol-sha256');ap.add_argument('--control-sha256');ap.add_argument('--source-gates-sha256');ap.add_argument('--project',choices=list(PROJECTS));ap.add_argument('--arm',choices=list(ARMS));args=ap.parse_args()
 handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
 def interrupted(*_):raise KeyboardInterrupt
 try:
  for sig in handlers:signal.signal(sig,interrupted)
  with p.validation_readback_session():
   if args.mode=='prepare':prepare(args.source_head,args.control_sha256,args.source_gates_sha256)
   else:
    plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
    if plan['git_head']!=args.source_head or args.protocol_sha256!=pin:raise p.Rejected('exact frozen HEAD/protocol required')
    if args.mode in ('read','report'):raise SystemExit(read(plan,pin) if args.mode=='read' else report(plan,pin))
    if (args.project,args.arm) not in ORDER:raise p.Rejected('exact frozen eligible arm required')
    raise SystemExit(worker(plan,pin,args.project,args.arm) if args.mode=='worker' else execute(plan,pin,args.project,args.arm))
 finally:
  for sig,handler in handlers.items():signal.signal(sig,handler)
