import app.freerouting.autoroute.pipeline.RoutingPipeline;
import app.freerouting.core.RoutingJob;
import app.freerouting.core.StoppableThread;
import app.freerouting.settings.RouterSettings;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Finite direct-pipeline diagnostic; its outputs require separate native checks. */
public final class SelectiveRoutingProbe {
  static final Gson JSON=new GsonBuilder().serializeNulls().create();
  static final String[] ARGV={"--router.autorouter.enabled=false","--router.optimizer.enabled=false",
    "--router.plane_as_obstacle=false","--router.fanout.enabled=false","--router.automatic_neckdown=false",
    "--router.neck_width_um=0","--router.autorouter.max_passes=30","--router.autorouter.algorithm=freerouting-router","--router.max_threads=1"};
  static Map<String,Object> map(Object... values){return MixedClassProbe.map(values);}
  static Map<String,Object> settings(RouterSettings s){
    // Gson omits transient fields, so bind the effective layer array separately.
    return map("configuration_json",JSON.toJson(s),"layers_json",JSON.toJson(s.layers),
      "board_specific_costs_applied",s.boardSpecificTraceCostsApplied);
  }
  static final class BoundedAction extends StoppableThread {
    final RoutingJob job;final long deadline;boolean deadlineReached=false,invoked=false,returned=false;
    BoundedAction(RoutingJob job,int seconds){this.job=job;deadline=System.nanoTime()+seconds*1_000_000_000L;}
    synchronized void deadline(){if(System.nanoTime()>=deadline){deadlineReached=true;requestStop();}}
    @Override public synchronized boolean isStopRequested(){deadline();return super.isStopRequested();}
    @Override public synchronized boolean isStopAutoRouterRequested(){deadline();return super.isStopAutoRouterRequested();}
    @Override protected void threadAction(){invoked=true;RoutingPipeline.createForHeadless(job).run();returned=true;}
  }
  static void save(Path output,Map<String,Object> value)throws IOException{
    byte[] raw=(AreaContactProbe.json(value)+"\n").getBytes(java.nio.charset.StandardCharsets.UTF_8);
    if(raw.length>SelectiveAreaProbe.OUTPUT_LIMIT)throw new IOException("observation output bound");
    Files.write(output,raw,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
  }
  static void run(byte[] raw,Path directory,Map<String,Object> result,boolean cancel)throws Exception{
    run(raw,directory,result,cancel,false);
  }
  static void run(byte[] raw,Path directory,Map<String,Object> result,boolean cancel,boolean adapter)throws Exception{
    run(raw,directory,result,cancel,adapter,false);
  }
  static void run(byte[] raw,Path directory,Map<String,Object> result,boolean cancel,boolean adapter,boolean lowVia)throws Exception{
    if(adapter&&cancel)throw new IllegalArgumentException("adapter-route is an explicit non-cancellation mode");
    if(lowVia&&!adapter)throw new IllegalArgumentException("low-via diagnostic requires corrected adapter");
    var row=map("status","failed");result.put("case",row);
    String[] argv=ARGV;
    if(lowVia){argv=Arrays.copyOf(ARGV,ARGV.length+2);argv[ARGV.length]="--router.scoring.via_costs=25";argv[ARGV.length+1]="--router.scoring.plane_via_costs=3";}
    var loaded=SelectiveAreaProbe.prepare(raw,row,argv,adapter);var job=loaded.job();var board=loaded.board();
    if(!board.getTraces().isEmpty()||!board.getVias().isEmpty())throw new IllegalArgumentException("zero ordinary seed copper required");
    RouterSettings s=job.routerSettings;
    if(s.getRunRouter()||s.getRunOptimizer()||s.isFanoutEnabled()||s.getAutomaticNeckdown()||s.getNeckWidthUm()!=0
        ||!RouterSettings.ALGORITHM_CURRENT.equals(s.autorouter.algorithm)||s.planeAsObstacle
        ||s.planeNets==null||s.planeNets.length!=0||s.getLayerCount()!=2||!s.getLayerActive(0)||!s.getLayerActive(1))
      throw new IllegalArgumentException("explicit completion-only settings differ");
    result.put("settings_loaded",settings(s));job.board=board;
    s.setRunRouter(true);result.put("settings_enabled",settings(s));
    var action=new BoundedAction(job,60);job.thread=action;if(cancel)action.requestStop();
    result.put("cancel_before_routing",cancel);
    save(directory.resolve("prepared.json"),result);
    Exception failure=null;long started=System.nanoTime();
    try{action.run();}catch(Exception e){failure=e;}
    boolean stopped=action.isStopRequested();
    result.put("routing",map("pipeline_invoked",action.invoked,"pipeline_returned",action.returned,
      "cooperative_deadline_seconds",60,"cooperative_deadline_reached",action.deadlineReached,
      "stop_requested",stopped,"wall_seconds",(System.nanoTime()-started)/1e9,
      "uses_final_job_board",job.board!=null,"board_object_replaced",job.board!=board));
    result.put("routing_executed",action.invoked);
    result.put("settings_final",settings(job.routerSettings));
    if(job.board==null)throw new IllegalArgumentException("pipeline returned no board");
    var finalState=map();result.put("final_state",finalState);
    try{MixedClassProbe.observe(job.board,finalState,adapter);}catch(Exception e){result.put("state_capture_error",MixedClassProbe.boundedError(e));if(failure==null)failure=e;}
    var finalGeometry=map();result.put("final_geometry",finalGeometry);
    try{MixedClassProbe.routeGeometry(job.board,finalGeometry,adapter);}catch(Exception e){result.put("geometry_capture_error",MixedClassProbe.boundedError(e));if(failure==null)failure=e;}
    var finalPredicates=map();result.put("final_predicates",finalPredicates);
    try{SelectiveAreaProbe.predicates(job.board,finalPredicates);}catch(Exception e){result.put("predicate_capture_error",MixedClassProbe.boundedError(e));if(failure==null)failure=e;}
    if(failure!=null)throw failure;
    // Manager replacement only assigns the selected board. Never reload/remerge settings.
    loaded.manager().replaceRoutingBoard(job.board);
    var writer=map();result.put("writer",writer);
    MixedClassProbe.writeSes(loaded.manager(),job.board,directory.resolve("raw.ses"),writer,adapter);
    result.put("ses_executed",true);result.put("status","observed");
  }
  public static void main(String[] args)throws Exception{
    if(args.length!=3||!(args[2].equals("route")||args[2].equals("cancel")||args[2].equals("adapter-route")||args[2].equals("adapter-low-via")))
      throw new IllegalArgumentException("input, fresh JSON, route|cancel|adapter-route|adapter-low-via required");
    Path input=Path.of(args[0]),output=Path.of(args[1]).toAbsolutePath();
    if(Files.isSymbolicLink(input)||!Files.isRegularFile(input,LinkOption.NOFOLLOW_LINKS)
        ||Files.isSymbolicLink(output.getParent())||!Files.isDirectory(output.getParent(),LinkOption.NOFOLLOW_LINKS)
        ||Files.exists(output,LinkOption.NOFOLLOW_LINKS))throw new IllegalArgumentException("regular input/fresh output required");
    byte[] raw;try(InputStream stream=Files.newInputStream(input)){raw=stream.readNBytes(SelectiveAreaProbe.INPUT_LIMIT+1);}
    if(raw.length==0||raw.length>SelectiveAreaProbe.INPUT_LIMIT)throw new IllegalArgumentException("input bound");
    var result=map("schema",1,"mode","selective_route_diagnostic","status","failed","routing_executed",false,"ses_executed",false);
    try{run(raw,output.getParent(),result,args[2].equals("cancel"),args[2].startsWith("adapter-"),args[2].equals("adapter-low-via"));}catch(Exception e){result.put("error",MixedClassProbe.boundedError(e));}
    save(output,result);if(!"observed".equals(result.get("status")))System.exit(2);
  }
}
