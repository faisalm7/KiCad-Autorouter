"""Read-only native class-parent observation via the existing same-load context.

Diagnostic only. GetName's comma encoding comes from pinned KiCad source;
closed literal class names make it unambiguous here, not for general KiCad.
No wildcard evaluator, setters, ownership changes, or production admission.
"""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter.floor_context import collect,inventory

FIELDS={
 'width_nm':('GetTrackWidth','GetTrackWidthParent','HasTrackWidth'),
 'clearance_nm':('GetClearance','GetClearanceParent','HasClearance'),
 'via_diameter_nm':('GetViaDiameter','GetViaDiameterParent','HasViaDiameter'),
 'via_drill_nm':('GetViaDrill','GetViaDrillParent','HasViaDrill'),
}
PRIMARY='https://raw.githubusercontent.com/KiCad/kicad-source-mirror/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/common/netclass.cpp'


def text(value):
 value=str(value)
 if not value or len(value.encode('utf8'))>4096 or '\x00' in value:raise ValueError('bounded nonempty native string required')
 return value


def namespace(project):
 classes=project['net_settings']['classes']
 if not isinstance(classes,list) or not 1<=len(classes)<=16:raise ValueError('bounded source class inventory required')
 names=[x['name'] for x in classes]
 if (any(not isinstance(x,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}',x) for x in names)
     or len(set(x.casefold() for x in names))!=len(names) or 'Default' not in names
     or any(x.casefold() in {'default','kicad_default'} and x!='Default' for x in names)):
  raise ValueError('closed unambiguous source class namespace required')
 return names


def decode(name,names):
 pieces=text(name).split(',')
 if not 1<=len(pieces)<=16 or len(set(pieces))!=len(pieces) or any(x not in names for x in pieces):
  raise ValueError('native encoded constituents outside closed source namespace')
 return pieces


def observer(names):
 def observe(board,pcbnew):
  rows=[];owners=[];failures=[]
  for name,net in board.GetNetsByName().items():
   if not str(name) or net.GetNetCode()<=0:continue
   if len(rows)>=10000:raise ValueError('native net cap')
   row={'name':text(name),'netcode':int(net.GetNetCode())}
   try:
    cls=net.GetNetClassSlow();owners.extend([net,cls])
    encoded=text(cls.GetName());parts=decode(encoded,names)
    row.update(effective_class_name=encoded,decoded_constituents=parts,
      effective_priority=int(cls.GetPriority()),tuning_profile=str(cls.GetTuningProfile()),
      effective_ownership_readonly=getattr(cls,'thisown',None),dimensions_nm={},parameter_parents={})
    for key,(getter,parent_getter,has_getter) in FIELDS.items():
     value=getattr(cls,getter)()
     if type(value) is not int or value<=0:raise ValueError('nonpositive native dimension')
     parent=getattr(cls,parent_getter)();owners.append(parent)
     if parent is None:raise ValueError('null native dimension parent')
     parent_name=text(parent.GetName())
     if parent_name not in names:raise ValueError('unknown or composite parameter parent')
     specified=getattr(parent,has_getter)()
     if type(specified) not in (bool,int) or specified not in (0,1):raise ValueError('native specified flag type')
     row['dimensions_nm'][key]=value
     row['parameter_parents'][key]={'name':parent_name,'value_nm':getattr(parent,getter)(),
       'specified':bool(specified),'specified_native_type':type(specified).__name__,
       'priority':int(parent.GetPriority()),'ownership_readonly':getattr(parent,'thisown',None)}
    row['proposed_structure_matches']=len(parts)==1 or len(parts)==2 and parts[-1]=='Default' and parts[0]!='Default'
   except Exception as exc:
    row['read_error']=type(exc).__name__+': '+str(exc);failures.append(row['name'])
   rows.append(row)
  if not rows:raise ValueError('empty native net inventory')
  return {'schema':1,'encoding_primary':PRIMARY,'encoding_scope':'GetName closed literal namespace only; no wildcard evaluation',
    'source_class_names':names,'nets':sorted(rows,key=lambda x:x['name']),
    'closed_namespace_decoding_complete':not failures,'failed_net_names':failures,
    'constituent_vector_api_called':False,'production_support_qualified':False,'routing_accepted':False}
 return observe


def main():
 board,context,dsn,observation=map(Path,sys.argv[1:5])
 before=inventory(board.parent)
 names=namespace(json.loads(board.with_suffix('.kicad_pro').read_text()))
 collect('export',str(board),str(context),str(dsn),observation_output=str(observation),observer=observer(names))
 if inventory(board.parent)!=before:raise ValueError('source namespace context changed')
if __name__=='__main__':main()
