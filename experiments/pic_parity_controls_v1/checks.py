"""Local diagnostic classification over unchanged captured native report data."""
import copy,re
from autorouter import pipeline as p,floor_route as f
import fixture as fx
from native_summary import parse_data
IGNORED=('footprint_filters_mismatch','silk_edge_clearance','track_not_centered_on_via','tuning_profile_track_geometries')
KIND='footprint_symbol_field_mismatch'

def predicate(case,raw,log,baseline=None):
    native=parse_data(raw,fx.BOARD)
    if case not in fx.CASES:raise ValueError('unknown fixed case')
    # Require evidence that the CLI actually enabled parity, including positives.
    counts=re.findall(r'^Found ([0-9]+) schematic parity issues\s*$',log,re.M)
    if len(counts)!=1 or int(counts[0])!=len(raw['schematic_parity']):raise ValueError('parity log/count absent or inconsistent')
    if any(x in log.lower()for x in ('failed to fetch schematic netlist','fully annotated schematic','no netlist provided','skipping schematic parity')):raise ValueError('parity was skipped or unavailable')
    if sorted(x['key']for x in raw['ignored_checks'])!=list(IGNORED):raise ValueError('effective ignored checks changed')
    ordinary=copy.deepcopy(raw);ordinary['schematic_parity']=[]
    normal=parse_data(ordinary,fx.BOARD)
    if not p.native_accepted(normal):raise ValueError('non-parity native findings fail ordinary policy')
    # Sort whole records only; preserve every field/value and duplicate multiplicity.
    fingerprint={key:sorted(copy.deepcopy(raw[key]),key=f.canonical)for key in ('violations','unconnected_items','ignored_checks','included_severities')}
    if case!='original_parity' and (baseline is None or f.canonical(fingerprint)!=f.canonical(baseline)):raise ValueError('non-parity findings changed or baseline absent')
    rows=raw['schematic_parity'];want=1 if case=='mismatched_custom_field'else 0
    passed=len(rows)==want
    if want and passed:
        row=rows[0];description=row.get('description','');items=row['items']
        exact=f"Field '{fx.FIELD}' differs (PCB: '{fx.MISMATCH}', Schematic: '{fx.MATCH}')"
        passed=(row['type']==KIND and row['severity']=='warning' and row.get('excluded',False)is False and len(items)==1
                and isinstance(items[0],dict)and items[0].get('uuid')==fx.FP and description==exact)
    return {'predicate_met':bool(passed),'parity_count':len(rows),'parity_log_count':int(counts[0]),'expected_parity_count':want,'ordinary_fingerprint':fingerprint,'native':native,'routing_accepted':False}
