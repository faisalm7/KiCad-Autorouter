import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.nio.file.attribute.PosixFilePermissions;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/** Two owned-scene selectors for the existing nonrouting loader/SES observer. */
public final class SesBridge {
    static final Set<String> SCENES = Set.of("back90-positive", "back90-false_hull");
    static final int INPUT_LIMIT = 64 * 1024;
    static final int JSON_LIMIT = 256 * 1024;

    static Path path(String value) {
        Path result = Path.of(value).toAbsolutePath();
        for (Path part : result) {
            if (part.toString().equals("..")) throw new IllegalArgumentException("no parent traversal");
        }
        result = result.normalize();
        for (Path part = result; part != null; part = part.getParent()) {
            if (Files.isSymbolicLink(part)) throw new IllegalArgumentException("no symbolic links");
        }
        return result;
    }

    static byte[] readInput(Path input) throws Exception {
        if (!Files.isRegularFile(input, LinkOption.NOFOLLOW_LINKS)
                || ((Number) Files.getAttribute(input, "unix:nlink", LinkOption.NOFOLLOW_LINKS)).longValue() != 1) {
            throw new IllegalArgumentException("regular single-link DSN required");
        }
        byte[] raw;
        try (InputStream stream = Files.newInputStream(input, LinkOption.NOFOLLOW_LINKS)) {
            raw = stream.readNBytes(INPUT_LIMIT + 1);
        }
        if (raw.length == 0 || raw.length > INPUT_LIMIT) throw new IllegalArgumentException("DSN byte bound");
        return raw;
    }

    static void unchanged(Path input, BasicFileAttributes before, String pin) throws Exception {
        BasicFileAttributes after = Files.readAttributes(input, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        if (before.fileKey() == null || !Objects.equals(before.fileKey(), after.fileKey())
                || before.size() != after.size() || !before.lastModifiedTime().equals(after.lastModifiedTime())
                || !pin.equals(AreaContactProbe.sha(readInput(input)))) {
            throw new IllegalArgumentException("input material changed");
        }
    }

    static void disabledSettings(Object value) {
        if (!(value instanceof Map<?, ?> settings)
                || !Boolean.FALSE.equals(settings.get("router_enabled"))
                || !Boolean.FALSE.equals(settings.get("optimizer_enabled"))
                || !Boolean.TRUE.equals(settings.get("plane_as_obstacle"))) {
            throw new IllegalArgumentException("nonrouting obstacle settings differ");
        }
    }

    static void completedWriter(Map<String, Object> row) {
        disabledSettings(row.get("settings_before"));
        disabledSettings(row.get("settings_after"));
        if (row.containsKey("local_override") || !Boolean.TRUE.equals(row.get("post_load_awaited"))
                || !"observed".equals(row.get("status"))
                || !(row.get("ses") instanceof Map<?, ?> ses)
                || !Boolean.TRUE.equals(ses.get("returned"))
                || !Boolean.TRUE.equals(ses.get("write_completed"))
                || !Boolean.TRUE.equals(ses.get("closed"))) {
            throw new IllegalArgumentException("nonrouting SES observation incomplete");
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 3 || !SCENES.contains(args[0])) {
            throw new IllegalArgumentException("back90-positive|back90-false_hull input.dsn fresh-output-directory");
        }
        Path input = path(args[1]), directory = path(args[2]);
        if (!input.getFileName().toString().equals(args[0] + ".dsn")) {
            throw new IllegalArgumentException("exact scene DSN filename required");
        }
        BasicFileAttributes before = Files.readAttributes(input, BasicFileAttributes.class, LinkOption.NOFOLLOW_LINKS);
        byte[] raw = readInput(input);
        String pin = AreaContactProbe.sha(raw);
        unchanged(input, before, pin);
        if (Files.exists(directory, LinkOption.NOFOLLOW_LINKS)
                || !Files.isDirectory(directory.getParent(), LinkOption.NOFOLLOW_LINKS)) {
            throw new IllegalArgumentException("fresh output with existing regular parent required");
        }
        Files.createDirectory(directory, PosixFilePermissions.asFileAttribute("rwx------"));
        Map<String, Object> row = AreaContactProbe.map("scene", args[0], "status", "starting",
                "requested_obstacle", true, "local250_requested", false);
        Map<String, Object> result = AreaContactProbe.map("schema", 1,
                "scope", "two-owned-scenes-nonrouting-headless-SES-observation-only",
                "scene", args[0], "input", input.toString(), "input_sha256", pin,
                "status", "failed", "routing_executed", false, "native_executed", false,
                "accepted", false, "production_admitted", false, "custom_pad_support_qualified", false,
                "exit_success_required", true, "case", row,
                "writer_design_name", "original-mixed.dsn",
                "settings_lifecycle_scope", "Before Headless load and after loader adjustments/awaitPostLoad; no scheduler final merge or routing pipeline.",
                "contact_scope", "Actual item contacts, net terminal IDs and connected sets from MixedClassProbe; no new internal-graph qualification.");
        try {
            // The retained method performs SettingsMerger, actual HeadlessBoardManager
            // load, awaitPostLoad, observation and bounded CREATE_NEW SES writing.
            // local250=false skips its original-PIC matrix edit. Its default
            // observation/writer overloads use adapter=false and invoke no router.
            MixedClassProbe.run(raw, true, row, false, directory.resolve("raw.ses"));
            completedWriter(row);
            result.put("status", "observed");
        } catch (Exception error) {
            row.put("status", "failed");
            result.put("error", MixedClassProbe.boundedError(error));
        }
        unchanged(input, before, pin);
        byte[] saved = (AreaContactProbe.json(result) + "\n").getBytes(StandardCharsets.UTF_8);
        if (saved.length > JSON_LIMIT) throw new IllegalArgumentException("observation JSON byte bound");
        Path output = directory.resolve("observations.json");
        Files.write(output, saved, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        unchanged(input, before, pin);
        if (!"observed".equals(result.get("status"))) System.exit(2);
    }
}
