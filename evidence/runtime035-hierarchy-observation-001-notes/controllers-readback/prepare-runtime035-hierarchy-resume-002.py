"""Resume only the unfinished Native observations; preserve failed001 intact."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[1];rt=R/'.runs/runtime-directory-035/runtime'
sys_path=str(rt)
import sys
sys.path.insert(0,sys_path);sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
old=R/'.runs/qualify-runtime035-hierarchy-observation-001.py';assert p.sha(old)=='ad4f7d25ea6b9f168fcbb153cfdb59197c51be3efb883e0b48b16c30266fbd04'
source=old.read_text().replace('qualify-runtime035-hierarchy-observation-001.py','qualify-runtime035-hierarchy-observation-002.py').replace('runtime035-hierarchy-observability-v1','runtime035-hierarchy-observability-resume-v2').replace('native7-comparison-control-runtime035-hierarchy-001','native7-comparison-control-runtime035-hierarchy-002')
needle='def execute(protocol, pin):'
addition='''def completed_export001(plan):
    row=plan['completed_export001'];root=RUNTIME/'.runs/native7-comparison-control-runtime035-hierarchy-001'
    require(row['root']==str(root) and p.sha(root/'result.json')==row['result_sha256'],'retained failed001 changed')
    data=f.read_json(root/'result.json')
    require(data['status']=='failed' and data['control_passed'] is False and data['accepted'] is False
        and data['error']=='Rejected: Native observation changed copied original project'
        and data['source_hashes']==plan['source_hashes'] and data['tools']==plan['tools'],'wrong prior observation')
    copied=root/'observation/candidate'/SOURCE.name
    require(io.inventory(copied.parent)==row['after_hashes'],'retained export inputs changed')
    require(all(row['after_hashes'].get(n)==v for n,v in plan['source_hashes'].items())
        and set(row['after_hashes'])-set(plan['source_hashes'])=={SOURCE.with_suffix('.kicad_prl').name},
        'prior export changed an original file or unexpected companion')
    netlist=root/'observation/hierarchy.net';require(p.sha(netlist)==row['netlist_sha256'],'prior Native netlist changed')
    argv=[*f.SANDBOX,str(c.CLI),'sch','export','netlist','--format','kicadsexpr','--output',str(netlist),str(copied.with_suffix('.kicad_sch'))]
    process=f.process_check(root/'observation',data,'hierarchy-netlist',argv)
    require(process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
        and process['log_truncated'] is False and len(data['steps'])==1,'prior export did not actually complete')
    require(p.sha(root/'observation/hierarchy-netlist-process.json')==row['process_sha256'],'prior process changed')
    return netlist,copied

'''
assert source.count(needle)==1;source=source.replace(needle,addition+needle)
needle="    prereq={Path(name):value for name,value in plan['prerequisite_files'].items()}"
assert source.count(needle)==1;source=source.replace(needle,"    prior_netlist,prior_board=completed_export001(plan)\n"+needle)
needle="    def stable():\n        require(h.owned_destination(owner)==out"
assert source.count(needle)==1;source=source.replace(needle,"    def stable():\n        completed_export001(plan)\n        require(h.owned_destination(owner)==out")
line="            ('hierarchy-netlist',[str(c.CLI),'sch','export','netlist','--format','kicadsexpr','--output',str(job.out/'hierarchy.net'),str(copied.with_suffix('.kicad_sch'))],job.out/'hierarchy.net'),\n"
assert source.count(line)==1;source=source.replace(line,'')
source=source.replace("observed=extract(job.out/'hierarchy.net',native,copied)","observed=extract(prior_netlist,native,prior_board)")
needle="        disposition='defer',whole_wall_full_cpu_budget_seconds=180"
assert source.count(needle)==1;source=source.replace(needle,"        completed_export001=plan['completed_export001'],source_zone_refill_performed=False,\n        prior_export_scope='Reused raw completed Native export from failed001. Every original17 file remains exact; added local preferences retained. Original missing post-export binding is not fabricated or promoted to acceptance. No export rerun.',\n        disposition='defer',whole_wall_full_cpu_budget_seconds=180")
q=R/'.runs/qualify-runtime035-hierarchy-observation-002.py';assert not q.exists();ast.parse(source);q.write_text(source)
planpath=R/'.runs/runtime035-hierarchy-observation-001/protocol.json';assert p.sha(planpath)=='1fecd2db34ad9f4b5a8aaa1258debf34cfc2a58f013c2be04f7189c89fe1e9f7'
plan=f.read_json(planpath);prior=Path(plan['output']);data=f.read_json(prior/'result.json')
assert p.sha(prior/'result.json')=='614f96781d9326d0639f890c90a7d8f4e4ffad17968f6b4f8da2ac63e30c6865'
after=p.tree_hash(prior/'observation/candidate');hashes=plan['source_hashes']
assert all(after[n]==v for n,v in hashes.items()) and set(after)-set(hashes)=={'multichannel_mixer.kicad_prl'}
assert p.tree_hash(Path(plan['source']).parent)==hashes
assert data['error']=='Rejected: Native observation changed copied original project'
for name,pin in plan['prerequisite_files'].items():assert p.sha(Path(name))==pin
assert p.tool_manifest()==plan['tools']
base=R/'.runs/runtime035-hierarchy-observation-002';out=rt/'.runs/native7-comparison-control-runtime035-hierarchy-002';child=rt/'.runs'/q.name
assert not base.exists() and not out.exists() and not child.exists();base.mkdir()
plan.update(kind='runtime035-hierarchy-observability-resume-v2',controller=str(child),controller_sha256=p.sha(q),output=str(out),
 completed_export001=dict(root=str(prior),result_sha256=p.sha(prior/'result.json'),after_hashes=after,
 netlist_sha256=p.sha(prior/'observation/hierarchy.net'),process_sha256=p.sha(prior/'observation/hierarchy-netlist-process.json'),
 complete_external_cost=dict(wall_seconds=1.93,CPU_seconds=1.61),
 scope='Raw Native datum from retained failed001, one generated PRL added and all17 original files unchanged. No retroactive Native input-binding or acceptance claim; no repeated export.'),
 preparation=dict(preparer_sha256=p.sha(Path(__file__)),reused_prior_protocol_sha256=p.sha(planpath),Native_executed=False),
 scope='Bounded continuation of exposed mixer observation: reuse actual completed export001; only missing PCB map and full source-schematic DRC on a fresh original17-file copy. Keep product hierarchy guard closed; raw observations never admit routing. No zone refill or route candidate claimed.')
child.write_bytes(q.read_bytes());assert p.sha(child)==plan['controller_sha256']
p.save_json(base/'protocol.json',plan)
print(json.dumps(dict(protocol=str(base/'protocol.json'),protocol_sha256=p.sha(base/'protocol.json'),controller_sha256=p.sha(q),Native_executed=False)))
