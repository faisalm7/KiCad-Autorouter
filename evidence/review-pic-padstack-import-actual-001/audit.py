"""Read-only actual importer evidence audit. Never launches Java, compiler or CAD."""
import argparse, ast, hashlib, json, math, os, re, stat, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'.runs/pic-padstack-import-probe-001'
HEAD='9da5f9cdfbd6f709c9dd4235e2c6598574c2c46d'
CHECKS=[]; SEEN={}

def pin(raw):return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def data(path,limit=1024**2):
    path=Path(path); info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size>limit:raise ValueError('nonregular/oversize '+str(path))
    with path.open('rb') as f:raw=f.read(limit+1)
    if len(raw)>limit or len(raw)!=info.st_size:raise ValueError('bounded read changed')
    key=str(path); p=pin(raw)
    if key in SEEN and SEEN[key]!=p:raise ValueError('stale '+key)
    SEEN[key]=p;return raw

def digest(path,limit=80*1024**2):
    path=Path(path);s=path.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_size>limit:raise ValueError('tool path/size')
    h=hashlib.sha256();n=0
    with path.open('rb') as f:
        while True:
            b=f.read(min(1024**2,limit-n+1))
            if not b:break
            n+=len(b)
            if n>limit:raise ValueError('tool growth')
            h.update(b)
    if n!=s.st_size:raise ValueError('tool size changed')
    return {'bytes':n,'sha256':h.hexdigest()}

def decode(raw):
    def pairs(rows):
        d={}
        for k,v in rows:
            if k in d:raise ValueError('duplicate JSON key')
            d[k]=v
        return d
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
def read(path):return decode(data(path))
def inventory(root):
    result={};stack=[root];entries=0;total=0
    while stack:
        with os.scandir(stack.pop()) as it:
            for item in it:
                entries+=1
                if entries>256 or item.is_symlink():raise ValueError('inventory cap/symlink')
                p=Path(item.path)
                if item.is_dir(follow_symlinks=False):stack.append(p)
                elif item.is_file(follow_symlinks=False):
                    if len(result)>=128:raise ValueError('file cap')
                    row=pin(data(p));total+=row['bytes']
                    if total>10*1024**2:raise ValueError('aggregate cap')
                    result[str(p.relative_to(root))]=row
                else:raise ValueError('special path')
    return dict(sorted(result.items()))
def ok(label,value):
    if value is not True:raise AssertionError(label)
    CHECKS.append(label)
def same(label,a,b):ok(label,type(a)==type(b) and a==b)
def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def area(p):return abs(sum(a[0]*b[1]-a[1]*b[0]for a,b in zip(p,p[1:]+p[:1])))/2
def ring(p):
    p=[tuple(v)for v in p];r=list(reversed(p))
    return min(tuple(q[i:]+q[:i])for q in (p,r)for i in range(len(q)))
def hull(p):
    p=sorted(set(p));lo=[];hi=[]
    for seq,out in ((p,lo),(list(reversed(p)),hi)):
        for v in seq:
            while len(out)>1 and cross(out[-2],out[-1],v)<=0:out.pop()
            out.append(v)
    return lo[:-1]+hi[:-1]
def inside(p,v):
    winding=0
    for a,b in zip(p,p[1:]+p[:1]):
        c=cross(a,b,v)
        if c==0 and all(min(a[i],b[i])<=v[i]<=max(a[i],b[i])for i in (0,1)):return False
        if a[1]<=v[1]<b[1] and c>0:winding+=1
        if b[1]<=v[1]<a[1] and c<0:winding-=1
    return winding!=0

def parse_scope(raw):
    text=raw.decode('ascii');tokens=re.findall(r'\(|\)|[^\s()]+',text);pos=0
    def one(depth=0):
        nonlocal pos
        if depth>8 or pos>=len(tokens):raise ValueError('malformed DSN')
        token=tokens[pos];pos+=1
        if token=='(':
            out=[]
            while pos<len(tokens) and tokens[pos]!=')':out.append(one(depth+1))
            if pos==len(tokens):raise ValueError('unclosed DSN')
            pos+=1;return out
        if token==')':raise ValueError('unexpected close')
        return token
    out=one()
    if pos!=len(tokens):raise ValueError('trailing token')
    return out

