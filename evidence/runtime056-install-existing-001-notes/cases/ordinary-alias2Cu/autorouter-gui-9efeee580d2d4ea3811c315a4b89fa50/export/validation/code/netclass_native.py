"""Scalar native netclass observation only; no decoding or routing admission.

Usable by KiCad's pinned Python3.9 worker without importing pcbnew here. Never
call constituent vectors, Contains or setters, or read/change proxy ownership.
"""
FIELDS=(
    ('width_nm','GetTrackWidth','GetTrackWidthParent','HasTrackWidth'),
    ('clearance_nm','GetClearance','GetClearanceParent','HasClearance'),
    ('via_diameter_nm','GetViaDiameter','GetViaDiameterParent','HasViaDiameter'),
    ('via_drill_nm','GetViaDrill','GetViaDrillParent','HasViaDrill'),
)
MAX_NAME_BYTES=4096
MAX_NATIVE_INTEGER=2147483647
SOURCE_ALL_LAYER_KEY='source_all_copper_layers'
SOURCE_ALL_LAYER_POLICY='source-all-two-copper-identity-v1'


def _layer_display(value):
    if type(value) is not str:
        raise ValueError('bounded source-all display name required')
    try:size=len(value.encode('utf8'))
    except UnicodeError:raise ValueError('invalid source-all display encoding') from None
    if (not 0<size<=256 or value!=value.strip()
            or any(ord(char)<32 or ord(char)==127 for char in value)):
        raise ValueError('bounded source-all display name required')
    return value


def _layer_names(rows):
    """Display names cannot alias any other physical or declared layer."""
    import re
    from autorouter.layer_policy import NONCOPPER
    reserved={name.casefold() for name in (*NONCOPPER.values(),
        'User.5','User.6','User.7','User.8','User.9','pcb','signal','power','mixed','jumper')}
    names=set()
    for canonical,display in rows:
        display=_layer_display(display);folded=display.casefold()
        if (folded in names or (folded==canonical.casefold() and display!=canonical)
                or (folded!=canonical.casefold()
                and (folded in reserved or re.fullmatch(r'(?:f|b|in[0-9]+)\.cu',folded)))):
            raise ValueError('colliding source-all layer display name')
        names.add(folded)


def source_all_two_copper_layers(tree):
    """Read original physical identities and optional display atoms, no edits.

    This opt-in source-all table is separate from the unchanged explicit layer
    mask and hierarchy gates. The existing literal table/stackup check still
    decides physical IDs/order/types; only a private copper-row copy omits the
    display atoms for that check. No board or DSN names are rewritten.
    """
    import re
    from autorouter import sexpr as sx
    from autorouter.layer_policy import NONCOPPER,_two_copper_table
    if (type(tree) is not list or not tree or tree[0]!='kicad_pcb'
            or sx.one(tree,'version') not in (['version','20241229'],['version','20260206'])):
        raise ValueError('qualified source-all two-copper source required')
    table=sx.one(tree,'layers')
    if type(table) is not list:
        raise ValueError('source-all layer table required')
    noncopper={**NONCOPPER,'47':'User.5','49':'User.6','51':'User.7','53':'User.8','55':'User.9'}
    if not 2<=len(table)-1<=2+len(noncopper):
        raise ValueError('bounded source-all physical layer table required')
    copy=['layers'];identities=[];displays=[];aliased=False
    for row in table[1:]:
        if (type(row) is not list or len(row) not in (3,4)
                or any(type(atom) is not str for atom in row)):
            raise ValueError('malformed source-all layer row')
        canonical=sx.unquote(row[1]);display=canonical
        if len(row)==4:
            if len(row[3])>514 or re.fullmatch(r'"(?:[^"\\]|\\["\\])*"',row[3]) is None:
                raise ValueError('bounded quoted source-all display atom required')
            display=_layer_display(sx.unquote(row[3]))
        displays.append((canonical,display))
        copper=row[2] in {'signal','power','mixed','jumper'} or canonical.endswith('.Cu')
        if copper:
            identities.append(dict(id=int(row[0]) if row[0].isascii() and row[0].isdigit() else -1,
                canonical=canonical,display_name=display,index=len(identities),type='signal'))
            aliased=aliased or len(row)==4
            copy.append(row[:3])
        else:copy.append(row[:])
    _layer_names(displays)
    probe=['kicad_pcb',copy]
    setup=sx.one(tree,'setup')
    if setup is not None:probe.append(setup)
    _two_copper_table(probe,noncopper=noncopper)
    return identities,aliased


