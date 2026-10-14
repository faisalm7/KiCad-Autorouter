import app.freerouting.io.BoardReadResult;
import app.freerouting.management.HeadlessBoardManager;
import app.freerouting.core.RoutingJob;
import app.freerouting.settings.*;
import app.freerouting.settings.sources.*;
import app.freerouting.board.facade.RoutingBoard;
import com.google.gson.Gson;
import java.io.ByteArrayInputStream;
import java.nio.file.*;
import java.util.*;

/** Bounded import-only observation of the actual pinned engine; never routes. */
public final class CellScanEdgeManagerProbe {
  public static void main(String[] args) throws Exception {
    if(args.length!=2)throw new IllegalArgumentException("input-directory output-json");
    Path dir=Path.of(args[0]),out=Path.of(args[1]);
    if(Files.exists(out))throw new IllegalArgumentException("fresh output required");
    List<Object> rows=new ArrayList<>();
    for(String name:List.of("raw","allclasses")){
      Path input=dir.resolve(name+".dsn");
      if(Files.isSymbolicLink(input)||!Files.isRegularFile(input)||Files.size(input)>1024*1024)throw new IllegalArgumentException("input bound");
      byte[] raw=Files.readAllBytes(input);
      SettingsSource[] sources={new DefaultSettings(),new DsnFileSettings(new ByteArrayInputStream(raw),input.toString()),new CliSettings(new String[]{"--router.autorouter.enabled=false","--router.optimizer.enabled=false"})};
      var job=new RoutingJob();job.routerSettings=new SettingsMerger(sources).merge();
      var manager=new HeadlessBoardManager(job);var parsed=manager.loadFromSpecctraDsn(new ByteArrayInputStream(raw),null,null);
      if(!(parsed instanceof BoardReadResult.Success success)||!(success.board() instanceof RoutingBoard board))throw new IllegalArgumentException("import failed "+parsed);
      board.awaitPostLoad();
      var m=board.rules.clearanceMatrix;var ct=board.communication.coordinateTransform;
      var outline=board.getOutline();if(outline==null||m.getClassCount()>20)throw new IllegalArgumentException("outline/class bound");
      int edge=outline.clearanceClassIndex();
      List<Object> classes=new ArrayList<>();
      for(int i=0;i<m.getClassCount();i++){
        List<Object> gaps=new ArrayList<>();
        for(int layer=0;layer<board.layerStructure.layers.length;layer++)gaps.add(ct.boardToDsn(m.getValue(i,edge,layer,false)));
        List<Object> ordinary=new ArrayList<>();
        for(int j=1;j<m.getClassCount();j++)if(j!=edge)ordinary.add(Map.of("other",m.getName(j),"gap_um",ct.boardToDsn(m.getValue(i,j,0,false))));
        classes.add(Map.of("ordinary_pairs",ordinary,"name",m.getName(i),"index",i,"outline_gap_um",gaps));
      }
      rows.add(Map.of("case",name,"warnings",success.warnings(),"outline_class_index",edge,"outline_class_name",m.getName(edge),"classes",classes,
        "configured_copper_to_edge_clearance_um",job.routerSettings.copperToEdgeClearanceUm,"input_sha256",HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(raw))));
    }
    byte[] bytes=(new Gson().toJson(Map.of("schema",1,"routing_executed",false,"cases",rows))+"\n").getBytes(java.nio.charset.StandardCharsets.UTF_8);
    if(bytes.length>16384)throw new IllegalArgumentException("output bound");Files.write(out,bytes,StandardOpenOption.CREATE_NEW);
  }
}
