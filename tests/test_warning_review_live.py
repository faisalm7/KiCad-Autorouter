"""Live acknowledgement proof controls with synthetic Native process seams.

Actual PCB qualification remains a separate installed/native gate.
"""
import copy,json,os,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import review_export as e,handoff as h,pipeline as p,sexpr as sx,gui
from tests import test_review_export as base
from tests import test_gui as gt

def finding(track_uuid='22222222-2222-4222-8222-222222222222',x=1.):
    return dict(type='connection_width',severity='warning',description='Same minimum0.1500mm/actual0.0790mm (B.Cu)',items=[
        dict(uuid='11111111-1111-4111-8111-111111111111',description='Via [SIG] on F.Cu - B.Cu',pos=dict(x=0.,y=0.)),
        dict(uuid=track_uuid,description='Track [SIG] on B.Cu, length 0.2000 mm',pos=dict(x=x,y=0.))])

def native(value):
    return dict(opens=0,blocking=0,warnings=1,exclusions=0,ignored_checks=[],findings=[value])

class WarningDeltaControls(unittest.TestCase):
    def setUp(self):
        self.old=native(finding());self.new=native(finding('33333333-3333-4333-8333-333333333333',2.))

    def test_retains_both_raw_lists_and_delta_without_equivalence_or_authority(self):
        before=copy.deepcopy((self.old,self.new));packet=e.warning_review_delta(self.old,self.new)
        self.assertEqual((self.old,self.new),before)
        self.assertEqual(packet['previous_findings'],self.old['findings']);self.assertEqual(packet['fresh_findings'],self.new['findings'])
        self.assertFalse(packet['findings_equivalent'])
        packet['delta']['fresh']['items'][1]['pos']['x']=77
        self.assertEqual(self.new['findings'][0]['items'][1]['pos']['x'],2.)

    def test_counts_rules_finding_type_description_or_anchor_changes_are_not_pending(self):
        def changed(fn):
            value=copy.deepcopy(self.new);fn(value);return value
        mutations=[lambda n:n.update(opens=1),lambda n:n.update(blocking=1),lambda n:n.update(warnings=2),
            lambda n:n.update(exclusions=1),lambda n:n.update(ignored_checks=[dict(key='clearance')]),
            lambda n:n['findings'][0].update(type='clearance'),lambda n:n['findings'][0].update(severity='error'),
            lambda n:n['findings'][0].update(description='different physical/rule warning'),lambda n:n['findings'][0].update(excluded=True),
            lambda n:n['findings'][0]['items'][0]['pos'].update(x=.5),lambda n:n['findings'][0]['items'][1].update(description='Track [+3V3] on B.Cu, length 0.2000 mm'),
            lambda n:n['findings'][0]['items'][1].update(description='Track [SIG] on F.Cu, length 0.2000 mm'),
            lambda n:n['findings'][0]['items'][1].update(uuid='malformed'),lambda n:n['findings'][0]['items'][1]['pos'].update(x=float('nan')),
            lambda n:n['findings'][0]['items'][1].update(extra='unknown')]
        for fn in mutations:
            with self.subTest(mutation=mutations.index(fn)),self.assertRaises(p.Rejected):e.warning_review_delta(self.old,changed(fn))

    def test_multiple_missing_or_unanchored_warning_changes_refuse(self):
        for old,new in [(self.old,self.old),
            (native(finding()),dict(self.new,findings=[])),
            (dict(self.old,findings=self.old['findings']*2,warnings=2),dict(self.new,findings=self.new['findings']*2,warnings=2))]:
            with self.subTest(old=old),self.assertRaises(p.Rejected):e.warning_review_delta(old,new)


def response(event, *_):
    return dict(kind='autorouter.warning-review-response.v1', decision='accept_updated_findings',
        nonce=event['nonce'], pending_sha256=event['pending_sha256'], delta_sha256=event['delta_sha256'])


