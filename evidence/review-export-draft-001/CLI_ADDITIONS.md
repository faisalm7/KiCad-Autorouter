# Additive CLI integration snippets for ROOT

Keep ROOT's current `improve` flags intact. Add these parser definitions beside review-choice:

```python
export_cmd=sub.add_parser('review-export',help='Fresh native validation into a new separate project after accept intent; no live apply')
export_cmd.add_argument('choice');export_cmd.add_argument('--output',required=True)
export_cmd.add_argument('--seconds',type=float,default=120)
export_check=sub.add_parser('review-export-check',help='Check stored export/source/report consistency; does not run fresh DRC')
export_check.add_argument('receipt')
```

Add these branches before the existing generic route/improve dispatch:

```python
if a.command=='review-export':
    from .review_export import export
    try:
        result=export(a.choice,a.output,a.seconds)
        print(json.dumps({key:result.get(key) for key in ('status','export_accepted','project_file','candidate_sha256','native_report_sha256','wall_seconds','total_cpu_seconds')},indent=2))
        return 0 if result['export_accepted'] else 2
    except Exception as exc:
        print(json.dumps({'status':'rejected','reason':str(exc)}));return 2
if a.command=='review-export-check':
    from .review_export import check_export
    try:
        print(json.dumps(check_export(a.receipt),indent=2));return 0
    except Exception as exc:
        print(json.dumps({'current':False,'reason':str(exc)}));return 2
```

The new module/test are additive. No handoff replacement or full CLI replacement is supplied. `source.patch` creates only those two files. ROOT owns combined CLI integration and native qualification.
