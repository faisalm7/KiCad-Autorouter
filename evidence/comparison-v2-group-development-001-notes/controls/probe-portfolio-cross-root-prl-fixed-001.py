"""Software composition probe with actual owned Mac PRL flags; no Native board acceptance."""
from pathlib import Path
import sys,os,stat,json
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from tests.test_portfolio_installed_context import ComparisonPortfolioAPITests as Fixture
from scripts import experiment_portfolio as m
from autorouter import local_settings as local,handoff as h
case=Fixture('test_live_contexts_fixed_order_reserved_paths_no_cli_and_winning_delivery_authority');case.setUp()
events={};fault={'changed':False};paths=[]
original=case.route

def route(*args,**kw):
 data=original(*args,**kw);root=args[1];folder=root/'probe-input';folder.mkdir();board=folder/'probe.kicad_pcb';board.write_bytes(b'(kicad_pcb)\n');prl=board.with_suffix('.kicad_prl');prl.write_bytes(b'{}\n');paths.append(prl)
 owner={};h.capture_destination(owner,root);before=m.p.tree_hash(folder)
 with local.preserve(prl,root,owner) as event:pass
 binding=dict(input=str(board),saved=False,before=before,local_settings_policy=local.JOB_POLICY)
 process=dict(argv=[str(m.c.CLI),'pcb','drc',str(board)],cleanup_complete=True,local_settings_policy=local.JOB_POLICY,local_settings_protection=event)
 process.update(name='probe-drc',cwd=str(root))
 data['steps'].append(process);m.p.save_json(root/'probe-drc-binding.json',binding);m.p.save_json(root/'probe-drc-process.json',process);m.p.save_json(root/'result.json',data)
 events[root]=(binding,process);return data

def metadata(root,*args):
 # Represents the later-root material/code read inside the shared helper,
 # then uses the real existing per-root event guard, with no byte changes.
 if case.summary_published and root==case.calls[1][3] and not fault['changed']:
  os.chflags(paths[0],stat.UF_IMMUTABLE,follow_symlinks=False);fault['changed']=True
 local.check_event(root,*events[root])
try:
 with patch.object(m.p,'route',side_effect=route),patch.object(m.p,'check_experimental_local_settings',side_effect=metadata),patch.object(m.f,'process_check',side_effect=lambda root,*args,**kwargs:events[root][1]):
  result=case.run_portfolio()
 record=dict(kind='software-fixed-cross-root-final-PRL-order-probe',actual_Native=False,actual_GUI=False,fault_observed=fault['changed'],first_owned_PRL_flags=paths[0].stat().st_flags,returned_status=result['status'],reason=result.get('reason'),returned_comparison_eligible=result['comparison_eligible'],unchanged_bytes=paths[0].read_bytes()==b'{}\n',scope='Authored trial/DRC rows and a process-reader seam, real preserve/check_event/group and owned Mac flags. Not a complete Native routing acceptance claim.')
 print(json.dumps(record));assert fault['changed'] and result['comparison_eligible'] is False and result['selected'] is None and paths[0].stat().st_flags==stat.UF_IMMUTABLE
finally:
 for path in paths:os.chflags(path,0,follow_symlinks=False)
 case.doCleanups()
