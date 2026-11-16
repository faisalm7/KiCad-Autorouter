"""Whole-module offline regression; existing runtime and paid screen stay frozen."""
import functools
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from autorouter import design_intent as design
from tests import test_placement_route_intent as shared


ROOT = Path(__file__).resolve().parents[2]
BASELINE_SHA256 = '998725516642ca551a4b0ea6b40df3740d8995c60c4f02f31feb545858d8d6f3'


@functools.lru_cache(maxsize=1)
def proposed_client():
    source = ROOT / 'autorouter/model_intent.py'
    if hashlib.sha256(source.read_bytes()).hexdigest() != BASELINE_SHA256:
        raise RuntimeError('Intent baseline changed; review this staged patch before applying it.')
    # A single small, owned verification copy; no project or installation clone.
    with tempfile.TemporaryDirectory(prefix='intent-contract-') as directory:
        scratch = Path(directory)
        target = scratch / 'autorouter/model_intent.py'
        target.parent.mkdir()
        target.write_bytes(source.read_bytes())
        subprocess.run(
            ['/usr/bin/git', 'apply', '--no-index', '--whitespace=error-all',
             str(Path(__file__).with_name('model_intent.patch'))],
            cwd=scratch, check=True, capture_output=True, timeout=5)
        specification = importlib.util.spec_from_file_location(
            'autorouter._intent_contract_proposed', target)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        return module


class ProposedSharedControls(shared.PlacementRouteIntent):
    """Reuse all existing real validator controls with the whole proposed client."""

    def setUp(self):
        replacement = patch.object(shared, 'client', proposed_client())
        replacement.start()
        self.addCleanup(replacement.stop)
        super().setUp()

    def test_wire_proposal_is_only_the_schema_defined_projection(self):
        def respond(_host, _port, body, _headers, _timeout):
            sent = json.loads(body)
            visible = json.loads(sent['messages'][1]['content'])['inspection']['placement_context']
            properties = sent['tools'][0]['function']['parameters']['properties']
            arguments = {'action': 'place_and_route', **{
                key: visible[key] for key in properties if key != 'action'}}
            self.assertEqual(arguments, self.request)
            self.assertEqual(set(arguments), set(properties))
            self.assertNotIn('components', arguments)
            self.assertNotIn('caller_rebuild_permission_present', arguments)
            self.assertIn('only the six fields defined by the tool schema',
                          sent['messages'][0]['content'])
            self.assertIn('read-only', sent['messages'][0]['content'])
            self.assertEqual(sent['tools'][0], design.placement_tool_schema())
            return json.dumps(shared.response(arguments)).encode()

        with patch.object(shared.client, '_post', side_effect=respond) as transport:
            result = shared.client.propose_placement_route(
                self.inspection, self.context, 'Use the visible choices.', self.config)
        transport.assert_called_once()
        self.assertEqual(result['proposal']['intent'], self.request)
        self.assertFalse(result['proposal']['execution_authorized'])
        self.assertFalse(result['proposal']['approval_granted'])

    def test_old_response_after_visible_change_has_freshness_priority(self):
        original = dict(self.request)

        def changed(*_args, **_kwargs):
            updated = self.make_context(route_seconds=120)
            self.context.clear()
            self.context.update(updated)
            return json.dumps(shared.response(original)).encode()

        with patch.object(shared.client, '_post', side_effect=changed) as transport:
            with self.assertRaisesRegex(shared.client.ModelIntentError,
                                        'changed while the request was pending'):
                shared.client.propose_placement_route(
                    self.inspection, self.context, 'Use the visible choices.', self.config)
        transport.assert_called_once()


if __name__ == '__main__':
    unittest.main()
