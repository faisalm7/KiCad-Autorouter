# Rational junction diagnosis — actual routing001 remains failed

The stored run at `9c0b2746b2566542ca49a2b411cf1efeeda56c8a` really invoked and returned from the routing pipeline and wrote SES. It contains 126 traces, no vias, and three noninteger corner witnesses, all at the same displayed junction. The captured checker still fails with `exact integer engine point required`; no fresh native stage ran. The failure and all original artifacts remain unchanged.

Traces 1177,1178 and 1179 belong to `Net-(Q2-C)` on `bottom_layer`, width 500µm. Their relevant corners are all class `RationalPoint`, `corners_board_integer=null`, displayed coordinates `(148924.45, -65104.45) µm`. The SES declares `(resolution um 10)` and all three matching paths use exact integer tokens `1489245 -651044`, meaning `(148924.5, -65104.4) µm`. Each differs by +0.05µm on both axes from the **displayed** engine value. All other corners of these three paths match their corresponding displayed values. The three SES paths still share a single serialized junction; this comparison is not a native connectivity result or an exact rational proof.

The recorded engine scale is 10 board units/µm and origin 0,0. Writer before/after geometry and observed state are identical, and the SES bytes match its writer receipt. Cached pinned `SesWriter.java:385–405` obtains each corner through `toFloat()`, may snap endpoints, and then uses `Math.round` for integer SES coordinates. The observed offsets are consistent with that finite-grid serialization. This does not establish the missing exact engine fraction, an acceptable tolerance, or native routing acceptance.

## Exact witness availability

No cached RationalPoint source was found. Exactly one missing primary file was fetched from the established commit:

https://raw.githubusercontent.com/freerouting/freerouting/b647a2f824cfbc54bc4dcaee71b03b7cd945eb76/src/main/java/app/freerouting/geometry/planar/RationalPoint.java

It is 9278 bytes, SHA256 `46d1ea1122909839c24670a7354a2fe5cd4cfe2ce6b9280645c9c1d61d2c20ec`. The HTTP 200/no-redirect receipt is retained. The source represents points as homogeneous `BigInteger x,y,z`, affine `(x/z,y/z)`; all three fields and the constructors are package-private. There are no public numerator/denominator getters. `toFloat()` converts the three integers to doubles and divides; `z=0` represents infinity. Cached public `Point` declarations expose exact construction and comparisons but no coordinate accessor; cached `Polyline.corner(int)` returns the original Point. These are source/API findings, not a new JVM result.

The smallest prospective witness is a tiny helper in the same `app.freerouting.geometry.planar` package reading the actual point's x,y,z fields, emitting bounded decimal strings with positive z and canonical common-gcd normalization (IntPoint can emit x,y,1). Reject unknown point classes, zero/negative denominator and oversized integers. Record its source/JAR hashes and exact transform before comparing fractions with SES. Package access and compilation remain ROOT-only prospective qualification; no reflection, JVM or helper compilation was attempted here. No floating value should be promoted to an exact rational. Re-importing the rounded saved SES also cannot recover the original fraction.

This diagnosis does not propose relaxing the strict equality predicate. Saved-native follow-up may assess the already written SES under original rules while retaining transport failure; it must not turn this run into an exact-survival or accepted-routing result.

`audit.py` reuses the captured checker and shared S-expression parser. It verifies the 99 frozen artifacts and 15 original files before/after, reproduces the failure, and matches each affected path uniquely using its net/layer/width and all other corners. Stored whole-job costs remain 5.286988750s wall / 8.149004s full CPU; the pipeline-reported portion is 1.737252417s and is not the full job cost. No original/run/source file was edited, no native/JVM/solver ran during this diagnosis, and no delegation occurred.
