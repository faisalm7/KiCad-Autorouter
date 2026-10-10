import json,sys,pcbnew
board=pcbnew.LoadBoard(sys.argv[1])
items=[f for f in board.GetFootprints() if f.m_Uuid.AsString()==sys.argv[2]]
assert len(items)==1
p=items[0].GetCenter()
with open(sys.argv[3],'x') as out:json.dump({'x_nm':int(p.x),'y_nm':int(p.y),'uuid':sys.argv[2],'version':pcbnew.GetBuildVersion()},out)
