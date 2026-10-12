import app.freerouting.board.facade.RoutingBoard;
import app.freerouting.board.model.items.*;
import app.freerouting.core.RoutingJob;
import app.freerouting.io.BoardReadResult;
import app.freerouting.management.HeadlessBoardManager;
import app.freerouting.settings.*;
import app.freerouting.settings.sources.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** One retained-board selective-obstacle observation; never routing or SES writing. */
public final class SelectiveAreaProbe {
  static Map<String,Object> map(Object... pairs){return MixedClassProbe.map(pairs);}
  static final int INPUT_LIMIT=1024*1024, OUTPUT_LIMIT=16*1024*1024;
  static final String[] ARGV={"--router.autorouter.enabled=false","--router.optimizer.enabled=false","--router.plane_as_obstacle=false"};

  static List<ConductionArea> targets(RoutingBoard board,Map<String,Object> row){
    if(!(row.get("local_override") instanceof Map<?,?> local)||!(local.get("targets") instanceof List<?> audit)||audit.size()!=2)
      throw new IllegalArgumentException("exact local override target audit required");
    List<ConductionArea> result=new ArrayList<>();Set<Integer> ids=new HashSet<>();
    for(Object entry:audit){
      if(!(entry instanceof Map<?,?> one)||!(one.get("area_id") instanceof Integer id)||!ids.add(id)
          ||!(board.getItem(id) instanceof ConductionArea area)||area.clearanceClassIndex()!=5
          ||area.getLayer()!=1||area.netCount()!=1||!"USER_FIXED".equals(area.getFixedState().name())
          ||area.getIsObstacle()||!Objects.equals(one.get("net"),board.rules.nets.get(area.getNetNumber(0)).name))
        throw new IllegalArgumentException("selective target identity differs from completed local override");
      result.add(area);
    }
    if(board.getConductionAreas().size()!=3||!board.rules.getIgnoreConduction())
      throw new IllegalArgumentException("expected false-global three-area baseline required");
    int original=0;
    for(ConductionArea area:board.getConductionAreas()){
      if(area.getIsObstacle())throw new IllegalArgumentException("baseline area unexpectedly enabled");
      if(!ids.contains(area.getId())){
        if(!"SYSTEM_FIXED".equals(area.getFixedState().name())||area.netCount()!=1
            ||!"GND".equals(board.rules.nets.get(area.getNetNumber(0)).name))
          throw new IllegalArgumentException("original plane identity differs");
        original++;
      }
    }
    if(original!=1)throw new IllegalArgumentException("one unchanged original plane required");
    return result;
  }