class LiveWarningControls(unittest.TestCase):
    def setUp(self):
        base.ExportControls.setUp(self)
        self.warning = finding()
        self.native['findings'] = [copy.deepcopy(self.warning)]
        board = Path(self.report['candidate'])
        tree = sx.read(board)
        tree += [sx.parse('(via (at 0 0) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1) (uuid "11111111-1111-4111-8111-111111111111"))')]
        for digit, x in [('2', 1), ('3', 2)]:
            uid = digit*8+'-'+digit*4+'-4'+digit*3+'-8'+digit*3+'-'+digit*12
            tree.append(sx.parse('(segment (start %s 0) (end %s 0) (width 0.25) (layer "B.Cu") (net 1) (uuid "%s"))' % (x, x+.2, uid)))
        sx.write(board, tree)
        self.report['native'] = self.native
        self.report['candidate_sha256'] = p.sha(board)
        self.identity['candidate_sha256'] = self.report['candidate_sha256']
        p.save_json(self.receipt, self.report)
        self.review = self.root/'second-review'
        h.review_copy(self.receipt, self.review)
        self.choice = self.root/'second-intent/choice.json'
        h.review_choice(self.review/'review.json', self.choice.parent, 'accept')
        self.output = self.root/'live-export'
        self.native_mode = 'warning-detail'
        self.inputs = {str(path): e.witness(path) for path in (self.source, self.run, self.review, self.choice.parent)}

    def native_run(self, argv, *, cwd, log, **kwargs):
        result = base.ExportControls.native_run(self, argv, cwd=cwd, log=log, **kwargs)
        if log.stem == 'final-drc' and self.native_mode in ('warning-detail', 'uuid-only'):
            path = Path(argv[argv.index('--output')+1]); data = json.loads(path.read_text())
            data['violations'][0] = finding('33333333-3333-4333-8333-333333333333', 1. if self.native_mode == 'uuid-only' else 2.)
            path.write_text(json.dumps(data))
        return result

    def no_positive(self):
        path = self.output/'export.json'
        if path.exists(): self.assertFalse(json.loads(path.read_text())['export_accepted'])
        with self.assertRaises((p.Rejected, FileNotFoundError)): e.check_export(path)

    def test_live_acknowledgement_preserves_both_raw_lists_and_current_final_proof(self):
        def accept(event, *args):
            pending = json.loads(Path(event['pending']).read_text())
            self.assertFalse(pending['export_accepted'])
            self.assertFalse(pending['resumable_after_exit'])
            self.assertFalse((self.output/'export.json').exists())
            text = gui.warning_review_text(event, self.output/'warning-review.json')
            self.assertIn('Complete previous findings', text)
            self.assertIn('Complete fresh findings', text)
            return response(event)
        data = e.export(self.choice, self.output, warning_review=accept)
        self.assertTrue(data['export_accepted'])
        self.assertTrue(e.check_export(self.output/'export.json')['current'])
        self.assertIn('warning-review.json', data['export_evidence']['files'])
        self.assertIn('warning-acknowledgement.json', data['export_evidence']['files'])
        pending = json.loads((self.output/'warning-review.json').read_text())
        self.assertEqual(pending['warning_review']['previous_findings'], self.report['native']['findings'])
        self.assertEqual(pending['warning_review']['fresh_findings'], data['native']['findings'])
        self.assertEqual(data['budget_seconds'], 120)
        p.check_resource_accounting(data, child_key='child_step_cpu_seconds')

    def test_default_remains_strict_and_prior_accept_intent_is_not_warning_ack(self):
        with self.assertRaises(p.Rejected): e.export(self.choice, self.output)
        self.assertFalse((self.output/'warning-review.json').exists())
        self.no_positive()

    def test_UUID_only_changed_member_remains_visible_in_both_rendered_lists(self):
        self.native_mode = 'uuid-only'
        def accept(event, *_):
            text = gui.warning_review_text(event, self.output/'warning-review.json')
            self.assertIn('22222222-2222-4222-8222-222222222222', text)
            self.assertIn('33333333-3333-4333-8333-333333333333', text)
            return response(event)
        self.assertTrue(e.export(self.choice, self.output, warning_review=accept)['export_accepted'])

    def test_equal_warnings_do_not_request_another_review(self):
        self.native_mode = 'valid'
        data = e.export(self.choice, self.output,
            warning_review=lambda *_: self.fail('equal warnings requested review'))
        self.assertTrue(e.check_export(self.output/'export.json')['current'])
        self.assertNotIn('warning_review_acknowledgement', data)

    def test_missing_replayed_reject_or_wrong_challenge_ack_never_accepts(self):
        for key in ('decision', 'nonce', 'pending_sha256', 'delta_sha256', 'kind'):
            with self.subTest(key=key):
                self.output = self.root/('bad-ack-'+key)
                def wrong(event, *_):
                    value = response(event); value[key] = 'wrong'; return value
                with self.assertRaises(p.Rejected): e.export(self.choice, self.output, warning_review=wrong)
                self.no_positive()

    def test_callback_evidence_mutation_cannot_become_new_baseline(self):
        for relative in ('warning-review.json', 'validation/final-drc.json', 'validation/metrics.json'):
            with self.subTest(relative=relative):
                self.output = self.root/('tamper-'+relative.replace('/', '-'))
                def mutate(event, *_):
                    target = self.output/relative; target.write_bytes(target.read_bytes()+b'\n')
                    return response(event)
                with self.assertRaises(p.Rejected): e.export(self.choice, self.output, warning_review=mutate)
                self.no_positive()

    def test_acknowledgement_cannot_be_rehashed_into_a_rejection_or_other_intent(self):
        data = e.export(self.choice, self.output, warning_review=response)
        path = self.output/'warning-acknowledgement.json'; ack = json.loads(path.read_text())
        ack['response']['decision'] = 'reject'; path.write_text(json.dumps(ack))
        data['warning_review_acknowledgement']['acknowledgement_sha256'] = p.sha(path)
        data['export_evidence'] = e.evidence(self.output)
        (self.output/'export.json').write_text(json.dumps(data))
        with self.assertRaises(p.Rejected): e.check_export(self.output/'export.json')

    def test_original_wall_deadline_includes_review_without_second_allowance(self):
        real = e.elapsed_time
        def expired(event, *_):
            self.stack.enter_context(patch.object(e, 'elapsed_time', side_effect=lambda: real()+121))
            return response(event)
        with self.assertRaises(p.Rejected): e.export(self.choice, self.output, warning_review=expired)
        self.no_positive()

    def test_invalid_rule_mutation_or_cancellation_never_requests_ack(self):
        for mode in ('invalid', 'rule-change', 'cancel'):
            with self.subTest(mode=mode):
                self.native_mode = mode; self.output = self.root/('invalid-'+mode)
                with self.assertRaises(p.Rejected):
                    e.export(self.choice, self.output, warning_review=lambda *_: self.fail('invalid result requested review'))
                self.no_positive()

    def test_cancel_during_warning_review_never_publishes_acceptance(self):
        def cancel(*_): raise KeyboardInterrupt
        with self.assertRaises(p.Rejected): e.export(self.choice, self.output, warning_review=cancel)
        self.assertEqual(json.loads((self.output/'export.json').read_text())['status'], 'cancelled')
        self.no_positive()

    def test_original_CPU_budget_is_not_reset_by_review(self):
        real = h.cpu_seconds
        def expired(event, *_):
            self.stack.enter_context(patch.object(h, 'cpu_seconds', side_effect=lambda: real()+121))
            return response(event)
        with self.assertRaisesRegex(p.Rejected, 'budget'): e.export(self.choice, self.output, warning_review=expired)
        self.no_positive()

    def test_reported_track_layer_must_match_actual_UUID_geometry(self):
        old = native(finding()); fresh = native(finding('33333333-3333-4333-8333-333333333333', 2.))
        for report in (old, fresh):
            report['findings'][0]['items'][1]['description'] = 'Track [SIG] on F.Cu, length 0.2000 mm'
        delta = e.warning_review_delta(old, fresh)
        with self.assertRaisesRegex(p.Rejected, 'actual track layer'):
            e._warning_copper_witness(Path(self.report['candidate']), delta)

    def test_source_change_during_review_cannot_be_acknowledged(self):
        path = self.source/'board.kicad_pro'; before = path.read_bytes()
        def changed(event, *_):
            path.write_bytes(before+b'\n'); return response(event)
        try:
            with self.assertRaises(p.Rejected): e.export(self.choice, self.output, warning_review=changed)
            self.no_positive()
        finally: path.write_bytes(before)

    def test_late_final_reader_failure_invalidates_acknowledged_export(self):
        with patch.object(e, '_check_export', side_effect=p.Rejected('deliberate late readback failure')):
            with self.assertRaises(p.Rejected): e.export(self.choice, self.output, warning_review=response)
        self.no_positive()
        self.assertTrue((self.output/'warning-review.json').is_file())
        self.assertTrue((self.output/'warning-acknowledgement.json').is_file())


