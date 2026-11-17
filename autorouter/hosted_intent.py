"""One consented hosted intent proposal, over the shared engineering contract.

The HTTPS framing, Responses envelope and usage checks are adapted from the
reviewed 098 confirmation client. Case lists, scoring, retries and comparison
orchestration are deliberately absent. A proposal confers no execution authority.

The GUI may use KiCad's Python; the private pipe worker uses the installation's
Python 3.11 and its normal verified TLS trust. Keys never enter argv, environment,
files or receipts. This is a cooperative application boundary, not a same-user
hostile-process sandbox or an OS-enforced memory/billing limit.
"""
from __future__ import annotations

import copy
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import re
import signal
import socket
import ssl
import stat
import subprocess
import sys
import threading
import time

if __package__ in (None, ''):  # Actual private worker, with no PYTHONPATH change.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from autorouter import design_intent as design, model_intent as client
    from autorouter import gui, pipeline, provenance, runner
    from autorouter.placement_clearance import read_bytes
else:
    from . import design_intent as design, model_intent as client
    from . import gui, pipeline, provenance, runner
    from .placement_clearance import read_bytes

ENDPOINT = 'https://api.openai.com/v1/responses'
MODEL = 'gpt-6.1-sol'
REASONING = 'medium'
INPUT_TOKENS = 8192
OUTPUT_TOKENS = 2048
INPUT_OVERHEAD_TOKENS = 1024
MAX_RESPONSE_BYTES = 128 * 1024
MAX_ENVELOPE_BYTES = 32 * 1024
DEADLINE_SECONDS = 30
CONSENT_SECONDS = 300
CAP_NANO_USD = 50_000_000
RESERVATION_NANO_USD = 40_960_000
WORKER_RSS_BYTES = 256 * 1024 * 1024
RATE_REVISION = '2026-11-14-standard-sol-2-input-10-output-30m-writes'


class HostedError(client.ModelIntentError):
    """Deliberately non-sensitive message and bounded non-secret metrics."""
    def __init__(self, message, metrics=None):
        super().__init__(message)
        self.metrics = metrics or {}


def _saved_diagnostics(metrics):
    """Small non-secret record; never save exceptions or provider text."""
    result = {}
    stages = {'pre_transport', 'transport', 'response_envelope', 'response_accounting',
              'response_contract', 'post_response_context_freshness', 'semantic_validation',
              'post_response_context_changed', 'publication', 'http_status', 'tls_certificate',
              'dns', 'transport_timeout', 'tls_handshake', 'credential_response', 'worker_failure'}
    stage = metrics.get('refusal_stage')
    if type(stage) is str and stage in stages:
        result['refusal_stage'] = stage
    code = metrics.get('refusal_code')
    if type(code) is str and code in {
            'response_envelope_unsupported', 'response_metadata_unsupported',
            'reasoning_profile_mismatch', 'output_missing', 'output_item_invalid',
            'reasoning_text_present', 'tool_call_invalid', 'tool_call_count',
            'tool_arguments_malformed', 'tool_arguments_not_object'}:
        result['refusal_code'] = code
    for name in ('wall_seconds', 'worker_CPU_seconds', 'monitor_CPU_seconds'):
        value = metrics.get(name)
        if type(value) in (int, float) and 0 <= value <= 86400 and math.isfinite(value):
            result[name] = value
    rss = metrics.get('sampled_worker_RSS_bytes')
    if type(rss) is int and 0 <= rss <= 2**50:
        result['sampled_worker_RSS_bytes'] = rss
    status = metrics.get('http_status')
    if type(status) is int and 100 <= status <= 599:
        result['http_status'] = status
    return result


def _encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(',', ':')).encode('utf-8')


def _digest(value):
    return hashlib.sha256(_encoded(value)).hexdigest()


