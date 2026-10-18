"""Diagnostic wrapper only; not a production Native worker or acceptance path.

SPDX-License-Identifier: GPL-3.0-or-later
Temporarily fixes existing task copper for one export/import invocation. Uses
the ordinary worker for all other behavior and restores locks before emission.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pcbnew
from autorouter import native
from autorouter.floor_context import route_width


def census(board):
    rows = {}
    for item in board.GetTracks():
        key = str(item.m_Uuid.AsString())
        if key in rows or len(rows) >= 100000:
            raise ValueError('unique bounded Native task copper required')
        def xy(value): return [int(value.x), int(value.y)]
        row = dict(uuid=key, kind=str(item.GetClass()), locked=item.IsLocked(),
                   net=str(item.GetNetname()), width_nm=route_width(item, pcbnew))
        if isinstance(item, pcbnew.PCB_VIA):
            row.update(at_nm=xy(item.GetPosition()), drill_nm=int(item.GetDrillValue()),
                       top=int(item.TopLayer()), bottom=int(item.BottomLayer()),
                       via_type=int(item.GetViaType()))
        else:
            row.update(start_nm=xy(item.GetStart()), end_nm=xy(item.GetEnd()), layer=int(item.GetLayer()))
            if isinstance(item, pcbnew.PCB_ARC): row['mid_nm'] = xy(item.GetMid())
        if type(row['locked']) is not bool:
            raise ValueError('Native typed lock required')
        rows[key] = row
    return rows


def wrap(action, function):
    def call(board, destination):
        before = census(board)
        events = dict(before=before)
        cause = None
        result = None
        try:
            for item in board.GetTracks(): item.SetLocked(True)
            fixed = census(board)
            if fixed != {k: dict(v, locked=True) for k, v in before.items()}:
                raise ValueError('fixing task copper changed Native geometry')
            events['fixed'] = fixed
            result = function(board, destination)
            after = census(board)
            if action == 'export':
                if after != fixed: raise ValueError('export changed fixed Native copper')
            elif any(after.get(k) != v for k, v in fixed.items()):
                raise ValueError('SES import changed/missed fixed original copper')
            events['after_operation'] = after
        except BaseException as exc:
            cause = exc
        finally:
            current = {str(item.m_Uuid.AsString()): item for item in board.GetTracks()}
            if len(current) != len(list(board.GetTracks())) or not set(before) <= set(current):
                raise ValueError('cannot safely restore task copper locks') from cause
            for key, row in before.items(): current[key].SetLocked(row['locked'])
            restored = census(board)
            if any(restored.get(k) != v for k, v in before.items()):
                raise ValueError('task copper restoration changed original Native geometry') from cause
            events['restored'] = restored
            path = Path(sys.argv[3]).with_suffix('.task-fixed-probe.json')
            with path.open('x') as stream:
                json.dump(dict(schema=1, action=action, native_version=pcbnew.GetBuildVersion(),
                               diagnostic_only=True, production_admitted=False,
                               operation_succeeded=result is True, events=events,
                               error=None if cause is None else type(cause).__name__+': '+str(cause)), stream, indent=2)
                stream.write('\n')
        if cause is not None: raise cause
        return result
    return call


if __name__ == '__main__':
    if pcbnew.GetBuildVersion() != '10.0.0' or sys.argv[1] not in ('export', 'import'):
        raise ValueError('bounded production-version export/import probe required')
    name = 'ExportSpecctraDSN' if sys.argv[1] == 'export' else 'ImportSpecctraSES'
    setattr(pcbnew, name, wrap(sys.argv[1], getattr(pcbnew, name)))
    native.main()
