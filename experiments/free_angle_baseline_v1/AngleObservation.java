// SPDX-License-Identifier: GPL-3.0-or-later
// Owned prospective loader diagnostic; UNCOMPILED and UNEXECUTED.
import app.freerouting.board.model.structure.AngleRestriction;
import app.freerouting.io.BoardReadResult;
import app.freerouting.io.specctra.DsnReader;
import java.io.ByteArrayInputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;

public final class AngleObservation {
  public static void main(String[] args) throws Exception {
    if (args.length != 2) throw new IllegalArgumentException("owned.dsn none|45");
    AngleRestriction expected = switch (args[1]) {
      case "none" -> AngleRestriction.NONE;
      case "45" -> AngleRestriction.FORTYFIVE_DEGREE;
      default -> throw new IllegalArgumentException("expected mode must be none or 45");
    };
    byte[] raw;
    try (var input = Files.newInputStream(Path.of(args[0]))) {
      raw = input.readNBytes(4 * 1024 * 1024 + 1);
    }
    if (raw.length == 0 || raw.length > 4 * 1024 * 1024)
      throw new IllegalArgumentException("nonempty DSN <=4MiB required");
    var result = DsnReader.readBoard(new ByteArrayInputStream(raw), null, null);
    if (!(result instanceof BoardReadResult.Success success)
        || success.board() == null || !success.warnings().isEmpty())
      throw new IllegalStateException("full DSN load failed or warned: " + result);
    var actual = success.board().rules.getTraceAngleRestriction();
    if (actual != expected) throw new IllegalStateException("loaded mode differs: " + actual);
    var sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    System.out.println("{\"input_sha256\":\"" + sha + "\",\"loaded_angle\":\"" + actual
        + "\",\"parse_warnings\":[],\"diagnostic_only\":true}");
  }
}
