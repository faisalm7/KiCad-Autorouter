"""Recheck same tiny controls after lead's stock-only compatibility edit."""
from pathlib import Path
root=Path(__file__).resolve().parent
body=(root/'postfix_continuation.py').read_text().replace('postfix-run-002','postfix-run-003').replace('postfix-continuation-results.json','postfix-final-source-results.json')
exec(compile(body,str(root/'postfix_continuation.py'),'exec'),{'__file__':str(root/'postfix_continuation.py'),'__name__':'__main__'})
