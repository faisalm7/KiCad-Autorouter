// SPDX-License-Identifier: GPL-3.0-or-later
import app.freerouting.io.BoardReadResult;
import app.freerouting.management.HeadlessBoardManager;
import app.freerouting.core.RoutingJob;
import app.freerouting.settings.*;
import app.freerouting.settings.sources.*;
import app.freerouting.board.facade.RoutingBoard;
import app.freerouting.board.model.items.ComponentOutline;
import app.freerouting.rules.DefaultItemClearanceClasses.ItemClass;
import com.google.gson.Gson;
import java.io.ByteArrayInputStream;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Prospective import-only extension of the retained CellScanEdgeManagerProbe.
 * Never runs routing/optimization. One prior revision failed closed after four
 * raw loads; this exact ComponentOutline instrumentation revision is unrun.
 */
public final class NamedEdgeManagerProbe {
  static final Gson JSON = new Gson();
  static final List<String> CASES = List.of("literal300", "parent300", "underscore300", "literal250");
  static final int MAX_CLASSES = 12;
  static final Set<String> ITEM_ENUM = Set.of("NONE", "TRACE", "VIA", "PIN", "SMD", "AREA");

  static void reached(int index, app.freerouting.rules.ClearanceMatrix matrix,
                      String source, SortedMap<String, Object> observations,
                      boolean eagerDiagnostic, List<Map<String, Object>> violations) {
    if (index < 0 || index >= matrix.getClassCount())
      throw new IllegalArgumentException("invalid clearance class index: " + source);
    String name = matrix.getName(index);
    if (observations.put(source, Map.of("index", index, "name", String.valueOf(name))) != null)
      throw new IllegalArgumentException("duplicate reachable assignment source");
    if (index == 0 && "null".equals(name)) {
      if (!eagerDiagnostic)
        throw new IllegalArgumentException("reachable Class0 clearance class: " + source);
      violations.add(Map.of("code", "reachable_class0", "source", source, "index", index, "name", name));
      return; // Only this explicit known eager-case semantic violation survives.
    }
    if (name == null || name.isBlank() || name.equals("null") || name.equals("board_edge") || name.equals("kicadedge"))
      throw new IllegalArgumentException("reachable unnamed/outline clearance class: " + source);
  }

  record Snapshot(Map<String, Object> observation,
                  SortedMap<String, SortedMap<String, List<Double>>> matrix,
                  SortedMap<String, Object> netClasses,
                  SortedMap<String, Object> vias,
                  SortedMap<String, Integer> items,
                  String outline, int layers) {}

  static Snapshot load(Path path) throws Exception { return load(path, false); }

