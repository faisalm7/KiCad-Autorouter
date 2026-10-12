import app.freerouting.board.facade.RoutingBoard;
import app.freerouting.board.model.items.*;
import app.freerouting.board.trace.PolylineTrace;
import app.freerouting.core.RoutingJob;
import app.freerouting.geometry.planar.*;
import app.freerouting.io.BoardReadResult;
import app.freerouting.management.HeadlessBoardManager;
import app.freerouting.rules.DefaultItemClearanceClasses.ItemClass;
import app.freerouting.settings.*;
import app.freerouting.settings.sources.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Retained-route observation; optional bounded SES save, never routing or optimization. */
public final class MixedClassProbe {
  static Map<String,Object> map(Object... x){return AreaContactProbe.map(x);}
  static List<Integer> ids(Collection<Item> items){
    if(items.size()>4096)throw new IllegalArgumentException("contact/connected census bound");
    List<Integer> out=new ArrayList<>();for(Item i:items)out.add(i.getId());Collections.sort(out);return out;
  }
  static Map<String,Object> item(Item i,RoutingBoard b){
    if(i.netCount()>8)throw new IllegalArgumentException("item net bound");
    List<String> nets=new ArrayList<>();for(int n=0;n<i.netCount();n++)nets.add(b.rules.nets.get(i.getNetNumber(n)).name);
    return map("id",i.getId(),"kind",i.getClass().getName(),"nets",nets,"fixed",i.getFixedState().name(),
      "clearance_class_index",i.clearanceClassIndex(),"first_layer",i.firstLayer(),"last_layer",i.lastLayer(),"contacts",ids(i.getNormalContacts()));
  }
  static Map<String,Object> settings(RouterSettings s){
    return map("plane_as_obstacle",s.planeAsObstacle,"plane_nets",s.planeNets==null?null:Arrays.asList(s.planeNets),
      "layer_count",s.getLayerCount(),"router_enabled",s.getRunRouter(),"optimizer_enabled",s.getRunOptimizer());
  }
  static void observe(RoutingBoard b,Map<String,Object> state){
    var ct=b.communication.coordinateTransform;var m=b.rules.clearanceMatrix;
    state.put("census",map("items",b.getItems().size(),"pins",b.getPins().size(),"traces",b.getTraces().size(),
      "vias",b.getVias().size(),"areas",b.getConductionAreas().size(),"components",b.components.count(),
      "layers",b.getLayerCount(),"max_net_number",b.rules.nets.maxNetNumber(),"clearance_classes",m.getClassCount()));
    if(b.getItems().size()>4096||b.getPins().size()>512||b.getTraces().size()>2048||b.getVias().size()>512||
       b.getConductionAreas().size()>32||b.components.count()>128||b.getLayerCount()!=2||b.rules.nets.maxNetNumber()>256||m.getClassCount()>32)
      throw new IllegalArgumentException("bounded original census exceeded; actual census retained");
    List<Object> pins=new ArrayList<>(),areas=new ArrayList<>(),items=new ArrayList<>(),nets=new ArrayList<>(),matrix=new ArrayList<>();
    List<String> layers=new ArrayList<>(),classes=new ArrayList<>();
    for(int l=0;l<b.getLayerCount();l++)layers.add(b.layerStructure.layers[l].name);
    for(int c=0;c<m.getClassCount();c++)classes.add(m.getName(c));
    state.putAll(map("layers",layers,"clearance_class_names",classes,"ignore_conduction",b.rules.getIgnoreConduction(),
      "board_units_per_um",ct.dsnToBoard(1.0),"board_origin_dsn_um",AreaContactProbe.point(ct,new FloatPoint(0,0)),
      "clearance_safety_margin_board_units",app.freerouting.rules.ClearanceMatrix.clearance_safety_margin,
      "items",items,"pins",pins,"areas",areas,"nets",nets,"matrix",matrix));
    for(int a=0;a<m.getClassCount();a++)for(int z=0;z<m.getClassCount();z++)for(int l=0;l<b.getLayerCount();l++)
      matrix.add(map("a",a,"b",z,"layer",l,"raw_board_units",m.getValue(a,z,l,false),"raw_um",ct.boardToDsn(m.getValue(a,z,l,false)),
        "compensated_board_units",m.getValue(a,z,l,true),"compensated_um",ct.boardToDsn(m.getValue(a,z,l,true))));
    for(Item i:b.getItems())items.add(item(i,b));
    for(Pin p:b.getPins()){
      var row=item(p,b);row.putAll(map("reference",p.componentName(),"number",p.name(),"position_um",AreaContactProbe.point(ct,p.getCenter().toFloat()),
        "padstack_name",p.getPadstack().name,"bounds_um",AreaContactProbe.box(ct,p.boundingBox())));pins.add(row);
    }
    for(ConductionArea a:b.getConductionAreas()){
      var row=item(a,b);areas.add(row);var shape=a.getArea();
      if(!(shape.getBorder() instanceof PolylineShape border))throw new IllegalArgumentException("nonpolyline retained area");
      int count=border.borderLineCount();row.put("corner_count",count);
      if(count<3||count>4096||shape.getHoles().length>32)throw new IllegalArgumentException("area contour bound");
      List<Object> ring=new ArrayList<>(),integerRing=new ArrayList<>();List<String> kinds=new ArrayList<>();
      for(int k=0;k<count;k++){Point p=border.corner(k);ring.add(AreaContactProbe.point(ct,p.toFloat()));integerRing.add(AreaContactProbe.integerPoint(p));kinds.add(p.getClass().getName());}
      List<Object> obstacles=new ArrayList<>();for(Pin p:b.getPins())if(p.netCount()==1&&!a.sharesNet(p))obstacles.add(map("pin_id",p.getId(),"is_obstacle",a.isObstacle(p),"trace_obstacle",a.isTraceObstacle(p.getNetNumber(0))));
      row.putAll(map("ring_um",ring,"ring_board_integer",integerRing,"ring_classes",kinds,"holes",shape.getHoles().length,
        "area_api_um2",shape.getBorder().area()*ct.boardToDsn(1.0)*ct.boardToDsn(1.0),"layer",layers.get(a.getLayer()),
        "obstacle",a.getIsObstacle(),"foreign_pin_predicates",obstacles));
    }
    for(int n=1;n<=b.rules.nets.maxNetNumber();n++){
      var net=b.rules.nets.get(n);if(net==null)continue;var nc=net.getNetClass();List<Object> widths=new ArrayList<>(),groups=new ArrayList<>();
      Map<String,Object> defaults=new LinkedHashMap<>();for(ItemClass ic:ItemClass.values())defaults.put(ic.name(),nc.defaultItemClearanceClasses.get(ic));
      for(int l=0;l<b.getLayerCount();l++)widths.add(ct.boardToDsn(2.0*b.rules.getTraceHalfWidth(n,l)));
      for(var group:b.getConnectedSets(n))groups.add(ids(group));
      nets.add(map("name",net.name,"number",n,"class",nc.getName(),"width_um",widths,"trace_clearance_class",nc.getTraceClearanceClass(),
        "default_item_classes",defaults,"contains_plane",net.containsPlane(),"terminal_ids",ids(net.getTerminalItems()),"connected_sets",groups));
    }
  }
  /** Finite post-load diagnostic for the two captured JP1 footprint overrides only. */
  static void applyLocal250(RoutingBoard b,Map<String,Object> row){
    var ct=b.communication.coordinateTransform;var m=b.rules.clearanceMatrix;
    String[] names={"null","default","smd","POWER","board_edge"};
    if(m.getClassCount()!=names.length||m.getLayerCount()!=2||b.getLayerCount()!=2)
      throw new IllegalArgumentException("local override requires original five-class/two-layer matrix");
    for(int c=0;c<names.length;c++)if(!names[c].equals(m.getName(c)))
      throw new IllegalArgumentException("original clearance class name/order differs");
    String className="native_local_250";
    if(m.getNo(className)>=0)throw new IllegalArgumentException("local class already exists");
    double converted=ct.dsnToBoard(250.0);
    if(!Double.isFinite(converted)||converted<=0||converted>Integer.MAX_VALUE||converted!=Math.rint(converted))
      throw new IllegalArgumentException("local clearance is not exact integer board units");
    int local=(int)converted;
    if((local&1)!=0||ct.boardToDsn(local)!=250.0)
      throw new IllegalArgumentException("local clearance would be rounded by matrix");
    String[] numbers={"1","2"},netNames={"VCC","/pic_sockets/VCC_PIC"};
    int[] pinClasses={3,2},areaClasses={3,1};
    List<Item> targets=new ArrayList<>();List<Object> targetAudit=new ArrayList<>();
    for(int k=0;k<numbers.length;k++){
      Pin pin=null;
      for(Pin p:b.getPins())if("JP1".equals(p.componentName())&&numbers[k].equals(p.name())){
        if(pin!=null)throw new IllegalArgumentException("duplicate JP1 target pin");pin=p;
      }
      if(pin==null||pin.netCount()!=1||!netNames[k].equals(b.rules.nets.get(pin.getNetNumber(0)).name)
          ||pin.clearanceClassIndex()!=pinClasses[k]||pin.firstLayer()!=1||pin.lastLayer()!=1)
        throw new IllegalArgumentException("JP1 target pin identity/class/layer differs");
      ConductionArea area=null;
      for(ConductionArea a:b.getConductionAreas())if(a.sharesNet(pin)){
        if(area!=null)throw new IllegalArgumentException("ambiguous same-net synthetic area");area=a;
      }
      if(area==null||area.netCount()!=1||area.getNetNumber(0)!=pin.getNetNumber(0)
          ||area.clearanceClassIndex()!=areaClasses[k]||area.getLayer()!=1||!"USER_FIXED".equals(area.getFixedState().name())
          ||!pin.getNormalContacts().contains(area)||!area.getNormalContacts().contains(pin))
        throw new IllegalArgumentException("unique reciprocal synthetic body identity differs");
      List<Integer> edge=new ArrayList<>();
      for(int l=0;l<2;l++){
        int value=m.getValue(pin.clearanceClassIndex(),4,l,false);
        if(value!=local||m.getValue(4,pin.clearanceClassIndex(),l,false)!=value)
          throw new IllegalArgumentException("original JP1 board-edge clearance is not symmetric 250um");
        edge.add(value);
      }
      targets.add(pin);targets.add(area);
      targetAudit.add(map("reference","JP1","number",numbers[k],"net",netNames[k],"pin_id",pin.getId(),"area_id",area.getId(),
        "original_pin_class",pin.clearanceClassIndex(),"original_area_class",area.clearanceClassIndex(),"preserved_board_edge_raw_board_units",edge));
    }
    if(new HashSet<>(targets).size()!=4)throw new IllegalArgumentException("four distinct local items required");
    List<Integer> changed=new ArrayList<>();List<Object> rowAudit=new ArrayList<>(),treeChecks=new ArrayList<>();
    var audit=map("class_name",className,"class_index",5,"changed_item_ids",changed,"targets",targetAudit,
      "raw_row",rowAudit,"tree_entry_checks",treeChecks,"tree_refresh_completed",false,"tree_entries_valid",false,
      "apis",List.of("ClearanceMatrix.appendClass","ClearanceMatrix.setValue(int,int,int,int)","Item.changeClearanceClassIndex",
        "SearchTreeManager.clearanceValueChanged","SearchTreeManager.reinsertTreeItems","SearchTreeManager.validateEntries"));
    row.put("local_override",audit);
    if(!m.appendClass(className)||m.getClassCount()!=6||m.getNo(className)!=5)
      throw new IllegalArgumentException("exact local class append failed");
    for(int c=0;c<6;c++)for(int l=0;l<2;l++){
      int value=c==0?0:local;
      m.setValue(5,c,l,value);m.setValue(c,5,l,value);
      if(m.getValue(5,c,l,false)!=value||m.getValue(c,5,l,false)!=value)
        throw new IllegalArgumentException("local matrix symmetric readback differs");
      rowAudit.add(map("other_class",c,"layer",l,"raw_board_units",value,"raw_um",ct.boardToDsn(value)));
    }
    for(Item i:targets){
      i.changeClearanceClassIndex(5);
      if(i.clearanceClassIndex()!=5)throw new IllegalArgumentException("local item assignment failed");
      changed.add(i.getId());
    }
    Collections.sort(changed);
    b.searchTreeManager.clearanceValueChanged();b.searchTreeManager.reinsertTreeItems();audit.put("tree_refresh_completed",true);
    boolean valid=true;
    for(Item i:targets){boolean one=b.searchTreeManager.validateEntries(i);treeChecks.add(map("id",i.getId(),"valid",one));valid&=one;}
    audit.put("tree_entries_valid",valid);
    if(!valid)throw new IllegalArgumentException("local item search-tree entries invalid after refresh");
  }
  /** Separate route geometry, emitted only by local250-ses; no approximate point is promoted to exact. */
  static void routeGeometry(RoutingBoard b,Map<String,Object> result){
    var ct=b.communication.coordinateTransform;
    List<Object> traces=new ArrayList<>(),vias=new ArrayList<>();
    result.putAll(map("trace_count",b.getTraces().size(),"via_count",b.getVias().size(),"traces",traces,"vias",vias));
    if(b.getTraces().size()>2048||b.getVias().size()>512||b.getLayerCount()!=2)
      throw new IllegalArgumentException("ordinary route geometry census bound");
    int totalCorners=0;
    for(Trace trace:b.getTraces()){
      var row=item(trace,b);traces.add(row);
      if(!(trace instanceof PolylineTrace poly))throw new IllegalArgumentException("nonpolyline ordinary trace");
      int n=poly.cornerCount(),layer=poly.getLayer();row.put("corner_count",n);
      totalCorners+=n;
      if(n<2||n>4096||totalCorners>16384||layer<0||layer>=b.getLayerCount()||poly.getHalfWidth()<=0)
        throw new IllegalArgumentException("ordinary trace corner/layer/width bound");
      List<Object> corners=new ArrayList<>(),integerCorners=new ArrayList<>();List<String> classes=new ArrayList<>();
      for(int k=0;k<n;k++){
        Point point=poly.polyline().corner(k);corners.add(AreaContactProbe.point(ct,point.toFloat()));
        integerCorners.add(AreaContactProbe.integerPoint(point));classes.add(point.getClass().getName());
      }
      row.putAll(map("layer_index",layer,"layer",b.layerStructure.layers[layer].name,"half_width_board_units",poly.getHalfWidth(),
        "width_um",ct.boardToDsn(2.0*poly.getHalfWidth()),"corners_um",corners,"corners_board_integer",integerCorners,"corner_classes",classes));
    }
    for(Via via:b.getVias()){
      var row=item(via,b);vias.add(row);Point center=via.getCenter();List<String> layers=new ArrayList<>();
      if(via.firstLayer()<0||via.lastLayer()<via.firstLayer()||via.lastLayer()>=b.getLayerCount()||via.getPadstack()==null)
        throw new IllegalArgumentException("ordinary via layer/padstack scope");
      for(int l=via.firstLayer();l<=via.lastLayer();l++)layers.add(b.layerStructure.layers[l].name);
      row.putAll(map("position_um",AreaContactProbe.point(ct,center.toFloat()),"position_board_integer",AreaContactProbe.integerPoint(center),
        "position_class",center.getClass().getName(),"padstack_name",via.getPadstack().name,"layers",layers,"bounds_um",AreaContactProbe.box(ct,via.boundingBox())));
    }
  }
  static final int SES_LIMIT=4*1024*1024;
  /** Bound bytes before the underlying write; CREATE_NEW is supplied by the caller. */
  static final class BoundedSesStream extends OutputStream {
    final OutputStream target;int count=0;boolean closed=false;
    BoundedSesStream(OutputStream target){this.target=target;}
    public void write(int value)throws IOException{
      if(closed||count>=SES_LIMIT)throw new IOException("SES output limit or closed stream");
      target.write(value);count++;
    }
    public void write(byte[] data,int offset,int length)throws IOException{
      Objects.checkFromIndexSize(offset,length,data.length);
      if(closed||length>SES_LIMIT-count)throw new IOException("SES output limit or closed stream");
      target.write(data,offset,length);count+=length;
    }
    public void flush()throws IOException{if(closed)throw new IOException("closed SES stream");target.flush();}
    public void close()throws IOException{if(!closed){target.close();closed=true;}}
  }
  static String boundedError(Exception e){
    String message=e.getClass().getName()+": "+e.getMessage();return message.length()>4096?message.substring(0,4096):message;
  }
  static void writeSes(HeadlessBoardManager manager,RoutingBoard board,Path path,Map<String,Object> row)throws Exception{
    var ses=map("executed",false,"returned",null,"closed",false,"bytes",0,"sha256",null,"path","raw.ses","write_completed",false);
    row.put("ses",ses);Exception failure=null;BoundedSesStream stream=null;
    try{
      stream=new BoundedSesStream(Files.newOutputStream(path,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE));
      ses.put("executed",true);
      boolean returned=manager.saveAsSpecctraSessionSes(stream,"original-mixed.dsn");ses.put("returned",returned);
      if(!returned)throw new IOException("manager SES save returned false");
    }catch(Exception e){failure=e;}
    finally{
      if(stream!=null){
        try{stream.close();}catch(Exception e){ses.put("close_error",boundedError(e));if(failure==null)failure=e;}
        ses.put("closed",stream.closed);ses.put("stream_accepted_bytes",stream.count);
        ses.put("write_completed",Boolean.TRUE.equals(ses.get("returned"))&&stream.closed&&stream.count>0);
        try{
          if(Files.isSymbolicLink(path)||!Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))throw new IOException("SES output not regular");
          byte[] saved;try(InputStream input=Files.newInputStream(path,LinkOption.NOFOLLOW_LINKS)){saved=input.readNBytes(SES_LIMIT+1);}
          ses.put("bytes",saved.length);
          if(saved.length>SES_LIMIT)throw new IOException("SES readback bound");
          ses.put("sha256",AreaContactProbe.sha(saved));
          if(saved.length==0||saved.length!=stream.count)throw new IOException("SES written/readback length differs");
        }catch(Exception e){ses.put("readback_error",boundedError(e));if(failure==null)failure=e;}
      }
      // Preserve after-observations even when the writer returned false or a file audit failed.
      var after=map();row.put("state_after_ses",after);
      try{observe(board,after);}catch(Exception e){ses.put("state_error",boundedError(e));if(failure==null)failure=e;}
      var geometry=map();row.put("route_geometry_after_ses",geometry);
      try{routeGeometry(board,geometry);}catch(Exception e){ses.put("geometry_error",boundedError(e));if(failure==null)failure=e;}
    }
    if(failure!=null){ses.put("error",boundedError(failure));throw failure;}
  }
  static void run(byte[] raw,boolean flag,Map<String,Object> row,boolean local250,Path sesPath)throws Exception{
    String[] argv={"--router.autorouter.enabled=false","--router.optimizer.enabled=false","--router.plane_as_obstacle="+flag};
    CliSettings cli=new CliSettings(argv);
    SettingsSource[] sources={new DefaultSettings(),new DsnFileSettings(new ByteArrayInputStream(raw),"original-mixed.dsn"),cli};
    RouterSettings settings=new SettingsMerger(sources).merge();RoutingJob job=new RoutingJob();job.routerSettings=settings;
    row.putAll(map("argv",Arrays.asList(argv),"settings_before",settings(settings),"input_sha256",AreaContactProbe.sha(raw)));
    // No input filename/counterpart file: only the explicitly provided bytes may be loaded.
    HeadlessBoardManager manager=new HeadlessBoardManager(job);
    BoardReadResult result=manager.loadFromSpecctraDsn(new ByteArrayInputStream(raw),null,null);
    row.put("parser_result_class",result.getClass().getName());
    if(!(result instanceof BoardReadResult.Success success)||!(success.board() instanceof RoutingBoard board))throw new IllegalArgumentException("successful RoutingBoard required");
    if(manager.getRoutingBoard()!=board)throw new IllegalArgumentException("manager identity differs");
    board.awaitPostLoad();row.putAll(map("post_load_awaited",true,"parser_warnings",success.warnings(),"settings_after",settings(job.routerSettings)));
    if(sesPath!=null){var geometry=map();row.put("route_geometry_before_local",geometry);routeGeometry(board,geometry);}
    if(local250){var before=map();row.put("state_before_local",before);observe(board,before);applyLocal250(board,row);}
    var state=map();row.put("state",state);observe(board,state);
    if(sesPath!=null){
      var geometry=map();row.put("route_geometry",geometry);routeGeometry(board,geometry);
      if(flag)writeSes(manager,board,sesPath,row);
    }
    row.put("status","observed");
  }
  public static void main(String[] args)throws Exception{
    if(args.length!=2&&(args.length!=3||!("local250".equals(args[2])||"local250-ses".equals(args[2]))))
      throw new IllegalArgumentException("input DSN, output JSON and optional literal local250 or local250-ses required");
    boolean local250=args.length==3;
    Path input=Path.of(args[0]),output=Path.of(args[1]);
    Path sesPath=args.length==3&&"local250-ses".equals(args[2])?output.toAbsolutePath().getParent().resolve("raw.ses"):null;
    if(sesPath!=null&&(output.getFileName().toString().equalsIgnoreCase("raw.ses")
        ||Files.isSymbolicLink(sesPath.getParent())||!Files.isDirectory(sesPath.getParent(),LinkOption.NOFOLLOW_LINKS)))
      throw new IllegalArgumentException("distinct JSON name and regular SES parent required");
    if(Files.isSymbolicLink(input)||!Files.isRegularFile(input)||Files.exists(output))throw new IllegalArgumentException("regular input/fresh output required");
    byte[] raw;try(InputStream stream=Files.newInputStream(input)){raw=stream.readNBytes(1048577);}
    if(raw.length==0||raw.length>1048576)throw new IllegalArgumentException("input bound");
    List<Object> cases=new ArrayList<>();var result=map("schema",1,"routing_executed",false,"ses_executed",false,"cases",cases);
    for(boolean flag:new boolean[]{false,true}){
      var row=map("requested_obstacle",flag,"status","failed","input_sha256",AreaContactProbe.sha(raw));cases.add(row);
      try{run(raw,flag,row,local250,sesPath);}catch(Exception e){row.put("error",sesPath==null?e.getClass().getName()+": "+e.getMessage():boundedError(e));}
      if(sesPath!=null&&row.get("ses") instanceof Map<?,?> ses&&Boolean.TRUE.equals(ses.get("write_completed")))result.put("ses_executed",true);
      byte[] saved=(AreaContactProbe.json(result)+"\n").getBytes(java.nio.charset.StandardCharsets.UTF_8);
      if(saved.length>16*1024*1024)throw new IllegalArgumentException("observation output bound");
      Files.write(output,saved);
    }
  }
}