def _compact_context(summary):
    """Lossless projection of the shared, already validated placement summary.

    Role flags and their repeated explanations follow exactly from selected /
    fixed membership. Keep all distinct source reasons in a small readable
    dictionary and an explicit reference-to-UUID table. Unsupported future
    summary changes refuse instead of silently discarding information.
    """
    result = copy.deepcopy(summary)
    selected, fixed = set(summary['selected']), set(summary['fixed'])
    reasons, rows = [], []
    fields = {'reference', 'uuid', 'selected', 'fixed', 'explicitly_fixed',
              'eligibility', 'reasons', 'source_fixed_reasons'}
    for row in summary['components']:
        chosen, pinned = row['uuid'] in selected, row['uuid'] in fixed
        task_reasons = (['Selected by caller; shared placement facts validated these exact settings.']
                        if chosen else ['Unselected components remain fixed in this task.'])
        if pinned:
            task_reasons.append('Explicit caller fixed-component request.')
        expected = {'selected': chosen, 'fixed': not chosen, 'explicitly_fixed': pinned,
                    'eligibility': 'selected_validated' if chosen else 'fixed_in_current_task',
                    'reasons': task_reasons}
        if set(row) != fields or any(row[key] != value for key, value in expected.items()):
            raise HostedError('The component summary contains unsupported information; no request was sent.')
        indexes = []
        for reason in row['source_fixed_reasons']:
            if reason not in reasons:
                reasons.append(reason)
            indexes.append(reasons.index(reason))
        rows.append([row['reference'], row['uuid'], indexes])
    result['components'] = {
        'fields': ['reference', 'uuid', 'source_fixed_reason_ids'],
        'source_fixed_reasons': reasons, 'rows': rows,
    }
    policy = result.pop('placement_settings')
    for key in ('selected', 'region_nm', 'copper_policy'):
        if policy[key] != result[key]:
            raise HostedError('Duplicated placement facts disagree; no request was sent.')
        del policy[key]
    # The validated settings kind repeats its schema. The false preservation
    # flag is also entailed by this composed workflow's explicit rebuild policy
    # and caller permission. Every other policy, protection and limit stays.
    if (type(policy['schema']) is not int
            or policy['kind'] != 'autorouter.selected-placement-settings.v' + str(policy['schema'])
            or policy['preserve_existing'] is not False
            or result['copper_policy'] != 'rebuild-affected-unlocked-v1'
            or result['caller_rebuild_permission_present'] is not True
            or result['all_unselected_fixed'] is not True):
        raise HostedError('Placement policy is unsupported by the compact context; no request was sent.')
    del policy['kind']; del policy['preserve_existing']
    result['placement_policy'] = policy
    return result


def _compact_nets(nets):
    """Keep every declared name/count; use a table only when it is smaller."""
    fields = ['name', 'terminal_count', 'existing_route_items', 'locked_route_items']
    if any(set(row) != set(fields) for row in nets):
        raise HostedError('The declared-net summary contains unsupported information; no request was sent.')
    table = {'fields': fields, 'rows': [[row[key] for key in fields] for row in nets]}
    return table if len(_encoded(table)) < len(_encoded(nets)) else copy.deepcopy(nets)


def prepare_request(inspection, context, request_text):
    """Prepare exactly the data to show before consent; do not connect or write.

    ``initial`` is caller-retained validation, not permission. Body bytes must
    stay in memory; the consent UI may display ``consent_summary`` as plain text.
    No source paths, full PCB text or Native report descriptions are added.
    """
    if (type(request_text) is not str or not request_text.strip()
            or len(request_text.encode('utf-8')) > client.MAX_REQUEST_TEXT):
        raise HostedError('Enter a nonempty request within 4096 UTF-8 bytes.')
    if type(context) is not dict:
        raise HostedError('Current visible placement and routing choices are required.')
    initial = design.validate_placement_route_proposal(
        inspection, context, design.placement_request(context))
    _, compact = client._summary(design.inspect_project(inspection['source']))
    compact['nets'] = _compact_nets(compact['nets'])
    compact['placement_context'] = _compact_context(client._placement_summary(inspection, initial))
    contract = design.placement_model_contract()
    material = {'inspection': compact, 'request': request_text}
    payload = {
        'model': MODEL, 'instructions': contract['instructions'],
        'input': [{'role': 'user', 'content': _encoded(material).decode('utf-8')}],
        'tools': [{'type': 'function', **tool['function']} for tool in contract['tools']],
        'tool_choice': 'required', 'parallel_tool_calls': False,
        'max_output_tokens': OUTPUT_TOKENS, 'reasoning': {'effort': REASONING},
        'service_tier': 'default', 'store': False, 'stream': False,
        'background': False, 'truncation': 'disabled',
        'prompt_cache_options': {'ttl': '30m'},
    }
    body = _encoded(payload)
    conservative_input_tokens = len(body) + INPUT_OVERHEAD_TOKENS
    if conservative_input_tokens > INPUT_TOKENS:
        raise HostedError('The compact request exceeds the conservative input bound; no request was sent.')
    return {
        'body': body, 'initial': initial,
        'request_sha256': hashlib.sha256(body).hexdigest(),
        'context_sha256': _digest(initial),
        'conservative_input_tokens': conservative_input_tokens,
        'consent_summary': {
            'provider': 'OpenAI', 'endpoint': ENDPOINT, 'model': MODEL,
            'reasoning': REASONING, 'service_tier': 'default',
            'data': copy.deepcopy(material),
            'omitted': ['project paths', 'PCB/schematic file contents', 'full Native reports', 'credentials'],
            'maximum_calls': 1, 'maximum_output_tokens': OUTPUT_TOKENS,
            'conservative_input_tokens': conservative_input_tokens,
            'reserved_nano_usd': RESERVATION_NANO_USD,
            'cost_basis': 'Frozen Standard list rates and requested 30-minute cache writes; not an invoice or provider billing quota.',
            'retention': 'store:false; this does not assert Zero Data Retention.',
            'authority': 'Proposal only; explicit review, execution, warning review and acceptance remain separate.',
        },
    }


