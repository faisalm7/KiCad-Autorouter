"""Shared real validators plus synthetic HTTP; no live AI/Native/GUI execution."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import design_intent as design, model_intent as client, placement_intent as placement
from autorouter import gui, sexpr as sx
from experiments.placement_native_proposal_v1 import multipad_fixture
from tests.test_model_intent import local_server, response as route_response


def response(arguments):
    value=route_response(arguments)
    value['choices'][0]['message']['tool_calls'][0]['function']['name']='propose_placement_route'
    return value


def clarification(reason='ambiguous_request', questions=None):
    arguments={'reason':reason,'questions':['Which connectors and location do you mean?']if questions is None else questions}
    value=route_response(arguments)
    value['choices'][0]['message']['tool_calls'][0]['function']['name']='clarify_design_request'
    return value


class PlacementRouteIntent(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='copilot-draft-',dir=Path.cwd())
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
        self.board=multipad_fixture.write_project(self.root/'owned source')
        self.selected=[multipad_fixture.uid(ref+'-footprint')for ref in('J1','J2')]
        self.fixed=[multipad_fixture.uid('J3-footprint')]
        self.settings=placement.settings(self.selected,[7_000_000,7_000_000,31_000_000,13_000_000],
            copper_policy=placement.COPPER_POLICY,protected_names=['KEEP'],protected_route_ids=[])
        self.inspection=placement.inspect_saved(self.board)
        self.context=self.make_context()
        self.request=design.placement_request(self.context)
        self.config=dict(endpoint='http://127.0.0.1:12345/v1/chat/completions',model='synthetic-placement')

    def make_context(self,**changes):
        options=dict(fixed_components=self.fixed,rebuild_permission=True,
            approved_route_nets=['ROUTE_A','ROUTE_B'],route_seconds=90)
        options.update(changes)
        return design.placement_route_context(self.inspection,self.settings,**options)

    def validate(self,proposal=None,context=None):
        return design.validate_placement_route_proposal(self.inspection,
            self.context if context is None else context,self.request if proposal is None else proposal)

    def test_ordinary_controls_and_model_share_exact_settings_and_never_execute(self):
        original=gui.source_inventory(self.board);before=copy.deepcopy((self.inspection,self.context,self.request))
        with patch('subprocess.Popen',side_effect=AssertionError('no product process')), \
                patch.object(placement,'propose',side_effect=AssertionError('no geometry search')):
            result=self.validate()
        self.assertEqual(result['placement_settings'],placement.validate_settings(self.settings))
        self.assertEqual(result['fixed_components'],self.fixed)
        self.assertEqual(result['copper_plan'],placement.copper_plan(self.inspection,self.settings))
        self.assertEqual(result['copper_plan']['incident_names'],['ROUTE_A','ROUTE_B'])
        self.assertEqual(result['routing_preferences']['scope'],'selected_nets')
        self.assertEqual(result['routing_preferences']['nets'],['ROUTE_A','ROUTE_B'])
        self.assertEqual(result['routing_preferences']['seconds'],90)
        for key in('native_validation_performed','execution_authorized','approval_granted','warning_acknowledged','routing_accepted'):
            self.assertIs(result[key],False)
        self.assertEqual((self.inspection,self.context,self.request),before)
        self.assertEqual(gui.source_inventory(self.board),original)

    def test_missing_rebuild_permission_and_incomplete_net_approval_need_clarification(self):
        for changes in(dict(rebuild_permission=False),dict(rebuild_permission='yes'),
                        dict(approved_route_nets=['ROUTE_A']),dict(approved_route_nets=['ROUTE_A','ROUTE_B','GND'])):
            with self.subTest(changes=changes),self.assertRaises(design.IntentError):self.make_context(**changes)
        preserve=placement.settings(self.selected,self.settings['region_nm'])
        with self.assertRaisesRegex(design.IntentError,'Clarification'):
            design.placement_route_context(self.inspection,preserve,fixed_components=self.fixed,
                rebuild_permission=True,approved_route_nets=['ROUTE_A','ROUTE_B'])

    def test_fixed_selected_overlap_unknown_ids_and_unsupported_requirements_refuse(self):
        for fixed in(self.selected,['not-an-observed-UUID']):
            with self.subTest(fixed=fixed),self.assertRaises(design.IntentError):self.make_context(fixed_components=fixed)
        for extra in({'approval_granted':True},{'rebuild_permission':True},{'warning_acknowledged':True},
                      {'command':'shell'},{'electrical_constraints':{'impedance_ohm':50}}):
            proposal=dict(self.request,**extra)
            with self.subTest(extra=extra),self.assertRaisesRegex(design.IntentError,'Clarification'):self.validate(proposal)

    def test_model_cannot_override_current_visible_selection_region_fixed_or_budget(self):
        changes=[('action','execute'),('selected',self.selected[::-1]),('fixed',[]),
            ('region_nm',[7_000_000,7_000_000,30_000_000,13_000_000]),
            ('route_nets',['GND']),('route_seconds',900),('route_seconds',90.0)]
        for key,value in changes:
            proposal=copy.deepcopy(self.request);proposal[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(design.IntentError):self.validate(proposal)

    def test_context_schema_and_inspection_cannot_be_forged_or_stale(self):
        for key,value in(('schema',True),('inspection_sha256','0'*64),('kind','other-context')):
            context=copy.deepcopy(self.context);context[key]=value
            with self.subTest(key=key),self.assertRaises(design.IntentError):self.validate(context=context)
        inspection=copy.deepcopy(self.inspection);inspection['components']=[]
        with self.assertRaises(design.IntentError):
            design.validate_placement_route_proposal(inspection,self.context,self.request)
        self.board.with_suffix('.kicad_pro').write_bytes(self.board.with_suffix('.kicad_pro').read_bytes()+b'\n')
        with self.assertRaisesRegex(design.IntentError,'source changed'):self.validate()

    def test_bounded_placement_tool_has_no_permission_or_execution_arguments(self):
        schema=design.placement_tool_schema()['function']['parameters']
        self.assertFalse(schema['additionalProperties']);self.assertEqual(set(schema['required']),set(self.request))
        self.assertNotIn('rebuild_permission',schema['properties'])
        self.assertNotIn('approval_granted',schema['properties'])
        schema['properties']['action']['enum'].append('execute')
        self.assertEqual(design.placement_tool_schema()['function']['parameters']['properties']['action']['enum'],['place_and_route'])

    def test_model_contract_uses_canonical_fresh_schema_and_only_its_intent_fields(self):
        contract = design.placement_model_contract()
        self.assertEqual(contract['tools'], [design.placement_tool_schema(), design.clarification_tool_schema()])
        self.assertEqual(contract['tool_choice'], 'required')
        parameters = contract['tools'][0]['function']['parameters']
        copied = [key for key in parameters['required'] if key != 'action']
        self.assertEqual(set(parameters['required']), set(self.request))
        self.assertIn('action=place_and_route', contract['instructions'])
        self.assertIn('copy only ' + '/'.join(copied), contract['instructions'])
        self.assertIn('read-only', contract['instructions'])
        self.assertIn('clarify instead of guessing', contract['instructions'])
        self.assertNotIn('echo the complete', contract['instructions'])
        contract['tools'][0]['function']['parameters']['required'].append('approval_granted')
        self.assertNotIn('approval_granted',
            design.placement_model_contract()['tools'][0]['function']['parameters']['required'])

    def test_actual_client_uses_shared_contract_and_only_schema_arguments(self):
        expected_contract = design.placement_model_contract()
        def respond(_host, _port, body, _headers, _timeout):
            sent = json.loads(body)
            self.assertEqual(sent['messages'][0]['content'], expected_contract['instructions'])
            self.assertEqual(sent['tools'], expected_contract['tools'])
            visible = json.loads(sent['messages'][1]['content'])['inspection']['placement_context']
            fields = sent['tools'][0]['function']['parameters']['required']
            arguments = {'action': 'place_and_route', **{
                key: visible[key] for key in fields if key != 'action'}}
            self.assertEqual(arguments, self.request)
            self.assertNotIn('components', arguments)
            self.assertNotIn('caller_rebuild_permission_present', arguments)
            return json.dumps(response(arguments)).encode()
        with patch.object(client, '_post', side_effect=respond) as transport:
            result = client.propose_placement_route(
                self.inspection, self.context, 'Use the visible choices.', self.config)
        transport.assert_called_once()
        self.assertEqual(result['proposal']['intent'], self.request)
        self.assertFalse(result['proposal']['execution_authorized'])
        self.assertFalse(result['proposal']['approval_granted'])

    def test_old_arguments_after_visible_change_have_freshness_priority(self):
        original = copy.deepcopy(self.request)
        def changed(*_args, **_kwargs):
            updated = self.make_context(route_seconds=120)
            self.context.clear(); self.context.update(updated)
            return json.dumps(response(original)).encode()
        with patch.object(client, '_post', side_effect=changed) as transport:
            with self.assertRaisesRegex(client.ModelIntentError, 'changed while the request was pending'):
                client.propose_placement_route(
                    self.inspection, self.context, 'Use the visible choices.', self.config)
        transport.assert_called_once()

    def test_shared_pending_fence_covers_clarification_permission_and_authority(self):
        initial = self.validate()
        self.assertEqual(design.validate_pending_placement_route_proposal(
            self.inspection, self.context, initial), initial)
        with self.assertRaises(design.IntentError):
            design.validate_pending_placement_route_proposal(
                self.inspection, self.context, initial, dict(self.request, approval_granted=True))
        changed = self.make_context(route_seconds=120)
        with self.assertRaises(design.PendingContextChanged):
            design.validate_pending_placement_route_proposal(
                self.inspection, changed, initial, self.request)
        with self.assertRaises(design.PendingContextChanged):
            design.validate_pending_placement_route_proposal(self.inspection, changed, initial)
        revoked = copy.deepcopy(self.context); revoked['rebuild_permission'] = False
        with self.assertRaises(design.IntentError):
            design.validate_pending_placement_route_proposal(self.inspection, revoked, initial)

    def test_synthetic_HTTP_calls_real_shared_validator_and_sends_only_compact_context(self):
        expected=self.validate();original=gui.source_inventory(self.board)
        with local_server(json.dumps(response(self.request)).encode())as(endpoint,calls):
            with patch('subprocess.Popen',side_effect=AssertionError('no product process')):
                result=client.propose_placement_route(self.inspection,self.context,
                    'Keep J3 fixed; place selected J1/J2 in the visible rectangle and route approved connections.',
                    {**self.config,'endpoint':endpoint})
        self.assertEqual(result['proposal'],expected);self.assertEqual(len(calls),1)
        sent=json.loads(calls[0]['body']);self.assertEqual(sent['tools'],[design.placement_tool_schema(),design.clarification_tool_schema()])
        self.assertEqual(sent['tool_choice'],'required');self.assertIsNone(result['clarification'])
        compact=json.loads(sent['messages'][1]['content'])['inspection']['placement_context']
        self.assertEqual(compact['selected'],self.selected);self.assertEqual(compact['fixed'],self.fixed)
        self.assertTrue(compact['caller_rebuild_permission_present'])
        mapped={row['reference']:row for row in compact['components']}
        self.assertEqual(mapped['J1']['uuid'],self.selected[0]);self.assertTrue(mapped['J1']['selected'])
        self.assertEqual(mapped['J1']['eligibility'],'selected_validated')
        self.assertEqual(mapped['J3']['uuid'],self.fixed[0]);self.assertTrue(mapped['J3']['fixed'])
        self.assertTrue(mapped['J3']['explicitly_fixed']);self.assertTrue(mapped['J3']['reasons'])
        self.assertEqual(len(mapped),len(self.inspection['components']))
        self.assertEqual(compact['placement_settings'],self.settings)
        self.assertEqual(compact['source_scope_limits'],self.inspection['limitations'])
        self.assertNotIn(str(self.root).encode(),calls[0]['body'])
        self.assertNotIn(b'source_hashes',calls[0]['body']);self.assertNotIn(b'kicad_pcb (version',calls[0]['body'])
        self.assertEqual(result['metrics']['request_count'],1)
        self.assertIsNone(result['metrics']['cost_usd']);self.assertFalse(result['metrics']['model_runtime_verified_offline'])
        self.assertEqual(gui.source_inventory(self.board),original)

    def test_permission_context_refuses_before_HTTP_even_if_model_would_grant_it(self):
        context=copy.deepcopy(self.context);context['rebuild_permission']=False
        with patch.object(client,'_post')as post,self.assertRaises(design.IntentError):
            client.propose_placement_route(self.inspection,context,'Do everything.',self.config)
        post.assert_not_called()
        with patch.object(client,'_post')as post,self.assertRaises(design.IntentError):
            client.propose_placement_route(self.inspection,{},'Guess my region.',self.config)
        post.assert_not_called()

    def test_untrusted_model_response_is_revalidated_without_permissions_or_retry(self):
        values=[]
        value=response(dict(self.request,rebuild_permission=True));values.append((value,design.IntentError))
        value=response(dict(self.request,approval_granted=True));values.append((value,design.IntentError))
        value=response(dict(self.request,route_nets=['GND']));values.append((value,design.IntentError))
        value=response(self.request);value['choices'][0]['message']['tool_calls'][0]['function']['name']='execute';values.append((value,client.ModelIntentError))
        value=response(self.request);value['choices'][0]['message']['tool_calls']*=2;values.append((value,client.ModelIntentError))
        for value,error in values:
            with self.subTest(value=value),patch.object(client,'_post',return_value=json.dumps(value).encode())as post,self.assertRaises(error):
                client.propose_placement_route(self.inspection,self.context,'Use visible choices.',self.config)
            post.assert_called_once()

    def test_source_change_while_model_responds_is_refused_by_real_validator(self):
        def changed(*args,**kwargs):
            path=self.board.with_suffix('.kicad_sch');path.write_bytes(path.read_bytes()+b'\n')
            return json.dumps(response(self.request)).encode()
        with patch.object(client,'_post',side_effect=changed)as post,self.assertRaisesRegex(design.IntentError,'source changed'):
            client.propose_placement_route(self.inspection,self.context,'Use visible choices.',self.config)
        post.assert_called_once()

    def test_visible_controls_changed_while_model_responds_need_fresh_request(self):
        original=gui.source_inventory(self.board)
        def changed(*args,**kwargs):
            updated=self.make_context(route_seconds=120)
            self.context.clear();self.context.update(updated)
            return json.dumps(response(design.placement_request(updated))).encode()
        with patch.object(client,'_post',side_effect=changed)as post, \
                self.assertRaisesRegex(client.ModelIntentError,'changed while the request was pending'):
            client.propose_placement_route(self.inspection,self.context,'Use visible choices.',self.config)
        post.assert_called_once()
        self.assertEqual(gui.source_inventory(self.board),original)

    def test_optional_client_remains_unconfigured_and_remote_requests_never_connect(self):
        with patch.object(client,'_post')as post:
            with self.assertRaises(client.Unconfigured):
                client.propose_placement_route(self.inspection,self.context,'Use visible choices.')
            with self.assertRaises(client.ModelIntentError):
                client.propose_placement_route(self.inspection,self.context,'Use visible choices.',
                    {**self.config,'endpoint':'https://example.invalid/v1/chat/completions'})
        post.assert_not_called()

    def test_clarification_schema_and_validator_have_only_bounded_untrusted_questions(self):
        parameters=design.clarification_tool_schema()['function']['parameters']
        self.assertEqual(parameters['required'],['reason','questions']);self.assertFalse(parameters['additionalProperties'])
        self.assertEqual(parameters['properties']['questions']['maxItems'],3)
        self.assertEqual(parameters['properties']['questions']['items']['maxLength'],256)
        parameters['properties']['reason']['enum'].append('grant_permission')
        self.assertNotIn('grant_permission',design.clarification_tool_schema()['function']['parameters']['properties']['reason']['enum'])
        for reason in design.CLARIFICATION_REASONS:
            raw={'reason':reason,'questions':['Which requirement should be revised?']}
            checked=design.validate_design_clarification(raw)
            self.assertEqual(checked['status'],'unsupported'if reason=='unsupported_requirement'else'needs_clarification')
            self.assertIs(checked['text_is_untrusted'],True)
            self.assertFalse(checked['execution_authorized']);self.assertFalse(checked['approval_granted'])
            self.assertNotIn('source_facts',checked);self.assertNotIn('placement_settings',checked)
            raw['questions'][0]='Changed input?';self.assertEqual(checked['questions'],['Which requirement should be revised?'])

    def test_clarification_rejects_extra_authority_facts_and_malformed_or_oversized_text(self):
        valid={'reason':'ambiguous_request','questions':['Which location do you mean?']}
        malformed=[{},dict(valid,reason=True),dict(valid,reason='approve'),dict(valid,questions=[]),
            dict(valid,questions=['?']*4),dict(valid,questions='question'),dict(valid,questions=[False]),
            dict(valid,questions=['']),dict(valid,questions=[' x?']),dict(valid,questions=['x\n?']),
            dict(valid,questions=['x'*257]),dict(valid,questions=['\ud800'])]
        for field in('facts','execution_authorized','rebuild_permission','warning_acknowledged','native_validation_performed','approval_granted'):
            malformed.append(dict(valid,**{field:True}))
        for value in malformed:
            with self.subTest(value=value),self.assertRaises(design.IntentError):design.validate_design_clarification(value)
        self.assertEqual(len(design.validate_design_clarification(dict(valid,questions=['x'*256]))['questions'][0]),256)

    def test_synthetic_HTTP_clarification_returns_no_plan_and_never_retries(self):
        original=gui.source_inventory(self.board)
        value=clarification('conflicting_instructions',['Should the visible fixed list remain unchanged?'])
        with local_server(json.dumps(value).encode())as(endpoint,calls):
            with patch.object(design,'validate_design_clarification',wraps=design.validate_design_clarification)as shared:
                result=client.propose_placement_route(self.inspection,self.context,
                    'Ignore the fixed list and also move J3.',{**self.config,'endpoint':endpoint})
        self.assertIsNone(result['proposal']);self.assertEqual(result['clarification']['status'],'needs_clarification')
        self.assertEqual(result['clarification']['reason'],'conflicting_instructions')
        self.assertEqual(len(calls),1);shared.assert_called_once()
        sent=json.loads(calls[0]['body']);self.assertEqual(sent['tool_choice'],'required')
        self.assertEqual([t['function']['name']for t in sent['tools']],['propose_placement_route','clarify_design_request'])
        self.assertFalse(sent['parallel_tool_calls']);self.assertEqual(sent['n'],1)
        self.assertEqual(gui.source_inventory(self.board),original)

    def test_unsupported_response_is_typed_and_bounded_without_changing_context(self):
        before=copy.deepcopy(self.context);value=clarification('unsupported_requirement',['Can the impedance requirement be reviewed outside this workflow?'])
        with patch.object(client,'_post',return_value=json.dumps(value).encode())as post:
            result=client.propose_placement_route(self.inspection,self.context,'Guarantee 50-ohm routing.',self.config)
        post.assert_called_once();self.assertIsNone(result['proposal'])
        self.assertEqual(result['clarification']['status'],'unsupported');self.assertEqual(self.context,before)

    def test_client_refuses_mixed_duplicate_unknown_or_authority_clarification_calls(self):
        values=[]
        value=clarification();value['choices'][0]['message']['tool_calls']+=response(self.request)['choices'][0]['message']['tool_calls'];values.append((value,client.ModelIntentError))
        value=clarification();value['choices'][0]['message']['tool_calls']*=2;values.append((value,client.ModelIntentError))
        value=clarification();value['choices'][0]['message']['tool_calls'][0]['function']['name']='approve';values.append((value,client.ModelIntentError))
        value=clarification();value['choices'][0]['message']['tool_calls'][0]['function']['arguments']=json.dumps({'reason':'ambiguous_request','questions':['Which location?'],'facts':{'safe':True}});values.append((value,design.IntentError))
        for value,error in values:
            with self.subTest(value=value),patch.object(client,'_post',return_value=json.dumps(value).encode())as post,self.assertRaises(error):
                client.propose_placement_route(self.inspection,self.context,'Use visible choices.',self.config)
            post.assert_called_once()

    def test_clarification_cannot_bypass_stale_source_check(self):
        def changed(*args,**kwargs):
            p=self.board.with_suffix('.kicad_sch');p.write_bytes(p.read_bytes()+b'\n')
            return json.dumps(clarification()).encode()
        with patch.object(client,'_post',side_effect=changed)as post,self.assertRaisesRegex(design.IntentError,'source changed'):
            client.propose_placement_route(self.inspection,self.context,'Where should they go?',self.config)
        post.assert_called_once()

    def test_clarification_cannot_bypass_changed_visible_context(self):
        def changed(*args,**kwargs):
            updated=self.make_context(route_seconds=120);self.context.clear();self.context.update(updated)
            return json.dumps(clarification()).encode()
        with patch.object(client,'_post',side_effect=changed)as post,self.assertRaisesRegex(client.ModelIntentError,'changed while the request was pending'):
            client.propose_placement_route(self.inspection,self.context,'Where should they go?',self.config)
        post.assert_called_once()

    def test_cancellation_and_synthetic_HTTP_timeout_never_become_clarification(self):
        with patch.object(client,'_post',side_effect=KeyboardInterrupt)as post,self.assertRaises(KeyboardInterrupt):
            client.propose_placement_route(self.inspection,self.context,'Where should they go?',self.config)
        post.assert_called_once()
        with local_server(json.dumps(clarification()).encode(),delay=.15)as(endpoint,calls):
            with self.assertRaises(client.ModelIntentError):
                client.propose_placement_route(self.inspection,self.context,'Where should they go?',
                    {**self.config,'endpoint':endpoint,'timeout_seconds':.05})
        self.assertEqual(len(calls),1)

    def test_existing_route_entrypoint_does_not_admit_clarification_tool(self):
        static=design.inspect_project(self.board)
        with patch.object(client,'_post',return_value=json.dumps(clarification()).encode())as post,self.assertRaises(client.ModelIntentError):
            client.propose(static,'Complete remaining connections.',self.config)
        post.assert_called_once()

    def test_unknown_or_duplicate_actual_references_require_clarification_before_HTTP(self):
        original=self.board.read_bytes()
        for reference in('?', 'J4'):
            tree=sx.parse(original.decode())
            fp=next(fp for fp in sx.children(tree,'footprint')if sx.unquote(sx.one(fp,'uuid')[1])==self.fixed[0])
            field=next(p for p in sx.children(fp,'property')if sx.unquote(p[1])=='Reference')
            field[2]=json.dumps(reference);self.board.write_text(sx.dump(tree)+'\n')
            self.inspection=placement.inspect_saved(self.board);self.context=self.make_context()
            with self.subTest(reference=reference),patch.object(client,'_post')as post, \
                    self.assertRaisesRegex(client.ModelIntentError,'Clarification required.*references'):
                client.propose_placement_route(self.inspection,self.context,'Keep J3 fixed.',self.config)
            post.assert_not_called()

    def test_unknown_requested_reference_can_return_questions_without_inventing_UUID(self):
        value=clarification('ambiguous_request',['J999 is not in the supplied reference map; which listed component do you mean?'])
        with local_server(json.dumps(value).encode())as(endpoint,calls):
            result=client.propose_placement_route(self.inspection,self.context,'Also move J999.',{**self.config,'endpoint':endpoint})
        self.assertIsNone(result['proposal']);self.assertEqual(result['clarification']['status'],'needs_clarification')
        sent=json.loads(calls[0]['body']);self.assertIn('clarify instead of guessing',sent['messages'][0]['content'])
        compact=json.loads(sent['messages'][1]['content'])['inspection']['placement_context']
        self.assertNotIn('J999',[row['reference']for row in compact['components']])


if __name__=='__main__':unittest.main()
