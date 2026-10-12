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

/** Original retained-route import only. No scheduler, autorouter, optimizer or SES writer. */
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
  static void run(byte[] raw,boolean flag,Map<String,Object> row)throws Exception{
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
    var state=map();row.put("state",state);observe(board,state);row.put("status","observed");
  }
  public static void main(String[] args)throws Exception{
    if(args.length!=2)throw new IllegalArgumentException("input DSN and output JSON required");
    Path input=Path.of(args[0]),output=Path.of(args[1]);
    if(Files.isSymbolicLink(input)||!Files.isRegularFile(input)||Files.exists(output))throw new IllegalArgumentException("regular input/fresh output required");
    byte[] raw;try(InputStream stream=Files.newInputStream(input)){raw=stream.readNBytes(1048577);}
    if(raw.length==0||raw.length>1048576)throw new IllegalArgumentException("input bound");
    List<Object> cases=new ArrayList<>();var result=map("schema",1,"routing_executed",false,"ses_executed",false,"cases",cases);
    for(boolean flag:new boolean[]{false,true}){
      var row=map("requested_obstacle",flag,"status","failed","input_sha256",AreaContactProbe.sha(raw));cases.add(row);
      try{run(raw,flag,row);}catch(Exception e){row.put("error",e.getClass().getName()+": "+e.getMessage());}
      byte[] saved=(AreaContactProbe.json(result)+"\n").getBytes(java.nio.charset.StandardCharsets.UTF_8);
      if(saved.length>16*1024*1024)throw new IllegalArgumentException("observation output bound");
      Files.write(output,saved);
    }
  }
}
