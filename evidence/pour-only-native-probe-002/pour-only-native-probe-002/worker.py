"""Owned native observation, no writes to boards or production admission."""
from pathlib import Path
import hashlib,json,sys
import pcbnew
source=Path(sys.argv[1]);output=Path(sys.argv[2]);before={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (source,source.with_suffix('.kicad_pro'))}
board=pcbnew.LoadBoard(str(source));zones=list(board.Zones());assert len(zones)<=16
flags={'tracks':'GetDoNotAllowTracks','vias':'GetDoNotAllowVias','pads':'GetDoNotAllowPads','copperpour':'GetDoNotAllowZoneFills','footprints':'GetDoNotAllowFootprints'}
def contours(poly):
 result=[];total=0
 for i in range(poly.OutlineCount()):
  row=poly.COutline(i);n=row.PointCount();total+=n;assert total<=10000
  result.append({'points_nm':[[int(row.CPoint(j).x),int(row.CPoint(j).y)] for j in range(n)],'closed':bool(row.IsClosed()),'holes':int(poly.HoleCount(i))})
 return result
areas=[];rows=[];passed=True
for area in zones:
 if not area.GetIsRuleArea():continue
 disallow={key:getattr(area,name)() for key,name in flags.items()};assert all(type(v) is bool for v in disallow.values())
 assert disallow=={'tracks':False,'vias':False,'pads':False,'copperpour':True,'footprints':False}
 outline=area.Outline();assert outline.OutlineCount()==1 and outline.ArcCount()==0 and outline.HoleCount(0)==0
 uid=str(area.m_Uuid.AsString());areas.append({'uuid':uid,'disallow':disallow,'outline':contours(outline)})
 for zone in zones:
  if zone.GetIsRuleArea():continue
  for layer in (pcbnew.F_Cu,pcbnew.B_Cu):
   if not zone.IsOnLayer(layer):continue
   filled=zone.GetFilledPolysList(layer);copy=pcbnew.SHAPE_POLY_SET(filled)
   stored_count=int(copy.OutlineCount());copy.BooleanIntersection(outline)
   overlap=contours(copy);applicable=bool(area.IsOnLayer(layer))
   row={'area_uuid':uid,'zone_uuid':str(zone.m_Uuid.AsString()),'layer':board.GetLayerName(layer),'applicable':applicable,'stored_fill_contours':stored_count,'intersection':overlap,'intersection_contours':len(overlap)}
   rows.append(row)
   if applicable and overlap:passed=False
assert areas
assert before=={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (source,source.with_suffix('.kicad_pro'))}
result={'schema':1,'kind':'native-saved-pour-exclusion-probe','native_version':pcbnew.GetBuildVersion(),'source':str(source),'board_sha256':before[str(source)],'project_sha256':before[str(source.with_suffix('.kicad_pro'))],'board_saved':False,'passed':passed,'areas':areas,'observations':rows,'production_admission':False}
output.write_text(json.dumps(result,indent=2)+'\n');raise SystemExit(0 if passed else 2)
