import app.freerouting.core.library.Padstack;
import app.freerouting.core.library.Padstacks;
import app.freerouting.geometry.planar.ConvexShape;
import app.freerouting.geometry.planar.IntPoint;
import app.freerouting.geometry.planar.IntBox;
import app.freerouting.geometry.planar.FloatPoint;
import app.freerouting.geometry.planar.PolylineShape;
import app.freerouting.io.CoordinateTransform;
import app.freerouting.io.specctra.parser.Keyword;
import app.freerouting.io.specctra.parser.Library;
import app.freerouting.io.specctra.parser.SpecctraDsnStreamReader;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Owned DSN padstack scopes only. No RoutingBoard, router, native CAD or renderer. */
public final class PadstackImportProbe {
    static final String[] CASES = {"convex", "concave", "sameAB", "sameBA", "distinct"};
    static final String[] LAYERS = {"F.Cu", "B.Cu"};
    static final String[] POINT_NAMES = {"origin", "notch", "a", "b"};
    static final int[][] POINTS = {{0, 0}, {-600, 0}, {-750, -750}, {750, 750}};

    static Map<String,Object> map(Object... pairs) {
        Map<String,Object> m = new LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) m.put((String)pairs[i], pairs[i+1]);
        return m;
    }

    static String json(Object v) {
        if (v == null) return "null";
        if (v instanceof String s) {
            StringBuilder b = new StringBuilder("\"");
            for (char c : s.toCharArray()) {
                if (c == '"' || c == '\\') b.append('\\').append(c);
                else if (c < 32) b.append(String.format("\\u%04x", (int)c));
                else b.append(c);
            }
            return b.append('"').toString();
        }
        if (v instanceof Boolean) return v.toString();
        if (v instanceof Number n) {
            if (!Double.isFinite(n.doubleValue())) throw new IllegalArgumentException("nonfinite observation");
            return v.toString();
        }
        if (v instanceof Map<?,?> m) {
            List<String> entries = new ArrayList<>();
            for (var e : m.entrySet()) entries.add(json(e.getKey()) + ":" + json(e.getValue()));
            return "{" + String.join(",", entries) + "}";
        }
        if (v instanceof List<?> l) {
            List<String> items = new ArrayList<>();
            for (Object item : l) items.add(json(item));
            return "[" + String.join(",", items) + "]";
        }
        throw new IllegalArgumentException("unexpected JSON type");
    }

    static String sha(byte[] raw) throws Exception {
        return java.util.HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }

    static Object observe(ConvexShape shape) {
        if (shape == null) return null;
        if (!(shape instanceof PolylineShape poly)) throw new IllegalArgumentException("nonpolygonal imported shape");
        int count = poly.borderLineCount();
        if (count < 3 || count > 32) throw new IllegalArgumentException("corner count outside probe bound");
        List<Object> corners = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            if (!poly.cornerIsBounded(i)) throw new IllegalArgumentException("unbounded corner");
            FloatPoint p = poly.cornerApprox(i);
            corners.add(List.of(p.x, p.y));
        }
        IntBox box = shape.boundingBox();
        Map<String,Object> membership = new LinkedHashMap<>();
        for (int i = 0; i < POINTS.length; i++)
            membership.put(POINT_NAMES[i], shape.containsInside(new IntPoint(POINTS[i][0], POINTS[i][1])));
        return map("class", shape.getClass().getName(), "area_um2", shape.area(),
                   "bounds_um", List.of(box.ll.x, box.ll.y, box.ur.x, box.ur.y),
                   "corners_um", corners, "strict_inside", membership);
    }

    static Map<String,Object> runCase(Path input, String name) throws Exception {
        if (Files.isSymbolicLink(input) || !Files.isRegularFile(input)) throw new IllegalArgumentException("regular input required");
        byte[] raw;
        try (InputStream stream = Files.newInputStream(input)) { raw = stream.readNBytes(16385); }
        if (raw.length == 0 || raw.length > 16384) throw new IllegalArgumentException("input size bound");
        var boardLayers = new app.freerouting.board.model.structure.LayerStructure(
            new app.freerouting.board.model.structure.Layer[]{
                new app.freerouting.board.model.structure.Layer("F.Cu", true),
                new app.freerouting.board.model.structure.Layer("B.Cu", true)});
        var layers = new app.freerouting.io.specctra.parser.LayerStructure(boardLayers);
        Padstacks stacks = new Padstacks(boardLayers);
        CoordinateTransform transform = new CoordinateTransform(1.0, 0.0, 0.0);
        if (transform.dsnToBoard(1.0) != 1.0 || transform.dsnToBoard(-600.0) != -600.0)
            throw new IllegalArgumentException("unexpected coordinate scale");
        SpecctraDsnStreamReader scanner = new SpecctraDsnStreamReader(new ByteArrayInputStream(raw));
        boolean parsed;
        try {
            if (scanner.nextToken() != Keyword.OPEN_BRACKET || scanner.nextToken() != Keyword.PADSTACK)
                throw new IllegalArgumentException("exact padstack scope start required");
            parsed = Library.readPadstackScope(scanner, layers, transform, stacks);
            if (scanner.nextToken() != null) throw new IllegalArgumentException("unexpected trailing token");
        } finally { scanner.yyclose(); }
        Padstack stack = stacks.get(name);
        if (!parsed || stacks.count() != 1 || stack == null || !stack.name.equals(name))
            throw new IllegalArgumentException("padstack import identity/count failed");
        Map<String,Object> shapes = new LinkedHashMap<>();
        for (int i = 0; i < LAYERS.length; i++) shapes.put(LAYERS[i], observe(stack.getShape(i)));
        return map("case", name, "status", "observed", "input_sha256", sha(raw),
                   "parser_return", parsed, "padstack_count", stacks.count(), "padstack_name", stack.name,
                   "board_layer_count", stack.boardLayerCount(), "layers", shapes);
    }

    static void save(Path target, Map<String,Object> result) throws Exception {
        byte[] raw = (json(result) + "\n").getBytes(StandardCharsets.UTF_8);
        if (raw.length > 262144) throw new IllegalArgumentException("observation output bound");
        Path partial = target.resolveSibling(target.getFileName() + ".partial");
        Files.write(partial, raw);
        Files.move(partial, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("input-directory output-json");
        Path input = Path.of(args[0]), output = Path.of(args[1]);
        if (Files.exists(output)) throw new IllegalArgumentException("fresh observation path required");
        List<Object> rows = new ArrayList<>();
        for (String name : CASES) rows.add(map("case", name, "status", "not_run"));
        Map<String,Object> result = map("schema", 1, "scope", "owned_padstack_import_only",
            "routing_executed", false, "native_executed", false,
            "coordinate_transform", List.of(1, 0, 0), "units", "micrometres", "cases", rows);
        save(output, result);
        boolean complete = true;
        for (int i = 0; i < CASES.length; i++) {
            try { rows.set(i, runCase(input.resolve(CASES[i] + ".dsn"), CASES[i])); }
            catch (Exception failure) {
                complete = false;
                String message = failure.getClass().getName() + ": " + String.valueOf(failure.getMessage());
                rows.set(i, map("case", CASES[i], "status", "failed", "error", message.substring(0, Math.min(1024, message.length()))));
            }
            save(output, result);
        }
        if (!complete) System.exit(2);
    }
}
