# Failed placement-routing fixture001: independent diagnosis and repair review

The actual attempt remains REJECTED before the engine. Source DRC and the new same-load observer exited successfully; the original source DRC was clean. No engine, SES import, candidate refill/final validation or routing qualification occurred. Recorded totals are3.013809875wall/1.957058CPU within60-second caps, sampled before final publication as disclosed. This review launched no native/router job.

43 offline checks passed. The complete original project/snapshot, ordinary stripped task, raw native DSN and both observed contexts agree by byte hashes and actual process/argv/cwd/step evidence. The exact four pad UUID/reference/number/net/layer mappings, two net identities/netcodes/two-terminal counts, original class preferences and hard floors match. Production floor context_binding and placement native_binding both pass on the observed files. Inputs and the whole failed run remain unchanged.

The rejecting component is autorouter.board_floor.source_net_identity, reached through floor policy_contract→transform→qualify. This named-net task has no root numbered net table; its four pad references are quoted SIGNAL_A/SIGNAL_B, while the explicitly unrestricted rule-area zone retains numeric(net0). The generic recursive resolver rejects that last reference as an unqualified named reference. The failed behavior is reproduced using the exact retained original module, independently of the later repair.

Pinned KiCad10.0.0 primary parser source explains the shape: parseZone calls parseNet at7843; parseNet accepts numeric legacy IDs at302 onward; lines8471–8478 expressly reset rule-area nets to unconnected/code0. A later legacy net_name repair exists, so contradictory names must not be silently ignored. Exact sourcecommit0feeca2a807f428ad2b3fa7c1e39625cb769f02c, parserSHA78f6380806e15b2a25300f8134c6492cd343d6dfb538546e299d60d26a62ec27. Source already retained with its license receipt; no download performed.

Primary URL: https://raw.githubusercontent.com/KiCad/kicad-source-mirror/0feeca2a807f428ad2b3fa7c1e39625cb769f02c/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr_parser.cpp

Independent downstream structural analysis found no second pure-stage problem: the raw DSN has exactly two named networks/four terminals; floor rules derive0.3mm width/clearance and1.5/0.3mm via from unchanged original floors/preferences; exact allowed floor edits pass; placement removes exactly two attributed generic keepouts; the both adapter adds nothing because this fixture has zero observed copper graphics. This analysis builds a separately checked context to isolate later grammar; it does not change source/observations, bypass a production gate, qualify a route or prove full-board/physical behavior.

## Narrow proposed repair

Reviewed isolated board_floor draft85b91527ec19f82a3869a4761c3dd597ef5b18ee600a6cf022100212e07f6cea and patch348171bedfb6587c16ac58cd612c414cbc87224d4323877fafb53d12a0c3d1e5. No immediate blocker found. In named mode only, the numeric-zero exception requires identity as an actual top-level board zone, exactly one net entry, exactly one literal empty net_name, and exactly five unique explicitly allowed keepout fields. It does not become a pad/route alias, alter legacy declared-net resolution or reinterpret quoted"0". No source bytes, constraints or native observations are rewritten.

23 independent pure controls passed against a copied draft and actual retained inputs: the actual floor transformation passes; nonzero/unknown/noncanonical numeric markers, numeric zero on pads/routes/nested footprint zones, ambiguous net/name entries and malformed/prohibited flags reject. Quoted"0" remains a distinct named net; valid legacy numeric tables still work and conflicting code/name references still reject. These are code/data controls, not native route qualification. The next gate remains a new checkpointed native owned-fixture run and readback before a full-board pair.

The first audit used current unchanged production code and passed. A second attempt to load the retained module failed because its relative-import package name was absent; that failed audit attempt is retained and is not a positive control. Corrected retained-module loading then reproduced all43 checks. No failed actual routing output was replaced.

This is AI review of mutable evidence consistency, not authentication, human PCB review or physical validation. Review directory is frozen.