  static void predicates(RoutingBoard board,Map<String,Object> out){
    List<Object> areas=new ArrayList<>(),queries=new ArrayList<>(),entries=new ArrayList<>();
    List<Item> routes=new ArrayList<>();routes.addAll(board.getTraces());routes.addAll(board.getVias());
    out.putAll(map("area_count",board.getConductionAreas().size(),"route_count",routes.size(),
      "item_count",board.getItems().size(),"areas",areas,"trace_queries",queries,"tree_entries",entries));
    if(board.getConductionAreas().size()!=3||routes.size()>2560||board.getItems().size()>4096)
      throw new IllegalArgumentException("predicate census bound; counts retained");
    boolean valid=true,rawValid=true;int indexed=0,unindexed=0;
    var tree=board.searchTreeManager.getDefaultTree();
    for(Item item:board.getItems()){
      boolean one=board.searchTreeManager.validateEntries(item);int shapes=item.treeShapeCount(tree),tiles=item.tileShapeCount();
      var leaves=item.getSearchTreeEntries(tree);
      entries.add(map("id",item.getId(),"kind",item.getClass().getName(),"on_board",item.isOnTheBoard(),
        "shape_count",shapes,"tile_shape_count",tiles,"entry_count",leaves==null?null:leaves.length,"valid",one));
      boolean outline=item.getClass()==ComponentOutline.class&&shapes==0&&tiles==0&&leaves==null&&!one;
      boolean included=shapes>0&&shapes<=16384&&leaves!=null&&leaves.length==shapes&&one;
      valid&=item.isOnTheBoard()&&(outline||included);rawValid&=one;
      if(outline)unindexed++;else if(included)indexed++;
    }
    out.putAll(map("all_tree_entries_valid",rawValid,"search_tree_population_verified",valid,
      "indexed_items",indexed,"unindexed_zero_shape_outlines",unindexed));
    for(ConductionArea area:board.getConductionAreas()){
      List<Object> rows=new ArrayList<>();areas.add(map("id",area.getId(),"filled",area.getIsFilled(),
        "obstacle",area.getIsObstacle(),"routes",rows));
      for(Item route:routes){
        if(route.netCount()!=1)throw new IllegalArgumentException("ordinary route single-net scope");
        int net=route.getNetNumber(0);
        rows.add(map("id",route.getId(),"kind",route instanceof Via?"via":"trace","net",board.rules.nets.get(net).name,
          "same_net",area.sharesNet(route),"shares_layer",area.sharesLayer(route),
          "item_obstacle",area.isObstacle(route),"trace_obstacle",area.isTraceObstacle(net),"drillable",area.isDrillable(net)));
      }
    }
    int total=0;
    for(Trace trace:board.getTraces()){
      int count=trace.tileShapeCount();total+=count;
      var query=map("id",trace.getId(),"shape_count",count);queries.add(query);
      if(count<1||count>4096||total>16384||trace.netCount()!=1)throw new IllegalArgumentException("trace query bound");
      Set<Integer> overlap=new TreeSet<>(),blocking=new TreeSet<>();boolean clear=true;
      for(int i=0;i<count;i++){
        var shape=trace.getTileShape(i);
        clear&=board.checkTraceShape(shape,trace.getLayer(),new int[]{trace.getNetNumber(0)},trace.clearanceClassIndex(),null);
        var found=board.overlappingItemsWithClearance(shape,trace.getLayer(),new int[]{trace.getNetNumber(0)},trace.clearanceClassIndex());
        if(found.size()>4096)throw new IllegalArgumentException("trace overlap bound");
        for(Item item:found){overlap.add(item.getId());if(item.isTraceObstacle(trace.getNetNumber(0)))blocking.add(item.getId());}
      }
      query.putAll(map("tree_trace_check_clear",clear,"raw_overlap_ids",new ArrayList<>(overlap),"flag_filtered_overlap_ids",new ArrayList<>(blocking)));
    }
    out.put("trace_shape_count",total);
    if(!valid)throw new IllegalArgumentException("complete search-tree entry validation failed");
  }

