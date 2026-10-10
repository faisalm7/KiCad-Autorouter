"""Fixed owned diagnostic board: no modification of the original project."""
import copy,uuid
from decimal import Decimal
from autorouter import sexpr as sx,pipeline as p
import recipes as g

VARIANTS=('front0','back90')
CASES=('positive','false_hull','foreign_intrusion')
ORDER=tuple((v,c) for v in VARIANTS for c in CASES)
NAMESPACE=uuid.UUID('f4c6ac21-e515-40a8-b549-d3a65c5ed056')
def uid(kind,identity,variant):return str(uuid.uuid5(NAMESPACE,variant+':'+kind+':'+identity))
def q(text):return '"'+text+'"'
def mm(value):return str(Decimal(value)/1000000)
def node_xy(key,point):return [key,*map(mm,point)]
def poly_ring(points):
    rows=[tuple(x) for x in points]
    if len(rows)>1 and rows[0]==rows[-1]:rows.pop()
    if len(rows)<3 or len(set(rows))!=len(rows):raise ValueError('ambiguous polygon ring')
    reversed_rows=list(reversed(rows))
    return min([tuple(rows[i:]+rows[:i]) for i in range(len(rows))]+
               [tuple(reversed_rows[i:]+reversed_rows[:i]) for i in range(len(rows))])

def prepare(original,case,variant):
    scene=g.scene(case,variant);layer=scene['copper_layer'];back=variant=='back90';angle='90' if back else '0'
    source_custom=[pad for fp in sx.children(original,'footprint') for pad in sx.children(fp,'pad') if pad[3]=='custom']
    if len(source_custom)!=2:raise ValueError('source custom census changed')
    by_number={sx.unquote(pad[1]):pad for pad in source_custom}
    for number,shape in [('1',g.CONVEX),('2',g.CONCAVE)]:
        pad=by_number[number];points=sx.one(sx.one(sx.one(pad,'primitives'),'gr_poly'),'pts')[1:]
        actual=tuple(tuple(int(Decimal(v)*1000000) for v in pt[1:]) for pt in points)
        if actual!=shape or sx.one(pad,'size')!=['size','0.3','0.3']:raise ValueError('original primitive/anchor differs')
    board=['kicad_pcb',*[copy.deepcopy(sx.one(original,k)) for k in ('version','generator','generator_version','general','paper','layers','setup')]]
    for row in scene['pads']:
        identity=row['id'];fpuid=uid('footprint',identity,variant);paduid=uid('pad',identity,variant)
        row.update(uuid=paduid,footprint_uuid=fpuid,reference=identity,number='1')
        fp=['footprint',q('Owned_'+identity),['layer',q(layer)],['uuid',q(fpuid)],['at',*map(mm,row['at']),angle],
            ['property',q('Reference'),q(identity),['at','0','0',angle],['layer',q('B.Fab' if back else 'F.Fab')],['hide','yes'],['effects',['font',['size','1','1'],['thickness','0.15']]]],
            ['property',q('Value'),q('Owned_'+identity),['at','0','0',angle],['layer',q('B.Fab' if back else 'F.Fab')],['hide','yes'],['effects',['font',['size','1','1'],['thickness','0.15']]]],['attr','smd']]
        if identity in ('CONVEX','CONCAVE'):
            pad=copy.deepcopy(by_number['1' if identity=='CONVEX' else '2']);pad[1]=q('1')
            for key,replacement in [('at',['at','0','0',angle]),('layers',['layers',q(layer),q('B.Mask' if back else 'F.Mask')]),('net',['net',q(row['net'])]),('uuid',['uuid',q(paduid)])]:
                old=sx.one(pad,key);pad[pad.index(old)]=replacement
            if back:
                for point in sx.one(sx.one(sx.one(pad,'primitives'),'gr_poly'),'pts')[1:]:point[2]=str(-Decimal(point[2]))
        else:
            pad=['pad',q('1'),'smd','circle',['at','0','0',angle],['size','1.5','1.5'],['layers',q(layer),q('B.Mask' if back else 'F.Mask')],['net',q(row['net'])],['uuid',q(paduid)]]
        fp.append(pad);board.append(fp)
    for row in scene['tracks']:
        row['uuid']=uid('track',row['id'],variant)
        board.append(['segment',node_xy('start',row['start']),node_xy('end',row['end']),['width','0.5'],['layer',q(layer)],['net',q(row['net'])],['uuid',q(row['uuid'])]])
    for index,(a,b) in enumerate(g.edges(tuple(scene['board_outline']))):
        board.append(['gr_line',node_xy('start',a),node_xy('end',b),['stroke',['width','0.05'],['type','default']],['layer',q('Edge.Cuts')],['uuid',q(uid('edge',str(index),variant))]])
    if len(p.routes(board))!=2 or len(sx.children(board,'footprint'))!=4:raise ValueError('owned fixture census changed')
    return (sx.dump(board)+'\n').encode(),scene
