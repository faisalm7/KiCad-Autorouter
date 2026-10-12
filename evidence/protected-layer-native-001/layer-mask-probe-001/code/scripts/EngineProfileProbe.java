import com.google.gson.*;
import com.google.gson.annotations.SerializedName;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import java.io.*;
import java.security.MessageDigest;
import app.freerouting.board.facade.RoutingBoard;
import app.freerouting.io.BoardReadResult;
import app.freerouting.io.specctra.DsnReader;
import app.freerouting.settings.RouterSettings;
import app.freerouting.settings.SettingsSource;
import app.freerouting.settings.SettingsMerger;
import app.freerouting.settings.sources.DefaultSettings;
import app.freerouting.settings.sources.DsnFileSettings;
import app.freerouting.settings.sources.CliSettings;

/** Loads actual pinned JAR settings/parser classes; never creates a routing job. */
public class EngineProfileProbe {
  static final String[] CASES = {"source-all", "front-only", "back-only", "reversed-mapping-negative"};
  static final boolean[][] MASKS = {{true,true},{true,false},{false,true},{false,true}};
  static final String DSN_SHA = "53bcbd2c1978ce85ffaeeabdc28adf0c590d786de63345ccfc1e23b4b61eeb22";
  static Map<String,Object> map(Object... pairs) {
    Map<String,Object> row = new LinkedHashMap<>();
    for (int i=0;i<pairs.length;i+=2) row.put((String)pairs[i],pairs[i+1]);
    return row;
  }
  static String sha(byte[] raw) throws Exception {
    return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
  }
  static Map<String,Object> boardState(RoutingBoard board) {
    List<Object> layers=new ArrayList<>(), items=new ArrayList<>();
    int count=board.getItems().size();
    Map<String,Object> row=map("layer_count",board.getLayerCount(),"item_count",count,
      "pin_count",board.getPins().size(),"trace_count",board.getTraces().size(),"via_count",board.getVias().size());
    if (count>64 || board.getLayerCount()>8) { row.put("bounded",false); return row; }
    for (int i=0;i<board.getLayerCount();i++) layers.add(map("index",i,"name",board.layerStructure.layers[i].name,
      "signal",board.layerStructure.layers[i].isSignal));
    for (var item:board.getItems()) {
      List<Integer> nets=new ArrayList<>();
      if (item.netCount()>8) throw new IllegalArgumentException("item net census bound");
      for(int i=0;i<item.netCount();i++) nets.add(item.getNetNumber(i));
      items.add(map("id",item.getId(),"class",item.getClass().getName(),"first_layer",item.firstLayer(),
        "last_layer",item.lastLayer(),"nets",nets));
    }
    items.sort(Comparator.comparingInt(x -> (Integer)((Map<?,?>)x).get("id")));
    row.putAll(map("bounded",true,"layers",layers,"items",items)); return row;
  }
  static Map<String,Object> layerState(RouterSettings settings,RoutingBoard board,String name) {
    List<Object> flags=new ArrayList<>();
    Integer count=settings.layers==null ? null : settings.layers.length;
    if(count!=null && count<=8) for(int i=0;i<count;i++) flags.add(map("index",i,
      "raw_routable",settings.layers[i]==null ? null : settings.layers[i].routable,"active",settings.getLayerActive(i)));
    return map("name",name,"settings_layer_count",count,"flags",flags,"board",boardState(board),
      "autorouter_enabled",settings.getRunRouter(),"optimizer_enabled",settings.getRunOptimizer(),
      "ignored_netclasses",settings.autorouter.ignoreNetClasses);
  }
  static void layerProbe(JsonObject request,Gson gson,Path output) throws Exception {
    if(!request.keySet().equals(Set.of("schema","mode","dsn","dsn_sha256","cases")) ||
       !request.get("schema").toString().equals("1") || !request.get("dsn_sha256").getAsString().equals(DSN_SHA))
      throw new IllegalArgumentException("fixed layer request schema");
    Path input=Path.of(request.get("dsn").getAsString()); byte[] raw;
    if(Files.isSymbolicLink(input)||!Files.isRegularFile(input))throw new IllegalArgumentException("regular DSN required");
    try(InputStream stream=Files.newInputStream(input)){raw=stream.readNBytes(65537);}
    if(raw.length>65536||!sha(raw).equals(DSN_SHA))throw new IllegalArgumentException("exact owned DSN required");
    JsonArray cases=request.getAsJsonArray("cases");
    if(cases.size()!=4)throw new IllegalArgumentException("four cases required");
    List<Object> rows=new ArrayList<>();
    Map<String,Object> result=map("schema",1,"mode","import_only_layer_masks","input_sha256",sha(raw),
      "routing_executed",false,"native_executed",false,"layer_support_qualified",false,"cases",rows);
    for(int index=0;index<4;index++) {
      JsonObject declared=cases.get(index).getAsJsonObject();
      Map<String,Object> row=map("case",CASES[index],"status","failed"); rows.add(row);
      try {
        if(!declared.keySet().equals(Set.of("case","requested_names","mapping_order","mask","argv")) ||
           !declared.get("case").getAsString().equals(CASES[index]))throw new IllegalArgumentException("fixed case identity");
        String[] requested=index==0?new String[]{"F.Cu","B.Cu"}:new String[]{index==2?"B.Cu":"F.Cu"};
        String[] order=index==3?new String[]{"B.Cu","F.Cu"}:new String[]{"F.Cu","B.Cu"};
        if(!gson.toJsonTree(requested).equals(declared.get("requested_names")) ||
           !gson.toJsonTree(order).equals(declared.get("mapping_order")))throw new IllegalArgumentException("fixed named mapping required");
        JsonArray mask=declared.getAsJsonArray("mask");
        if(mask.size()!=2)throw new IllegalArgumentException("exact two Boolean mask required");
        for(int i=0;i<2;i++)if(!mask.get(i).isJsonPrimitive()||!mask.get(i).getAsJsonPrimitive().isBoolean()||
          mask.get(i).getAsBoolean()!=MASKS[index][i])throw new IllegalArgumentException("fixed Boolean mask differs");
        String[] argv={"--router.autorouter.enabled=false","--router.optimizer.enabled=false",
          "--router.layers.routable="+MASKS[index][0]+","+MASKS[index][1]};
        if(!gson.toJsonTree(argv).equals(declared.get("argv")))throw new IllegalArgumentException("exact CLI request required");
        CliSettings cli=new CliSettings(argv);
        SettingsSource[] sources={new DefaultSettings(),new DsnFileSettings(new ByteArrayInputStream(raw),"fixture.dsn"),cli};
        List<Object> sourceRows=new ArrayList<>();
        for(SettingsSource source:sources)sourceRows.add(map("class",source.getClass().getName(),"name",source.getSourceName(),"priority",source.getPriority()));
        RouterSettings settings=new SettingsMerger(sources).merge();
        row.putAll(map("argv",argv,"parsed_cli_arguments",cli.getParsedArguments(),"sources",sourceRows,"input_sha256",sha(raw)));
        BoardReadResult imported=DsnReader.readBoard(new ByteArrayInputStream(raw),null,null);
        row.put("parser_result_class",imported.getClass().getName());
        if(!(imported instanceof BoardReadResult.Success success))throw new IllegalArgumentException("DSN import did not succeed");
        row.put("parser_warnings",success.warnings());
        if(!(success.board() instanceof RoutingBoard board))throw new IllegalArgumentException("RoutingBoard required");
        board.awaitPostLoad(); List<Object> states=new ArrayList<>(); row.put("states",states);
        states.add(layerState(settings,board,"before_init"));
        settings.applyBoardSpecificOptimizations(board); settings.applyNetClassExclusions(board);
        states.add(layerState(settings,board,"after_init"));
        settings.applyBoardSpecificOptimizationsIfNeeded(board);
        states.add(layerState(settings,board,"after_if_needed")); row.put("status","observed");
      }catch(Exception ex){row.put("error",ex.getClass().getName()+": "+ex.getMessage());}
    }
    byte[] saved=(gson.toJson(result)+"\n").getBytes(java.nio.charset.StandardCharsets.UTF_8);
    if(saved.length>262144)throw new IllegalArgumentException("bounded observation required");
    Files.write(output,saved,StandardOpenOption.CREATE_NEW);
  }
  static Object field(Object object, String name) throws Exception {
    for (Field candidate : object.getClass().getFields()) {
      SerializedName serialized = candidate.getAnnotation(SerializedName.class);
      if (candidate.getName().equals(name) || (serialized != null && serialized.value().equals(name))) {
        return candidate.get(object);
      }
    }
    throw new NoSuchFieldException(object.getClass().getName() + ":" + name);
  }
  static Object path(Object object, String name) throws Exception {
    for (String part : name.replaceFirst("^router\\.", "").split("\\.")) object = field(object, part);
    return object;
  }
  public static void main(String[] args) throws Exception {
    Gson gson = new GsonBuilder().serializeNulls().setPrettyPrinting().create();
    if(args.length==3) {
      if(!args[2].equals("--layer-mask"))throw new IllegalArgumentException("unknown probe mode");
      byte[] raw;try(InputStream stream=Files.newInputStream(Path.of(args[0]))){raw=stream.readNBytes(16385);}
      if(raw.length>16384)throw new IllegalArgumentException("request bound");
      JsonObject request=JsonParser.parseString(new String(raw,java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
      if(!request.get("mode").getAsString().equals("import_only_layer_masks"))throw new IllegalArgumentException("unknown request mode");
      layerProbe(request,gson,Path.of(args[1])); return;
    }
    if(args.length!=2)throw new IllegalArgumentException("request and output paths required");
    JsonObject request = JsonParser.parseString(Files.readString(Path.of(args[0]))).getAsJsonObject();
    Class<?> cliClass = Class.forName("app.freerouting.settings.sources.CliSettings");
    Class<?> defaultsClass = Class.forName("app.freerouting.settings.sources.DefaultSettings");
    Class<?> sourceClass = Class.forName("app.freerouting.settings.SettingsSource");
    Class<?> mergerClass = Class.forName("app.freerouting.settings.SettingsMerger");
    Class<?> textClass = Class.forName("app.freerouting.util.TextManager");
    Method parseTime = textClass.getMethod("parseTimespanString", String.class);
    Map<String,Object> result = new LinkedHashMap<>();
    result.put("execution", "actual pinned JAR settings and parser only; no routing job, DSN load, or native engine");
    result.put("jar_code_source", cliClass.getProtectionDomain().getCodeSource().getLocation().toString());
    Map<String,Object> timespans = new LinkedHashMap<>();
    for (JsonElement value : request.getAsJsonArray("timespans")) timespans.put(value.getAsString(), parseTime.invoke(null, value.getAsString()));
    result.put("timespans_to_seconds", timespans);
    List<Object> profiles = new ArrayList<>();
    for (JsonElement element : request.getAsJsonArray("profiles")) {
      JsonObject profile = element.getAsJsonObject();
      String[] flags = gson.fromJson(profile.get("argv"), String[].class);
      Object cli = cliClass.getConstructor(String[].class).newInstance((Object) flags);
      Object sources = Array.newInstance(sourceClass, 2);
      Array.set(sources, 0, defaultsClass.getConstructor().newInstance());
      Array.set(sources, 1, cli);
      Object merger = mergerClass.getConstructor(sources.getClass()).newInstance(sources);
      Object settings = mergerClass.getMethod("merge").invoke(merger);
      Map<String,Object> output = new LinkedHashMap<>();
      output.put("name", profile.get("name").getAsString());
      output.put("argv", flags);
      output.put("parsed_cli_arguments", cliClass.getMethod("getParsedArguments").invoke(cli));
      Map<String,Object> effective = new LinkedHashMap<>();
      for (String flag : flags) {
        if (!flag.startsWith("--router.")) continue;
        String property = flag.substring(2, flag.indexOf('='));
        effective.put(property, path(settings, property));
      }
      output.put("effective_requested_settings", effective);
      output.put("autorouter_enabled", settings.getClass().getMethod("getRunRouter").invoke(settings));
      output.put("optimizer_enabled", settings.getClass().getMethod("getRunOptimizer").invoke(settings));
      output.put("effective_job_timeout_seconds", parseTime.invoke(null, (String)path(settings,"router.job_timeout")));
      output.put("effective_optimizer_timeout_seconds", parseTime.invoke(null, (String)path(settings,"router.optimizer.timeout")));
      profiles.add(output);
    }
    result.put("profiles", profiles);
    Files.writeString(Path.of(args[1]), gson.toJson(result) + "\n", StandardOpenOption.CREATE_NEW);
  }
}
