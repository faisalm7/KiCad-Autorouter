"""Pure prospective checks. No production admission or source rewriting."""
import copy
from decimal import Decimal
from autorouter import sexpr as sx,netclass as nc,adapter

def inactive_default(project,context,dsn_text):
    nc.reject_tuning_intent(project)
    settings=project['net_settings'];classes=settings['classes']
    if (len(classes)!=2 or {x['name'] for x in classes}!={'Default','5mil'}
            or settings.get('netclass_assignments') not in (None,{}) or settings.get('netclass_patterns') not in (None,[])):
        raise ValueError('exact unused 5mil metadata required')
    if any(row['class']!='Default' for row in context['nets']):raise ValueError('nondefault native class is active')
    # This read-only audit projection never becomes a saved or native input.
    # Native effective membership must prove the omitted definition is unused.
    view=copy.deepcopy(project);view['net_settings']['classes']=[x for x in view['net_settings']['classes'] if x['name']=='Default']
    native={'schema':1,'native_version':context['native_version'],'units':context['units'],'nets':context['nets']}
    result=nc.audit_mapping(adapter._parse_dsn(dsn_text),native,view)
    result.update(scope='read-only inactive-definition proof projection; exact original project retained',production_support_qualified=False)
    return result

def layer_text(tree,diagnostic,dsn_text):
    observed=diagnostic['observation_before_export']
    if observed!=diagnostic['observation_after_export'] or diagnostic['same_loaded_board'] is not True:raise ValueError('same-load observation differs')
    wanted=[{'name':sx.unquote(n[1]),'canonical':sx.unquote(n[1]),'type':n[2]} for n in sx.one(tree,'layers')[1:] if n[1] in ('"F.Cu"','"B.Cu"')]
    if observed['layers']!=wanted:raise ValueError('native layer intent differs')
    structure=sx.one(adapter._parse_dsn(dsn_text),'structure');exported=sx.children(structure,'layer')
    if [(sx.unquote(n[1]),sx.one(n,'type')[1]) for n in exported]!=[(n['name'],n['type']) for n in wanted]:raise ValueError('DSN layer type/order differs')
    texts=[]
    for node in sx.children(tree,'gr_text'):
        layer=sx.one(node,'layer')
        if layer[1] not in ('"F.Cu"','"B.Cu"'):continue
        at=sx.one(node,'at');texts.append({'uuid':sx.unquote(sx.one(node,'uuid')[1]),'text':sx.unquote(node[1]),'layer':sx.unquote(layer[1]),
            'knockout':layer[2:]==['knockout'],'position_nm':[int(Decimal(x)*1000000) for x in at[1:3]]})
    native=[{key:row[key] for key in ('uuid','text','layer','knockout','position_nm')} for row in observed['copper_text']]
    if sorted(texts,key=lambda x:x['uuid'])!=native or len({r['uuid'] for r in native})!=len(native):raise ValueError('native copper text differs')
    if any(not r['shape_outlines'] for r in observed['copper_text']):raise ValueError('missing native copper text shape')
    return {'passed':True,'layers':wanted,'text_uuids':[r['uuid'] for r in native],'production_support_qualified':False}

def crossing(native,negative,text_uuid,track_uuid):
    pairs=[r for r in native['findings'] if {text_uuid,track_uuid}<={i['uuid'] for i in r.get('items',[])}
           and r['severity']=='error' and r['type'] in ('clearance','shorting_items')]
    if native['opens'] or native['exclusions']:return False
    if negative:return bool(pairs) and native['blocking']==len(pairs)
    return native['blocking']==0 and not pairs