def validate_source_all_layers(value):
    """Validate the closed scalar observation; process/source binding is external."""
    if (type(value) is not dict or set(value)!={'schema','policy','copper_count','layers'}
            or type(value['schema']) is not int or value['schema']!=1
            or value['policy']!=SOURCE_ALL_LAYER_POLICY
            or type(value['copper_count']) is not int or value['copper_count']!=2
            or type(value['layers']) is not list or len(value['layers'])!=2):
        raise ValueError('source-all two-copper Native identity schema differs')
    result=[]
    for index,(row,(code,name)) in enumerate(zip(value['layers'],((0,'F.Cu'),(2,'B.Cu')))):
        expected=dict(id=code,canonical=name,standard_name=name,index=index,type='signal',
                      enabled=True,canonical_lookup_id=code,display_lookup_id=code)
        if (type(row) is not dict or set(row)!=set(expected)|{'display_name'}
                or any(type(row[key]) is not type(wanted) or row[key]!=wanted for key,wanted in expected.items())):
            raise ValueError('source-all Native physical identity differs')
        result.append({**expected,'display_name':_layer_display(row['display_name'])})
    _layer_names([(row['canonical'],row['display_name']) for row in result])
    return result


def _has_source_all_alias(tree):
    from autorouter import sexpr as sx
    table=sx.one(tree,'layers',[])
    return any(type(row) is list and len(row)==4 and type(row[1]) is str and type(row[2]) is str
        and (sx.unquote(row[1]).endswith('.Cu') or row[2] in {'signal','power','mixed','jumper'}) for row in table[1:])


def check_source_all_layers(native, tree):
    """Source alias atoms require their own same-load observation, even if deleted."""
    marked=SOURCE_ALL_LAYER_KEY in native
    aliased=_has_source_all_alias(tree)
    if not marked and not aliased:return None  # Historical canonical2Cu/4Cu maps unchanged.
    if (native.get('native_version')!='10.0.7' or 'copper_layers' in native
            or native.get('board_saved') is not False):
        raise ValueError('source-all layer observation outside normal Native7 two-copper scope')
    source,aliased=source_all_two_copper_layers(tree)
    if not aliased or not marked:
        raise ValueError('source-all alias needs its Native identity observation')
    observed=validate_source_all_layers(native[SOURCE_ALL_LAYER_KEY])
    expected=[{key:row[key] for key in ('id','canonical','display_name','index','type')} for row in observed]
    if source!=expected:
        raise ValueError('source-all source/Native layer identity differs')
    return observed


def observe_source_all_layers(board, raw, pcbnew):
    """Read scalar layer identities on the SAME board used for class/DSN export."""
    from autorouter import sexpr as sx
    if type(raw) is not bytes or not 0<len(raw)<=sx.MAX_BYTES:
        raise ValueError('bounded source-all board bytes required')
    tree=sx.parse(raw.decode('utf8'))
    if not _has_source_all_alias(tree):return None
    source,aliased=source_all_two_copper_layers(tree)
    if not aliased:return None  # No new map field or Native getters for canonical sources.
    if pcbnew.GetBuildVersion()!='10.0.7':
        raise ValueError('source-all layer observation needs Native10.0.7')
    rows=[]
    for row,layer in zip(source,(pcbnew.F_Cu,pcbnew.B_Cu)):
        display=_layer_display(board.GetLayerName(layer))
        kind=board.GetLayerType(layer)
        if type(kind) is not int or kind!=pcbnew.LT_SIGNAL:
            raise ValueError('source-all Native signal type required')
        rows.append(dict(id=layer,canonical=row['canonical'],standard_name=str(pcbnew.LayerName(layer)),
            display_name=display,index=row['index'],type='signal',enabled=board.IsLayerEnabled(layer),
            canonical_lookup_id=board.GetLayerID(row['canonical']),display_lookup_id=board.GetLayerID(display)))
    value=dict(schema=1,policy=SOURCE_ALL_LAYER_POLICY,copper_count=board.GetCopperLayerCount(),layers=rows)
    observed=check_source_all_layers(dict(native_version='10.0.7',board_saved=False,
        **{SOURCE_ALL_LAYER_KEY:value}),tree)
    if observed!=validate_source_all_layers(value):raise ValueError('source-all observation differs')
    return value

