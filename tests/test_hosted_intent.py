"""Owned synthetic outputs and real pipe workers; zero external network/model."""
import copy
import io
import json
from pathlib import Path
import ssl
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

from autorouter import hosted_intent as hosted, design_intent as design, gui, runner
from tests import test_placement_route_intent as fixtures

KEY = 'owned_synthetic_credential_12345'


def usage(**changes):
    value = {'input_tokens': 1000, 'output_tokens': 50, 'total_tokens': 1050,
             'output_tokens_details': {'reasoning_tokens': 20},
             'input_tokens_details': {'cached_tokens': 100, 'cache_write_tokens': 200,
                 'cache_write_tokens_details': {'ttl_30m_tokens': 200, 'ttl_12h_tokens': 0}}}
    value.update(changes)
    return value


def response(arguments, *, name='propose_placement_route', **changes):
    value = {'object': 'response', 'status': 'completed', 'model': hosted.MODEL,
             'service_tier': 'default', 'reasoning': {'effort': 'medium', 'summary': None},
             'usage': usage(), 'output': [{'type': 'function_call', 'call_id': 'owned_call',
                 'name': name, 'arguments': json.dumps(arguments), 'status': 'completed'}]}
    value.update(changes)
    return value


def tagged(value):
    return b'J' + json.dumps(value).encode()