def _ledger_path(value):
    path = provenance.canonical(Path(value).absolute())
    provenance._directory(path.parent)
    return path


def make_consent(prepared, *, ledger_path, cap_nano_usd=CAP_NANO_USD):
    """Return an unapproved, expiring consent draft for one exact owned task."""
    if (type(cap_nano_usd) is not int or not RESERVATION_NANO_USD <= cap_nano_usd <= CAP_NANO_USD):
        raise HostedError('The task cap must cover the $0.04096 reservation and be at most $0.05.')
    now = runner.elapsed_time()
    if not math.isfinite(now) or now < 0:
        raise HostedError('A usable elapsed clock is required before consent.')
    path = _ledger_path(ledger_path)
    return {
        'schema': 1, 'kind': 'autorouter.hosted-intent-consent.v1',
        'approved': False, 'endpoint': ENDPOINT, 'model': MODEL, 'reasoning': REASONING,
        'request_sha256': prepared['request_sha256'],
        'context_sha256': prepared['context_sha256'],
        'summary_sha256': _digest(prepared['consent_summary']),
        'ledger_path_sha256': hashlib.sha256(os.fsencode(path)).hexdigest(),
        'max_calls': 1, 'cap_nano_usd': cap_nano_usd,
        'created_elapsed_time': now, 'expires_elapsed_time': now + CONSENT_SECONDS,
    }


def _check_consent(consent, prepared, path):
    fields = {'schema', 'kind', 'approved', 'endpoint', 'model', 'reasoning',
              'request_sha256', 'context_sha256', 'summary_sha256', 'ledger_path_sha256',
              'max_calls', 'cap_nano_usd', 'created_elapsed_time', 'expires_elapsed_time'}
    if (type(consent) is not dict or set(consent) != fields
            or type(consent['schema']) is not int or consent['schema'] != 1
            or consent['kind'] != 'autorouter.hosted-intent-consent.v1'
            or consent['approved'] is not True or consent['endpoint'] != ENDPOINT
            or consent['model'] != MODEL or consent['reasoning'] != REASONING
            or type(consent['max_calls']) is not int or consent['max_calls'] != 1
            or type(consent['cap_nano_usd']) is not int
            or not RESERVATION_NANO_USD <= consent['cap_nano_usd'] <= CAP_NANO_USD):
        raise HostedError('Explicit current hosted-task consent and cost limit are required.')
    expected = {
        'request_sha256': prepared['request_sha256'],
        'context_sha256': prepared['context_sha256'],
        'summary_sha256': _digest(prepared['consent_summary']),
        'ledger_path_sha256': hashlib.sha256(os.fsencode(path)).hexdigest(),
    }
    if any(consent[k] != value for k, value in expected.items()):
        raise HostedError('The consented request, visible context or task ledger changed; review consent again.')
    now = runner.elapsed_time()
    before, after = consent['created_elapsed_time'], consent['expires_elapsed_time']
    if (any(type(v) not in (int, float) or not math.isfinite(v) for v in (before, after, now))
            or not 0 <= before <= now < after or not 0 < after - before <= CONSENT_SECONDS):
        raise HostedError('Hosted-task consent expired or its clock changed; no request is authorized.')


def _usage(data):
    value = data.get('usage') if type(data) is dict else None
    if type(value) is not dict:
        return None
    keys = ('input_tokens', 'output_tokens', 'total_tokens')
    if (any(type(value.get(k)) is not int or not 0 <= value[k] <= 1_000_000 for k in keys)
            or value['total_tokens'] != value['input_tokens'] + value['output_tokens']):
        return None
    details, inp = value.get('output_tokens_details'), value.get('input_tokens_details')
    if (type(details) is not dict or type(details.get('reasoning_tokens')) is not int
            or not 0 <= details['reasoning_tokens'] <= value['output_tokens']
            or type(inp) is not dict or not {'cached_tokens', 'cache_write_tokens'} <= set(inp)):
        return None
    cached, writes = inp['cached_tokens'], inp['cache_write_tokens']
    if any(type(n) is not int or n < 0 for n in (cached, writes)) or cached + writes > value['input_tokens']:
        return None
    write_details = inp.get('cache_write_tokens_details', {})
    if type(write_details) is not dict:
        return None
    write30, write12 = write_details.get('ttl_30m_tokens', 0), write_details.get('ttl_12h_tokens', 0)
    if (any(type(n) is not int or n < 0 for n in (write30, write12)) or write30 + write12 != writes):
        return None
    return {k: value[k] for k in keys} | {
        'reasoning_tokens': details['reasoning_tokens'], 'cached_tokens': cached,
        'cache_write_tokens': writes, 'cache_write_30m_tokens': write30,
        'cache_write_12h_tokens': write12,
    }


