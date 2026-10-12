"""Pure scoped review: actual source bytes, synthetic predicates, no native jobs."""
from pathlib import Path
import ast, copy, hashlib, json, math, subprocess, sys, unittest

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
HERE = ROOT / 'experiments/pic_custom_native_controls_v1'
sys.dont_write_bytecode = True
sys.path[:0] = [str(HERE), str(ROOT)]
import driver as d
import clearance_controls as cc
import recipes as r
import test_clearance_controls as tests
from test_controls import native_report, summary

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def inventory():
    return {str(path.relative_to(ROOT)): sha(path) for path in
            [*(HERE / name for name in d.HELPERS), *sorted(d.SOURCE.parent.rglob('*'))]
            if path.is_file()}
before = inventory()
original = d.sx.read(d.SOURCE)
project = d.read(d.SOURCE.with_suffix('.kicad_pro'))
checks = []
def check(name, condition):
    checks.append({'name': name, 'passed': bool(condition)})
    assert condition, name

geometry = []
for case, (gap, override, positive) in cc.CASES.items():
    raw, scene = cc.prepare(original, case, 'front0')
    target = next(x for x in scene['pads'] if x['id'] == 'CONCAVE')
    foreign = next(x for x in scene['tracks'] if x['id'] == 'FOREIGN_TRACK')
    contact = next(x for x in scene['tracks'] if x['id'] == 'CONTACT_TRACK')
    a, b = foreign['start'], foreign['end']
    copper_d2 = r.segment_gap2(a, b, target['polygon'])
    anchor_d2 = r.segment_gap2(a, b, r.move(r.ANCHOR, target['at']))
    contact_d2 = min(r.distance2(a,contact['start'],contact['end']),
                     r.distance2(b,contact['start'],contact['end']),
                     r.distance2(contact['start'],a,b),r.distance2(contact['end'],a,b))
    check(case + ': exact flat-edge capsule', copper_d2 == (gap+250000)**2)
    check(case + ': target anchor clear', anchor_d2 > (250000+800000)**2)
    check(case + ': other-net track clear', not r.intersects(a,b,contact['start'],contact['end']) and contact_d2 > (500000+280000)**2)
    check(case + ': both foreign terminals retained', all(r.on(a,b,pad['at']) for pad in scene['pads'] if pad['net']=='FOREIGN'))
    check(case + ': no foreign short', copper_d2 > 250000**2)
    geometry.append({'case':case,'gap_nm':gap,'foreign_end_nm':list(b),
        'centerline_to_copper_squared_nm':str(copper_d2),
        'capsule_to_anchor_gap_nm':math.sqrt(anchor_d2)-250000,
        'capsule_to_other_track_gap_nm':math.sqrt(contact_d2)-500000,
        'fixture_sha256':hashlib.sha256(raw).hexdigest(),
        'footprint_override_nm':override,'expected_native_pass':positive})

predicates = []
for case in cc.CASES:
    scene = cc.prepare(original,case,'front0')[1]
    raw = native_report('positive' if cc.CASES[case][2] else 'foreign_intrusion',scene,list(d.OBSERVED_IGNORED))
    check(case + ': unchanged synthetic predicate', cc.predicate(case,summary(raw),raw,scene,list(d.OBSERVED_IGNORED))[0])
    for mutation in ('shorting_not_clearance','companion_mask','wrong_pair','unrelated_open','unknown_warning','critical_warning','ignored_missing'):
        changed = copy.deepcopy(raw)
        if mutation in ('shorting_not_clearance','companion_mask','wrong_pair') and cc.CASES[case][2]: continue
        if mutation == 'shorting_not_clearance': changed['violations'][0]['type']='shorting_items'
        if mutation == 'companion_mask':
            mask=copy.deepcopy(changed['violations'][0]);mask['type']='solder_mask_bridge';changed['violations'].append(mask)
        if mutation == 'wrong_pair': changed['violations'][0]['items'][0]['uuid']=scene['pads'][0]['uuid']
        if mutation == 'unrelated_open': changed['unconnected_items']=[{'type':'unconnected_items','severity':'error','items':[{'uuid':'unrelated'}]}]
        if mutation == 'unknown_warning': changed['violations'].append({'type':'unknown_provider','severity':'warning','items':[]})
        if mutation == 'critical_warning': changed['violations'].append({'type':'padstack_invalid','severity':'warning','items':[]})
        if mutation == 'ignored_missing': changed['ignored_checks'].pop()
        frozen=copy.deepcopy(changed)
        accepted=cc.predicate(case,summary(changed),changed,scene,list(d.OBSERVED_IGNORED))[0]
        check(case+': reject '+mutation, not accepted and changed == frozen)
        predicates.append({'case':case,'mutation':mutation,'predicate':accepted,'raw_unmodified':changed==frozen})

check('shared 180s/32MiB caps', (d.SECONDS,d.LIMIT,d.RESERVE)==(180,32*1024**2,2*1024**2))
check('four fixed front-only cases', cc.ORDER==tuple(('front0',case) for case in cc.CASES) and len(cc.ORDER)==4)
check('original six-case protocol retained', d.protocol()==d.read(HERE/'PROTOCOL.json'))
check('new exact protocol retained', d.protocol(cc.SUITE)==d.read(HERE/'CLEARANCE_PROTOCOL.json'))
check('paired prerequisites independently chosen', cc.POSITIVE['class_260_negative']=='class_290_positive' and cc.POSITIVE['override_240_negative']=='override_260_positive')
check('VCC original POWER mapping', any(row.get('netclass')=='POWER' and row.get('pattern')=='VCC' for row in project['net_settings']['netclass_patterns']))

old = subprocess.run(['git','show','HEAD:experiments/pic_custom_native_controls_v1/driver.py'],cwd=ROOT,text=True,capture_output=True,check=True).stdout
def definitions(text):
    return {node.name:ast.dump(node,include_attributes=False) for node in ast.parse(text).body if isinstance(node,(ast.FunctionDef,ast.ClassDef))}
past,now=definitions(old),definitions((HERE/'driver.py').read_text())
for name in ('ControlJob','publish','source_binding','snapshot','drc_binding','observe_argv','drc_argv','cpu','inventory','size','owned'):
    check('reused lifecycle AST unchanged: '+name, past[name]==now[name])

with (OUT/'focused-tests.log').open('w') as stream:
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(tests.ClearanceControls))
check('four existing focused pure test methods', result.wasSuccessful() and result.testsRun==4)
after=inventory()
check('original15 files and all helper bytes unchanged', after==before)
output={'schema':1,'scope':'Independent pure geometry/design and synthetic predicate review. No native, Java, network, routing or production edits.',
    'passed':all(row['passed'] for row in checks),'checks':checks,'geometry':geometry,'predicate_falsifiers':predicates,
    'source_sha256':before,'source_unchanged':before==after,'original_file_count':len([x for x in before if x.startswith('.data/')]),
    'planned_eight_complete_copy_bytes':8*1366598,'native_executed':False,'routing_accepted':False,
    'limitations':['Actual local-override effect remains untested in this prospective batch.','No independent native GetLocalClearance observation is added; exact authored AST plus class census and pairwise DRC are the tested contract.','Finite material sampling is not atomic authentication.']}
(OUT/'review.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'passed':output['passed'],'geometry_cases':len(geometry),'focused_test_methods':result.testsRun,'all_checks':len(checks),'native_executed':False}))