  record Prepared(RoutingJob job,HeadlessBoardManager manager,RoutingBoard board) {}
  static Prepared prepare(byte[] raw,Map<String,Object> row,String[] argv)throws Exception{
    CliSettings cli=new CliSettings(argv);
    SettingsSource[] sources={new DefaultSettings(),new DsnFileSettings(new ByteArrayInputStream(raw),"original-mixed.dsn"),cli};
    RouterSettings settings=new SettingsMerger(sources).merge();RoutingJob job=new RoutingJob();job.routerSettings=settings;
    row.putAll(map("requested_obstacle",false,"argv",Arrays.asList(argv),"settings_before",MixedClassProbe.settings(settings),
      "input_sha256",AreaContactProbe.sha(raw)));
    HeadlessBoardManager manager=new HeadlessBoardManager(job);
    BoardReadResult loaded=manager.loadFromSpecctraDsn(new ByteArrayInputStream(raw),null,null);
    row.put("parser_result_class",loaded.getClass().getName());
    if(!(loaded instanceof BoardReadResult.Success success)||!(success.board() instanceof RoutingBoard board)||manager.getRoutingBoard()!=board)
      throw new IllegalArgumentException("successful identical manager RoutingBoard required");
    board.awaitPostLoad();row.putAll(map("post_load_awaited",true,"parser_warnings",success.warnings(),"settings_after",MixedClassProbe.settings(job.routerSettings)));
    var beforeLocal=map();row.put("state_before_local",beforeLocal);MixedClassProbe.observe(board,beforeLocal);
    var geometryBeforeLocal=map();row.put("route_geometry_before_local",geometryBeforeLocal);MixedClassProbe.routeGeometry(board,geometryBeforeLocal);
    MixedClassProbe.applyLocal250(board,row);
    var state=map();row.put("state",state);MixedClassProbe.observe(board,state);
    var geometry=map();row.put("route_geometry",geometry);MixedClassProbe.routeGeometry(board,geometry);
    List<ConductionArea> targets=targets(board,row);
    var before=map();row.put("predicates_before",before);predicates(board,before);
    List<Integer> changed=new ArrayList<>();for(ConductionArea area:targets)changed.add(area.getId());Collections.sort(changed);
    var audit=map("changed_area_ids",changed,"global_ignore_before",board.rules.getIgnoreConduction(),
      "global_ignore_after",null,"tree_refresh_completed",false,
      "apis",List.of("ConductionArea.setIsObstacle","BoardRules.setIgnoreConduction","SearchTreeManager.reinsertTreeItems","SearchTreeManager.validateEntries"));
    row.put("selective_override",audit);
    Exception failure=null;
    try{
      for(ConductionArea area:targets)area.setIsObstacle(true);
      board.rules.setIgnoreConduction(false);audit.put("global_ignore_after",board.rules.getIgnoreConduction());
      board.searchTreeManager.reinsertTreeItems();audit.put("tree_refresh_completed",true);
    }catch(Exception e){failure=e;}
    // Capture each post-mutation stage independently, preserving any earlier cause.
    var afterState=map();row.put("state_after_selective",afterState);
    try{MixedClassProbe.observe(board,afterState);}catch(Exception e){row.put("state_capture_error",MixedClassProbe.boundedError(e));if(failure==null)failure=e;}
    var afterGeometry=map();row.put("route_geometry_after_selective",afterGeometry);
    try{MixedClassProbe.routeGeometry(board,afterGeometry);}catch(Exception e){row.put("geometry_capture_error",MixedClassProbe.boundedError(e));if(failure==null)failure=e;}
    var after=map();row.put("predicates_after",after);
    try{predicates(board,after);}catch(Exception e){row.put("predicate_capture_error",MixedClassProbe.boundedError(e));if(failure==null)failure=e;}
    try{row.put("settings_after_selective",MixedClassProbe.settings(job.routerSettings));}
    catch(Exception e){row.put("settings_capture_error",MixedClassProbe.boundedError(e));if(failure==null)failure=e;}
    if(failure!=null)throw failure;
    row.put("status","observed");
    return new Prepared(job,manager,board);
  }
  static void run(byte[] raw,Map<String,Object> row)throws Exception{prepare(raw,row,ARGV);}

  public static void main(String[] args)throws Exception{
    if(args.length!=2)throw new IllegalArgumentException("input DSN and fresh output JSON required");
    Path input=Path.of(args[0]),output=Path.of(args[1]).toAbsolutePath();
    if(Files.isSymbolicLink(input)||!Files.isRegularFile(input,LinkOption.NOFOLLOW_LINKS)
        ||Files.isSymbolicLink(output.getParent())||!Files.isDirectory(output.getParent(),LinkOption.NOFOLLOW_LINKS)
        ||Files.exists(output,LinkOption.NOFOLLOW_LINKS))throw new IllegalArgumentException("regular input/fresh output required");
    byte[] raw;try(InputStream stream=Files.newInputStream(input,LinkOption.NOFOLLOW_LINKS)){raw=stream.readNBytes(INPUT_LIMIT+1);}
    if(raw.length==0||raw.length>INPUT_LIMIT)throw new IllegalArgumentException("input bound");
    var row=map("status","failed");var result=map("schema",1,"mode","selective_local250","routing_executed",false,"ses_executed",false,"case",row);
    try{run(raw,row);}catch(Exception e){row.put("error",MixedClassProbe.boundedError(e));}
    byte[] saved=(AreaContactProbe.json(result)+"\n").getBytes(java.nio.charset.StandardCharsets.UTF_8);
    if(saved.length>OUTPUT_LIMIT)throw new IllegalArgumentException("observation output bound");
    Files.write(output,saved,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
    if(!"observed".equals(row.get("status")))System.exit(2);
  }
}
