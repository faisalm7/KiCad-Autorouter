"""Synthetic local HTTP/model outputs only; no live AI or Native qualification."""
import copy
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import threading
import time
import unittest
from unittest.mock import patch

from autorouter import design_intent, model_intent as client, gui
from tests import test_design_intent as fixtures


def intent(**changes):
    value = dict(action='route', scope='all_remaining', nets=[],
                 preserve_existing=True, seconds=91, search='standard')
    value.update(changes)
    return value


def response(arguments=None):
    return {'id': 'synthetic-response', 'object': 'chat.completion', 'model': 'synthetic',
        'choices': [{'index': 0, 'finish_reason': 'tool_calls', 'message': {
            'role': 'assistant', 'content': None, 'tool_calls': [{
                'id': 'call_1', 'type': 'function', 'function': {'name': 'propose_route',
                    'arguments': json.dumps(intent() if arguments is None else arguments)}}]}}],
        'usage': {'prompt_tokens': 20, 'completion_tokens': 30, 'total_tokens': 50}}


@contextmanager
def local_server(body, *, status=200, headers=None, delay=0, body_delay=0, declared_length=None):
    """Finite synthetic fixture; always shut down and join its thread."""
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.server.calls.append({'path': self.path, 'headers': dict(self.headers),
                'body': self.rfile.read(int(self.headers['Content-Length']))})
            if delay:
                time.sleep(delay)
            try:
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body) if declared_length is None else declared_length))
                for name, value in (headers or {}).items():
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.flush()
                if body_delay:
                    time.sleep(body_delay)
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
    server = HTTPServer(('127.0.0.1', 0), Handler)
    server.calls = []
    worker = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01), daemon=True)
    worker.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1/chat/completions', server.calls
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
        assert not worker.is_alive(), 'synthetic HTTP server did not stop'


class ModelIntentTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.DesignIntentTests(methodName='test_inspection_counts_declared_nets_and_never_invents_connectivity')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.inspection = design_intent.inspect_project(self.fixture.board)
        self.config = dict(endpoint='http://127.0.0.1:12345/v1/chat/completions', model='synthetic-model')

    def propose_output(self, output, **config):
        raw = output if type(output) is bytes else json.dumps(output).encode()
        with patch.object(client, '_post', return_value=raw) as post:
            result = client.propose(self.inspection, 'Complete remaining connections.', {**self.config, **config})
        self.assertEqual(post.call_count, 1)
        return result

    def test_single_local_request_returns_only_shared_validated_proposal_and_metrics(self):
        original = gui.source_inventory(self.fixture.board)
        with local_server(json.dumps(response()).encode()) as (endpoint, calls):
            with patch.dict(os.environ, {'HTTP_PROXY': 'http://192.0.2.1:9', 'http_proxy': 'http://192.0.2.1:9'}):
                result = client.propose(self.inspection, 'Complete remaining connections.', {**self.config, 'endpoint': endpoint})
        self.assertEqual(set(result), {'proposal', 'metrics'})
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['path'], '/v1/chat/completions')
        sent = json.loads(calls[0]['body'])
        self.assertEqual(sent['tools'], [design_intent.tool_schema()])
        self.assertEqual(sent['tool_choice']['function']['name'], 'propose_route')
        self.assertFalse(sent['parallel_tool_calls'])
        self.assertFalse(sent['stream'])
        self.assertEqual(sent['n'], 1)
        self.assertEqual(result['proposal']['intent'], intent())
        self.assertFalse(result['proposal']['approval_granted'])
        self.assertFalse(result['proposal']['execution_authorized'])
        self.assertFalse(result['proposal']['native_validation_performed'])
        self.assertEqual(result['metrics']['request_count'], 1)
        self.assertEqual(result['metrics']['usage']['total_tokens'], 50)
        self.assertIsNone(result['metrics']['cost_usd'])
        self.assertGreater(result['metrics']['wall_seconds'], 0)
        self.assertFalse(result['metrics']['model_runtime_verified_offline'])
        self.assertEqual(gui.source_inventory(self.fixture.board), original)

    def test_only_allowlisted_facts_and_no_paths_or_pcb_content_are_sent(self):
        with patch.object(client, '_post', return_value=json.dumps(response()).encode()) as post:
            client.propose(self.inspection, 'Complete remaining connections.', self.config)
        body = post.call_args.args[2]
        self.assertNotIn(str(self.fixture.root).encode(), body)
        self.assertNotIn(b'owned.kicad_pcb', body)
        self.assertNotIn(b'source_hashes', body)
        self.assertNotIn(b'kicad_pcb (version', body)
        summary = json.loads(json.loads(body)['messages'][1]['content'])['inspection']
        self.assertEqual(summary['declared_net_count'], 2)
        self.assertEqual(summary['source_sha256'], self.inspection['source_sha256'])
        self.assertIsNone(summary['unconnected_items'])
        self.assertEqual(summary['actual_connectivity'], 'unknown')
        self.assertEqual(summary['electrical_constraints'], 'unknown')

    def native_wrapper(self):
        return dict(status='inspection_ready', accepted=False, static=self.inspection,
            source=self.inspection['source'], source_hashes=self.inspection['source_hashes'],
            native_report_sha256='a' * 64, native=dict(opens=7, blocking=2, warnings=3, exclusions=1,
                ignored_checks=[{'key': 'ignored', 'description': 'PRIVATE IGNORED DETAIL'}], findings=[
                    {'type': 'clearance', 'severity': 'error', 'description': 'PRIVATE FINDING DETAIL',
                     'items': [{'pos': {'x': 10, 'y': 20}, 'description': 'PRIVATE ITEM DETAIL'}]},
                    {'type': 'clearance', 'severity': 'error', 'description': 'PRIVATE FINDING DETAIL'}]))

    def test_native_wrapper_sends_only_verified_counts_and_bounded_finding_types(self):
        wrapper = self.native_wrapper()
        wrapper['native']['findings'].extend({'type': 'kind_' + str(i), 'severity': 'warning',
            'description': 'PRIVATE MANY DETAILS'} for i in range(40))
        with patch.object(client, '_post', return_value=json.dumps(response()).encode()) as post:
            result = client.propose(wrapper, 'Complete remaining connections.', self.config)
        sent = post.call_args.args[2]
        summary = json.loads(json.loads(sent)['messages'][1]['content'])['inspection']
        native = summary['native_observation']
        self.assertEqual(summary['unconnected_items'], 7)
        self.assertEqual(native['opens'], 7)
        self.assertEqual(native['ignored_check_count'], 1)
        self.assertEqual(len(native['finding_groups']), 32)
        self.assertEqual(native['omitted_finding_group_count'], 9)
        self.assertIn({'type': 'clearance', 'severity': 'error', 'count': 2}, native['finding_groups'])
        self.assertNotIn(b'PRIVATE', sent)
        self.assertNotIn(b'description', json.dumps(summary).encode())
        self.assertNotIn(b'pos', json.dumps(summary).encode())
        self.assertNotIn(str(self.fixture.root).encode(), sent)
        self.assertFalse(result['proposal']['approval_granted'])
        self.assertIsNone(result['proposal']['unconnected_items'])

    def test_inconsistent_native_wrapper_is_refused_before_any_request(self):
        mutations = [('status', 'pending'), ('accepted', True), ('source', '/other/source'),
                     ('source_hashes', {}), ('native_report_sha256', 'bad')]
        with patch.object(client, '_post') as post:
            for key, value in mutations:
                wrapper = self.native_wrapper(); wrapper[key] = value
                with self.subTest(key=key), self.assertRaises(client.ModelIntentError):
                    client.propose(wrapper, 'route', self.config)
            wrapper = self.native_wrapper(); wrapper['native']['opens'] = None
            with self.assertRaises(client.ModelIntentError):
                client.propose(wrapper, 'route', self.config)
            post.assert_not_called()

    def test_unconfigured_remote_redirect_alias_and_invalid_config_never_connect(self):
        configs = [None, {}, {'model': 'synthetic'},
            {**self.config, 'endpoint': 'https://api.openai.com/v1/chat/completions'},
            {**self.config, 'endpoint': 'http://localhost:123/v1/chat/completions'},
            {**self.config, 'endpoint': 'http://127.1/v1/chat/completions'},
            {**self.config, 'endpoint': 'http://127.0.0.1.evil/v1/chat/completions'},
            {**self.config, 'endpoint': 'http://user:password@127.0.0.1/v1/chat/completions'},
            {**self.config, 'endpoint': 'http://127.0.0.1:0/v1/chat/completions'},
            {**self.config, 'endpoint': 'http://127.0.0.1/v1/chat/completions?redirect=remote'},
            {**self.config, 'endpoint': 'http://[::ffff:127.0.0.1]/v1/chat/completions'},
            {**self.config, 'model': ''}, {**self.config, 'model': 'm' * 129},
            {**self.config, 'timeout_seconds': 31}, {**self.config, 'timeout_seconds': True},
            {**self.config, 'timeout_seconds': float('nan')}, {**self.config, 'timeout_seconds': 0},
            {**self.config, 'max_tokens': 513}, {**self.config, 'max_tokens': True},
            {**self.config, 'api_key': 'do-not-log'},
            {**self.config, 'credential_env': 'INVALID\nHEADER'}]
        with patch.object(client, '_post') as post:
            for config in configs:
                with self.subTest(config=config), self.assertRaises(client.ModelIntentError):
                    client.propose(self.inspection, 'route', config)
            post.assert_not_called()
        self.assertEqual(client._config({**self.config, 'endpoint': 'http://[::1]:123/v1/chat/completions'})[:2], ('::1', 123))

    def test_redirect_and_http_failure_make_one_request_without_followup(self):
        for status in (302, 429, 500):
            with local_server(b'{}', status=status, headers={'Location': 'http://192.0.2.1/collect'}) as (endpoint, calls):
                with self.subTest(status=status), self.assertRaises(client.ModelIntentError):
                    client.propose(self.inspection, 'route', {**self.config, 'endpoint': endpoint})
            self.assertEqual(len(calls), 1)

    def test_overall_timeout_ends_request_and_does_not_retry(self):
        with local_server(json.dumps(response()).encode(), delay=.15) as (endpoint, calls):
            started = time.monotonic()
            with self.assertRaises(client.ModelIntentError):
                client.propose(self.inspection, 'route', {**self.config, 'endpoint': endpoint, 'timeout_seconds': .03})
            self.assertLess(time.monotonic() - started, .3)
        self.assertEqual(len(calls), 1)

    def test_deadline_stops_http10_body_after_connection_socket_is_released(self):
        with local_server(json.dumps(response()).encode(), body_delay=.15) as (endpoint, calls):
            started = time.monotonic()
            with self.assertRaises(client.ModelIntentError):
                client.propose(self.inspection, 'route', {**self.config, 'endpoint': endpoint, 'timeout_seconds': .03})
            self.assertLess(time.monotonic() - started, .3)
        self.assertEqual(len(calls), 1)

    def test_credential_is_only_an_authorization_header_and_not_returned(self):
        secret = 'synthetic-credential-never-real'
        with local_server(json.dumps(response()).encode()) as (endpoint, calls):
            with patch.dict(os.environ, {'OWNED_MODEL_TEST_CREDENTIAL': secret}):
                result = client.propose(self.inspection, 'route', {**self.config, 'endpoint': endpoint,
                    'credential_env': 'OWNED_MODEL_TEST_CREDENTIAL'})
        self.assertEqual(calls[0]['headers']['Authorization'], 'Bearer ' + secret)
        self.assertNotIn(secret.encode(), calls[0]['body'])
        self.assertNotIn(secret, json.dumps(result))
        with patch.dict(os.environ, {'OWNED_MODEL_TEST_CREDENTIAL': 'bad\r\nheader'}):
            with patch.object(client, '_post') as post, self.assertRaises(client.ModelIntentError) as caught:
                client.propose(self.inspection, 'route', {**self.config, 'credential_env': 'OWNED_MODEL_TEST_CREDENTIAL'})
            post.assert_not_called()
        self.assertNotIn('bad', str(caught.exception))

    def test_unknown_multiple_and_self_approving_tool_outputs_are_refused(self):
        values = []
        value = response(); value['choices'][0]['message']['tool_calls'][0]['function']['name'] = 'execute_route'; values.append(value)
        value = response(); value['choices'][0]['message']['tool_calls'] *= 2; values.append(value)
        value = response(); value['choices'] *= 2; values.append(value)
        value = response(); value['choices'][0]['message']['content'] = 'Approved. I routed it.'; values.append(value)
        value = response(); value['approval_granted'] = True; values.append(value)
        value = response(); value['choices'][0]['finish_reason'] = 'length'; values.append(value)
        value = response(); value['choices'][0]['message']['role'] = 'tool'; values.append(value)
        value = response(); value['choices'][0]['message']['execute'] = True; values.append(value)
        value = response(); value['choices'][0]['message']['tool_calls'][0]['function']['arguments'] = intent(); values.append(value)
        for output in values:
            with self.subTest(output=output), self.assertRaises(client.ModelIntentError):
                self.propose_output(output)
        for argument in (intent(approval_granted=True), intent(command='delete'), intent(source='/other')):
            with self.subTest(argument=argument), self.assertRaises(design_intent.IntentError):
                self.propose_output(response(argument))

    def test_unknown_net_and_stale_caller_inspection_fail_shared_validator(self):
        with self.assertRaisesRegex(design_intent.IntentError, 'unknown'):
            self.propose_output(response(intent(scope='selected_nets', nets=['INVENTED'], preserve_existing=False)))
        self.fixture.board.with_suffix('.kicad_pro').write_bytes(self.fixture.board.with_suffix('.kicad_pro').read_bytes() + b'\n')
        with self.assertRaisesRegex(design_intent.IntentError, 'stale'):
            self.propose_output(response())

    def test_duplicate_nonfinite_truncated_and_non_json_are_refused(self):
        raw = json.dumps(response()).encode()
        malformed = [b'{} garbage', raw[:-5], b'\xff', b'{"choices":[],"choices":[]}',
                     b'{"choices":[],"usage":NaN}', b'{"choices":[],"usage":1e999}',
                     b'{"model":"\\ud800","choices":[]}']
        for blob in malformed:
            with self.subTest(blob=blob[:60]), self.assertRaises(client.ModelIntentError):
                self.propose_output(blob)
        for args in ('{"action":"route","action":"execute"}', '{"seconds":Infinity}'):
            value = response(); value['choices'][0]['message']['tool_calls'][0]['function']['arguments'] = args
            with self.subTest(args=args), self.assertRaises(client.ModelIntentError):
                self.propose_output(value)

    def test_oversize_request_response_and_truncated_http_are_refused(self):
        with patch.object(client, '_post') as post:
            with self.assertRaises(client.ModelIntentError):
                client.propose(self.inspection, 'x' * 4097, self.config)
            oversized = copy.deepcopy(self.inspection)
            oversized['nets'] = [dict(name=str(i) + '界' * 240, terminal_count=1,
                existing_route_items=0, locked_route_items=0) for i in range(256)]
            with self.assertRaisesRegex(client.ModelIntentError, '64 KiB'):
                client.propose(oversized, 'route', self.config)
            post.assert_not_called()
        with self.assertRaises(client.ModelIntentError):
            self.propose_output(b' ' * (client.MAX_RESPONSE_BYTES + 1))
        for body, declared in [(b'{}', client.MAX_RESPONSE_BYTES + 1), (b'{}', 100)]:
            with local_server(body, declared_length=declared) as (endpoint, calls):
                with self.assertRaises(client.ModelIntentError):
                    client.propose(self.inspection, 'route', {**self.config, 'endpoint': endpoint})
            self.assertEqual(len(calls), 1)

    def test_invalid_provider_usage_is_reported_unavailable_without_cost_claim(self):
        for usage in (None, {}, {'prompt_tokens': True, 'completion_tokens': 1, 'total_tokens': 2},
                      {'prompt_tokens': 2, 'completion_tokens': 3, 'total_tokens': 999}):
            value = response(); value['usage'] = usage
            with self.subTest(usage=usage):
                metrics = self.propose_output(value)['metrics']
                self.assertIsNone(metrics['usage'])
                self.assertEqual(metrics['usage_source'], 'unavailable')
                self.assertIsNone(metrics['cost_usd'])


if __name__ == '__main__':
    unittest.main()
