"""Offline retained-native audit using shared validators; no subprocesses."""
from pathlib import Path
from collections import Counter
import copy,hashlib,json,subprocess,sys,time
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc
from autorouter import sexpr as sx,strategy as s,schematic_field_evidence as fields
from scripts import experiment_portfolio as portfolio
RUN=ROOT/'.runs/nus-native-paired-002/run'
def read(path):return f.read_json(path)
def require(test,message):
    if not test:raise ValueError(message)
def forbidden(*args,**kwargs):raise AssertionError('Offline audit cannot launch subprocess/native/Git/network')
def inventory(path):return pc.inventory(path,max_bytes=96*1024**2,max_files=16000,max_entries=32000)
before=inventory(RUN);protocol=read(RUN/'protocol.json');freeze=protocol['freeze'];source=Path(protocol['source'])
source_before=pc.inventory(source.parent);original=p.preflight(source);summary=read(RUN/'paired-summary.json');outer=read(RUN.parent/'execution.json')
require(source_before==freeze['source_hashes'],'source freeze changed')
require(protocol['wall_budget_per_arm_seconds']==protocol['cpu_budget_per_arm_seconds']==120,'outer budgets differ')
require(summary['protocol_sha256']==p.sha(RUN/'protocol.json'),'protocol byte hash differs')
require([row['id'] for row in summary['results']]==protocol['arm_order']==['B0','B1','B2_portfolio','C_feedback'],'arm population differs')
for relative,digest in freeze['files_sha256'].items():require(p.sha(RUN/'frozen-code'/relative)==digest,'frozen file changed: '+relative)
core_differences=[rel for rel,digest in freeze['tools']['implementation_sha256'].items() if p.sha(ROOT/rel)!=digest]
require(core_differences==[],'actual core differs from measured code')
all_differences=[rel for rel,digest in freeze['files_sha256'].items() if p.sha(ROOT/rel)!=digest]
require(all_differences==['scripts/experiment_portfolio.py'],'unexpected resume code difference')
require(outer['log_sha256']==p.sha(RUN.parent/'command.log'),'outer command log changed')
require(outer['process']['status']=='success' and outer['process']['exit_code']==0 and outer['process']['cleanup_complete'] is True and outer['process']['log_truncated'] is False,'outer process failed')
records={};checks={}
with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden):
    for name,relative in [('B1','B1'),('B2_completed','B2_portfolio/01-via_default'),('C_incumbent','C_feedback/incumbent'),('C_final','C_feedback')]:
        folder=RUN/relative;record=read(folder/'result.json');records[name]=record
        checks[name]=p.check_result(folder/'result.json')
        require(record['source_hashes']==source_before and record['tools']==freeze['tools'],'receipt/source/tool lineage differs')
        require(pc.inventory(folder/'snapshot')==source_before,'snapshot differs')
        require(p.immutable(sx.read(record['candidate']))==p.immutable(original),'original design changed')
        require(p.parse_report(folder/'final-drc.json',source.name)==record['native'],'raw final report differs')
        require([record['native'][k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,10,0],'native counts differ')
        require(record['whole_project_drc_clean'] is False,'warnings hidden')
        require(record['metrics']==read(folder/'metrics.json'),'metrics changed')
        p.check_resource_accounting(record)
        for step in record['steps']:
            retained=read(Path(step['cwd'])/(step['name']+'-process.json'))
            require(all(step.get(k)==v for k,v in retained.items()),'process history differs')
            require(retained['cleanup_complete'] is True and retained['status'] in ('success','nonzero_exit'),'failed/cancelled worker concealed')
            require(Path(retained['log']).stat().st_size==retained['log_bytes'] and retained['log_truncated'] is False,'log bytes/truncation differs')
    psum=read(RUN/'B2_portfolio/portfolio-summary.json')
    require(psum['status']=='invalidated' and psum['comparison_eligible'] is False and psum['selected'] is None,'original incomplete B2 status rewritten')
    require(len(psum['trials'])==1 and psum['trials'][0]['id']=='via_default','completed B2 population changed')
    checks['fixed_B2_row']=portfolio.verify_row(psum['trials'][0],source,freeze)
    require(not (RUN/'B2_portfolio/02-via_low').exists() and not (RUN/'B2_portfolio/03-via_high').exists(),'unattempted profiles were actually executed')
    # Legacy native C owns its tuned incumbent; replay the one actual deletion
    # and every fresh candidate check without treating a trial as a root receipt.
    c=records['C_final'];inc=records['C_incumbent'];folder=RUN/'C_feedback/trials/trial-0000';trial=read(folder/'result.json')
    require(len(c['trials'])==1 and c['improvements']==1 and trial['accepted'] is True and trial['status']=='improvement_validated','trial population/acceptance differs')
    require(trial['base_candidate_sha256']==p.sha(Path(inc['candidate'])),'trial parent changed')
    nets=s.zone_net_ids(original);protected=p.protected_for_record(c,original)
    require(trial['proposal']==s.proposals(sx.read(inc['candidate']),nets,protected,True)[0],'source-zone proposal replay differs')
    deleted=s.delete_routes(sx.read(inc['candidate']),trial['proposal']['route_ids'],nets,protected)
    candidate=folder/'candidate'/source.name;expected=dict(source_before);expected[source.name]=hashlib.sha256((sx.dump(deleted)+'\n').encode()).hexdigest()
    refill=folder/'refill'/source.name
    f.check_drc_stage(folder,trial,'refill-drc',refill,refill,True,expected,sandboxed=False)
    require((sx.dump(p.transplant_fill(deleted,sx.read(refill)))+'\n').encode()==pc.read_bytes(candidate),'trial deletion/refill bytes differ')
    expected[source.name]=trial['candidate_sha256']
    native=f.check_drc_stage(folder,trial,'final-drc',candidate,folder/'final-drc-input'/source.name,False,expected,schematic_parity=True,sandboxed=False)
    require(native==trial['native'] and p.sha(folder/'final-drc.json')==trial['native_report_sha256'],'actual trial final native differs')
    f.process_check(folder,trial,'pour-keepout-audit',[str(p.c.PYTHON),str(ROOT/'autorouter/native.py'),'pour-audit',str(candidate),str(folder/'pour-keepout-audit.json')])
    from autorouter import pour_rule_area
    pour_rule_area.verify_native_record(read(folder/'pour-keepout-audit.json'),candidate)
    require(p.immutable(sx.read(candidate))==p.immutable(original),'trial immutable design changed')
    require(p.sha(candidate)==trial['candidate_sha256']==c['candidate_sha256'],'final differs from fresh best trial')
    require(trial['metrics']==c['metrics'] and s._warning_signatures(native)==s._warning_signatures(inc['native'])==s._warning_signatures(records['B1']['native']),'quality/warning parity differs')
    require(Counter(sx.dump(row) for row in p.routes(sx.read(candidate)))<=Counter(sx.dump(row) for row in p.routes(sx.read(inc['candidate']))),'deletion changed or added routes')

rows={row['id']:row for row in summary['results']}
for row in summary['results']:
    require(abs(row['charged_wall_seconds']-row['invocation_wall_seconds']-summary['shared_overhead_wall_seconds'])<1e-6,'shared wall charge omitted')
    require(abs(row['charged_cpu_seconds']-row['invocation_cpu_seconds']-summary['shared_overhead_cpu_seconds'])<1e-6,'shared CPU charge omitted')
require(rows['B2_portfolio']['invocation_cpu_seconds']==19.94571,'old full B2 CPU prefix differs')
require(abs(rows['B2_portfolio']['invocation_wall_seconds']-19.723558500001673)<1e-9,'old full B2 wall prefix differs')
require(rows['B2_portfolio']['accepted'] is False and rows['B2_portfolio']['status']=='invalidated','strong baseline falsely admitted')
extra_wall=max(0,outer['wall_seconds']-summary['batch_wall_seconds']);extra_cpu=max(0,outer['full_cpu_seconds']-summary['batch_cpu_seconds'])
require(rows['C_feedback']['charged_wall_seconds']+extra_wall<120 and rows['C_feedback']['charged_cpu_seconds']+extra_cpu<120,'conservative enclosing C cap differs')
require(pc.inventory(source.parent)==source_before and inventory(RUN)==before,'actual artifacts changed during readback')
result={'schema':1,'scope':'actual retained NUS exposed development pair; no new native execution','checks':checks,'core_differences':core_differences,'other_frozen_file_differences':all_differences,
    'candidate_sha256':records['C_final']['candidate_sha256'],'B1_length_mm':records['B1']['metrics']['track_length_mm'],'C_length_mm':c['metrics']['track_length_mm'],
    'C_vias':c['metrics']['vias'],'gain_vs_B1_mm':records['B1']['metrics']['track_length_mm']-c['metrics']['track_length_mm'],'native_counts':[0,0,10,0],
    'deleted_records':len(trial['proposal']['route_ids']),'delete_types':dict(Counter(row[0] for row in p.routes(sx.read(inc['candidate'])) if s.route_id(row) in set(trial['proposal']['route_ids']))),
    'C_charged_wall_seconds':rows['C_feedback']['charged_wall_seconds'],'C_charged_cpu_seconds':rows['C_feedback']['charged_cpu_seconds'],
    'C_conservative_full_outer_wall_seconds':rows['C_feedback']['charged_wall_seconds']+extra_wall,'C_conservative_full_outer_cpu_seconds':rows['C_feedback']['charged_cpu_seconds']+extra_cpu,
    'B2_original_status':psum['status'],'B2_completed_length_mm':records['B2_completed']['metrics']['track_length_mm'],
    'B2_full_prefix_wall_seconds':rows['B2_portfolio']['invocation_wall_seconds'],'B2_full_prefix_cpu_seconds':rows['B2_portfolio']['invocation_cpu_seconds'],
    'original_shared_wall_seconds':summary['shared_overhead_wall_seconds'],'original_shared_cpu_seconds':summary['shared_overhead_cpu_seconds'],
    'original_outer_excess_wall_seconds':extra_wall,'original_outer_excess_cpu_seconds':extra_cpu,'strong_B2_gain_qualified':False,'whole_project_clean':False,
    'actual_run_inventory_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),'source_inventory':source_before}
print(json.dumps(result,indent=2))
