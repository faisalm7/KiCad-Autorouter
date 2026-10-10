"""Pure adversarial draft review. No native calls, board writes or routing."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
DRAFT = ROOT/'.runs/thermal-generalization-draft-001/qualification-001'
sys.path.insert(0, str(DRAFT))
import copper_path as c
import attempt_paths_v2 as attempt

M = 1_000_000


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pad(uid, center):
    return {'uuid':uid, 'net_code':100, 'position_nm':center,
            'logical_terminal':['controlled-footprint', uid],
            'effective_hole':{'start_nm':center, 'end_nm':center, 'width_nm':800000},
            'drill_is_round':True, 'is_pth':True, 'orientation_degrees':0,
            'layers':[{'id':2, 'on_layer':True, 'flash_layer':True,
                       'shape_is_circle':True, 'size_nm':[1400000,1400000],
                       'offset_nm':[0,0], 'shape_position_nm':center}]}


def body(index, poly):
    return {'native_outline_index':index, 'layer_id':2, 'zone_uuid':'controlled-zone',
            'net_code':100, 'selected':True, 'holes_nm':[], 'hole_count':0,
            'native_total_arc_count':0, 'native_outer_closed':True, 'outer_nm':poly}


def scene():
    return {'api_error_count':0, 'source_unchanged':True,
            'layers':[{'id':2,'canonical':'B.Cu'}],
            'class':{'width_nm':500000}, 'native_max_error_nm':10000,
            'target_pad_uuid':'target', 'zone_uuid':'controlled-zone', 'net_code':100,
            'pads':[pad('target',[0,0]),pad('other',[2*M,0])],
            'vias':[{'uuid':'gap-drill', 'net_code':0, 'position_nm':[750000,-250000],
                     'drill_nm':100000, 'layer_membership':[2]}],
            'bodies':[body(0,[[-M,-M],[600000,-M],[600000,M],[-M,M]]),
                      body(1,[[900000,-M],[3*M,-M],[3*M,M],[900000,M]])]}


start = time.monotonic()
paths = ['copper_path.py','attempt_paths_v2.py','diagnose.py']
before = {name:digest(DRAFT/name) for name in paths}
g = scene()
result = attempt.run(g)
crossing = []
for proposal in result['path_certificate_candidates']:
    clear = c.farther_point_segment([750000,-250000], proposal['start_nm'],
                                    proposal['end_nm'], 50000+10000)
    if not clear:
        crossing.append(proposal)
wrong_net = copy.deepcopy(g)
wrong_net['pads'][0]['net_code'] = 999
wrong_net['bodies'][1]['net_code'] = 999
wrong_result = attempt.run(wrong_net)

box = [[0,0],[10*M,0],[10*M,10*M],[0,10*M]]
guard = lambda:c.Guard(seconds=1,operations=10000)
checks = {
    'valid_integer_leg_accepted':c.certified_leg([M,M],[9*M,9*M],box,[],10000,guard()),
    'exact_margin_boundary_rejected':not c.certified_leg([M,10000],[9*M,10000],box,[],10000,guard()),
    'drill_center_crossing_rejected':not c.certified_leg([M,5*M],[9*M,5*M],box,[{'center':[5*M,5*M],'radius':M}],10000,guard()),
    'subnanometre_distance_exact':c.point_segment_sq([2,0],[0,0],[4,1])==(4,17),
    'reviewed_sources_unchanged':before=={name:digest(DRAFT/name) for name in paths},
}
report = {'scope':'pure review of unqualified copper-path draft; no native or engine process',
          'source_sha256':before, 'audit_script_sha256':digest(Path(__file__)),
          'native_executed':False, 'routing_executed':False,
          'kernel_controls':checks,
          'wrapper_reproductions':{
              'bridge_hole_crossing':{'reproduced':bool(crossing),'input':g,'unsafe_proposals':crossing},
              'net_identity_mismatch':{'reproduced':bool(wrong_result['path_certificate_candidates']),
                                       'input':wrong_net,'emitted_count':len(wrong_result['path_certificate_candidates'])}},
          'interpretation':['Exact leg geometry is consistent with a positive-margin path proof given validated integer domain and complete physical holes.',
                            'A new bridge must itself be checked against drills before claiming an entire local connection.',
                            'Native observation identity/binding, target uniqueness, same zone/layer/net, complete physical hole census and final budget check remain qualification requirements.',
                            'Actual saved attempts emitted no proposals and correctly leave scene, global topology and routing acceptance false.'],
          'wall_seconds':time.monotonic()-start}
out=Path(__file__).resolve().parent/'audit.json'
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'kernel_controls':checks,'bridge_hole_crossing_reproduced':bool(crossing),
                  'net_identity_mismatch_reproduced':bool(wrong_result['path_certificate_candidates'])}))
