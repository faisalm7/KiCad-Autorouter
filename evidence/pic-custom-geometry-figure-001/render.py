"""Render the observed local shape discrepancy; no native or routing claim."""
from pathlib import Path
import hashlib, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Circle
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
p=ROOT/'evidence/pic-custom-observation-002/custom-pads.json'
s=ROOT/'evidence/pic-custom-observation-002/summary.json'
assert hashlib.sha256(s.read_bytes()).hexdigest()=='5a192888d1db6c3b607288ff2059dd6a9ce3ce3e28aba122f5a8f051959b97d4'
obs=json.loads(p.read_text());summary=json.loads(s.read_text())
uid='5b196d03-cd44-4c2b-9a91-fadc24ae5f4b'
pad=next(r for r in obs['observation_before_export']['pads'] if r['uuid']==uid)
assert obs['observation_before_export']==obs['observation_after_export']
native=[[x/1e6,y/1e6] for x,y in pad['merged_local']['outlines'][0]['outline']['points_nm']]
match=next(r for r in summary['dsn_correspondence']['custom_pads'] if r['uuid']==uid)
polygon=next(r for r in match['padstack_ast'] if isinstance(r,list) and r[0]=='shape')[1]
assert polygon[:3]==['polygon','top_layer','0']
hull=[[float(polygon[i])/1000,float(polygon[i+1])/1000] for i in range(3,len(polygon),2)]
def area(ring):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(ring,ring[1:]+ring[:1])))/2
assert abs(area(native)-1.35)<1e-12 and abs(area(hull)-1.725)<1e-12
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'pic-custom-observation-002','svg.fonttype':'none'})
fig,axs=plt.subplots(1,2,figsize=(10.8,5.8),layout='constrained')
fig.suptitle('A routing outline can include space with no copper',fontsize=17,fontweight='bold')
for ax in axs:
 ax.add_patch(Polygon(hull,facecolor='#f5d9aa',edgecolor='#a76610',linewidth=1.8,linestyle='--',label='Exported DSN outline'))
 ax.add_patch(Polygon(native,facecolor='#3e8fa2',edgecolor='#154e5a',linewidth=1.5,label='Native custom-pad copper'))
 ax.add_patch(Rectangle((-.15,-.15),.3,.3,facecolor='none',edgecolor='#103642',linewidth=1.4,label='0.3 mm anchor'))
 ax.set(xlim=(-1.2,.9),ylim=(-1,1),xlabel='Local x (mm)',ylabel='Local y (mm)')
 ax.set_aspect('equal');ax.grid(alpha=.13);ax.set_axisbelow(True)
axs[0].set_title('Observed JP1 pad 2 shape',loc='left',fontweight='bold')
axs[0].annotate('Notch filled by export',xy=(-.47,0),xytext=(-1.15,.88),arrowprops={'arrowstyle':'->','color':'#81510f'},color='#81510f',fontsize=10)
axs[0].legend(loc='lower left',bbox_to_anchor=(-.08,-.30),frameon=False,fontsize=9)
axs[1].set_title('Planned false-contact control',loc='left',fontweight='bold')
axs[1].plot([-1.15,-.60],[.55*.25/8.9,0],color='#934843',linewidth=1.3,linestyle=':',zorder=3)
axs[1].add_patch(Circle((-.60,0),.25,facecolor='#e9b8b3',edgecolor='#934843',linewidth=1.5,zorder=3))
axs[1].plot(-.60,0,'o',color='#682d29',markersize=4,zorder=4)
axs[1].annotate('Track endpoint inside outline\n0.5 mm diameter cap shown',xy=(-.60,0),xytext=(-1.15,.88),arrowprops={'arrowstyle':'->','color':'#682d29'},color='#682d29',fontsize=10)
axs[1].text(-.03,-.30,'Whole track cap misses copper.\nNative disconnection test is still pending.',transform=axs[1].transAxes,fontsize=10,color='#333333')
fig.supxlabel('Pad-local comparison only; backside placement is not qualified by this drawing.\nGeometry: KiCad pic_programmer demo, commit 69cafb9, CC BY-SA 4.0. Native observation 002.',fontsize=9)
fig.savefig(OUT/'custom-pad-gap.png',dpi=170)
fig.savefig(OUT/'custom-pad-gap.svg',metadata={'Date':None})
manifest={'schema':1,'kind':'static local-shape illustration','native_control_executed':False,'routing_qualified':False,'source_pad_uuid':uid,'native_area_mm2':area(native),'dsn_hull_area_mm2':area(hull),'input_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [p,s]},'files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),OUT/'custom-pad-gap.png',OUT/'custom-pad-gap.svg']},'license':'CC-BY-SA-4.0 diagram derived from attributed demo geometry; original notices preserved with evidence/pic-custom-observation-002'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest))
