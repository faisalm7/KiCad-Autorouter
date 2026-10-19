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
