"""Lead-only, pinned 10.0.7 SWIG observation/translation of an owned task copy.

Never imported by ordinary Python tests. No native execution at import time.
The whole saved board is independently compared; normalization is a refusal.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def exact_native_layer(item, expected):
    """Native layer identity is an enum, not its version-specific display name."""
    actual = item.GetLayer()
    return type(actual) is int and type(expected) is int and actual == expected


def capture(native, pcbnew, raw, contract, fc):
    expected = contract.inspect_board(raw)
    need = contract.need
    need(native.GetCopperLayerCount() == 2, 'Native two-copper census differs')
    need(not list(native.GetTracks()), 'Native task unexpectedly contains tracks/vias')

    def uid(item):return str(item.m_Uuid.AsString())
    def xy(point):
        values = [point.x, point.y]
        need(all(type(v) is int and abs(v) <= 2_000_000_000 for v in values), 'Exact native integer coordinates required')
        return values
    def integer(value):
        need(type(value) is int and 0 <= value <= 2_000_000_000, 'Exact native integer dimension required')
        return value
    def boolean(value):
        need(type(value) is bool, 'Exact native Boolean required')
        return value
    def shape(item):
        need(isinstance(item, pcbnew.PCB_SHAPE) and item.GetShape() == pcbnew.SHAPE_T_RECT,
             'Native shape is not an exact rectangle')
        return dict(uuid=uid(item), bounds_nm=xy(item.GetStart()) + xy(item.GetEnd()), stroke_nm=integer(item.GetWidth()))

    drawings = list(native.GetDrawings())
    need(len(drawings) == 1 and exact_native_layer(drawings[0], pcbnew.Edge_Cuts), 'Native edge/cutout census differs')
    edge = shape(drawings[0]); need(edge == expected['outline'], 'Native/source rectangle differs')
    pads_by_fp = {}; pad_ids = set(); netcodes = {}
    for pad in native.GetPads():
        pid = uid(pad); parent = pad.GetParentFootprint()
        need(pid not in pad_ids and len(pad_ids) < 32 and parent is not None, 'Native pad census differs')
        pad_ids.add(pid)
        need(pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and not pad.IsFlipped()
             and pad.GetOrientationDegrees() == 0 and xy(pad.GetFPRelativePosition()) == [0, 0], 'Native centred unrotated PTH pad required')
        sizes = []
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            need(pad.IsOnLayer(layer) and pad.GetShape(layer) == pcbnew.PAD_SHAPE_CIRCLE
                 and xy(pad.GetOffset(layer)) == [0, 0], 'Native circular outer pad geometry differs')
            sizes.append(xy(pad.GetSize(layer)))
        need(sizes[0] == sizes[1], 'Layer-specific pad size differs')
        netcode = integer(pad.GetNetCode()); need(netcode > 0, 'Positive native net required')
        netcodes[pid] = netcode
        pads_by_fp.setdefault(uid(parent), []).append(dict(uuid=pid, number=str(pad.GetNumber()), net=str(pad.GetNetname()),
            position_nm=xy(pad.GetPosition()), size_nm=sizes[0], drill_nm=xy(pad.GetDrillSize())))
    footprints = []; ids = set()
    for fp in native.GetFootprints():
        identity = uid(fp)
        need(identity not in ids and len(ids) < 16, 'Native footprint UUID census differs'); ids.add(identity)
        need(fp.GetOrientationDegrees() == 0 and boolean(fp.IsFlipped()) is False
             and exact_native_layer(fp, pcbnew.F_Cu) and not list(fp.Zones()), 'Native front/unrotated footprint scope differs')
        graphics = list(fp.GraphicalItems())
        need(len(graphics) == 1 and exact_native_layer(graphics[0], pcbnew.F_CrtYd), 'Native courtyard census differs')
        footprints.append(dict(uuid=identity, reference=str(fp.GetReference()), position_nm=xy(fp.GetPosition()),
            angle=0, side='front', locked=boolean(fp.IsLocked()), courtyard=shape(graphics[0]),
            pads=sorted(pads_by_fp.get(identity, []), key=lambda r: r['uuid'])))
    footprints.sort(key=lambda r: r['uuid'])
    need(footprints == expected['footprints'] and set(pads_by_fp) <= ids, 'Native/source footprint, pad, net or geometry differs')
    areas = fc.observe_areas(native, pcbnew)
    need(areas['footprint_zone_count'] == areas['footprint_rulearea_count'] == 0, 'Native footprint area unsupported')
    by_id = {r['uuid']: r for r in areas['zones']}
    need(len(by_id) == len(areas['zones']) == len(expected['zones']), 'Native zone population differs')
    for row in expected['zones']:
        observed = by_id.get(row['uuid'])
        need(observed is not None and all(observed.get(k) == value for k, value in row.items()), 'Native/source zone geometry differs')
        need(observed['is_rule_area'] is False and observed['placement_enabled'] is False
             and all(value is False for value in observed['disallow'].values()), 'Native keepout/placement rule unsupported')
    return expected, dict(native_pad_netcodes=netcodes, actual_native_areas=areas)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--runtime', required=True); ap.add_argument('--request', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args(argv)
    runtime = Path(args.runtime); root = Path(__file__).resolve().parents[2]
    sys.dont_write_bytecode = True; sys.path[:0] = [str(runtime), str(root)]
    from autorouter import config as c, pipeline as p, floor_route as f, floor_context as fc
    from autorouter import handoff as h, placement_clearance as pc
    from experiments.placement_native_proposal_v1 import contract
    need = contract.need
    need(c.ROOT == runtime and c.NATIVE_VERSION == '10.0.7'
         and Path(sys.executable).resolve() == c.PYTHON.resolve(), 'Pinned installed 10.0.7 interpreter required')
    request, output = h.real_path(args.request), h.real_path(args.output, existing=False)
    spec = f.read_json(request)
    need(set(spec) == {'schema','mode','board','source_hashes','candidate','moves_nm','job','job_identity',
                       'runtime_manifest_sha256','wrapper_sha256','code_sha256'}, 'Exact worker request required')
    need(type(spec['schema']) is int and spec['schema'] == 1 and spec['mode'] in ('capture', 'translate'), 'Worker mode/schema differs')
    job = h.real_path(spec['job']); owner = dict(destination=job, directory_identity=tuple(spec['job_identity']))
    need(h.owned_destination(owner) == job and request.parent == output.parent == job, 'Owned worker paths differ')
    board = h.real_path(spec['board']); need(job in board.parents and request.parent != board.parent, 'Owned isolated source required')
    candidate = h.real_path(spec['candidate']) if spec['candidate'] is not None else None
    need((candidate is not None) == (spec['mode'] == 'translate'), 'Translate requires explicit owned copy')
    if candidate is not None:
        need(candidate != board and candidate.parent != board.parent and job in candidate.parents
             and pc.inventory(candidate.parent) == spec['source_hashes'], 'Translation target must be a distinct exact owned copy')
    wrapper = c.PCBNEW.with_name('pcbnew.py')

    def fresh():
        h.owned_destination(owner)
        need(pc.inventory(board.parent) == spec['source_hashes'], 'Worker source changed')
        need(p.sha(runtime / 'runtime-distribution.json') == spec['runtime_manifest_sha256'], 'Runtime manifest changed')
        need(p.sha(wrapper) == spec['wrapper_sha256'], 'Native SWIG wrapper changed')
        need(all((name.startswith('experiments/placement_native_proposal_v1/') or name.startswith('experiments/constrained_placement_v1/'))
                 and '..' not in Path(name).parts and p.sha(h.real_path(root / name)) == value for name, value in spec['code_sha256'].items()), 'Probe code changed')
        need(f.read_json(request) == spec, 'Worker request changed')
        p.check_recorded_tool_pins(p.tool_manifest())

    record = dict(schema=1, status='failed', accepted=False, routing_accepted=False,
                  native_version='10.0.7', source=str(board), source_hashes=spec['source_hashes'],
                  request_sha256=p.sha(request), board_saved=False, actual_native_observation=False)
    try:
        fresh()
        import pcbnew, _pcbnew
        need(pcbnew.GetBuildVersion() == '10.0.7' and Path(pcbnew.__file__).resolve() == wrapper.resolve()
             and Path(_pcbnew.__file__).resolve() == c.PCBNEW.resolve(), 'Loaded Native module identity differs')
        raw = pc.read_bytes(board, contract.MAX_BYTES); native = pcbnew.LoadBoard(str(board))
        need(native is not None, 'Native load failed')
        observed, details = capture(native, pcbnew, raw, contract, fc)
        record.update(observation=observed, details=details, actual_native_observation=True)
        if candidate is not None:
            contract.validate_moves(observed, spec['moves_nm'])
            expected_tree = contract.translated_tree(raw, spec['moves_nm'])
            expected_raw = (contract.sx.dump(expected_tree) + '\n').encode()
            footprints = {str(fp.m_Uuid.AsString()): fp for fp in native.GetFootprints()}
            need(set(spec['moves_nm']) == set(contract.SELECTED), 'Exact prospectively selected UUIDs required')
            for identity, target in spec['moves_nm'].items():
                need(not footprints[identity].IsLocked(), 'Native locked footprint cannot move')
                footprints[identity].SetPosition(pcbnew.VECTOR2I(*target))
            capture(native, pcbnew, expected_raw, contract, fc)
            pcbnew.SaveBoard(str(candidate), native); record['board_saved'] = True
            written = pc.read_bytes(candidate, contract.MAX_BYTES)
            record['saved_candidate_sha256'] = hashlib.sha256(written).hexdigest()
            record['immutable_check'] = contract.check_translation(raw, written, spec['moves_nm'])
            capture(pcbnew.LoadBoard(str(candidate)), pcbnew, written, contract, fc)
            need({k:v for k,v in pc.inventory(candidate.parent).items() if k != board.name}
                 == {k:v for k,v in spec['source_hashes'].items() if k != board.name}, 'Native save changed sidecars')
        else:
            need(spec['moves_nm'] == {}, 'Capture cannot carry transforms')
        fresh(); record['status'] = 'observed' if candidate is None else 'translated_copy'
    except (Exception, KeyboardInterrupt) as exc:
        record.update(reason=type(exc).__name__ + ': ' + str(exc))
    h.owned_destination(owner)
    need(not output.exists(), 'Worker report already exists')
    p.save_json(output, record)
    return 0 if record['status'] in ('observed', 'translated_copy') else 2


if __name__ == '__main__':
    raise SystemExit(main())
