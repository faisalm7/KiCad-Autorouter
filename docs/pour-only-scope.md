# Pour-only rule areas

The experimental source branch adds support for a narrow root board rule area that prohibits copper pours and explicitly allows tracks, vias, pads and footprints. Placement must be absent or disabled. It requires explicit F.Cu/B.Cu layers, one simple XY outline, unique UUIDs, at most16rootzones, and no footprint zones. Other restrictions and unsupported syntax reject. Original definitions, rules and all warnings remain unchanged.

The pinned KiCad10.0.0 nonsaving refill DRC can conceal bad stored fill. The pipeline therefore keeps the exact pre-refill board, reconstructs the final candidate from the actual saving refill, and runs a separate native saved-fill intersection audit bound to hashes captured before board loading. The full source-declared area/ordinary-zone/layer matrix is mandatory. Missing or altered evidence rejects; editable local JSON is not cryptographic authentication.

Stock KiCad's DSN exporter emits a generic track/via keepout for this pour-only area. Corrected workflows remove only the exactly attributed polygon obstacle, with every other interchange atom preserved. This is a B1 adapter correction. Stock B0 retains its actual native raw DSN. Original KiCad fill exclusion is required for every final candidate/trial/export, including stock. No new routing-quality claim arises from this correction.

Native probe002 proves saving-refill F.Cu exclusion and allowed B.Cu overlap, plus rejection of deliberately intruding stored F.Cu fill concealed by nonsaving refill. Current production integration and broader shape/layer native controls are still being qualified. NUS protected original via serialization remains refused; only whole unlocked routing can be evaluated if the other gates pass. No source repair or rule relaxation is permitted.

Root gr_text supports exactly one knockout atom on declared F.SilkS/B.SilkS. Copper/Edge.Cuts/nested or unknown layer grammar remains blocked. Actual native front/back serialization and plots are inspected; this does not establish physical/electrical approval.