class WarningWireControls(unittest.TestCase):
    def test_real_pipe_exchange_and_duplicate_or_oversized_input_refusal(self):
        for wire in (b'{"decision":"owned"}\n', b'{"decision":1,"decision":2}\n', b'x'*4097):
            with self.subTest(wire_bytes=len(wire)):
                input_read, input_write = os.pipe(); output_read, output_write = os.pipe()
                with os.fdopen(input_read, 'rb') as incoming, os.fdopen(output_write, 'wb', buffering=0) as outgoing:
                    os.write(input_write, wire); os.close(input_write)
                    with patch.object(e.sys, 'stdin', incoming), patch.object(e.sys, 'stdout', outgoing):
                        if wire == b'{"decision":"owned"}\n':
                            self.assertEqual(e.stdio_warning_review({'kind':'owned-wire'}, lambda:1., lambda:None), {'decision':'owned'})
                        else:
                            with self.assertRaises(p.Rejected): e.stdio_warning_review({'kind':'owned-wire'}, lambda:1., lambda:None)
                    self.assertTrue(os.get_blocking(output_write))
                with os.fdopen(output_read, 'rb') as emitted:
                    self.assertEqual(json.loads(emitted.read()), {'kind':'owned-wire'})

    def test_full_stdout_pipe_expires_and_restores_its_own_descriptor_mode(self):
        read_fd, write_fd = os.pipe()
        with os.fdopen(read_fd, 'rb') as unread, os.fdopen(write_fd, 'wb', buffering=0) as output:
            os.set_blocking(write_fd, False)
            try:
                while True: os.write(write_fd, b'x'*4096)
            except BlockingIOError: pass
            os.set_blocking(write_fd, True)
            deadline = e.elapsed_time()+.1
            def guard():
                if e.elapsed_time() >= deadline: raise p.Rejected('owned wire deadline')
            with patch.object(e.sys, 'stdout', output), self.assertRaisesRegex(p.Rejected, 'deadline|budget'):
                e.stdio_warning_review({'kind':'owned-wire'}, lambda:max(0., deadline-e.elapsed_time()), guard)
            self.assertTrue(os.get_blocking(write_fd))

    def test_actual_GUI_child_handshake_reply_and_closed_input(self):
        import tempfile
        for answer in ('accept_updated_findings', 'reject'):
            with self.subTest(answer=answer), tempfile.TemporaryDirectory(dir=Path(__file__).parent) as temp:
                root=Path(temp).resolve(); job=gui.CliJob()
                event=gt.warning_challenge(root, seconds=2.)
                program='import json,sys; print(sys.argv[1],flush=True); a=json.loads(sys.stdin.readline()); assert a["nonce"]=="c"*32; sys.exit(0 if a["decision"]=="accept_updated_findings" else 2)'
                result=job.run([sys.executable,'-B','-c',program,json.dumps(event),'--warning-review-stdio'], root/'export.command.log',
                    timeout=3, on_warning_review=lambda value:job.reply_warning_review(value,answer))
                self.assertEqual(result['exit_code'], 0 if answer=='accept_updated_findings' else 2)
                self.assertTrue(job.process.stdin.closed); self.assertTrue(job.process.stdout.closed)
                with self.assertRaises(ValueError): job.reply_warning_review(event, answer)