class HostedIntent(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PlacementRouteIntent(
            methodName='test_ordinary_controls_and_model_share_exact_settings_and_never_execute')
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.board = self.fixture.board
        self.inspection = self.fixture.inspection
        self.context = self.fixture.context
        self.request = self.fixture.request
        self.text = 'Keep fixed parts and KEEP unchanged. Place selected parts in the visible region, then route approved connections.'
        self.path = self.fixture.root / 'hosted-ledger.json'
        self.prepared = hosted.prepare_request(self.inspection, self.context, self.text)
        self.consent = hosted.make_consent(self.prepared, ledger_path=self.path)
        self.consent['approved'] = True

    def call(self, raw=None, **changes):
        args = dict(credential=KEY, consent=self.consent, ledger_path=self.path)
        args.update(changes)
        value = tagged(response(self.request)) if raw is None else raw
        with patch.object(hosted, '_run_worker', return_value=(value, {})) as transport:
            result = hosted.propose_placement_route(self.inspection, self.context, self.text, **args)
        self.assertEqual(transport.call_count, 1)
        return result

    def test_preparation_uses_shared_contract_and_only_allowlisted_data_without_authority(self):
        with patch('subprocess.Popen', side_effect=AssertionError('no worker in preparation')):
            prepared = hosted.prepare_request(self.inspection, self.context, self.text)
        sent = json.loads(prepared['body']); contract = design.placement_model_contract()
        self.assertEqual(sent['instructions'], contract['instructions'])
        self.assertEqual(sent['tools'], [{'type': 'function', **row['function']} for row in contract['tools']])
        self.assertFalse(sent['store']); self.assertFalse(sent['background'])
        self.assertFalse(sent['parallel_tool_calls']); self.assertFalse(sent['stream'])
        self.assertNotIn(str(self.fixture.root).encode(), prepared['body'])
        self.assertNotIn(b'kicad_pcb', prepared['body'])
        self.assertEqual(prepared['initial']['intent'], self.request)
        self.assertFalse(prepared['initial']['approval_granted'])
        self.assertFalse(prepared['initial']['execution_authorized'])
        self.assertLessEqual(prepared['conservative_input_tokens'], hosted.INPUT_TOKENS)
        draft = hosted.make_consent(prepared, ledger_path=self.path)
        self.assertIs(draft['approved'], False)

    def test_proposal_and_actual_cost_use_shared_validators_with_no_source_changes(self):
        original = gui.source_inventory(self.board)
        result = self.call()
        self.assertEqual(result['proposal']['intent'], self.request)
        self.assertIsNone(result['clarification'])
        self.assertFalse(result['proposal']['approval_granted'])
        self.assertFalse(result['proposal']['execution_authorized'])
        self.assertEqual(result['metrics']['request_count'], 1)
        self.assertEqual(result['metrics']['cost_nano_usd'], 2_410_000)
        self.assertEqual(result['metrics']['request_sha256'], self.prepared['request_sha256'])
        self.assertEqual(result['metrics']['context_sha256'], self.prepared['context_sha256'])
        record = json.loads(self.path.read_bytes())
        self.assertEqual(record['attempts'], 1)
        self.assertEqual(record['outcome'], 'intent_proposed')
        self.assertEqual(record['cost_nano_usd'], 2_410_000)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertNotIn(KEY, self.path.read_text())
        self.assertNotIn(self.text, self.path.read_text())
        self.assertEqual(gui.source_inventory(self.board), original)

    def test_useful_clarification_is_not_a_proposal_or_execution(self):
        args = {'reason': 'ambiguous_request', 'questions': ['Which selected component should be nearest the edge?']}
        result = self.call(tagged(response(args, name='clarify_design_request')))
        self.assertIsNone(result['proposal'])
        self.assertEqual(result['clarification'], design.validate_design_clarification(args))
        self.assertEqual(json.loads(self.path.read_bytes())['outcome'], 'clarification_received')

    def test_consent_requires_explicit_approval_exact_data_path_and_unexpired_context(self):
        cases = [dict(approved=False), dict(max_calls=2), dict(cap_nano_usd=50_000_001),
                 dict(request_sha256='0' * 64), dict(ledger_path_sha256='0' * 64),
                 dict(expires_elapsed_time=0)]
        for changes in cases:
            with self.subTest(changes=changes), patch.object(hosted, '_run_worker') as transport:
                consent = {**self.consent, **changes}
                with self.assertRaises(hosted.HostedError):
                    hosted.propose_placement_route(self.inspection, self.context, self.text,
                        credential=KEY, consent=consent, ledger_path=self.path)
                transport.assert_not_called(); self.assertFalse(self.path.exists())
        with patch.object(hosted, '_run_worker') as transport, self.assertRaises(hosted.HostedError):
            hosted.propose_placement_route(self.inspection, self.context, self.text + ' changed',
                credential=KEY, consent=self.consent, ledger_path=self.path)
        transport.assert_not_called(); self.assertFalse(self.path.exists())

    def test_cannot_reuse_one_approval_with_another_ledger_or_append_to_used_ledger(self):
        self.call()
        before = self.path.read_bytes()
        for path in (self.path, self.path.with_name('second-ledger.json')):
            with self.subTest(path=path.name), patch.object(hosted, '_run_worker') as transport:
                with self.assertRaises(hosted.HostedError):
                    hosted.propose_placement_route(self.inspection, self.context, self.text,
                        credential=KEY, consent=self.consent, ledger_path=path)
                transport.assert_not_called()
        self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_semantic_extra_authority_is_accounted_but_never_adopted(self):
        with self.assertRaises(hosted.HostedError) as caught:
            self.call(tagged(response({**self.request, 'approval_granted': True})))
        self.assertEqual(caught.exception.metrics['cost_nano_usd'], 2_410_000)
        row = json.loads(self.path.read_bytes())
        self.assertEqual(row['outcome'], 'response_rejected')
        self.assertNotIn('approval_granted', row)

    def test_changed_context_has_priority_over_bad_model_arguments(self):
        def changed(*args, **kwargs):
            new = self.fixture.make_context(route_seconds=120)
            self.context.clear(); self.context.update(new)
            return tagged(response({'action': 'wrong'})), {}
        with patch.object(hosted, '_run_worker', side_effect=changed):
            with self.assertRaises(hosted.HostedError) as caught:
                hosted.propose_placement_route(self.inspection, self.context, self.text,
                    credential=KEY, consent=self.consent, ledger_path=self.path)
        self.assertEqual(caught.exception.metrics['refusal_stage'], 'post_response_context_changed')
        self.assertEqual(caught.exception.metrics['cost_nano_usd'], 2_410_000)
        self.assertEqual(json.loads(self.path.read_bytes())['outcome'], 'response_rejected')

    def test_changed_source_after_response_is_refused_with_accounting_retained(self):
        def changed(*args, **kwargs):
            self.board.with_suffix('.kicad_prl').write_text('{"changed":true}')
            return tagged(response(self.request)), {}
        with patch.object(hosted, '_run_worker', side_effect=changed):
            with self.assertRaises(hosted.HostedError) as caught:
                hosted.propose_placement_route(self.inspection, self.context, self.text,
                    credential=KEY, consent=self.consent, ledger_path=self.path)
        self.assertTrue(caught.exception.metrics['transport_invoked'])
        self.assertEqual(json.loads(self.path.read_bytes())['outcome'], 'response_rejected')

    def test_unknown_transport_usage_and_wrong_identity_retain_reservation(self):
        values = [b'E', b'not-json', tagged(response(self.request, usage=None)),
                  tagged(response(self.request, model='other-model'))]
        for index, raw in enumerate(values):
            with self.subTest(index=index):
                path = self.path.with_name('unknown-' + str(index) + '.json')
                consent = hosted.make_consent(self.prepared, ledger_path=path); consent['approved'] = True
                with self.assertRaises(hosted.HostedError): self.call(raw, consent=consent, ledger_path=path)
                row = json.loads(path.read_bytes())
                self.assertEqual(row['reserved_nano_usd'], 40_960_000)
                self.assertIsNone(row['cost_nano_usd'])
                self.assertEqual(row['attempts'], 1)

    def test_cancel_before_reservation_and_after_response_cannot_adopt(self):
        event = threading.Event(); event.set()
        with patch.object(hosted, '_run_worker') as transport, self.assertRaises(hosted.HostedError):
            hosted.propose_placement_route(self.inspection, self.context, self.text,
                credential=KEY, consent=self.consent, ledger_path=self.path, cancel_event=event)
        transport.assert_not_called(); self.assertFalse(self.path.exists())
        event.clear()
        def cancelled(*args, **kwargs):
            event.set(); return tagged(response(self.request)), {}
        with patch.object(hosted, '_run_worker', side_effect=cancelled), self.assertRaises(hosted.HostedError):
            hosted.propose_placement_route(self.inspection, self.context, self.text,
                credential=KEY, consent=self.consent, ledger_path=self.path, cancel_event=event)
        self.assertEqual(json.loads(self.path.read_bytes())['outcome'], 'response_rejected')

    def test_provider_http_refusal_is_actionable_and_never_retried(self):
        with self.assertRaises(hosted.HostedError) as caught: self.call(b'H403')
        self.assertEqual(caught.exception.metrics['http_status'], 403)
        self.assertEqual(caught.exception.metrics['refusal_stage'], 'http_status')
        self.assertEqual(json.loads(self.path.read_bytes())['outcome'], 'transport_unknown')

    def test_wrong_reasoning_and_unrequested_cache_retention_refuse(self):
        wrong = response(self.request, reasoning={'effort': 'high'})
        with self.assertRaises(hosted.HostedError): self.call(tagged(wrong))
        path = self.path.with_name('cache-12h.json')
        consent = hosted.make_consent(self.prepared, ledger_path=path); consent['approved'] = True
        u = usage(input_tokens_details={'cached_tokens': 0, 'cache_write_tokens': 1000,
            'cache_write_tokens_details': {'ttl_30m_tokens': 0, 'ttl_12h_tokens': 1000}})
        with self.assertRaises(hosted.HostedError):
            self.call(tagged(response(self.request, usage=u)), consent=consent, ledger_path=path)
        self.assertEqual(json.loads(path.read_bytes())['cost_nano_usd'], 5_500_000)

    def test_reflected_and_json_escaped_credentials_are_not_in_errors_or_receipts(self):
        args = {'reason': 'ambiguous_request', 'questions': ['Credential: ' + KEY]}
        raw = tagged(response(args, name='clarify_design_request'))
        raw = raw.replace(KEY.encode(), ('\\u%04x' % ord(KEY[0])).encode() + KEY[1:].encode())
        with self.assertRaises(hosted.HostedError) as caught: self.call(raw)
        self.assertNotIn(KEY, str(caught.exception))
        self.assertNotIn(KEY, json.dumps(caught.exception.metrics))
        self.assertNotIn(KEY, self.path.read_text())

    def test_source_directory_ledger_unavailable_worker_and_unqualified_platform_refuse_pre_send(self):
        inside = self.board.parent / 'ledger.json'
        consent = hosted.make_consent(self.prepared, ledger_path=inside); consent['approved'] = True
        with self.assertRaises(hosted.HostedError): self.call(consent=consent, ledger_path=inside)
        self.assertFalse(inside.exists())
        with self.assertRaises(hosted.HostedError): self.call(worker_python=self.fixture.root / 'missing')
        self.assertFalse(self.path.exists())
        with patch.object(hosted, '_supported_platform', return_value=False), self.assertRaises(hosted.HostedError):
            self.call()
        self.assertFalse(self.path.exists())


class HostedWorker(unittest.TestCase):
    # Patches are explicit synthetic dependencies in a real private Python3.11
    # child. No test-only transport mode or endpoint is exposed in product code.
    def controlled_argv(self, code):
        return [sys.executable, '-B', '-c', code]

    def test_actual_worker_rejects_secret_probe_and_malformed_input_without_tls_or_output_echo(self):
        code = 'from autorouter import hosted_intent as h; h._worker_main()'
        for body in (b'bad-json', json.dumps({'probe': True, 'credential': KEY,
                     'body': None, 'timeout': 1}).encode()):
            process = subprocess.run(self.controlled_argv(code), input=body, capture_output=True, timeout=3)
            self.assertEqual(process.stdout, b'E'); self.assertNotIn(KEY.encode(), process.stderr)

    def test_actual_private_worker_mocked_tls_probe_has_no_http_or_credentials(self):
        code = '''from autorouter import hosted_intent as h
class Sock:
 def version(self): return 'TLSv1.3'
class HTTPS:
 def __init__(self, host, port, timeout, context):
  assert host=='api.openai.com' and port==443 and context.check_hostname
  self.sock=Sock()
 def connect(self): pass
 def request(self,*args,**kwargs): raise AssertionError('zero HTTP for TLS probe')
 def close(self): pass
h.http.client.HTTPSConnection=HTTPS
h._worker_main()
'''
        with patch.object(hosted, '_worker_argv', return_value=self.controlled_argv(code)):
            result = hosted.probe_tls()
        self.assertEqual(result['HTTP_requests'], 0)
        self.assertEqual(result['TLS_version'], 'TLSv1.3')
        self.assertTrue(result['hostname_check']); self.assertTrue(result['certificate_required'])
        self.assertGreaterEqual(result['worker_CPU_seconds'], 0)

    def test_actual_owned_child_deadline_and_cancel_reap_without_leaking_threads(self):
        code = 'import sys,time; sys.stdin.buffer.read(); time.sleep(5)'
        original = subprocess.Popen; children = []
        def track(*args, **kwargs):
            child = original(*args, **kwargs); children.append(child); return child
        for event in (None, threading.Event()):
            timer = None
            if event is not None:
                timer = threading.Timer(.15, event.set); timer.start()
            try:
                with patch.object(hosted, '_worker_argv', return_value=self.controlled_argv(code)), \
                        patch.object(hosted.subprocess, 'Popen', side_effect=track), self.assertRaises(hosted.HostedError):
                    hosted._run_worker(b'{}', KEY, runner.elapsed_time() + .8, event)
            finally:
                if timer is not None: timer.cancel(); timer.join()
        self.assertEqual(len(children), 2)
        self.assertTrue(all(child.returncode is not None for child in children))
        self.assertFalse(any(t.name in ('hosted-private-input', 'hosted-bounded-output') for t in threading.enumerate()))

    def test_tls_verification_failure_and_oversized_child_output_are_safe(self):
        code = '''from autorouter import hosted_intent as h
def fail(): raise h.ssl.SSLCertVerificationError('synthetic private detail')
h._tls_context=fail
h._worker_main()
'''
        with patch.object(hosted, '_worker_argv', return_value=self.controlled_argv(code)):
            with self.assertRaises(hosted.HostedError) as caught: hosted.probe_tls()
        self.assertEqual(caught.exception.metrics['refusal_stage'], 'tls_certificate')
        self.assertNotIn('synthetic private detail', str(caught.exception))
        code = 'import sys; sys.stdin.buffer.read(); sys.stdout.buffer.write(b"x"*140000); sys.stdout.buffer.flush()'
        with patch.object(hosted, '_worker_argv', return_value=self.controlled_argv(code)), self.assertRaises(hosted.HostedError):
            hosted._run_worker(b'{}', KEY, runner.elapsed_time() + 2)


if __name__ == '__main__':
    unittest.main()
