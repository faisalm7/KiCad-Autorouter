"""Owned-board qualification of the KiCad 10.0.7 live PCB path.

The existing installed runtime supplies the official IPC client, native tools
and shared validation. This experiment is separate from the saved-project
launcher and does not install a plugin or grant live writes to other boards.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'examples/owned-placement-routing/source'
NAME = 'owned-placement-ordinary'
SELECTION = {'J1', 'J2'}
TITLE = 'Copperpath · Open board'
STEP_NM = 1_000_000
REGION_NM = [8_000_000, 7_500_000, 30_000_000, 13_500_000]
IPC_TIMER_MS = 1800


class EditorContextChanged(ValueError):
    """The proposal needs a fresh inspection of the current editor state."""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, text):
    if not condition:
        raise ValueError(text)


def requested_offset(request, reference):
    """Interpret one explicit local instruction within the owned move scope."""
    if request is None:
        return STEP_NM, 0  # Preserve the earlier fixed-step experiment.
    example = f'Try “Move {reference} right by 0.5 mm.” Choose a direction and a distance up to 1 mm.'
    require(type(request) is str and len(request) <= 128, example)
    move = re.fullmatch(r'move (selected(?: part| footprint)?|[a-z]+[0-9]+) (left|right|up|down) by '
                        r'([0-9]{1,2}(?:\.[0-9]{1,6})?) *mm\.?',
                        ' '.join(request.strip().lower().split()), flags=re.ASCII)
    require(move is not None, example)
    component, direction, distance = move.groups()
    require(component.startswith('selected') or component.upper() == reference,
            f'{reference} is selected in KiCad. Change the request or read the intended selection again.')
    from autorouter.placement_transform import nm

    length = nm(distance, 1_000_000)
    require(0 < length <= STEP_NM, 'Choose a distance greater than zero and no more than 1 mm.')
    return {'left': (-length, 0), 'right': (length, 0),
            'up': (0, -length), 'down': (0, length)}[direction]


def board_file(editor_bytes):
    """Remove the redundant per-footprint clipboard headers, and only those."""
    from autorouter import sexpr
    from experiments.placement_native_proposal_v1 import contract

    tree = contract.read_board(editor_bytes)
    keys = ('version', 'generator', 'generator_version')
    headers = [sexpr.one(tree, key) for key in keys]
    require(all(headers), 'Missing KiCad serialization headers.')
    for footprint in sexpr.children(tree, 'footprint'):
        require(footprint[2:5] == headers, 'Unexpected clipboard footprint headers.')
        del footprint[2:5]
        require(not any(sexpr.children(footprint, key) for key in keys),
                'Duplicate footprint serialization headers.')
    return (sexpr.dump(tree) + '\n').encode()


def editor_scene(raw, selected=()):
    from autorouter import placement_view
    from experiments.placement_native_proposal_v1 import contract

    observation = contract.inspect_board(board_file(raw), scope=contract.THT_BASELINE_SCOPE)
    anchors = {row['uuid']: row['position_nm'] for row in observation['footprints'] if row['uuid'] in selected}
    return placement_view.scene(observation, anchors, list(anchors), REGION_NM,
        title='Open PCB in KiCad', state='Editor snapshot · existing copper remains protected',
        protection=(True, (), ()))


def checked_result_scene(raw, selected=()):
    try:
        return editor_scene(raw, selected)
    except Exception:
        # Readback is already definitive. An optional drawing cannot change it.
        return None


class Session:
    def __init__(self, run, runtime, *, direct_trial=False, source=None, connection=None):
        from autorouter import config as c, placement_clearance as pc, gui
        from kipy import KiCad
        from kipy.proto.common.types import DocumentType

        require(run.parent == ROOT / '.runs' and run.resolve() == run,
                'Use a fresh owned experiment under .runs.')
        require(c.ROOT == runtime and c.NATIVE_VERSION == '10.0.7',
                'The selected runtime must supply pinned KiCad 10.0.7.')
        self.run = run
        self.source = run / 'inspection' if source is None else source
        self.path = gui.saved_project_board(self.source / (NAME + '.kicad_pro'))
        for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch'):
            expected = pc.read_bytes(FIXTURE / (NAME + suffix))
            require(pc.read_bytes(self.path.with_suffix(suffix)) == expected,
                    'The open PCB must be the exact disposable owned example.')
        if connection is None:
            endpoint = os.environ.pop('KICAD_API_SOCKET', '')
            token = os.environ.pop('KICAD_API_TOKEN', '')
        else:
            endpoint, token = connection
        socket = Path(endpoint.removeprefix('ipc://'))
        require(bool(token) and socket.is_absolute(), 'Launch from the owned KiCad PCB toolbar.')
        info = socket.lstat()
        require(stat.S_ISSOCK(info.st_mode) and info.st_uid == os.getuid(),
                'Expected the launching user’s local PCB socket.')
        self.editor = KiCad(socket_path='ipc://' + str(socket), kicad_token=token,
                            timeout_ms=IPC_TIMER_MS)
        self.document_type = DocumentType.DOCTYPE_PCB
        version = self.editor.get_version()
        self.direct_trial = direct_trial
        self.direct_attempted = False
        expected = (10, 0, 8) if direct_trial else (10, 0, 7)
        require((version.major, version.minor, version.patch) == expected,
                'The launching KiCad editor version differs from the owned trial.')
        self.pcb = self.editor.get_board()
        self.doc_id = self.identity()
        self.plan = None
        self.displayed_selection = None
        self.applied = None
        self.interactive = None
        self.apply_disabled = False
        self.index = 0
        self.started = time.monotonic()
        self.initial = self.snapshot()
        capture = self.run / ('editor-' + self.initial['sha256'][:16] + '.kicad_pcb')
        if not capture.exists():
            with capture.open('xb') as output:
                output.write(self.initial['raw'])
        self.write('connected', editor_version='.'.join(map(str, expected)), original_disk=self.initial['disk'], editor_sha256=self.initial['sha256'],
                   capture=capture.name)

    def identity(self):
        docs = self.editor.get_open_documents(self.document_type)
        require(len(docs) == 1, 'Expected one open PCB in the launching editor.')
        doc = docs[0]
        require(doc.type == self.document_type and doc.board_filename == self.path.name
                and doc.project.name == NAME
                and Path(doc.project.path).resolve() == self.source,
                'The active PCB or project changed. Reopen Copperpath from the test board.')
        return doc.SerializeToString(deterministic=True)

    def disk(self):
        from autorouter import placement_clearance as pc

        return {suffix: digest(pc.read_bytes(self.path.with_suffix(suffix)))
                for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch')}

    def snapshot(self):
        from experiments.placement_native_proposal_v1 import contract

        require(self.identity() == self.doc_id, 'The active editor document changed.')
        disk = self.disk()
        raw = self.pcb.get_as_string().encode()
        contract.read_board(raw)
        require(self.identity() == self.doc_id and self.disk() == disk,
                'The document or saved inputs changed during capture.')
        require(not self.path.with_suffix('.kicad_dru').exists(),
                'A new custom rule file appeared. Live testing stopped.')
        return dict(raw=raw, sha256=digest(raw), disk=disk)

    def write(self, event, **facts):
        with (self.run / 'ipc-events.jsonl').open('a', encoding='utf-8') as log:
            print(json.dumps(dict(event=event, seconds=round(time.monotonic()-self.started, 4),
                                  **facts), sort_keys=True), file=log)

    def selected(self):
        from kipy.board_types import FootprintInstance

        items = self.pcb.get_selection()
        return [item for item in items if isinstance(item, FootprintInstance)]

    def inspect(self, *, board_view=False):
        from autorouter import sexpr

        if board_view:
            self.plan = None
            self.displayed_selection = None
        snapshot = self.snapshot()
        items = self.selected()
        selected = [item.reference_field.text.value for item in items]
        self.write('selection', refs=selected, editor_sha256=snapshot['sha256'],
                   disk_unchanged=snapshot['disk'] == self.initial['disk'])
        result = dict(project=NAME, selection=selected,
                    board_changed=sexpr.parse(snapshot['raw'].decode())
                    != sexpr.parse(self.initial['raw'].decode()))
        if board_view:
            identities = tuple(item.id.value for item in items)
            result['scene'] = editor_scene(snapshot['raw'], identities)
            result['saved_context'] = {'source': str(self.path), 'selection': list(identities),
                                       'files': {self.path.with_suffix(ext).name: digest
                                                 for ext, digest in snapshot['disk'].items()}}
            self.displayed_selection = (snapshot['sha256'], identities)
        return result

    def preview(self, request=None, *, board_view=False):
        from autorouter import sexpr
        from experiments.placement_native_proposal_v1 import contract

        self.plan = None
        require(not self.apply_disabled, 'A write needs inspection in KiCad before any further test.')
        snapshot = self.snapshot()
        require(snapshot['disk'] == self.initial['disk'],
                'Saved project files changed. Keep working in KiCad or reopen the saved-project workspace.')
        selection = self.selected()
        require(len(selection) == 1, 'Select one footprint in KiCad, then preview again.')
        item = selection[0]
        reference = item.reference_field.text.value
        require(reference in SELECTION, 'Select one of the movable footprints J1 or J2 in KiCad.')
        uid = item.id.value
        if request is not None and self.displayed_selection != (snapshot['sha256'], (uid,)):
            raise EditorContextChanged('The board or selection changed. Read selection in KiCad before previewing.')
        start = [item.position.x, item.position.y]
        target = [coordinate + offset for coordinate, offset in zip(start, requested_offset(request, reference))]
        options = dict(scope=contract.THT_BASELINE_SCOPE, selected=[uid], region_nm=REGION_NM)
        source = board_file(snapshot['raw'])
        observation = contract.inspect_board(source, scope=options['scope'])
        observed = next((part for part in observation['footprints'] if part['uuid'] == uid), None)
        if observed is None or observed['reference'] != reference or observed['position_nm'] != start:
            raise EditorContextChanged('The selected footprint differs from the live PCB. Read selection again.')
        contract.validate_moves(observation, {uid: target}, **options)
        expected = contract.translated_tree(source, {uid: target}, **options)
        if self.snapshot() != snapshot or [part.id.value for part in self.selected()] != [uid]:
            raise EditorContextChanged('The board or selection changed while preparing the move. Read selection again.')
        self.index += 1
        proposal = dict(id=self.index, ref=reference, uid=uid, from_nm=start, to_nm=target)
        self.plan = dict(info=proposal, snapshot=snapshot, source=source, expected=expected, options=options,
                         candidate=(sexpr.dump(expected) + '\n').encode())
        self.write('preview', **proposal, editor_sha256=snapshot['sha256'])
        if board_view:
            from autorouter import placement_view
            return dict(proposal, scene=placement_view.scene(observation, {uid: target}, [uid], REGION_NM,
                title=f'Proposed move · {reference}', state='Preview · check the exact move before applying',
                protection=(True, (), ())))
        return proposal

    def fresh(self, proposal):
        if self.plan is None or self.plan['info']['id'] != proposal:
            raise ValueError('Preview a new move before applying.')
        info = self.plan['info']
        try:
            if (self.snapshot() != self.plan['snapshot']
                    or [item.id.value for item in self.selected()] != [info['uid']]):
                raise EditorContextChanged('KiCad changed after preview. Read the selection and preview again.')
        except Exception:
            # Once freshness fails, even restoring the old inputs needs a new check.
            self.plan = None
            self.displayed_selection = None
            raise
        return info

    def reject(self):
        self.plan = None
        self.write('proposal_discarded', editor_sha256=self.snapshot()['sha256'])
        return {}

    def native_checks(self, plan):
        from autorouter import floor_route, gui, pipeline
        from autorouter import placement_clearance as pc
        from experiments.placement_native_proposal_v1 import contract

        output = self.run / ('native-move-' + uuid.uuid4().hex)
        from autorouter.runner import elapsed_time
        deadline = elapsed_time() + 40
        job = floor_route.FloorJob(output, 40, lambda: deadline - elapsed_time(),
                                   protect_local_settings=True)
        native = {}
        for name, raw in [('source', plan['source']), ('move', plan['candidate'])]:
            board = output / name / self.path.name
            board.parent.mkdir(mode=0o700)
            for suffix in ('.kicad_pro', '.kicad_sch'):
                data = pc.read_bytes(self.path.with_suffix(suffix))
                require(digest(data) == plan['snapshot']['disk'][suffix], 'Saved inputs changed.')
                board.with_suffix(suffix).write_bytes(data)
            board.write_bytes(raw)
            before = gui.source_inventory(board)
            result = job.drc(name + '-drc', board, save=False, schematic_parity=True)
            native[name] = floor_route.check_drc_stage(
                output, dict(steps=job.steps), name + '-drc', board,
                output / (name + '-drc-input') / board.name, False, before, schematic_parity=True)
            require(result == native[name], 'Native report readback differs.')
        contract.check_translation(plan['source'], plan['candidate'],
                                   {plan['info']['uid']: plan['info']['to_nm']}, **plan['options'])
        # This test board starts with open connections. Translation must not
        # create a new open, blocker, exclusion or warning. No routing claim.
        for key in ('opens', 'blocking', 'warnings', 'exclusions', 'ignored_checks'):
            require(native['source'][key] == native['move'][key], 'A Native finding count changed.')
        require(not native['move']['blocking'] and not native['move']['exclusions'],
                'Native found a blocking violation or excluded finding.')
        from autorouter import placement
        placement.finding_continuity(native['move'], native['source'],
            contract.inspect_board(plan['source'], scope=plan['options']['scope']),
            {plan['info']['uid']: plan['info']['to_nm']}, plan['options']['scope'])
        pipeline.save_json(output / 'checked.json', native)
        findings = native['move']
        summary = dict(opens=findings['opens'], warnings=findings['warnings'],
            ignored=len(findings['ignored_checks']),
            findings=[f.get('description', f['type']) for f in findings['findings']])
        self.write('native_checked', **summary, output=output.name)
        return summary

    def validate(self, proposal):
        info = self.fresh(proposal)
        plan = self.plan
        result = self.native_checks(plan)
        self.fresh(info['id'])
        plan['native'] = result
        return result

    def review_in_kicad(self, proposal):
        """Start manual native review without writing anything to the editor."""
        info = self.fresh(proposal)
        require(self.interactive is None, 'Finish or cancel the current move in KiCad first.')
        require('native' in self.plan, 'Check the exact preview before reviewing it in KiCad.')
        self.interactive = self.plan
        self.write('native_review_started', ref=info['ref'], target_nm=info['to_nm'],
                   editor_sha256=self.plan['snapshot']['sha256'])
        return {}

    def check_native_move(self):
        from kipy.errors import ApiError
        from kipy.proto.common import ApiStatusCode

        plan = self.interactive
        require(plan is not None, 'Open a checked move in KiCad first.')
        try:
            # GetSelection reports AS_BUSY while a native tool is open.
            self.pcb.get_selection()
            now = self.snapshot()
        except ApiError as exc:
            if exc.code == ApiStatusCode.AS_BUSY:
                raise ValueError('Finish or cancel the KiCad dialog, then check again.') from exc
            raise
        self.interactive = None
        if now == plan['snapshot']:
            self.write('interactive_unchanged', editor_sha256=now['sha256'])
            return dict(applied=False)
        self.plan = None
        if not unchanged_outside_move(plan, now):
            self.write('interactive_readback', exact=False, editor_sha256=now['sha256'])
            raise ValueError('The exact preview could not be verified. Inspect KiCad before continuing.')
        self.applied = plan['snapshot']
        self.apply_disabled = True
        self.write('interactive_readback', exact=True, editor_sha256=now['sha256'],
                   ref=plan['info']['ref'], target_nm=plan['info']['to_nm'], disk_unchanged=True)
        return dict(applied=True)

    def cancelled_transaction(self, proposal, *, partial_failure=False):
        """Owned fault control. This command never pushes a footprint update."""
        from kipy.geometry import Vector2
        from kipy.proto.common.commands import editor_commands_pb2 as commands
        from kipy.util import pack_any

        info = self.fresh(proposal)
        plan = self.plan
        self.plan = None
        item, = self.selected()
        item.position = Vector2.from_xy(*info['to_nm'])
        commit = self.pcb.begin_commit()
        try:
            require(self.snapshot() == plan['snapshot'], 'KiCad changed before the transaction.')
            if partial_failure:
                # First entry is a real staged update. The second references a
                # nonexistent footprint. Read every per-item result explicitly.
                cmd = commands.UpdateItems()
                cmd.header.document.CopyFrom(self.pcb._doc)
                cmd.items.append(pack_any(item.proto))
                item.proto.id.value = '9d4372ec-c454-427b-b027-578b5430ed70'
                cmd.items.append(pack_any(item.proto))
                response = self.editor._client.send(cmd, commands.UpdateItemsResponse)
                results = [row.status.code for row in response.updated_items]
                self.write('mixed_update_response', statuses=results)
                require(len(results) == 2 and results[0] != results[1], 'Expected a partial API update.')
            else:
                updated, = self.pcb.update_items(item)
                require(updated.id.value == info['uid']
                        and [updated.position.x, updated.position.y] == info['to_nm'],
                        'KiCad staged a different component position.')
            staged = self.snapshot()
            self.write('transaction_staged', snapshot_unchanged=staged == plan['snapshot'])
            require(staged == plan['snapshot'], 'Editor state changed before commit.')
        finally:
            self.apply_disabled = True
            self.pcb.drop_commit(commit)
            restored = self.snapshot() == plan['snapshot']
            self.write('transaction_dropped', unchanged=restored,
                       partial_failure=partial_failure)
            require(restored, 'Dropping the transaction changed the board. Inspect KiCad.')
            self.apply_disabled = False
        return dict(dropped=True)

    def check_undo(self, *, board_view=False):
        require(self.applied is not None, 'Apply a reviewed test move before verifying Undo.')
        now = self.snapshot()
        unchanged = now == self.applied
        self.write('undo_readback', exact=unchanged, editor_sha256=now['sha256'])
        require(unchanged, 'The PCB has not returned to its state before the move.')
        scene = checked_result_scene(now['raw']) if board_view else None
        self.applied = None
        self.apply_disabled = False
        return dict(undo_verified=True, scene=scene) if board_view else dict(undo_verified=True)

    def apply_direct_trial(self, proposal, *, board_view=False):
        """One guarded, approved IPC update of the exact owned 10.0.8 board."""
        from kipy.geometry import Vector2

        info = self.fresh(proposal)
        plan = self.plan
        require(self.direct_trial and not self.direct_attempted and not self.apply_disabled and 'native' in plan,
                'Check the exact move on the isolated 10.0.8 test board first.')
        item, = self.selected()
        item.position = Vector2.from_xy(*info['to_nm'])
        # A missing response does not establish whether KiCad opened a transaction.
        self.apply_disabled = True
        try:
            commit = self.pcb.begin_commit()
        except Exception:
            self.plan = None
            self.write('begin_commit_unconfirmed')
            raise ValueError('KiCad did not confirm opening the transaction. Inspect KiCad before further work.') from None
        try:
            self.fresh(proposal)
            updated, = self.pcb.update_items(item)
            require(updated.id.value == info['uid']
                    and [updated.position.x, updated.position.y] == info['to_nm'],
                    'KiCad staged a different component or position.')
            self.fresh(proposal)
        except Exception:
            self.plan = None
            try:
                self.pcb.drop_commit(commit)
                require(self.snapshot() == plan['snapshot'], 'The staged change did not drop exactly.')
            except Exception:
                self.write('drop_commit_unconfirmed')
                raise ValueError('KiCad could not verify discarding the staged move. Further moves are disabled.') from None
            self.apply_disabled = False
            self.write('staged_move_discarded', exact=True)
            raise
        # An ambiguous push cannot authorize another write or a whole-board reload.
        self.plan = None
        self.direct_attempted = True
        self.applied = plan['snapshot']
        self.pcb.push_commit(commit, 'Copperpath checked component move')
        now = self.snapshot()
        exact = unchanged_outside_move(plan, now)
        with (self.run / 'direct-editor-readback.kicad_pcb').open('xb') as stream:
            stream.write(now['raw'])
        self.write('direct_readback', exact=exact, editor_sha256=now['sha256'],
                   expected_sha256=digest(plan['candidate']), disk_unchanged=now['disk'] == plan['snapshot']['disk'])
        result = dict(applied=True, exact=exact)
        if board_view and exact:
            result['scene'] = checked_result_scene(now['raw'], [info['uid']])
        return result


def unchanged_outside_move(plan, after):
    from autorouter import sexpr

    expected, actual = plan['expected'], sexpr.parse(board_file(after['raw']).decode())
    # The editor may enumerate top-level items in a different order.
    return (after['disk'] == plan['snapshot']['disk'] and actual[0] == expected[0]
            and sorted(sexpr.dump(item) for item in actual[1:])
            == sorted(sexpr.dump(item) for item in expected[1:]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--diagnostics', action='store_true')
    parser.add_argument('--direct-1008-trial', action='store_true')
    args = parser.parse_args()
    sys.path.insert(0, str(args.runtime))
    from autorouter import config as c, gui

    session = Session(args.run, args.runtime, direct_trial=args.direct_1008_trial)
    argv = [str(c.PYTHON), '-B', str(Path(__file__).with_name('panel.py'))]
    if args.diagnostics:
        argv.append('--diagnostics')
    if args.direct_1008_trial:
        argv.append('--direct-1008-trial')
    view = subprocess.Popen(argv,
        cwd=args.run, env=gui.child_environment(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        text=True, encoding='utf-8')
    operations = {'inspect': session.inspect, 'preview': session.preview,
        'discard': session.reject, 'validate': session.validate,
        'open_move': session.review_in_kicad, 'check_live_move': session.check_native_move,
        'undo': session.check_undo}
    if args.diagnostics:
        operations.update(drop_test=session.cancelled_transaction,
                          partial_test=lambda proposal: session.cancelled_transaction(proposal, partial_failure=True))
    if args.direct_1008_trial:
        operations['apply_direct'] = session.apply_direct_trial
    state = dict(panel_pid=view.pid, ipc_pid=os.getpid(), diagnostics=args.diagnostics)
    launch = args.run / ('companion-' + str(view.pid) + '.json')
    with launch.open('x') as output:
        json.dump(state, output)
    (args.run / 'companion.json').write_text(json.dumps(state))
    try:
        for line in view.stdout:
            name = 'unknown'
            try:
                request = json.loads(line)
                name = request['command']
                values = operations[name](*request.get('args', []))
                result = dict(ok=True, value=values)
            except Exception as exc:
                # Transport details may contain the private endpoint.
                message = str(exc) if type(exc) is ValueError and str(exc) else type(exc).__name__
                session.write('operation_refused', command=name, reason=message)
                result = dict(ok=False, message=message)
            print(json.dumps(result), file=view.stdin, flush=True)
    finally:
        view.stdin.close()
        view.wait(timeout=4)


if __name__ == '__main__':
    main()