def main(output):
    before=inventory(RUN);summary=read(RUN/'summary.json');observed=read(RUN/'observations.json');runtime=read(RUN/'runtime.json')
    protocol=read(RUN/'code/experiments/pic_padstack_import_probe_v1/PROTOCOL.json')
    same('completed actual run',summary['status'],'completed')
    for key in ('observations_complete','expected_observations_match','import_process_requested','import_process_executed'):same(key,summary[key],True)
    for key in ('routing_accepted','routing_executed','native_executed','custom_pad_support_qualified'):same(key,summary[key],False)
    same('scope',summary['scope'],'owned_padstack_import_only');same('schema',summary['schema'],1)
    same('runtime exact summary',runtime,summary['runtime']);same('recorded code HEAD',runtime['git']['head'],HEAD)
    same('complete frozen inventory',summary['frozen_evidence'],{k:v for k,v in before.items()if k!='summary.json'})
    same('observation SHA',pin(data(RUN/'observations.json'))['sha256'],summary['observations_sha256'])
    for relative,expected in runtime['sources'].items():
        raw=data(RUN/'code'/relative);same('frozen source '+relative,pin(raw),expected)
        result=subprocess.run(['git','show',HEAD+':'+relative],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=5,check=True)
        same('committed source '+relative,result.stdout,raw)
        same('current source '+relative,data(ROOT/relative),raw)
    tools={}
    for name,row in protocol['tools'].items():
        path=Path(row['path']);path=path if path.is_absolute()else ROOT/path
        tools[name]=digest(path);same('actual pinned tool '+name,tools[name],{k:row[k]for k in ('bytes','sha256')})
        same('runtime tool '+name,runtime['tools'][name],tools[name])
    for relative,expected in protocol['source_provenance'].items():same('prior API receipt '+relative,pin(data(ROOT/relative)),expected)
    convex=[(1000,0),(500,-750),(-500,-750),(-500,750),(500,750)]
    concave=[(500,-750),(-650,-750),(-150,0),(-650,750),(500,750)]
    a=[(-1000,-1000),(-500,-1000),(-500,-500),(-1000,-500)]
    b=[(500,500),(1000,500),(1000,1000),(500,1000)]
    targets={'convex':{'F.Cu':convex,'B.Cu':None},'concave':{'F.Cu':hull(concave),'B.Cu':None},'sameAB':{'F.Cu':b,'B.Cu':None},'sameBA':{'F.Cu':a,'B.Cu':None},'distinct':{'F.Cu':a,'B.Cu':b}}
    inputs={'convex':[('F.Cu',convex)],'concave':[('F.Cu',concave)],'sameAB':[('F.Cu',a),('F.Cu',b)],'sameBA':[('F.Cu',b),('F.Cu',a)],'distinct':[('F.Cu',a),('B.Cu',b)]}
    recipe=data(ROOT/'experiments/pic_custom_native_controls_v1/recipes.py');constants={}
    for node in ast.parse(recipe).body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('CONVEX','CONCAVE'):constants[node.targets[0].id]=ast.literal_eval(node.value)
    for name,points in [('CONVEX',convex),('CONCAVE',concave)]:same('previous native control recipe '+name,[(x//1000,y//1000)for x,y in constants[name]],points)
    same('exact case order',list(targets),protocol['case_ids']);same('observed case order',[r['case']for r in observed['cases']],list(targets))
    same('actual coordinate transform',observed['coordinate_transform'],[1,0,0]);same('actual units',observed['units'],'micrometres')
    for key in ('native_executed','routing_executed'):same('raw '+key,observed[key],False)
    points={'origin':(0,0),'notch':(-600,0),'a':(-750,-750),'b':(750,750)};geometry=[]
    for row in observed['cases']:
        name=row['case'];raw=data(RUN/'inputs'/(name+'.dsn'));scope=parse_scope(raw)
        same(name+' input identity',scope[:2],['padstack',name]);same(name+' input hash',pin(raw)['sha256'],protocol['input_sha256'][name+'.dsn']);same(name+' native input hash',row['input_sha256'],pin(raw)['sha256'])
        declared=[]
        for shape in scope[2:]:
            same(name+' shape wrapper',shape[0],'shape');same(name+' singular shape',len(shape),2);s=shape[1]
            if s[0]=='polygon':
                same(name+' zero polygon width',s[2],'0');nums=list(map(int,s[3:]));poly=list(zip(nums[::2],nums[1::2]))
            else:
                same(name+' rectangle type',s[0],'rect');same(name+' rectangle arity',len(s),6);x1,y1,x2,y2=map(int,s[2:]);poly=[(x1,y1),(x2,y1),(x2,y2),(x1,y2)]
            declared.append((s[1],poly))
        same(name+' exact input shape order',declared,inputs[name]);same(name+' parser success',row['parser_return'],True);same(name+' completed',row['status'],'observed')
        same(name+' sole named padstack',row['padstack_name'],name);same(name+' count',row['padstack_count'],1);same(name+' layer census',row['board_layer_count'],2);same(name+' layer names',sorted(row['layers']),['B.Cu','F.Cu'])
        out={}
        for layer,expected in targets[name].items():
            got=row['layers'][layer]
            if expected is None:same(name+layer+' empty',got,None);continue
            same(name+layer+' exact observed polygon up to winding/start',ring(got['corners_um']),ring(expected))
            same(name+layer+' analytic area',float(got['area_um2']),float(area(expected)))
            same(name+layer+' bbox',got['bounds_um'],[min(v[0]for v in expected),min(v[1]for v in expected),max(v[0]for v in expected),max(v[1]for v in expected)])
            same(name+layer+' strict point membership',got['strict_inside'],{k:inside(expected,v)for k,v in points.items()})
            same(name+layer+' shape class',got['class'],'app.freerouting.geometry.planar.'+('Simplex'if name=='convex'else'IntBox'))
            out[layer]={'area_um2':area(expected),'corners_um':expected,'strict_inside':got['strict_inside']}
        geometry.append({'case':name,'raw_shapes':len(declared),'observed':out})
    same('analytic raw concave area',area(concave),1350000.0);same('analytic hull area',area(hull(concave)),1725000.0)
    ok('notch false native copper membership',not inside(concave,points['notch']));ok('notch true imported hull membership',inside(hull(concave),points['notch']))
    same('actual summary five exact comparisons',summary['case_comparison'],[{'case':name,'expected_observation_matches':True}for name in targets])
    prefix=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)'];jar=str(ROOT/protocol['tools']['jar']['path'])
    commands={
      'compile':prefix+[protocol['tools']['javac']['path'],'-J-Xmx256m','-J-Duser.home='+str(RUN/'home'),'-proc:none','-classpath',jar,'-d',str(RUN/'classes'),str(RUN/'code/experiments/pic_padstack_import_probe_v1/PadstackImportProbe.java')],
      'import':prefix+[protocol['tools']['java']['path'],'-Xmx256m','-Djava.awt.headless=true','-Duser.home='+str(RUN/'home'),'-Djava.io.tmpdir='+str(RUN/'tmp'),'-cp',str(RUN/'classes')+':'+jar,'PadstackImportProbe',str(RUN/'inputs'),str(RUN/'observations.json')]}
    same('all process stages',[x['name']for x in summary['steps']],list(commands));processes=[]
    for step in summary['steps']:
        name=step['name'];record=read(RUN/(name+'-process.json'));same(name+' process step exact',{k:v for k,v in step.items()if k!='name'},record)
        same(name+' actual argv',record['argv'],commands[name]);same(name+' actual cwd',record['cwd'],str(RUN));same(name+' exit',record['exit_code'],0);same(name+' status',record['status'],'success')
        same(name+' cleanup',record['cleanup_complete'],True);same(name+' cancellation enabled',record['signal_cancellation_enabled'],True)
        same(name+' log path',record['log'],str(RUN/(name+'.log')));same(name+' logbytes',record['log_bytes'],len(data(RUN/(name+'.log'))));same(name+' log untruncated',record['log_truncated'],False)
        same(name+' sampled resource caps',record['resource_guards']['max_group_rss_bytes'],1024**3);same(name+' disk cap',record['resource_guards']['max_workdir_bytes'],10*1024**2);same(name+' polling not OS hard cap',record['resource_guards']['os_enforced'],False)
        for key in ('wall_seconds','cpu_seconds','supervisor_cpu_seconds','monitor_cpu_seconds'):ok(name+' finite '+key,type(record[key])in(int,float) and math.isfinite(record[key])and 0<=record[key]<60)
        ok(name+' observed RSS/disk within caps',record['max_rss_bytes']<1024**3 and record['sampled_peak_group_rss_bytes']<1024**3 and record['sampled_peak_workdir_bytes']<10*1024**2)
        processes.append({k:step[k]for k in ('name','exit_code','wall_seconds','cpu_seconds','max_rss_bytes','sampled_peak_group_rss_bytes','sampled_peak_workdir_bytes')})
    execution=read(ROOT/'.runs/pic-padstack-import-probe-001-execution.json');wrapper=ROOT/'.runs/run-pic-padstack-import-probe-001.py';log=ROOT/'.runs/pic-padstack-import-probe-001-command.log'
    expected=['python3','-B','experiments/pic_padstack_import_probe_v1/driver.py','--run-import','--output','.runs/pic-padstack-import-probe-001']
    same('outer argv',execution['argv'],expected);same('outer head',execution['git_head'],HEAD);same('outer cwd',execution['cwd'],str(ROOT));same('actual controller exit',execution['exit_code'],0);same('outer no cleanup needed',execution['cleanup_signals'],[])
    same('outer wrapper SHA',pin(data(wrapper))['sha256'],execution['wrapper_sha256']);same('outer log exact',pin(data(log)),{'sha256':execution['log_sha256'],'bytes':execution['log_bytes']})
    declared=next(n.value for n in ast.parse(data(wrapper)).body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='argv'for t in n.targets));same('wrapper declared argv',ast.literal_eval(declared),expected)
    emitted=read(log);same('stdout canonical result subset',emitted,{k:summary[k]for k in emitted})
    same('wallcap',summary['budget_seconds'],60.0);same('CPUcap',summary['cpu_budget_seconds'],60.0)
    ok('sample covered by final outer wall',0<summary['wall_seconds']<=execution['wall_seconds']<60)
    ok('sample covered by final outer waited CPU',0<summary['total_cpu_seconds']<=execution['waited_child_cpu_seconds']<60)
    ok('CPU includes parent/metadata beyond primary child stages',summary['total_cpu_seconds']>=sum(x['cpu_seconds']for x in summary['steps']))
    same('output ceiling',summary['max_output_bytes'],10*1024**2)
    for name,row in protocol['tools'].items():
        path=Path(row['path']);path=path if path.is_absolute()else ROOT/path
        same('tool unchanged after audit '+name,digest(path),tools[name])
    before_seen=dict(SEEN)
    for path,expected in before_seen.items():same('material unchanged '+str(Path(path).relative_to(ROOT)),pin(data(path)),expected)
    same('complete raw tree unchanged after audit',inventory(RUN),before)
    result={'schema':1,'audit_passed':True,'checks':len(CHECKS),'run':str(RUN.relative_to(ROOT)),'run_head':HEAD,'run_summary':before['summary.json'],'observations':before['observations.json'],'raw_files':len(before),'raw_bytes':sum(x['bytes']for x in before.values()),'geometry':geometry,'concave_raw_area_um2':area(concave),'concave_imported_hull_area_um2':area(hull(concave)),'extra_hull_area_um2':area(hull(concave))-area(concave),'processes':processes,'stored_prepublication_wall_seconds':summary['wall_seconds'],'stored_prepublication_full_cpu_seconds':summary['total_cpu_seconds'],'outer_wall_seconds':execution['wall_seconds'],'outer_waited_child_cpu_seconds':execution['waited_child_cpu_seconds'],'controller_exit_code':execution['exit_code'],'tool_pins':tools,'source_and_evidence_unchanged':True,'native_executed_by_auditor':False,'java_or_compiler_executed_by_auditor':False,'routing_executed_by_auditor':False,'network_used_by_auditor':False,'routing_support_qualified':False,'limitations':['Five isolated padstack scopes, not whole-board import or a router trial.','Analytic checks independently recompute rings, areas and point membership; they do not establish electrical connectivity.','Saved evidence and source/tool bytes are consistency checked, not cryptographically authenticated execution.','Resource values are recorded samples/outer process measurements; polling guards are not hard OS memory enforcement.'],'dependencies':{str(Path(k).relative_to(ROOT)):v for k,v in sorted(SEEN.items())}}
    output=Path(output)
    with output.open('x')as f:f.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'audit_passed':True,'checks':len(CHECKS),'raw_files':len(before),'output_sha256':pin(data(output))['sha256']}))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);main(parser.parse_args().output)