  static Snapshot load(Path path, boolean eagerDiagnostic) throws Exception {
    if (Files.isSymbolicLink(path) || !Files.isRegularFile(path) || Files.size(path) > 1024 * 1024)
      throw new IllegalArgumentException("bounded real DSN input required");
    byte[] raw = Files.readAllBytes(path);
    SettingsSource[] sources = {
      new DefaultSettings(),
      new DsnFileSettings(new ByteArrayInputStream(raw), path.toString()),
      new CliSettings(new String[]{"--router.autorouter.enabled=false", "--router.optimizer.enabled=false"})
    };
    var job = new RoutingJob(); job.routerSettings = new SettingsMerger(sources).merge();
    var manager = new HeadlessBoardManager(job);
    var parsed = manager.loadFromSpecctraDsn(new ByteArrayInputStream(raw), null, null);
    if (!(parsed instanceof BoardReadResult.Success success) || !(success.board() instanceof RoutingBoard board))
      throw new IllegalArgumentException("full manager import failed: " + parsed);
    board.awaitPostLoad();
    var m = board.rules.clearanceMatrix; var ct = board.communication.coordinateTransform;
    int layers = board.layerStructure.layers.length;
    if (board.getOutline() == null || m.getClassCount() > MAX_CLASSES || (layers != 2 && layers != 4)
        || board.rules.netClasses.count() > 4 || board.rules.viaInfos.count() > 16 || board.getItems().size() > 1024)
      throw new IllegalArgumentException("fixed small class/layer/item scope exceeded");
    String outline = m.getName(board.getOutline().clearanceClassIndex());
    if (!"null".equals(m.getName(0))) throw new IllegalArgumentException("exact Class0 identity required");
    var reached = new TreeMap<String, Object>();
    var violations = new ArrayList<Map<String, Object>>();
    var displayOutlines = new TreeMap<String, Object>();
    var indices = new TreeMap<String, Integer>();
    var enumNames = new TreeSet<String>();
    for (ItemClass kind : ItemClass.values()) enumNames.add(kind.name());
    if (enumNames.size() != ItemClass.values().length || !enumNames.equals(ITEM_ENUM))
      throw new IllegalArgumentException("unknown routed item-default enum census");
    var matrix = new TreeMap<String, SortedMap<String, List<Double>>>();
    for (int i = 0; i < m.getClassCount(); i++) {
      indices.put(m.getName(i), i);
      var row = new TreeMap<String, List<Double>>();
      for (int j = 0; j < m.getClassCount(); j++) {
        var values = new ArrayList<Double>();
        for (int layer = 0; layer < layers; layer++) {
          double value = ct.boardToDsn(m.getValue(i, j, layer, false));
          if (!Double.isFinite(value) || value < 0) throw new IllegalArgumentException("nonfinite/negative matrix");
          values.add(value);
        }
        if (row.put(m.getName(j), values) != null) throw new IllegalArgumentException("duplicate matrix name");
      }
      if (matrix.put(m.getName(i), row) != null) throw new IllegalArgumentException("duplicate matrix name");
    }
    var netClasses = new TreeMap<String, Object>();
    for (int i = 0; i < board.rules.netClasses.count(); i++) {
      var cls = board.rules.netClasses.get(i); var defaults = new TreeMap<String, String>();
      reached(cls.getTraceClearanceClass(), m, "netclass:" + cls.getName() + ":trace", reached, eagerDiagnostic, violations);
      for (ItemClass kind : ItemClass.values()) {
        int index = cls.defaultItemClearanceClasses.get(kind);
        if (index < 0 || index >= m.getClassCount())
          throw new IllegalArgumentException("invalid explicit item-default clearance index");
        if (!kind.name().equals("NONE"))
          reached(index, m, "netclass:" + cls.getName() + ":default:" + kind.name(), reached, eagerDiagnostic, violations);
        defaults.put(kind.name(), m.getName(index));
      }
      var viaRule = new ArrayList<String>();
      if (cls.getViaRule() != null)
        for (int j = 0; j < cls.getViaRule().viaCount(); j++) viaRule.add(cls.getViaRule().getVia(j).getName());
      var nets = new TreeSet<String>();
      for (int j = 1; j <= board.rules.nets.maxNetNumber(); j++) {
        var net = board.rules.nets.get(j);
        if (net != null && net.getNetClass() == cls) nets.add(net.name);
      }
      if (netClasses.put(cls.getName(), Map.of("trace_clearance_class", m.getName(cls.getTraceClearanceClass()),
          "default_item_classes", defaults, "via_rule", viaRule, "member_nets", nets)) != null)
        throw new IllegalArgumentException("duplicate netclass name");
    }
    var vias = new TreeMap<String, Object>();
    for (int i = 0; i < board.rules.viaInfos.count(); i++) {
      var via = board.rules.viaInfos.get(i);
      reached(via.getClearanceClassIndex(), m, "via-info:" + via.getName(), reached, eagerDiagnostic, violations);
      if (vias.put(via.getName(), Map.of("clearance_class", m.getName(via.getClearanceClassIndex()),
          "padstack", via.getPadstack().name, "attach_smd_allowed", via.attachSmdAllowed())) != null)
        throw new IllegalArgumentException("duplicate via info");
    }
    // Census actual imported item assignments by kind/net identity/class. Exact
    // geometry/terminal identity remains the separate original-DSN/Native proof.
    var items = new TreeMap<String, Integer>();
    int itemIndex = 0;
    for (var item : board.getItems()) {
      if (item == board.getOutline()) continue;
      String identity = "item:" + itemIndex++ + ":" + item.getClass().getName();
      if (item.getClass() == ComponentOutline.class) {
        // Exact pinned class: empty nets, zero search-tree shapes, Item overload
        // always false. Do not extend this exception to subclasses, copper,
        // obstacle areas or inherited isObstacle(net)/isTraceObstacle(net).
        var display = (ComponentOutline)item;
        if (item.netCount() != 0 || item.clearanceClassIndex() != 0 || !"null".equals(m.getName(0))
            || item.tileShapeCount() != 0 || item.isObstacle(item))
          throw new IllegalArgumentException("ComponentOutline display-only predicates differ");
        displayOutlines.put(identity, Map.of("index", 0, "name", m.getName(0), "net_count", item.netCount(),
            "tile_shape_count", item.tileShapeCount(), "obstacle_Item_overload", item.isObstacle(item),
            "is_front", display.isFront(), "is_courtyard", display.isCourtyard(),
            "is_fabrication", display.isFabrication(), "is_closed", display.isClosed()));
      } else {
        reached(item.clearanceClassIndex(), m, identity, reached, eagerDiagnostic, violations);
      }
      var nets = new TreeSet<String>();
      for (int i = 0; i < item.netCount(); i++) {
        var net = board.rules.nets.get(item.getNetNumber(i));
        if (net == null) throw new IllegalArgumentException("unknown imported item net");
        nets.add(net.name);
      }
      Object displayFlags = item.getClass() == ComponentOutline.class
          ? List.of(((ComponentOutline)item).isFront(), ((ComponentOutline)item).isCourtyard(),
                    ((ComponentOutline)item).isFabrication(), ((ComponentOutline)item).isClosed()) : List.of();
      String key = JSON.toJson(List.of(item.getClass().getName(), nets, m.getName(item.clearanceClassIndex()), displayFlags));
      items.merge(key, 1, Integer::sum);
    }
    var observation = new LinkedHashMap<String, Object>();
    observation.put("input_sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
    observation.put("warnings", success.warnings());
    observation.put("configured_edge_um", job.routerSettings.copperToEdgeClearanceUm);
    observation.put("outline_class", outline); observation.put("layers", layers);
    observation.put("matrix_um", matrix); observation.put("matrix_class_indices", indices);
    observation.put("actual_nonoutline_trace_defaults_via_reachability", reached);
    observation.put("display_only_ComponentOutline_raw_reachability", displayOutlines);
    observation.put("known_reachable_class0_violations", violations);
    observation.put("eager_diagnostic_only", eagerDiagnostic);
    observation.put("actual_full_manager_load_completed", true);
    observation.put("item_default_enum_names", enumNames);
    observation.put("class0_reachable_in_routed_scope", !violations.isEmpty());
    observation.put("none_enum_is_explicit_nonroutable_default", true);
    observation.put("net_classes", netClasses);
    observation.put("via_infos", vias); observation.put("item_assignment_census", items);
    return new Snapshot(observation, matrix, netClasses, vias, items, outline, layers);
  }

  static SortedMap<String, SortedMap<String, List<Double>>> ordinary(Snapshot snapshot) {
    var result = new TreeMap<String, SortedMap<String, List<Double>>>();
    for (var entry : snapshot.matrix.entrySet()) {
      if (entry.getKey().equals(snapshot.outline)) continue;
      var row = new TreeMap<>(entry.getValue()); row.remove(snapshot.outline);
      result.put(entry.getKey(), row);
    }
    return result;
  }

  static Map<String, Boolean> compare(Snapshot raw, Snapshot changed, double requested, int layers) {
    boolean symmetric = true, edge = true, rawEdge = true;
    for (Snapshot snapshot : List.of(raw, changed))
      for (var row : snapshot.matrix.entrySet())
        for (var column : row.getValue().entrySet())
          symmetric &= column.getValue().equals(snapshot.matrix.get(column.getKey()).get(row.getKey()));
    for (var row : changed.matrix.entrySet()) {
      if (row.getKey().equals("null")) continue; // load() has rejected every actual routed Class0 assignment.
      for (double value : row.getValue().get(changed.outline)) edge &= Double.compare(value, requested) == 0;
    }
    for (var row : raw.matrix.entrySet()) {
      if (row.getKey().equals("null")) continue;
      for (double value : row.getValue().get(raw.outline)) rawEdge &= Double.compare(value, 250.0) == 0;
    }
    return Map.of("same_exact_nonedge_matrix_all_layers", ordinary(raw).equals(ordinary(changed)),
        "same_trace_and_default_item_classes_and_via_rules", raw.netClasses.equals(changed.netClasses),
        "same_via_info_overrides", raw.vias.equals(changed.vias),
        "same_imported_item_assignment_census", raw.items.equals(changed.items),
        "symmetric_all_pairs_all_layers", symmetric,
        "exact_source_edge_all_nonzero_classes_all_layers", edge,
        "actual_raw_guessed_edge250_all_nonzero_classes_all_layers", rawEdge,
        "full_manager_guessed250_raw_and_explicit_corrected", raw.outline.equals("board_edge")
          && changed.outline.equals("kicadedge")
          && Objects.equals(raw.observation.get("configured_edge_um"), 250.0)
          && Objects.equals(changed.observation.get("configured_edge_um"), 250.0),
        "exact_layer_population", raw.layers == layers && changed.layers == layers,
        "same_import_warnings", Objects.equals(raw.observation.get("warnings"), changed.observation.get("warnings")));
  }

  public static void main(String[] args) throws Exception {
    if (args.length != 2) throw new IllegalArgumentException("input-directory fresh-output-json");
    Path directory = Path.of(args[0]), output = Path.of(args[1]);
    if (Files.isSymbolicLink(directory) || !Files.isDirectory(directory) || Files.exists(output))
      throw new IllegalArgumentException("real input directory and fresh output required");
    var rows = new ArrayList<Object>(); boolean passed = true;
    for (String name : CASES) {
      try {
        var raw = load(directory.resolve(name + "-raw.dsn"));
        var changed = load(directory.resolve(name + "-corrected.dsn"));
        var checks = compare(raw, changed, name.equals("literal250") ? 250.0 : 300.0, name.equals("parent300") ? 4 : 2);
        boolean current = checks.values().stream().allMatch(Boolean::booleanValue);
        rows.add(Map.of("case", name, "raw", raw.observation, "corrected", changed.observation,
                        "checks", checks, "matrix_checks_passed", current));
        passed &= current;
        if (name.equals("literal300")) {
          var eager = load(directory.resolve("literal300-eager-control.dsn"), true);
          var negative = compare(raw, eager, 300.0, 2);
          boolean class0Violation = !((List<?>)eager.observation.get("known_reachable_class0_violations")).isEmpty();
          boolean detected = class0Violation || !negative.get("same_exact_nonedge_matrix_all_layers")
              || !negative.get("same_trace_and_default_item_classes_and_via_rules")
              || !negative.get("same_via_info_overrides") || !negative.get("same_imported_item_assignment_census");
          rows.add(Map.of("case", "eager_named_row_negative", "observation", eager.observation,
                          "checks", negative, "known_class0_assignment_violation", class0Violation,
                          "initialization_change_detected", detected));
          passed &= detected;
        }
      } catch (Exception failure) {
        rows.add(Map.of("case", name, "matrix_checks_passed", false,
                        "error", failure.getClass().getName() + ": " + failure.getMessage()));
        passed = false;
      }
    }
    byte[] result = (JSON.toJson(Map.of("schema", 1, "kind", "named-edge-full-manager-observation",
        "routing_executed", false, "native_executed", false, "production_admitted", false,
        "matrix_checks_passed", passed, "cases", rows)) + "\n").getBytes(java.nio.charset.StandardCharsets.UTF_8);
    if (result.length > 512 * 1024) throw new IllegalArgumentException("observation output bound exceeded");
    Files.write(output, result, StandardOpenOption.CREATE_NEW);
    if (!passed) throw new IllegalStateException("named edge importer controls failed; observations retained");
  }
}