def _cost(usage):
    # nanoUSD/token: input2000, cached100, 30m-write2500, 12h-write5000,
    # output10000. Output includes reasoning, never counted a second time.
    ordinary = usage['input_tokens'] - usage['cached_tokens'] - usage['cache_write_tokens']
    return (ordinary * 2000 + usage['cached_tokens'] * 100
            + usage['cache_write_30m_tokens'] * 2500
            + usage['cache_write_12h_tokens'] * 5000 + usage['output_tokens'] * 10000)


def _function(data):
    allowed = {'id','object','created_at','completed_at','status','error','incomplete_details','instructions',
               'max_output_tokens','model','output','parallel_tool_calls','previous_response_id','reasoning',
               'store','temperature','text','tool_choice','tools','top_p','top_logprobs','truncation','usage',
               'user','metadata','service_tier','background','max_tool_calls','safety_identifier',
               'prompt_cache_key','prompt_cache_retention','prompt_cache_options','conversation',
               'context_management','tool_usage','access_programs','billing','frequency_penalty',
               'presence_penalty','image','input_transformations','moderation'}
    if (type(data) is not dict or set(data) - allowed or data.get('object', 'response') != 'response'
            or data.get('status') != 'completed' or data.get('error') is not None
            or data.get('incomplete_details') is not None or data.get('service_tier') != 'default'
            or data.get('model') != MODEL):
        raise HostedError('The provider response is incomplete or its exact model/tier is unsupported.',
                          {'refusal_code': 'response_envelope_unsupported'})
    if (('billing' in data and data['billing'] != {'payer':'developer'})
            or any(type(data.get(k, 0)) not in (int, float) or data.get(k, 0) != 0
                   for k in ('frequency_penalty', 'presence_penalty'))
            or data.get('input_transformations', []) != [] or data.get('moderation') is not None
            or data.get('image') not in (None, {'context_compression':'enabled'}, {'context_compression':'disabled'})):
        raise HostedError('The provider returned unsupported non-default metadata.',
                          {'refusal_code': 'response_metadata_unsupported'})
    reasoning = data.get('reasoning')
    # Modern Responses returns the effective default execution/context mode.
    # These bounded metadata values confer no tool or approval authority. The
    # old effort/summary-only envelope remains supported; unknown/pro modes do not.
    if (type(reasoning) is not dict or set(reasoning) - {'effort', 'summary', 'mode', 'context'}
            or reasoning.get('effort') != REASONING or reasoning.get('summary') is not None
            or reasoning.get('mode', 'standard') != 'standard'
            or reasoning.get('context') not in (None, 'current_turn', 'all_turns')):
        raise HostedError('The provider did not confirm the consented reasoning profile.',
                          {'refusal_code': 'reasoning_profile_mismatch'})
    output = data.get('output')
    if type(output) is not list or not 1 <= len(output) <= 8:
        raise HostedError('The provider output is missing or malformed.', {'refusal_code': 'output_missing'})
    calls = []
    for item in output:
        if type(item) is not dict:
            raise HostedError('The provider output item is malformed.', {'refusal_code': 'output_item_invalid'})
        if item.get('type') == 'reasoning':
            if (set(item) - {'type','id','summary','status','encrypted_content','content'}
                    or item.get('summary') != [] or item.get('content') not in (None, [])):
                raise HostedError('Reasoning text is not a placement proposal.',
                                  {'refusal_code': 'reasoning_text_present'})
            continue
        if (item.get('type') != 'function_call'
                or set(item) - {'id','type','call_id','name','arguments','status'}
                or item.get('status', 'completed') != 'completed'
                or type(item.get('call_id')) is not str or not 1 <= len(item['call_id']) <= 128
                or item.get('name') not in {'propose_placement_route', 'clarify_design_request'}
                or type(item.get('arguments')) is not str or not 0 < len(item['arguments']) <= 16384):
            raise HostedError('Only one bounded placement proposal or clarification is supported.',
                              {'refusal_code': 'tool_call_invalid'})
        calls.append(item)
    if len(calls) != 1:
        raise HostedError('Exactly one proposal or clarification is required.', {'refusal_code': 'tool_call_count'})
    try:
        arguments = client._strict_json(calls[0]['arguments'])
    except client.ModelIntentError:
        raise HostedError('Proposal arguments must be valid JSON.', {'refusal_code': 'tool_arguments_malformed'}) from None
    if type(arguments) is not dict:
        raise HostedError('Proposal arguments must be a JSON object.', {'refusal_code': 'tool_arguments_not_object'})
    return calls[0]['name'], arguments