def validate_floors(value, project=None):
    """Copy exact observed floors and check any explicitly present source floors.

    Absent source fields remain absent. This validates scalar observations only;
    the caller must bind their Native process, source bytes and original rules.
    """
    from autorouter.floor_context import FLOORS
    if type(value) is not dict:
        raise ValueError('complete native board floor object required')
    result=value.copy()
    if (set(result)!=set(FLOORS)
            or any(type(item) is not int or not 0<=item<=MAX_NATIVE_INTEGER for item in result.values())):
        raise ValueError('complete bounded integer native board floors required')
    if project is not None:
        if type(project) is not dict:
            raise ValueError('original project object required for floor comparison')
        rules=project
        for key in ('board','design_settings','rules'):
            if key not in rules:
                return result
            rules=rules[key]
            if type(rules) is not dict:
                raise ValueError('malformed original floor object: '+key)
        from autorouter.netclass import _millimetres_to_nm
        for key in FLOORS:
            if key in rules and _millimetres_to_nm(rules[key],allow_zero=True)!=result[key]:
                raise ValueError('explicit source/native board floor differs: '+key)
    return result

def observe_floors(board):
    """Read hard floors from the same loaded board, including implicit values."""
    from autorouter.floor_context import FLOORS
    settings=board.GetDesignSettings()
    return validate_floors({key:getattr(settings,attribute) for key,attribute in FLOORS.items()})

def _name(value):
    if (type(value) is not str or not value or len(value.encode('utf8'))>MAX_NAME_BYTES
            or any(ord(ch)<32 or ord(ch)==127 for ch in value)):
        raise ValueError('bounded nonempty native class name required')
    return value

def _dimension(value):
    if type(value) is not int or not 0<value<=MAX_NATIVE_INTEGER:
        raise ValueError('positive bounded integer native dimension required')
    return value

def _priority(value):
    if type(value) is not int or not -1<=value<=MAX_NATIVE_INTEGER:
        raise ValueError('bounded integer native parent priority required')
    return value

def _specified(value):
    # Pinned HasViaDrill returns int; the other Has* getters return bool.
    if type(value) not in (bool,int) or value not in (0,1):
        raise ValueError('native specified flag must be bool or integer0/1')
    return bool(value)

def observe_class(cls):
    """Return exact encoded class name, four dimensions and scalar parent data.

    All parent proxies remain strongly referenced until every scalar record is
    complete. No constituent inference, source policy or ownership mutation.
    Caller binds this observation to its live board/source/process and performs
    source qualification; this record alone never establishes routing support.
    """
    if cls is None:raise ValueError('null native class')
    try:
        parents=[getattr(cls,parent_getter)() for _,_,parent_getter,_ in FIELDS]
        if any(parent is None for parent in parents):raise ValueError('null native parameter parent')
        result={'class':_name(cls.GetName()),'parameter_parents':{}}
        for (key,getter,_,has_getter),parent in zip(FIELDS,parents):
            result[key]=_dimension(getattr(cls,getter)())
            result['parameter_parents'][key]={
                'name':_name(parent.GetName()),
                'value_nm':_dimension(getattr(parent,getter)()),
                'specified':_specified(getattr(parent,has_getter)()),
                'priority':_priority(parent.GetPriority()),
            }
        return result
    except (AttributeError,TypeError,UnicodeError) as exc:
        raise ValueError('malformed native class scalar observation') from exc
