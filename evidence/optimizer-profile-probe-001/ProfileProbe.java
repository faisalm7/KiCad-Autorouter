import com.google.gson.*;
import com.google.gson.annotations.SerializedName;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;

/** Loads actual pinned JAR settings/parser classes; never creates a routing job. */
public class ProfileProbe {
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