class _Ledger:
    """One exclusive reservation; no append, recovery cursor or old allowance."""
    def __init__(self, path, consent, prepared):
        self.path = path
        self.parent_identity = (path.parent.stat().st_dev, path.parent.stat().st_ino)
        self.value = {
            'schema': 1, 'kind': 'autorouter.hosted-intent-ledger.v1',
            'consent_sha256': _digest(consent), 'request_sha256': prepared['request_sha256'],
            'context_sha256': prepared['context_sha256'], 'model': MODEL,
            'reasoning': REASONING, 'endpoint': ENDPOINT, 'rate_revision': RATE_REVISION,
            'attempts': 1, 'max_calls': 1, 'cap_nano_usd': consent['cap_nano_usd'],
            'reserved_nano_usd': RESERVATION_NANO_USD, 'outcome': 'reserved',
            'usage': None, 'cost_nano_usd': None, 'response_sha256': None,
        }
        raw = _encoded(self.value) + b'\n'
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        except OSError:
            raise HostedError('The task ledger already exists or cannot be created; no request was sent.') from None
        self.expected_sha256 = hashlib.sha256(raw).hexdigest()

    def save(self):
        if (self.path.parent.stat().st_dev, self.path.parent.stat().st_ino) != self.parent_identity:
            raise HostedError('The task ledger directory changed; stop further requests.')
        meta = self.path.lstat()
        if (not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1 or meta.st_mode & 0o077
                or hashlib.sha256(read_bytes(self.path, 16384)).hexdigest() != self.expected_sha256):
            raise HostedError('The task ledger changed; its reservation must be reviewed.')
        pipeline.save_json(self.path, self.value)
        # The common atomic writer creates a fresh inode. This is our newly
        # created non-secret task receipt, never a retained source/board file.
        self.path.chmod(0o600)
        raw = read_bytes(self.path, 16384)
        if client._strict_json(raw) != self.value:
            raise HostedError('The task ledger could not be read back; stop further requests.')
        self.expected_sha256 = hashlib.sha256(raw).hexdigest()


