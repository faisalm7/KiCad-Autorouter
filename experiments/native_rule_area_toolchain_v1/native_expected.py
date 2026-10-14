from autorouter import pipeline as p
def native_expected(case,native,expected,ignored):
    for key in ('opens','blocking','warnings','exclusions'):
        if type(native.get(key)) is not int or native[key]<0:return False,[]
    if native['opens'] or native['warnings'] or native['exclusions'] or native.get('ignored_checks')!=ignored:
        return False,[]
    findings=native.get('findings')
    if not isinstance(findings,list):return False,[]
    targets=set(expected['prohibited_target_uuids'])
    if not targets:return p.native_accepted(native) and not findings,[]
    hits=[];seen=set()
    for row in findings:
        if not isinstance(row,dict) or row.get('type')!='items_not_allowed' or row.get('severity')!='error' or row.get('excluded',False):return False,[]
        items=row.get('items')
        if not isinstance(items,list) or any(not isinstance(x,dict) for x in items):return False,[]
        intersect=targets & {x.get('uuid') for x in items}
        if not intersect:return False,[]
        seen.update(intersect);hits.append(row)
    return seen==targets and bool(hits) and not p.native_accepted(native),hits
