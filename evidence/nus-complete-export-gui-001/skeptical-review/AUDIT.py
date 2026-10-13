"""Read-only GUI/native finding and explicit-project comparison, no native/Git."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).absolute().parents[2];HERE=Path(__file__).absolute().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import placement_clearance as pc,floor_route as f
GUI=ROOT/'.runs/nus-complete-export-gui-001';NATIVE=ROOT/'.runs/nus-complete-schematic-workflow-export-002'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
read=lambda path:json.loads(path.read_text())
before=read(GUI/'before.json');proof=NATIVE/'export.json';candidate=NATIVE/'validation/candidate'
assert sha(proof)==before['export_proof_sha256']
assert pc.inventory(candidate)==before['authoritative_before']
gb=GUI/'project/usb_led.kicad_pcb';gp=gb.with_suffix('.kicad_pro');nb=candidate/'usb_led.kicad_pcb';np=nb.with_suffix('.kicad_pro')
observed_hashes={str(path.relative_to(ROOT)):sha(path) for path in (gb,gp,np,proof,GUI/'project/DRC.json',NATIVE/'validation/final-drc.json')}
assert sha(gb)==sha(nb)==before['candidate_sha256']
g=read(GUI/'project/DRC.json');n=read(NATIVE/'validation/final-drc.json')
assert g['ignored_checks']==n['ignored_checks'] and len(g['ignored_checks'])==2
assert set(g['included_severities'])==set(n['included_severities'])=={'error','warning','exclusion'}
assert g['source']==n['source']=='usb_led.kicad_pcb' and g['kicad_version']==n['kicad_version']=='10.0.0'
assert Counter(f.canonical(x) for x in g['schematic_parity'])==Counter(f.canonical(x) for x in n['schematic_parity'])
def findings(value):return value['violations']+value['unconnected_items']+value['schematic_parity']
def counts(value):
    items=findings(value)
    return {'opens':len(value['unconnected_items']),'errors':sum(x['severity']=='error' for x in items),'warnings':sum(x['severity']=='warning' for x in items),'exclusions':sum(x['severity']=='exclusion' or x.get('excluded',False) for x in items)}
assert counts(g)=={'opens':0,'errors':0,'warnings':6,'exclusions':0}
assert counts(n)=={'opens':0,'errors':0,'warnings':10,'exclusions':0}
summary=lambda value:[{'type':x['type'],'severity':x['severity'],'description':x.get('description'),'references':[i['description'] for i in x['items']]} for x in value['violations']]
a,b=read(np),read(gp);added=[];removed=[];changed=[]
def diff(a,b,path=''):
    if isinstance(a,dict) and isinstance(b,dict):
        for key in a.keys()-b.keys():removed.append(path+'/'+key)
        for key in b.keys()-a.keys():added.append(path+'/'+key)
        for key in a.keys()&b.keys():diff(a[key],b[key],path+'/'+key)
    elif a!=b:changed.append(path)
diff(a,b)
assert not removed
assert a['board']['design_settings']['rules']==b['board']['design_settings']['rules']
assert all(b['board']['design_settings']['rule_severities'].get(key)==value for key,value in a['board']['design_settings']['rule_severities'].items())
oldclasses={x['name']:x for x in a['net_settings']['classes']};newclasses={x['name']:x for x in b['net_settings']['classes']}
assert oldclasses.keys()==newclasses.keys()
assert all(newclasses[name].get(key)==value for name,row in oldclasses.items() for key,value in row.items())
assert pc.inventory(candidate)==before['authoritative_before'] and sha(proof)==before['export_proof_sha256']
assert all(sha(ROOT/path)==digest for path,digest in observed_hashes.items())
result={'schema':1,'native_gui_process_executed':False,'GUI_observed_counts':counts(g),'authoritative_native_counts':counts(n),'same_exact_two_ignored_checks':True,'same_exact_five_parity_findings':True,'native_library_findings':summary(n),'GUI_library_findings':summary(g),'board_bytes_unchanged':True,'authoritative_candidate_inventory_unchanged':True,'authoritative_export_proof_unchanged':True,'explicit_rules_unchanged':True,'all_original_explicit_severities_unchanged':True,'all_original_explicit_netclass_values_unchanged':True,'GUI_metadata_added_keys':sorted(added),'GUI_metadata_changed_container_paths':sorted(changed),'GUI_netclass_schema_before_after':[a['net_settings']['meta']['version'],b['net_settings']['meta']['version']],'GUI_added_class_defaults':{name:{key:value for key,value in row.items() if key not in oldclasses[name]} for name,row in newclasses.items()},'report_and_input_sha256':observed_hashes,'conclusion':'Library-context diagnostic difference: five Native missing-library findings become one GUI loaded-library mismatch plus four absent library findings. No ignored-check/rule weakening, model-migration cause or GUI qualification is asserted.'}
(HERE/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:result[k] for k in ('GUI_observed_counts','authoritative_native_counts','board_bytes_unchanged','explicit_rules_unchanged','same_exact_two_ignored_checks','same_exact_five_parity_findings')},sort_keys=True))
