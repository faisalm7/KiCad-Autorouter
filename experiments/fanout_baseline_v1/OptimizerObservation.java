// SPDX-License-Identifier: GPL-3.0-or-later
// Owned source-file getter diagnostic; not a routing job. UNEXECUTED.
import app.freerouting.board.model.structure.AngleRestriction;
import app.freerouting.io.BoardReadResult;
import app.freerouting.io.specctra.DsnReader;
import app.freerouting.settings.SettingsMerger;
import app.freerouting.settings.sources.DefaultSettings;
import app.freerouting.settings.sources.CliSettings;
import app.freerouting.settings.sources.DsnFileSettings;
import com.google.gson.Gson;
import java.io.ByteArrayInputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.LinkedHashMap;

public final class OptimizerObservation {
  public static void main(String[] args) throws Exception {
    if (args.length < 2) throw new IllegalArgumentException("actual.dsn actual --router.* arguments");
    byte[] raw;
    try (var input = Files.newInputStream(Path.of(args[0]))) { raw = input.readNBytes(4*1024*1024+1); }
    if (raw.length == 0 || raw.length > 4*1024*1024) throw new IllegalArgumentException("bounded DSN required");
    String[] flags = Arrays.copyOfRange(args,1,args.length);
    for (String flag : flags) if (!flag.startsWith("--router.") || !flag.contains("="))
      throw new IllegalArgumentException("only exact retained router settings arguments");
    var loaded = DsnReader.readBoard(new ByteArrayInputStream(raw),null,null);
    if (!(loaded instanceof BoardReadResult.Success success) || success.board()==null || !success.warnings().isEmpty())
      throw new IllegalStateException("full DSN load failed or warned: "+loaded);
    var cli = new CliSettings(flags);
    var settings = new SettingsMerger(new DefaultSettings(),new DsnFileSettings(new ByteArrayInputStream(raw),Path.of(args[0]).getFileName().toString()),cli).merge();
    var actualAngle = success.board().rules.getTraceAngleRestriction();
    if (actualAngle != AngleRestriction.NONE || settings.getRunOptimizer() || settings.getRunFanout())
      throw new IllegalStateException("effective angle/optimizer/fanout differs");
    if (!"false".equals(cli.getParsedArguments().get("router.optimizer.enabled"))
        || !"false".equals(cli.getParsedArguments().get("router.fanout.enabled")))
      throw new IllegalStateException("explicit disabled settings not parsed");
    var jar = Path.of(CliSettings.class.getProtectionDomain().getCodeSource().getLocation().toURI());
    var digest = MessageDigest.getInstance("SHA-256");
    long total=0;
    try (var input=Files.newInputStream(jar)) {
      byte[] block=new byte[1024*1024];int count;
      while ((count=input.read(block))!=-1) { total+=count;if(total>128L*1024*1024)throw new IllegalStateException("bounded JAR required");digest.update(block,0,count); }
    }
    var output=new LinkedHashMap<String,Object>();
    output.put("diagnostic_only",true);output.put("parse_warnings",new String[0]);
    output.put("input_sha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    output.put("jar_sha256",HexFormat.of().formatHex(digest.digest()));output.put("loaded_angle",actualAngle.toString());
    output.put("optimizer_enabled",settings.getRunOptimizer());output.put("fanout_enabled",settings.getRunFanout());
    output.put("actual_settings_argv",flags);output.put("parsed_cli_arguments",cli.getParsedArguments());
    output.put("settings_sources",new String[]{"pinned defaults","actual DSN","actual CLI"});
    System.out.println(new Gson().toJson(output));
  }
}
