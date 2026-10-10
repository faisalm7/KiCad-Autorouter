"""Independent fixed recipe/predicate checks; no workers or source mutations."""
import copy, hashlib, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
AUTHOR=ROOT/'.runs/pic-severity-controls-draft-001'
sys.path.insert(0,str(AUTHOR))
spec=importlib.util.spec_from_file_location('severity_recipe_driver',AUTHOR/'driver.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
fx=d.fixture;checks=d.checks
out=Path(__file__).resolve().parent
before,total=d.source_binding();original=d.sx.read(d.SOURCE);project=d.read(d.SOURCE.with_suffix('.kicad_pro'))
records=[]
def check(label,value):
    if not value:raise AssertionError(label)
    records.append({'check':label,'passed':True})
def report():
    return {'violations':[],'unconnected_items':[],'schematic_parity':[],
        'ignored_checks':[{'key':k} for k in d.OBSERVED_IGNORED]}
def verdict(case,scene,raw):return checks.predicate(case,checks.summary(raw),raw,scene,list(d.OBSERVED_IGNORED))
baseline_tree=None
for case in fx.CASES:
    raw,changed,scene=fx.prepare(original,project,case);tree=d.sx.parse(raw.decode())
    check(case+': original stackup/layers/setup exact',all(d.sx.one(tree,k)==d.sx.one(original,k) for k in ('layers','setup')))
    delta=fx.project_delta(project,changed,case)
    check(case+': profile-only delta scope',bool(delta)==case.startswith('missing_') and changed['board']==project['board'])
    raw=report();target=None
    if case.startswith('missing_'):
        target={'type':'missing_tuning_profile','severity':'warning','items':[],
            'description':'Missing tuning profile (Net Class: '+scene['target_class']+', Tuning Profile: MissingOwnedProfile)'}
    elif case in ('board_edge_text','footprint_edge_text'):
        target={'type':'text_on_edge_cuts','severity':'error','items':[{'uuid':fx.uid('boardtext' if case=='board_edge_text' else 'fptext')}]}
    elif case=='pad_front_counterbore':
        target={'type':'track_on_post_machined_layer','severity':'error','items':[{'uuid':fx.uid('pad2')},{'uuid':fx.uid('trackSIGNAL_A')}]}
    if target is not None:raw['violations']=[target]
    check(case+': exact expected finding passes',verdict(case,scene,raw)['predicate_met'])
    wrong=copy.deepcopy(raw);wrong['violations'].append({'type':'unknown_provider','severity':'warning','items':[]})
    check(case+': unknown residual warning rejects',not verdict(case,scene,wrong)['predicate_met'])
    wrong=copy.deepcopy(raw);wrong['violations'].append({'type':'padstack_invalid','severity':'warning','items':[]})
    check(case+': critical residual warning rejects',not verdict(case,scene,wrong)['predicate_met'])
    wrong=copy.deepcopy(raw);wrong['ignored_checks']=wrong['ignored_checks'][:-1]
    check(case+': missing ignored-key rejects',not verdict(case,scene,wrong)['predicate_met'])
    if target is not None:
        wrong=copy.deepcopy(raw);wrong['violations'].append(copy.deepcopy(target))
        check(case+': duplicate target rejects',not verdict(case,scene,wrong)['predicate_met'])
        wrong=copy.deepcopy(raw);wrong['violations'][0]['items']=[{'uuid':'unrelated'}]
        check(case+': wrong target identity rejects',not verdict(case,scene,wrong)['predicate_met'])
    if case=='missing_default_profile':
        result=verdict(case,scene,report())
        check('Default omission is completed coverage probe, not provider detection',result['predicate_met'] and result['coverage_probe'] and not result['provider_detected'] and result['coverage_outcome']=='finding_omitted_despite_loaded_intent')
check('complete original 15-file inventory unchanged',d.source_binding()==(before,total))
receipt={'scope':'Pure recipes and invented raw findings only; no native execution, enforcement, or routing qualification.',
    'source_file_count':len(before),'source_bytes':total,'source_hashes':before,
    'author_sources':{n:hashlib.sha256((AUTHOR/n).read_bytes()).hexdigest() for n in d.HELPERS},
    'checks':records,'passed':True}
(out/'pure-recipe-audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'passed':True,'checks':len(records),'source_unchanged':True}))