def _tls_context():
    context = ssl.create_default_context()
    if (context.check_hostname is not True or context.verify_mode != ssl.CERT_REQUIRED
            or context.cert_store_stats().get('x509_ca', 0) <= 0):
        raise HostedError('Verified TLS trust and hostname checking are required.')
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def _https_exchange(body, credential, timeout, *, probe=False):
    """Exact endpoint, no redirect/proxy discovery; bounded safe tagged output."""
    connection = response = None
    try:
        context = _tls_context()
        connection = http.client.HTTPSConnection('api.openai.com', 443, timeout=timeout, context=context)
        if probe:
            if body is not None or credential is not None:
                raise ValueError
            connection.connect()
            return b'T' + _encoded({
                'python': sys.version.split()[0], 'TLS_version': connection.sock.version(),
                'hostname_check': context.check_hostname,
                'certificate_required': context.verify_mode == ssl.CERT_REQUIRED,
                'trust': 'python_default_verified_trust', 'HTTP_requests': 0,
            })
        connection.request('POST', '/v1/responses', body=body, headers={
            'Authorization': 'Bearer ' + credential, 'Content-Type': 'application/json',
            'Accept': 'application/json', 'Accept-Encoding': 'identity', 'Connection': 'close'})
        response = connection.getresponse()
        if response.status != 200:
            status = response.status
            return b'H' + str(status).encode('ascii') if type(status) is int and 100 <= status <= 599 else b'E'
        if (response.getheader('Content-Type', '').split(';', 1)[0].strip().lower() != 'application/json'
                or response.getheader('Content-Encoding', 'identity').lower() != 'identity'):
            raise ValueError
        length = response.getheader('Content-Length')
        if length is not None and (not length.isascii() or not length.isdecimal() or int(length) > MAX_RESPONSE_BYTES):
            raise ValueError
        raw = bytearray()
        while True:
            chunk = response.read1(min(8192, MAX_RESPONSE_BYTES + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise ValueError
        if length is not None and len(raw) != int(length):
            raise ValueError
        if credential.encode('ascii') in raw:
            return b'K'  # Do not put a reflected credential onto the parent pipe.
        return b'J' + bytes(raw)
    except BaseException as exc:
        return (b'C' if isinstance(exc, ssl.SSLCertVerificationError) else
                b'D' if isinstance(exc, socket.gaierror) else
                b'O' if isinstance(exc, TimeoutError) else
                b'L' if isinstance(exc, ssl.SSLError) else b'E')
    finally:
        if response is not None:
            response.close()
        if connection is not None:
            connection.close()


def _worker_main():
    """Private protocol; all errors are safe tags, never tracebacks or input."""
    result = b'E'
    try:
        if sys.version_info[:2] != (3, 11):
            raise ValueError
        raw = sys.stdin.buffer.read(MAX_ENVELOPE_BYTES + 1)
        if not raw or len(raw) > MAX_ENVELOPE_BYTES:
            raise ValueError
        value = client._strict_json(raw)
        if (type(value) is not dict or set(value) != {'probe','body','credential','timeout'}
                or type(value['probe']) is not bool
                or type(value['timeout']) not in (int, float)
                or not math.isfinite(value['timeout']) or not 0 < value['timeout'] <= DEADLINE_SECONDS):
            raise ValueError
        probe, body, credential = value['probe'], value['body'], value['credential']
        if probe:
            if body is not None or credential is not None:
                raise ValueError
        elif (type(body) is not str or not 0 < len(body.encode()) + INPUT_OVERHEAD_TOKENS <= INPUT_TOKENS
                or type(credential) is not str or re.fullmatch(r'[A-Za-z0-9_-]{8,4096}', credential) is None):
            raise ValueError
        def no_descendants(event, _args):
            if event in ('subprocess.Popen', 'os.fork', 'os.forkpty', 'os.posix_spawn', 'os.exec'):
                raise RuntimeError('This HTTPS worker cannot spawn descendants.')
        sys.addaudithook(no_descendants)
        result = _https_exchange(None if probe else body.encode(), credential, value['timeout'], probe=probe)
        credential = None; value = None; raw = None
    except BaseException:
        result = b'E'
    try:
        sys.stdout.buffer.write(result); sys.stdout.buffer.flush()
    except BaseException:
        pass


def _worker_argv(worker_python=None):
    path = Path(worker_python) if worker_python is not None else Path(__file__).resolve().parents[1] / '.venv/bin/python'
    path = path.absolute()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise HostedError('The installation Python 3.11 HTTPS worker is unavailable.')
    return [str(path), '-B', str(Path(__file__).resolve()), '--https-worker']


def _supported_platform():
    return sys.platform == 'darwin' or sys.platform.startswith('linux')


def _run_worker(body, credential, deadline, cancel_event=None, *, worker_python=None, probe=False):
    """One bounded owned child, private stdin, no detached DNS or socket thread.

    Reuses the reviewed child lifecycle and shared elapsed/RSS helpers. Worker
    code cannot create descendants. Pipe helpers are joined after owned-child
    termination; stderr is discarded, never a credential-bearing debug log.
    Darwin/Linux have qualified RSS units; Windows refuses before spawning.
    """
    if not _supported_platform():
        raise HostedError('Hosted-worker resource guards are not qualified on this platform; no request was sent.')
    if probe and (body is not None or credential is not None):
        raise HostedError('A TLS probe cannot contain a credential or project data.')
    if cancel_event is not None and cancel_event.is_set():
        raise HostedError('Cancelled before hosted-worker startup.')
    remaining = deadline - runner.elapsed_time() - .5
    if not 0 < remaining <= DEADLINE_SECONDS:
        raise HostedError('The hosted-worker deadline is unavailable or expired.')
    envelope = _encoded({'probe': probe, 'body': None if probe else body.decode('ascii'),
                         'credential': credential, 'timeout': remaining})
    if len(envelope) > MAX_ENVELOPE_BYTES:
        raise HostedError('The private hosted-worker envelope exceeds its bound.')
    environment = gui.child_environment()
    for name in list(environment):
        if name.upper().endswith(('_API_KEY', '_ACCESS_TOKEN')):
            del environment[name]
    process = subprocess.Popen(_worker_argv(worker_python), cwd=Path(__file__).resolve().parents[1],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        env=environment, start_new_session=True, close_fds=True, shell=False)
    output, io_errors, overflow = bytearray(), [], threading.Event()
    def send():
        try:
            process.stdin.write(envelope); process.stdin.flush()
        except (OSError, ValueError):
            io_errors.append(True)
        finally:
            try: process.stdin.close()
            except (OSError, ValueError): pass
    def receive():
        try:
            while True:
                chunk = process.stdout.read1(8192)
                if not chunk: break
                if len(output) + len(chunk) > MAX_RESPONSE_BYTES + 1:
                    overflow.set(); break
                output.extend(chunk)
        except (OSError, ValueError):
            io_errors.append(True)
    sender = threading.Thread(target=send, name='hosted-private-input', daemon=False)
    receiver = threading.Thread(target=receive, name='hosted-bounded-output', daemon=False)
    sender_started = receiver_started = False
    reaped = False; stats = {'worker_CPU_seconds': None, 'sampled_worker_RSS_bytes': 0,
                            'monitor_CPU_seconds': 0.0,
                            'resource_guard_os_enforced': False}
    def reap():
        nonlocal reaped
        if not reaped:
            pid, status, usage = os.wait4(process.pid, os.WNOHANG)
            if pid:
                reaped = True; process.returncode = os.waitstatus_to_exitcode(status)
                stats['worker_CPU_seconds'] = usage.ru_utime + usage.ru_stime
    def signal_owned(number):
        # Popen.send_signal calls poll(), which would become a second reaper
        # racing this wait4. An unreaped child PID cannot have been reused.
        if not reaped:
            try: os.kill(process.pid, number)
            except ProcessLookupError: pass
    try:
        sender.start(); sender_started = True
        receiver.start(); receiver_started = True
        next_rss = 0
        while runner.elapsed_time() < deadline - .5:
            if cancel_event is not None and cancel_event.is_set():
                raise HostedError('Hosted request cancelled; any uncertain usage remains reserved.')
            if overflow.is_set():
                raise HostedError('Hosted-worker output exceeded its bound.')
            reap()
            if reaped and not receiver.is_alive() and not sender.is_alive():
                if process.returncode != 0 or io_errors:
                    raise HostedError('Hosted worker ended without a complete response.')
                return bytes(output), stats
            if not reaped and runner.elapsed_time() >= next_rss:
                rss, monitor_cpu = runner._group_rss_bytes(process.pid, Path(__file__).resolve().parents[1])
                stats['monitor_CPU_seconds'] += monitor_cpu
                stats['sampled_worker_RSS_bytes'] = max(stats['sampled_worker_RSS_bytes'], rss)
                if rss > WORKER_RSS_BYTES:
                    raise HostedError('Hosted worker exceeded its memory bound.')
                next_rss = runner.elapsed_time() + .25
            time.sleep(.025)
        raise HostedError('Hosted request deadline reached; no retry was made.')
    finally:
        if not reaped:
            signal_owned(signal.SIGTERM)
            stop = time.monotonic() + .25
            while not reaped and time.monotonic() < stop:
                reap(); time.sleep(.005)
            if not reaped:
                signal_owned(signal.SIGKILL); stop = time.monotonic() + .5
                while not reaped and time.monotonic() < stop:
                    reap(); time.sleep(.005)
        if sender_started: sender.join(timeout=.5)
        if receiver_started: receiver.join(timeout=.5)
        process.stdout.close()
        if not reaped or sender.is_alive() or receiver.is_alive():
            raise HostedError('Hosted-worker cleanup is incomplete; stop further calls.')
        envelope = None; credential = None


def _decode_transport(raw, *, probe=False):
    if type(raw) is not bytes or not raw or len(raw) > MAX_RESPONSE_BYTES + 1:
        raise HostedError('The hosted worker returned invalid framing.')
    if (len(raw) == 4 and raw[:1] == b'H' and raw[1:].isdigit()
            and 100 <= int(raw[1:]) <= 599):
        raise HostedError('The hosted endpoint refused the request; no retry was made.',
                          {'http_status': int(raw[1:]), 'refusal_stage': 'http_status'})
    stages = {b'C':'tls_certificate', b'D':'dns', b'O':'transport_timeout', b'L':'tls_handshake',
              b'K':'credential_response', b'E':'worker_failure'}
    if raw in stages:
        raise HostedError('The verified hosted connection or response was refused; no retry was made.',
                          {'refusal_stage': stages[raw]})
    if raw[:1] != (b'T' if probe else b'J'):
        raise HostedError('The hosted worker response mode was invalid.')
    return client._strict_json(raw[1:])


def probe_tls(*, worker_python=None, cancel_event=None):
    """Actual same-worker verified TLS handshake; zero HTTP/model/data request."""
    raw, stats = _run_worker(None, None, runner.elapsed_time() + DEADLINE_SECONDS,
                             cancel_event, worker_python=worker_python, probe=True)
    value = _decode_transport(raw, probe=True)
    if (type(value) is not dict
            or set(value) != {'python','TLS_version','hostname_check','certificate_required','trust','HTTP_requests'}
            or type(value['python']) is not str or not value['python'].startswith('3.11.')
            or value['TLS_version'] not in ('TLSv1.2', 'TLSv1.3')
            or value['hostname_check'] is not True or value['certificate_required'] is not True
            or value['trust'] != 'python_default_verified_trust' or value['HTTP_requests'] != 0):
        raise HostedError('The actual-worker TLS proof was incomplete.')
    return dict(value, **stats)


def propose_placement_route(inspection, context, request_text, *, credential, consent,
                            ledger_path, cancel_event=None, worker_python=None):
    """One request; return shared proposal/clarification/metrics, never execute."""
    started = runner.elapsed_time(); deadline = started + DEADLINE_SECONDS
    if not _supported_platform():
        raise HostedError('Hosted-worker resource guards are not qualified on this platform; no request was sent.')
    prepared = prepare_request(inspection, context, request_text)
    path = _ledger_path(ledger_path)
    source_parent = Path(inspection['source']).parent
    if path == source_parent or source_parent in path.parents:
        raise HostedError('Keep the hosted-task ledger outside the immutable source project.')
    _check_consent(consent, prepared, path)
    if (type(credential) is not str or re.fullmatch(r'[A-Za-z0-9_-]{8,4096}', credential) is None):
        raise HostedError('Enter the dedicated credential only in the private masked field.')
    if credential.encode('ascii') in prepared['body']:
        raise HostedError('Credential material cannot be included in request data.')
    if cancel_event is not None and cancel_event.is_set():
        raise HostedError('Cancelled before reserving or sending the hosted request.')
    _worker_argv(worker_python)  # Unavailable executable refuses before reservation.
    metrics = {'request_count': 0, 'transport_invoked': False, 'refusal_stage': None,
               'model': MODEL, 'reasoning': REASONING, 'endpoint': ENDPOINT,
               'service_tier': 'default', 'usage': None, 'cost_nano_usd': None,
               'cost_usd': None, 'cost_status': 'unknown', 'proposal_only': True,
               'request_sha256': prepared['request_sha256'],
               'context_sha256': prepared['context_sha256'],
               'reserved_nano_usd': RESERVATION_NANO_USD,
               'conservative_input_tokens': prepared['conservative_input_tokens'],
               'model_runtime_verified_offline': False}
    ledger = _Ledger(path, consent, prepared); metrics['request_count'] = 1
    stage = 'pre_transport'
    try:
        _check_consent(consent, prepared, path)
        design.validate_pending_placement_route_proposal(inspection, context, prepared['initial'])
        if runner.elapsed_time() >= deadline - .5 or cancel_event is not None and cancel_event.is_set():
            raise HostedError('Hosted request cancelled or expired before transport.')
        stage = 'transport'; metrics['transport_invoked'] = True
        raw, stats = _run_worker(prepared['body'], credential, deadline, cancel_event,
                                 worker_python=worker_python)
        metrics.update(stats)
        stage = 'response_envelope'
        data = _decode_transport(raw)
        stage = 'response_accounting'
        usage = _usage(data)
        priced = type(data) is dict and data.get('model') == MODEL and data.get('service_tier') == 'default'
        ledger.value['response_sha256'] = hashlib.sha256(raw[1:]).hexdigest()
        ledger.value['usage'] = usage
        ledger.value['cost_nano_usd'] = _cost(usage) if usage is not None and priced else None
        ledger.value['outcome'] = 'usage_unknown' if usage is None else 'response_rejected'
        ledger.save()  # Durable accounting precedes intent/semantic handling.
        metrics.update(usage=usage, response_sha256=ledger.value['response_sha256'],
                       cost_nano_usd=ledger.value['cost_nano_usd'],
                       cost_usd=None if ledger.value['cost_nano_usd'] is None else ledger.value['cost_nano_usd'] / 1e9,
                       cost_status='unknown; reservation retained' if ledger.value['cost_nano_usd'] is None
                           else 'Provider usage at frozen Standard rates; not invoice/tax/discount verification.')
        if (usage is None or ledger.value['cost_nano_usd'] is None
                or usage['input_tokens'] > prepared['conservative_input_tokens']
                or usage['input_tokens'] > INPUT_TOKENS or usage['output_tokens'] > OUTPUT_TOKENS
                or usage['cache_write_12h_tokens'] > 0
                or ledger.value['cost_nano_usd'] > RESERVATION_NANO_USD):
            raise HostedError('Provider identity, usage or accounting is uncertain or outside the consented bounds.')
        if credential.encode('ascii') in _encoded(data):
            raise HostedError('Provider credential material was refused without retaining response text.')
        stage = 'response_contract'
        name, arguments = _function(data)
        if credential.encode('ascii') in _encoded(arguments):
            raise HostedError('Provider credential material was refused without retaining response text.')
        stage = 'post_response_context_freshness'
        current = design.validate_pending_placement_route_proposal(
            inspection, context, prepared['initial'], arguments if name == 'propose_placement_route' else None)
        stage = 'semantic_validation'
        clarification = None if name == 'propose_placement_route' else design.validate_design_clarification(arguments)
        if runner.elapsed_time() >= deadline or cancel_event is not None and cancel_event.is_set():
            raise HostedError('Hosted result was cancelled or expired; no proposal was adopted.')
        ledger.value['outcome'] = 'intent_proposed' if clarification is None else 'clarification_received'
        ledger.save()
        # Receipt publication cannot revive stale or cancelled context.
        stage = 'publication'
        _check_consent(consent, prepared, path)
        design.validate_pending_placement_route_proposal(inspection, context, prepared['initial'])
        if runner.elapsed_time() >= deadline or cancel_event is not None and cancel_event.is_set():
            raise HostedError('Hosted result expired during publication; no proposal was adopted.')
        metrics['wall_seconds'] = runner.elapsed_time() - started
        return {'proposal': current if clarification is None else None,
                'clarification': clarification, 'metrics': metrics}
    except BaseException as exc:
        if isinstance(exc, HostedError):
            metrics.update(_saved_diagnostics(exc.metrics))
        if not metrics.get('refusal_stage'):
            metrics['refusal_stage'] = 'post_response_context_changed' if isinstance(exc, design.PendingContextChanged) else stage
        if ledger.value['outcome'] == 'reserved':
            ledger.value['outcome'] = 'transport_unknown'
        elif ledger.value['outcome'] in ('intent_proposed', 'clarification_received'):
            ledger.value['outcome'] = 'response_rejected'
        metrics['wall_seconds'] = runner.elapsed_time() - started
        ledger.value['diagnostics'] = _saved_diagnostics(metrics)
        try: ledger.save()
        except Exception: metrics['ledger_update_failed'] = True
        raise HostedError('Hosted plan was refused; no retry, fallback, execution or approval occurred.', metrics) from None
    finally:
        credential = None


if __name__ == '__main__':
    if sys.argv[1:] == ['--https-worker']:
        _worker_main()
