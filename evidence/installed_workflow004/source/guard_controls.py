"""Regression for late diagnostic publication cancellation; no Native."""
import ast,unittest
from pathlib import Path
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parent
child=ast.parse((ROOT/'installed-gui-workflow-diagnostic-004.py').read_bytes())
parent=ast.parse((ROOT/'run-installed-gui-workflow-diagnostic-004.py').read_bytes())
class Guards(unittest.TestCase):
 def test_actual_exception_handler_clears_late_delivery(self):
  handler=next(n for n in child.body if isinstance(n,ast.Try)).handlers[0]
  for error in (KeyboardInterrupt(),ValueError('late failure')):
   node=ast.Try(body=[ast.Raise(exc=ast.Name(id='error',ctx=ast.Load()))],handlers=[handler],orelse=[],finalbody=[])
   report=dict(workflow_delivered=True,status='completed');ns=dict(report=report,error=error)
   exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'actual-diagnostic-handler','exec'),ns)
   self.assertIs(report['workflow_delivered'],False)
 def test_actual_child_exit_requires_completed(self):
  expression=child.body[-1].exc.args[0];code=compile(ast.fix_missing_locations(ast.Expression(body=expression)),'actual-child-exit','eval')
  for status,expected in (('completed',0),('cancelled',130),('failed',2)):
   self.assertEqual(eval(code,dict(report=dict(workflow_delivered=True,status=status))),expected)
 def test_actual_parent_refuses_noncompleted_or_unclean_delivery(self):
  expression=next(n.value for n in parent.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='passed' for t in n.targets));code=compile(ast.fix_missing_locations(ast.Expression(body=expression)),'actual-parent-predicate','eval')
  for status,delivered,cleanup,expected in (('completed',True,True,True),('cancelled',True,True,False),('failed',True,True,False),('completed',1,True,False),('completed',True,False,False)):
   process=dict(status='success',exit_code=0,cleanup_complete=cleanup,log_truncated=False);data=dict(status=status,workflow_delivered=delivered)
   self.assertEqual(eval(code,dict(data=data,process=process,pin='same',driver=None,p=NS(sha=lambda _:'same'))),expected)
if __name__=='__main__':unittest.main()
