"""Nonsaving no-export same-load continuation; ROOT sequential native lane only.

Requires the shared final-mode paired diagnostic guard. It does not change
board/reference/class/layer/rules or qualify DSN transport/routing support.
"""
import json,sys
from collections import Counter
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/floor_context.py').is_file())
HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path[:0]=[str(ROOT),str(HERE)]
from autorouter import floor_context as fc,sexpr as sx
if __package__:
    from .worker import observe as base_observe
else:
    from worker import observe as base_observe

def source_footprints(tree):
    rows=[]
    for fp in sx.children(tree,'footprint'):
        refs=[n for n in sx.children(fp,'property') if sx.unquote(n[1])=='Reference']
        uid=sx.one(fp,'uuid')
        if len(refs)!=1 or uid is None or len(uid)!=2:raise ValueError('unambiguous original footprint identity required')
        rows.append({'uuid':sx.unquote(uid[1]),'reference':sx.unquote(refs[0][2]),'pad_count':len(sx.children(fp,'pad'))})
    if not rows or len(rows)>512 or len({r['uuid'] for r in rows})!=len(rows):raise ValueError('bounded unique footprint UUID census required')
    return sorted(rows,key=lambda row:row['uuid'])

def observe(board,pcbnew,original):
    result=base_observe(board,pcbnew);rows=[]
    pads=list(board.GetPads());footprints=list(board.GetFootprints())
    if len(pads)>10000 or len(footprints)>512:raise ValueError('native footprint/pad census ceiling')
    counts=Counter(str(pad.GetParentFootprint().m_Uuid.AsString()) for pad in pads)
    for fp in footprints:
        uid=str(fp.m_Uuid.AsString());rows.append({'uuid':uid,'reference':str(fp.GetReference()),'pad_count':counts.get(uid,0)})
    if set(counts)-{row['uuid'] for row in rows}:raise ValueError('native pad has no observed parent footprint')
    rows.sort(key=lambda row:row['uuid'])
    if rows!=original or len({r['uuid'] for r in rows})!=len(rows):raise ValueError('native/source footprint UUID/reference/pad census differs')
    references=Counter(row['reference'] for row in rows)
    groups=[{'reference':name,'footprints':[r for r in rows if r['reference']==name]} for name,n in sorted(references.items()) if n>1]
    result.update(footprints=rows,source_footprints=original,duplicate_reference_groups=groups,
                  duplicate_reference_export_hypothesis=bool(groups),dsn_export_attempted=False)
    return result

def collect_only(source,output,diagnostic):
    source,output,diagnostic=map(fc.canonical_path,(source,output,diagnostic))
    before=fc.inventory(source.parent);original=source_footprints(sx.read(source))
    def observer(native,pcbnew):return observe(native,pcbnew,original)
    # Shared helper performs one LoadBoard, both callbacks, full context and
    # nonsaving input checks. No duplicate native board load or exporter call.
    fc.collect('final',source,output,observation_output=diagnostic,observer=observer)
    context=json.loads(output.read_text());extra=json.loads(diagnostic.read_text());captured=extra.get('observation_before_export')
    if (not isinstance(captured,dict) or captured.get('footprints')!=original or captured.get('source_footprints')!=original
            or context.get('native_version')!='10.0.0' or extra.get('native_version')!='10.0.0'
            or context.get('units')!='integer nanometres' or extra.get('units')!='integer nanometres'
            or fc.inventory(source.parent)!=before or context.get('mode')!='final' or extra.get('mode')!='final'
            or context.get('source')!=str(source) or extra.get('source')!=str(source)
            or context.get('dsn_sha256') is not None or extra.get('dsn_sha256') is not None
            or context.get('input_hashes_before')!=before or context.get('input_hashes_after')!=before
            or extra.get('input_hashes_before')!=before or extra.get('input_hashes_after')!=before
            or extra.get('floor_context_sha256')!=fc.sha(output) or extra.get('same_loaded_board') is not True
            or extra.get('observation_before_export')!=extra.get('observation_after_export')
            or context.get('board_saved') is not False or extra.get('board_saved') is not False
            or context.get('routing_accepted') is not False or extra.get('routing_accepted') is not False):
        raise ValueError('no-export context/diagnostic/source binding differs')
    return context,extra

if __name__=='__main__':
    if len(sys.argv)!=4:raise ValueError('exact source/context/diagnostic arguments required')
    collect_only(*sys.argv[1:])
