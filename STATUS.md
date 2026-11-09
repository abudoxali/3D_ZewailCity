# Zewail City 3D — execution status (single status file)

**V15.0.0 — READY FOR OWNER VISUAL REVIEW (G1 → Administration corridor pilot).** Verified 2026-11-09.
Owner decision 2026-11-09: old versions are archived outside the project (not deleted), V15 became the
main project tree after QA passed, and the project is published to https://github.com/abudoxali/3D_ZewailCity
without reference photographs. History below is kept; paths in older sections refer to the archive.

## V15 photorealistic ground & road reconstruction pilot (Claude Code) — 2026-11-09

**Scope.** One demonstration corridor: outside Main Gate G1 → gate lanes → main approach (both carriageways,
palm median, verges, walkways, crossover) → ring junction → drop-off loop → Administration forecourt.
Nothing else was intentionally changed; the other five gates and all buildings are untouched.

**Baseline.** V11 was the last official release; V12.1, V13 and V14 were unpromoted candidates. V15 was built
on the V14 candidate (latest chain, all suites passing) in an isolated copy, compared at matched poses against
an unmodified copy of the V14 Godot project. Checkpoint: 1,450 protected files (V11 release/scene/GLB, V11
sources, V12–V14 candidates and releases; 2.75 GB) SHA-256-hashed before editing and re-verified 1,450/1,450
unchanged after the final build (`output/validation/v15/checkpoint/`). V12's rejected curb candidate and the
dusty asphalt trial were not inherited.

**What replaced what (generator `src/utilities/v15_corridor.py`, hooks in `ground_system.py`, `site.py`,
`build_scene.py`, `build_game_assets.py`; Godot `ground_surface.gdshader`, `campus_loader.gd`, `pbr_materials.gd`):**

| V14 system | V15 replacement | Evidence |
|---|---|---|
| One continuous extruded/profiled kerb strip | **2,155 modular precast kerb units** (1.0 m; 0.5 m on curves), mitred joints, 6 mm V-grooves, rounded road arris, ±1.5 mm unit-height variation, 146,540 tris; split at turns > 80°; 523 of 541 m² of zone kerb converted. Visual only — the player still collides with the V13/V14 box kerb proxy (step-up unchanged). | C02 (unit joints), C01 |
| Flat green lawn strips between carriageway and walkway; low-poly blob shrubs | **Raised kerbed planting beds** (3,139 m²: verges + outer beds) of brown soil, Poly Haven `dirt` (CC0, 2 m tile), kerbed on the walkway side too (29 m² flush edge → kerb); **3,349 ice-plant groundcover clumps** in 0.7 m rows (Poly Haven `crystalline_iceplant`, CC0; 611–855 tris each, no shadows, 150 m draw range); 120 blob shrubs removed | C02 verges |
| Uniform carriageway pavers at the crossover | **Dark transverse paver bands** (4 × 1.6 m) either side of the OSM median crossover | C02 |
| Narrow-masked lawn median, centre dip below road level | Raised **worn median lawn** (green with sandy patches) over the whole median incl. the G1 flare | C02 |
| Hard-edged NDVI soil/sand/lawn patches | **Feathered natural ground**: 3.5 m soft transitions via COLOR_0.a and world-noise breakup (corridor ±150 m), denser 2.5 m terrain grid there; irrigated lawn patches kept | S-2 NDVI distribution kept |
| Plants standing on pavement | 19 shrubs/xerophytes on road surfaces removed (median gaps; G1 exterior curves) | V14 defect |
| G1 sand strip behind the gatehouse (V14 unresolved) | Gate island bed extended to the gatehouse back wall; vegetation placement unchanged | C01 |
| 0.9 m blurred tan fringe on corridor road edges | Narrower 0.5 m kerb-side sand margin in the zone, faded over 6 m at its edge | C01/C02 |

Open bed edges against the road at footway crossings (25 m) are graded down to road level (no open step).
Heights (bed +0.16–0.17 m, kerb top +0.24 m, road +0.06 m) and band/bed widths are ESTIMATED from photos.

**External assets** (`output/validation/v15/external_asset_manifest.json`; provider MD5 verified for every file):
installed `dirt` 2K and `crystalline_iceplant` 1K (+ a greener derived albedo, `tools/v15_iceplant_tint.py`);
`asphalt_01` 2K evaluated, not upgraded (no gain over the installed calibrated 1K); rejected `aerial_asphalt_01`
(30 m tile = 68 px/m, distinctive tyre marks), `dry_ground_01` (cracked clay, not this site), `concrete_pavement`
(no gain over V11 slab sidewalks). No PSX/stylised/low-poly packs.

**Verification after the last source change (final3 build):**

| Check | Result |
|---|---|
| Full source rebuild (scene, game assets, paths, source GLB, game/V8/scene checks, import) | all exit 0 |
| Surface partition | overlap 0 m², plot uncovered 0 m², all topology checks pass |
| Regressions (Godot) | **18/18 suites, 326 assertions, 0 failures** (17 inherited + new `V15Corridor` 9/9) |
| V15Corridor | continuous walk outside G1 → walkway → Administration forecourt; perpendicular crossings of both verge beds (road kerb → raised bed → walkway kerb) and of the median; both carriageways through the bands; 0 floor losses (max floor gap 0.19 m); 0.5 m physics-ray grid over the corridor (35,689 samples): 0 holes (V14: 0 holes, 16 single-ray edge misses; V15: 3), 0 raised invisible barriers; kerb units add no collider |
| Gates / journeys | V11Gates 37/37, V11GateCoverage 18/18, V11PerimeterSeal 12/12, V11FullJourney 2/2 — closed-gate collision and pedestrian access unchanged |
| Material diagnostics | 15 maps, 0 failures |
| Geometry vs V14 | non-vegetation changes only in the 9 ground/road meshes; Academic courtyard identical vertex set; vegetation 0 horizontal moves, 0 mesh swaps, 207 Z re-seats (≤ 0.14 m, plants in raised beds; ≤ 3 mm outside the corridor); Academic inner court still tree-free |
| Packaged Windows | `releases/ZewailCityExplorer_Windows_V15/ZewailCityExplorer.exe` 15.0.0, smoke **38/38**, exit 0, source/GLB hashes match, 0 control ports, 0 real input events, SHA-256 `c2bd10df…4aee` |

**Performance** (RTX 4070, 1920×1080 High, FOV 84.25, VSync off / max_fps 0, 12 stored views, 90 + 180 frames,
V14/V15 alternating ×2; `output/validation/v15/bench/performance_v14_v15.json`):

| Metric | V14 | V15 |
|---|---:|---:|
| Aggregate FPS | 186.6 | **177.9 (−4.7 %)** |
| Slowest view | 135.3 (approach aerial) | 127.4 (approach aerial) |
| Worst p99 | 8.38 ms | 9.01 ms |
| Draw calls | 337–1,281 | 347–1,312 |
| Rendered primitives | 5.07–6.81 M | 5.36–7.71 M |
| Texture memory | 1.297 GB | 1.356 GB |
| Load (ms) | ~1,610 | ~1,885 |

Every view > 60 FPS; slowest > 90 FPS.

**Post-promotion re-verification (main tree, after archiving).** Godot import, `verify_scene.py` and V8 source
checks exit 0; regressions **18/18 suites, 326 assertions, 0 failures** (`output/validation/v15/logs/v15_promoted_regressions.log`);
packaged exe at `releases/ZewailCityExplorer_Windows_V15/` smoke **38/38**, exit 0, hashes match.

**Visual evidence.** 29 matched V14 | V15 boards (same stored pose, FOV, preset, 1080p):
`output/validation/v15/final3/comparisons/` — required views: G1 exterior (`G1_exterior_eye`), G1 interior
(`O02_G1_inside`, `V15_g1_inside_kerbs`), first junction after G1 (`V14_g1_median_nose`), median at eye level
(`V15_median_eye`, `main_approach_road`), aerial (`V13_approach_aerial`, `drone_overview`), kerb/road intersections
(`V15_kerb_close`, `V15_ring_junction_kerbs`, `V12_junction_dropoff_eye`), road-to-sand (`V14_g1_gate_sand`),
Administration forecourt (`admin_entrance_axis`), plus bands and verge-bed close-ups.
Walkthrough: `output/validation/v15/walkthrough/v15_walkthrough_G1_to_admin.mp4` (real Godot Movie Maker
capture, 1920×1080, 30 fps, 52.8 s, outside G1 → gate lane → approach → ring junction → forecourt).

**Independent visual QA** (Sonnet, `output/validation/v15/qa/final_visual_qa.md`): round 1 PARTIAL (muddy aerial
feathering, sparse oversized groundcover, median lawn seam, see-through crack at an unkerbed bed edge, faint
bands) → one repair round → round 2 **READY FOR OWNER VISUAL REVIEW**; BETTER in 11 prioritised views, SAME or
slightly better in the rest, no new severe regression, no change visible outside the corridor at ground level.

**Code review** (Sonnet, read-only, 12 findings) — fixed: unfiltered groundcover ray-cast, silent early return,
bed riser/step, kerb z-fight risk (unit tops 1 cm above legacy, vertex-based trim, overlap de-dupe), silent face
loss (now fails the build), sharp-turn mitres, feather grid resolution, zone-edge fringe seam, layout drift guard,
material-slot assertion, comments/dead code, test strictness. A vegetation-placement side effect found in
verification (island polygon shifted the random stream) was fixed; plants are back to their V14 positions.

**Rejected / not done.** Upgrading asphalt to 2K; aerial asphalt; dry_ground; leaf-shrub or new tree species;
inventing young trees in the verges (C02 shows them; V14 has none there and none were invented).

**Remaining inaccuracies (honest).**
- Beds read as young planting on bare soil, still sparser than C02's dense rows.
- Crossover bands are clearly visible close up but fainter than C02 at distance.
- One kerb end at a footway crossing (`V15_kerb_close`, inbound verge near y ≈ 156) ends abruptly beside a flat
  light strip; the crossing itself is evidence-free (OSM footway).
- Inherited, unchanged: a hard sand wedge and sand/paver line at G1 (`V14_g1_median_nose`, `V14_g1_gate_sand`),
  a tan asphalt streak at G1, flat Administration forecourt paving, G2's ~25 m sand gap (by rule), 7 Texture RID
  shutdown warnings.
- Widths/heights are photo estimates, not survey.

**MCP.** Blender MCP: the single live listener (Blender 5.2, port 9876) accepted the connection but did not
answer `execute_code` within 60 s (known stall); all Blender inspection in V15 was done with background
`blender -b` scripts (ray-cast probes, geometry fingerprints, equivalence checks). Godot MCP tools were not
available in this session; runtime behaviour was verified by real engine runs (captures, 18 suites, Movie
Maker, packaged smoke test).

**Agent ledger.**

| Agent | Model | Task | Tokens / time |
|---|---|---|---|
| Main | Claude Opus 5.5 | implementation, verification, release | UNKNOWN |
| Code review | Claude Sonnet (subagent) | read-only diff review | 175,393 / 355.5 s |
| Visual QA r1 | Claude Sonnet (subagent) | 29 boards | 111,770 / 60.0 s |
| Visual QA r2 | Claude Sonnet (same agent, resumed) | final3 boards | 132,499 / 30.0 s |

Cost and quota UNKNOWN. T3 Code orchestration, Gemini and Codex were not used in this session.

**Layout after promotion.** `src/`, `game/godot/`, `references/` (photos local only), `output/Zewail_City_3D.blend`, `releases/ZewailCityExplorer_Windows_V15/` (local, not committed); V15 evidence in `output/validation/v15/`; generator data read by the Godot tests stays in the legacy path `output/validation/v11/`. Tools: `tools/v15_rebuild.sh`, `v15_regressions.py`, `v15_capture.sh`, `v15_bench.sh`, `verify_windows_v15.ps1`.

**Rollback.** Everything replaced is in `C:/Users/Abud/Desktop/GitHub/zc/_archive_zewail_old/<UTC stamp>/`
(full move log: `output/validation/v15/archive_moves.json`): V11 release, V11 `src/`/`game/`/outputs,
V4–V14 validation trees and candidates (incl. the V14 candidate and its exe), `backups/` (15.5 GB) and old tools.
To roll back to V14: copy `<archive>/output/validation/v14/candidate/{src,game,references}` over the project
and its `output/Zewail_City_3D.blend`; to V11: restore `<archive>/src`, `<archive>/game`,
`<archive>/output/*` and `<archive>/releases/ZewailCityExplorer_Windows`. Checkpoint hashes:
`output/validation/v15/checkpoint/protected_sha256.json` (re-verify with `tools/v15_checkpoint.py <json> --verify`
against the archive copy).

## Earlier status headline (V11, historical)

**V11.0.0 — PARTIAL. Technical Windows delivery PASS; architectural/visual acceptance PARTIAL.**
Verified 2026-11-08. The interrupted implementation was continued, with no V10 rollback or Git initialization.

## V14 terrain, roads & access reconstruction (Claude Code + Codex) — 2026-11-09

**V14 — PARTIAL candidate. Not promoted.** V11 remains the official release; V12.1 and V13 still await the owner.
- Isolated tree: `output/validation/v14/candidate/` (a copy of V13, version 14.0.0).
- Packaged exe: `candidate/releases/ZewailCityExplorer_Windows_V14/ZewailCityExplorer.exe`, SHA-256 `8698a28b…3cbf`.
- Evidence: `output/validation/v14/`.
- Verdict: measurable ground repairs, but the independent QA judged the visible change NOT SUBSTANTIAL.

**Source changes** (all in `candidate/src`, reproduced by full source rebuilds):

`utilities/ground_system.py`:
- Constrained per-cell triangulation with shared-edge refinement, a 1.8 m road inset band and float32 welding (`region_triangles` / `grid_triangles` / `mesh_region`).
- Local lawn grading in `grade_zones`.
- `g1_shoulders`: 51 m² of G1 apron paving.
- `g1_exterior_asphalt`: exterior asphalt spur to the G1 gate line, y 314.6.
- `profile_kerb`: precast kerb with a 30 mm road chamfer, 10 mm batter and 6×10 mm back arris.
- `Kerb_Box_Collision_Proxy`: box kerb used for collision only.

`utilities/v11_ground.py`:
- `repair_curb_runs` / `round_curb_tips`: closed rounded median noses and 30 mm crack closing.

`utilities/site.py`:
- `_bed_prism`: removes the Flower_Beds duplicate faces.

`build_game_assets.py`:
- `COL_Ground` takes the kerb from the box proxy, because the chamfered profile stalled the player's kerb step-up.
- Without the proxy, V11GateCoverage G6 failed at Godot (342.85, 0.87, 219.84).

**Ground audit (1 m grid, V13 → V14):**

| Metric | V13 | V14 |
|---|---:|---:|
| Exposed-terrain clusters | 11 | 1 (the one left is at (−200, −27); 0 at G1) |
| Curb kinks | 29 | 0 |
| Curb stubs | 24 | 0 |
| Coplanar Flower_Beds pairs | 1 | 0 (110 m²) |
| Height-step clusters | 1007 | 961 (high-severity steps 3 → 0) |
| Sliver triangles | 7199 | 4991 |
| Corridor samples without ground | 0 | 0 |
| Floating objects | 4 | 4 (pre-existing) |
| Structure-vs-ground coplanar pairs | 13 | 15 (+2) |

**Class changes and geometry fingerprints:**
- Class delta: 70 samples changed, all in repair zones. Forbidden changes (curb↔road, paved→sand/soil, lawn→road): 0.
- Geometry fingerprints against V13, 1860 meshes:
  - 1823 unchanged, 0 missing, 1 added (the collision proxy).
  - 9 ground meshes changed.
  - 27 plants changed by Z re-seat only (|dz| ≤ 6 cm; XY, scale and mesh identical).
  - Architecture, gates, stairs and perimeter are untouched.

**MCP:**
- Blender MCP, live: on the 1 m G1 grid, desert-sand samples went from 216 to 194, and inside the gate apron from 46 to 34.
- The remaining sand strip is at x −5.5..6.5, y 326.5..330.5.
- Admin/Academic junction: 0.5 m steps over 0.15 m went from 17 (max 0.17 m) to 0.
- Vegetation is still 546 replacements; the Academic inner court has no trees.
- Godot MCP runtime: runtime tree, Start click and explore tree all worked.

**Tests and performance:**
- Regressions: 17 suites, 0 failures (V11GateCoverage 18/18, V11FullJourney, V11Ui 41/41 Arabic UI).
- Packaged smoke ×3: 38/38 each, exit 0. Source and GLB hashes match; no control ports; 0 real input events.
- Bench, V13 → V14 (2 alternating runs each, 1920×1080 High, RTX 4070):

  | Metric | V13 | V14 |
  |---|---:|---:|
  | Aggregate FPS | 193.4 | 190.0 (−1.8 %) |
  | Slowest view (`main_approach_road`) | 148.4 FPS | 144.9 FPS |
  | Worst p99 | 7.84 ms | 8.09 ms |
  | Draw calls | 337–1281 | 337–1281 |
  | Primitives | 6.62 M | 6.81 M |
  | Texture memory | 1297 MB | 1297 MB |

- Collision tris: 407,641.

**Independent QA** (Sonnet, after the final source change; 31 matched boards; `output/validation/v14/qa/final_visual_qa.md`):

| Defect | Visual result |
|---|---|
| G1 sand | IMPROVED |
| Median noses | IMPROVED (marginal) |
| Flower-bed z-fighting | UNCHANGED visually |
| Junction step | UNCHANGED visually |
| Ring steps | UNCHANGED visually |
| Approach / asphalt spur | IMPROVED (clear) |
| Kerb chamfer | IMPROVED (subtle) |
| Building entrance grounds | UNCHANGED |
| Inner court | UNCHANGED, tree-free |

Minor regressions:
- Warm tint patches on G1 pavers: the per-vertex drift mask is now sampled on the denser mesh.
- A kerb strip now closes the far end of the G1 lawn, which has lost the V13 gate-shade tone.
- A tan fringe along the new asphalt edge.

**Unresolved:**
- G1 sand strip behind the gatehouse.
- The three minor regressions above.
- The G2 ~25 m sand gap (by rule).
- Entrance grounds: no visible change.

**Agents:**

| Agent | Work | Tokens / time |
|---|---|---|
| Codex `gpt-6.1-sol` (ChatGPT subscription) | Wave B | 292,187 / 70 min |
| Codex | Wave D | 174,701 / 29 min |
| Codex | Wave C | 167,079 / 22 min; hit the usage limit; validated by Claude |
| Haiku | Explore | 111,594 |
| Sonnet | QA | 130,613 |

Codex quota percentage: UNKNOWN. T3: unavailable.

**Preservation:** all protected V11/V12/V12.1 files and the 91 V12.1 sources are byte-identical. The V13 candidate's newest file is its 00:27 export (`output/validation/v14/preservation_check.json`).

## V13 realism pass (Claude Code) — 2026-11-09

**V13 — PARTIAL candidate. Not promoted. V11 remains official, and V12.1 still awaits owner approval.**
V13 lives in an isolated tree, `output/validation/v13/candidate/` (a copy of V12.1). Checkpoint `output/validation/v13/checkpoint/` confirms that the V11 scene/GLB/exe, the V12 and V12.1 executables, and the V12.1 scene/GLB and 91 source files are all byte-identical.

**Integrated (generator `candidate/src/utilities/v12_realism.py` stage `v13`; runtime `game/godot/scripts/{main,pbr_materials,campus_loader,smoke_test}.gd`; reproduced by full source rebuilds):**
- **Trees:** all 490 broadleaf trees now use Poly Haven `pachira_aquatica_01` (CC0), variants c/d. These are the 402 procedural low-poly trees plus the 88 V12.1 trees.
- **Palms:**
  - All 35 procedural date palms now use the Innerscene "Mature date palm tree" (CC0, 56k tris).
  - All 21 procedural fan palms now use the Innerscene "Palm, detailed" (CC0, 38k tris). This is a pinnate stand-in, because no CC0 fan palm was found.
- **Placement:** location, yaw and original height are kept. Every plant stands upright, is scaled uniformly and keeps its original trunk collider. Each is ground-snapped 4–6 cm into the surface: the MCP audit found 8 palms floating 0.17–0.39 m before the fix.
- **Sky:** daytime uses Poly Haven `kloofendal_48d_partly_cloudy_puresky` (CC0). It is sun-clamped (the directional light remains the sun), rotated −93° to the sun azimuth, with energy 0.6, background 1.25 and fog sky-affect 0.45. Evening keeps the procedural sky.
- **Smoke-test input control:**
  - The smoke window is now non-focusable, and real OS events are consumed and counted in `smoketest.json`.
  - Two runs before the snap fix blocked 64 and 278 real mouse events (including 2 clicks).
  - This confirms that the intermittent V12.1 failures were external input.
- **Source/manifests:**
  - Sources and licences are in `output/validation/v13/external_asset_manifest.json` and `candidate/references/assets/*/manifest.json`; downloads are in `output/validation/v13/downloads/`.
  - Source previews are genuine V13 Godot captures.

**Tried and rejected after QA:**
- ambientCG `PavingStones125A` pavers: stone grain smeared at grazing angles and joints vanished. Pavers stay at V12.1.
- Leaf-geometry shrubs built from Pachira leaves (two attempts): they read as dead leaf piles. The V12.1 shrubs are kept.
- Poly Haven `kloofendal_43d_clear_puresky`: rendered a flat grey sky.
- Pachira variants a/b, and the other rejections listed in the manifest.

**Not done (honest scope):**
- No road, curb, junction or terrain geometry changes. The owner's markup-15 junction strips remain.
- No architecture, entrance, door or interior changes.
- Shrubs, cacti, agave, cycads and cypress are still procedural.
- No new street furniture.
- G2 sand gap unchanged.

**Independent QA:** one Sonnet review, done before the correction round. Its verdict was PARTIAL: sky and palms better; trees the same as V12.1 in the corridor views; shrubs and pavers worse. Those two regressions were then rolled back, and the post-rollback state was checked in captures, not re-reviewed. The 28 matched V11 | V12.1 | V13 boards (same pose, FOV 84.25, High, 1080p) are in `output/validation/v13/final/comparisons/`; earlier states are in `final_presnap/`, `final_correction1/` and `final_pre_correction/`.

**Verification after the last source change (ground snap):**

| Check | Result |
|---|---|
| Rebuild | All steps exit 0 |
| Source / V8 source / game-asset checks | 24/24, 30/30, 15/15 |
| Geometry fingerprints | Only the 546 vegetation meshes changed; 0 non-vegetation changes, 1,313 unchanged; collision tris unchanged at 418,705 |
| Blender MCP (native tool, live Blender Lab server) | 546 plants embedded 4–6 cm in lawn, soil or planting; none on paving; none in the Academic inner court |
| Godot MCP (debug runtime) | Tree query and Start click worked; Campus, Player, roads, vegetation and HUD loaded; 0 errors |
| Material diagnostics | 15 maps, 0 failures |
| Regressions | **17/17 suites, 317/317** |
| Packaged smoke test | **3/3 runs at 38/38**, exit 0, v13.0.0, hashes matched, 0 ports |

**Performance** (RTX 4070, 1080p High, VSync off, 10 views, V11/V12.1/V13 alternating ×2; `output/validation/v13/bench/performance_v11_v121_v13.json`):

| Metric | V13 | V12.1 | V11 |
|---|---:|---:|---:|
| Aggregate FPS | **202.0** | 251.3 | 267.2 |
| Change | −19.6 % vs V12.1, −24.4 % vs V11 | | |
| Slowest view | 153.4 FPS (main approach) | | |
| Worst p99 | 7.25 ms | | |
| Render triangles | 15.8 M (from about 1.4 M) | | |
| Draw calls | 337–1,281 | | |
| Texture memory | 1.30 GB | 1.29 GB | |

All views exceed 60 FPS and the slowest exceeds 90; the drop comes from authored vegetation geometry.

**Windows candidate:** `output/validation/v13/candidate/releases/ZewailCityExplorer_Windows_V13/ZewailCityExplorer.exe`, SHA-256 `c6daa30f…1c8f`.

**Agent ledger:**
- Primary: Claude Opus 5.5; tokens, time and cost UNKNOWN.
- Haiku asset-sourcing subagent: 149,421 tokens, 165.6 s.
- Sonnet visual-QA subagent: 101,796 tokens, 37.8 s.
- Costs and quota UNKNOWN.
- T3 Code orchestration tools and Gemini were not available in this session; Codex was not used (quota previously exhausted).

## V12.1 final visual refinement (Claude Code) — 2026-11-08

**V12.1 candidate — recommended ACCEPT, awaiting owner approval. Not promoted. V11 remains the official release.** Built in the isolated candidate tree on top of V12. V11 sources, scene and executable are untouched (`recovery/preservation.json`: 220/220 archived originals, V11 scene and exe byte-equal).

**Implemented (generator `candidate/src/utilities/v12_realism.py` + `candidate/game/godot/scripts/pbr_materials.gd`; reproduced by two full source rebuilds):**
- **Internal paver roads and dormitory paths.** Reference photo D02 (inside G1) shows rectangular grey pavers in running bond with low-contrast joints. V12's `concrete_pavers` zig-zag was the wrong unit shape; its 1.92 m is the texture sample size, not a paver size. Roads and paths now keep the V11 0.22 × 0.11 m running bond, with per-unit tone and sand-drift masks, plus fine `concrete_pavement_03` detail at 12 %. No surface class or geometry changed.
- **Asphalt haze.** Bounded isolation showed the cause is specular sheen, not the macro tone: setting roughness to 1 removed the left/right gradient, while turning the macro tone off did not. The roughness floor went from 0.86 to 0.93, which cut the mid-distance gradient from 17 to 10 luminance levels (V11: 11). V12's neutral tone and the shadow-acne fix are kept.
- **Vegetation.** Every tree in the two main-approach roadside rows and the Administration frontage now uses the CC0 Pachira model (88 trees; previously 14 mixed with low-poly trees). C02 shows the approach lined with slender broadleaf trees. After the review, the one correction round switched to uniform scaling from the original height with upright trunks; per-axis fitting had produced flat, sprawling crowns. Positions and collision are unchanged; palms, shrubs and all other trees are untouched.
- **Version and export.** Version 12.1.0. Exported separately to `releases/ZewailCityExplorer_Windows_V12_1/`; the V12 exe is preserved. The V12 blend is preserved at `recovery/v121/v12_final_Zewail_City_3D.blend`.

**Rejected:** `concrete_pavers` as a road surface (wrong unit shape for this campus; busy at grazing angles) and per-axis Pachira fitting.

**Comparisons:** 21 matched V11 | V12 | V12.1 boards (same stored pose, FOV 84.25, High, 1920×1080) in `output/validation/v12/recovery/v121/final/comparisons/`. They cover G1 paving, the main approach, paver close-ups, the junction, ring road, Administration entrance and frontage, Academic court, dormitory paths, asphalt and the aerial view. The pre-correction set is in `v121/captures/comparisons/`.

**Independent QA (one Sonnet review, before the tree correction):**
- Paving: V12.1 BETTER than V12 and matches D02; SAME as V11.
- Asphalt: BETTER than V12.
- Vegetation consistency: BETTER than V12.
- Verdicts: clear improvement over V12 in the targeted defects — YES; broken paving — NO; major vegetation mismatch — NO; new severe artifact — NO.
- The low-severity sprawling/leaning tree findings were corrected afterwards and checked in captures, not re-reviewed.

**Verification after the last source change:**

| Check | Result |
|---|---|
| Source rebuild | All 8 steps exit 0 |
| Source / V8 source / game-asset checks | 24/24, 30/30, 15/15 |
| Geometry fingerprints | 1,771/1,859 meshes identical to the V11 checkpoint; only the 88 trees changed; 0 non-vegetation changes, so no curb or surface-class change |
| Blender MCP (live scene reopened) | 88 tree bases within 3.7 cm of soil, lawn or planting, none on paving; only `M_Asphalt` is a whole-provider surface; stairs on stone/granite |
| Godot MCP (debug runtime with bridge) | `get_runtime_tree` and `click` Start worked; Campus, Player, roads and HUD loaded; 0 script or shader errors |
| Material diagnostics | 18 maps, 0 failures |
| Regressions | **17/17 suites, 317/317 assertions** |

**Performance** (RTX 4070, 1080p High, VSync off, 10 views, alternating runs; `v121/final/performance_v11_v121.json`):

| Metric | V12.1 | V11 |
|---|---:|---:|
| Aggregate FPS | **259.2** (−5.5 %) | 274.2 |
| Mean frame time | 3.86 ms | 3.65 ms |
| Slowest view | 214.8 FPS (dormitory) | — |
| Worst p99 | 5.44 ms | — |
| Draw calls | 357–1,567 | 357–1,552 |
| Texture memory | 1.29 GB | UNKNOWN (V11 harness does not report it) |

**Windows candidate:**
- Executable: `output/validation/v12/recovery/candidate/releases/ZewailCityExplorer_Windows_V12_1/ZewailCityExplorer.exe`, SHA-256 `53b84217…2cc4`.
- Latest packaged smoke run: 38/38, exit 0, v12.1.0 PE and app, source and GLB hashes match, 0 control ports. Evidence in `v121/windows_build/`.
- **Smoke-test caveat.** The real-time packaged runs were intermittent: 4 of 5 V12.1 runs failed one walking check each, and the byte-identical V12 exe also failed once in an interleaved control (V12 pass, V12.1 pass, V12 fail). This is environmental, consistent with real input reaching the smoke window while it holds mouse capture. All runs are logged in `v121/smoke_run_log.json`. A clean confirmation run on an idle PC is advisable before release.

**Remaining:**
- Paving equals V11 quality plus fine detail; it is not a dramatic upgrade.
- The Pachira canopy is somewhat dark and sparse.
- Low-poly shrubs in the median sit next to the naturalistic trees.
- Other campus tree rows (outside the targeted zones) remain low-poly.
- G2 sand gap unchanged.
- Seven inherited Texture RID warnings.

**Agent accounting:** parent Claude Opus 5.5 (tokens, time and cost UNKNOWN). One Sonnet visual-QA subagent: 90,014 tokens, 28.9 s; cost UNKNOWN. No Haiku agent was used; inspection was done inline. Codex was not used.

## V12 recovery and final candidate (Claude Code) — 2026-11-08

**V12 PARTIAL — technically complete and packaged, but NOT promoted. V11 remains the official release.**
The final candidate passes every technical gate. The independent visual review judged the change BETTER for trees and modestly BETTER for external asphalt. It was not clearly better for internal paver roads, which it found busier than V11's running bond. The brief requires clear improvement in roads AND paving, so the candidate was not promoted. Promotion now waits on an owner decision.

**Codex's state at interruption (recovered from logs, timestamps and diffs):**
- Isolated candidate in `output/validation/v12/recovery/candidate/`.
- 6 Poly Haven CC0 texture sets plus the Pachira tree, with verified MD5s.
- A `pbr_world.gdshader` that *replaced* the V11 ground shader.
- 58 Pachira shrubs and 14 trees.
- "final2" captures (18:03) and a 17/17 regression run (18:05).
- A stair "concrete micro" experiment (18:13–18:16). It was captured but never validated.
- Unvalidated edits (18:21–18:22) to the loader, smoke test, `v12_materials.gd` and `v12_manifest.py`.
- The 17:57 export predated all of the above.

**Rejected after matched captures:**
- Stair micro-concrete. It turned the stone stairs dark blue-grey and clashed with the landings and the evidence (stone treads, dark granite nosings). Files moved to `output/validation/v12/recovery/rejected/`. The stairs keep V11 stone plus fine `beige_wall_001` detail; geometry is unchanged.
- The 58 Pachira shrubs. At shrub scale they read as sparse twigs; V11 shrubs restored.
- `sand_01` and `sparse_grass` as whole surfaces. They gave grey cracked crust and chocolate-brown soil in the aerial view.
- Codex's cool ambient light. It turned concrete blue.

**Root causes and fixes (all in the regenerating source):**
- Codex's shader dropped V11's macro tone, anti-tiling and Blender drift/relief/contact masks. That is what caused the flat sand and the hard road/shoulder edges. Provider maps now feed the V11 `ground_surface.gdshader`:
  - mode 1: whole provider surface, tinted to the approved V11 mean colour (`tools/v12_tone_targets.py` → `assets/pbr/tone_targets.json`);
  - mode 2: fine detail on the V11 surface;
  - mode 3: worn road paint.
- Asphalt is now neutral, at its physical 2.1 m tile, with an always-mixed rotated second sample and subtle aggregate (cavity term plus distance-faded chips).
- The asphalt "grid" was **directional shadow acne**. It was inherited from V11's `shadow_bias` 0.04 and only exposed by the cleaner asphalt; proved by tests with constant material and with shadows off. Now 0.1; stair-nosing and tree contact shadows are unchanged. Codex's `shadow_normal_bias` 0.65 was reverted to 1.2.
- Daylight: V11 warm ambient and sun restored; Codex's glow-off and 0.96 exposure kept.
- Generator: `candidate/src/utilities/v12_realism.py` mirrors the Godot setup. Files: `candidate/game/godot/scripts/pbr_materials.gd`, `scripts/campus_loader.gd`, `shaders/ground_surface.gdshader`, `scripts/main.gd`.

**PBR assets applied (Poly Haven CC0; manifest `candidate/game/godot/assets/pbr/manifest.json`):**

| Asset | Where it is used |
|---|---|
| `asphalt_01` | External carriageways and road paint |
| `concrete_pavers` (1.92 m) | Internal interlocking paver roads (G1, approach, ring, Administration lanes; photo D02) and dormitory garden paths |
| `concrete_pavement_03` | Detail on slab sidewalks, G1 threshold, Administration forecourt, Academic court, curbs and edge restraints |
| `sand_01` | Detail on sand, soil and earth |
| `sparse_grass` | Detail on lawns and planted soil |
| `beige_wall_001` | Facades and stairs |
| `pachira_aquatica_01` | 14 trees (10 on the main approach, 4 at the Administration frontage) |

**Verification after the last source change:**

| Check | Result |
|---|---|
| Fresh full rebuild (scene, game assets, paths, source GLB, import) | All exit 0 |
| Source checks | 24/24 |
| V8 source checks | 30/30 |
| Game-asset checks | 15/15 |
| Geometry fingerprints | 1,845/1,859 meshes byte-identical to the V11 checkpoint; only the 14 intended trees changed; zero non-vegetation changes, so no curb-to-road reclassification |
| Tree bases (live Blender MCP ray cast) | All 14 within ±3.6 cm of ground, on lawn or planted beds |
| Material diagnostics | 18 maps, 0 failures |
| Regressions | **17/17 suites, 317/317 assertions**, including gates, both stairs, the full journey and the Arabic UI |

**Performance (RTX 4070, 1920×1080 High, FOV 84.25, VSync off):**
- Method: 10 stored views, 90+180 frames, alternating V11/V12/V11/V12.
- Aggregate: **V12 256.9 vs V11 265.9 FPS (−3.4 %)**.
- Slowest view: V12 209.2 (V11 207.9) FPS.
- Worst p99: 5.42 ms.
- Report: `output/validation/v12/recovery/claude/final/performance_v11_v12.json`.

**Windows candidate:**
- Executable: `output/validation/v12/recovery/candidate/releases/ZewailCityExplorer_Windows_V12/ZewailCityExplorer.exe`, SHA-256 `b879138d…f7f`.
- Packaged smoke test: 38/38, exit 0, v12.0.0 in PE file and app, source and GLB hashes match, 0 control ports, Arabic menu rendered.
- Remaining warnings: the 7 inherited Texture RID warnings.
- Evidence: `output/validation/v12/recovery/windows_build/`. Codex's stale 17:57 run is kept in `windows_build_codex_pre_claude/`.

**Comparisons and reviews:**
- 31 matched V11/V12 1080p boards (same pose, FOV, preset and resolution) in `output/validation/v12/recovery/claude/final/comparisons/`.
- Review sheets in `claude/qa/`.
- Four new eye-level junction poses (`tools/v12_add_road_poses.py`).

**Preservation:** all 220 archived V11 originals, the V11 scene and the V11 exe are byte-equal (`recovery/preservation.json`). Nothing was promoted, and `game/godot`, `src/` and `releases/ZewailCityExplorer_Windows/` are untouched.

**Unresolved:**
- Paver busyness at grazing angles. Two correction iterations were used: contrast 0.6 → 0.45, normal 0.26 → 0.17, more macro tone.
- Mixed tree styles. The approach has 14 Pachira trees among low-poly ones.
- A faint specular haze band on the mid-distance asphalt.
- The G2 ~25 m sand gap remains (not invented).
- No geometric curb or intersection repair was made; no broken curb was seen on the inspected route.
- Texture memory baseline for V11 is UNKNOWN.

**Agent accounting:**
- Parent: Claude Opus 5.5. Tokens, duration and cost UNKNOWN.
- Two independent visual-QA subagents on Sonnet: 88,754 tokens / 34.5 s and 89,322 tokens / 30.2 s. Quota and cost UNKNOWN.
- Codex was not invoked.

## V12 material continuation — 2026-11-08

**PARTIAL — isolated asphalt experiment only; no V12 release or accepted source change.** The existing checkpoint archive, Blender scene and V11 executable match their recorded SHA-256. Of 221 archived source files, 220 match current paths; only this status file differs. The live Blender scene matches the checkpoint and was clean. The repository has no Git metadata, so unarchived files cannot be classified as clean or dirty by Git. V11 executable remains unchanged.

Poly Haven `asphalt_01` CC0 1.0 originals (diffuse, OpenGL normal, roughness; 1K JPEG) matched the prior SHA-256 manifest in `output/validation/v12/material_trial/asphalt_01/manifest.json`. In an isolated Godot project at `output/validation/v12/material_trial/runtime_a/game/godot/`, a shader experiment samples the maps at the advertised 2.1 m tile scale on asphalt; no geometry or collision was changed. This experiment currently applies to all asphalt surfaces and retains original sampling, and is **not accepted**. Existing G1 approach views showed no change because the main approach is paver material, not asphalt. A new same-pose actual-game external asphalt close-up visibly changes: `output/validation/v12/material_trial/runtime_a/game_captures/asphalt_baseline_vs_trial.png`. Independent review identifies a brown/dusty result, broad bright patch, unverified normal/tangent orientation, unclear photographic fit, and additional texture sampling. Do not promote until those issues, additional views, physical scale, regression tests and benchmark are resolved. No pavement, sand, foliage, lighting, or architecture changes were implemented.

Godot 4.6.2 Forward+ on RTX 4070 rendered the isolated trial and original V11 source at 1920×1080 High, FOV 84.25, VSync off, same new detail pose, 90 warmup and 180 measured frames. Single-view samples: V11 319.7 FPS (3.13 ms), trial 294.2 FPS (3.40 ms); these are not the required 10-view aggregate benchmark and do not establish performance acceptance. Both detail runs exited 0; seven inherited Texture RID shutdown warnings remain. No regression suite, candidate export, or packaged smoke test was run for this trial. The seven warnings were not root-caused.

Blender MCP successfully inspected the actual editable scene and asphalt source; installed addon protocol 14 vs server 15 warning remains. Godot MCP inspected the isolated editor scene tree, and real runtime captures were made with the existing capture harness. Original Blender scene, game source and executable remain unchanged; V11 remains the release. G2's approximately 25 m external gap and the prior rejected geometry candidate remain unresolved.

Agent accounting: two read-only child tasks (asset/license scouting and baseline audit, the latter also independent trial visual QA); inherited user-selected parent model; actual provider/model, durations, tokens, quota and costs UNKNOWN. Parent accounting UNKNOWN. Source and runtime artifact locations above are evidence, not a completed release.

## V12 execution — 2026-11-08

**V12 PARTIAL — candidate rejected; V11 remains the release.** A lightweight checkpoint is under `output/validation/v12/checkpoint/` (source archive and editable Blender scene; not a full project backup). V11 Windows smoke rerun: 37/37, exit 0, no control ports. Blender MCP inspected the V11 scene with an addon protocol 14/server 15 warning. Godot MCP inspected editor and bridged runtime after starting an owned editor/runtime.

An isolated generator candidate fills the G1 lane seam. Same audit: exposed clusters 11 → 9, sliver metrics 7199 → 7184, height-step clusters 1007 → 1005, curb kinks 29 → 29, curb stubs 24 → 24. However, same-grid surface comparison detects 12 curb-to-road samples as well as 10 sand-to-road: `output/validation/v12/class_delta.json`. Independent read-only review recommends rejection; the nine matched comparison boards in `output/validation/v12/comparisons/` do not establish visible improvement. Source candidate and generated artifacts remain isolated under `output/validation/v12/candidate/`; no candidate is promoted. The next candidate requires protecting existing curbs and a fresh visual and collision evaluation; the requested one targeted correction has already been used.

Poly Haven asphalt maps are downloaded for evaluation only: `output/validation/v12/material_trial/asphalt_01/manifest.json`. License CC0 checked against the provider, 1K originals verified by provider MD5; scene fit and physical UV scale not yet tested. No material, asset, lighting, or release change is claimed. G2 external connection remains unresolved.

Agent accounting: asset scout read-only, inherited parent model (actual model/provider UNKNOWN), self-reported approximately one minute; token usage and cost UNKNOWN. Independent QA used requested `gpt-6-luna` medium override; actual provider/model telemetry, elapsed time, tokens, and cost UNKNOWN. Parent model/provider, elapsed time, token usage and cost UNKNOWN. Candidate verification: 17/17 existing suites exited 0; logs contain no `[FAIL]`, numbered failed summary, or script error. The continuous G1-to-dormitory journey passed with zero floor losses. Native RTX 4070 1920×1080 High, 10 stored V11 views, VSync off, 90 warmup + 180 measured frames/view: candidate aggregate 266.5 FPS versus V11 273.7 (−2.6%); slowest candidate view 208.9 FPS; 357–1552 draw calls. These are measurements for the rejected geometry candidate, not an accepted V12. Texture memory was not captured and remains UNKNOWN. Seven Texture RID shutdown warnings persist. Full report: `output/validation/v12/performance/summary.json`.

## Actual recovery changes
- Closed the real pedestrian bypasses at G1–G6: all vehicle/pedestrian leaves share gate state (19 leaves).
- Secondary vehicle leaves overlap pylons at local t=-1.20 m; original local leaf orientation is retained.
- Corrected the G3 test's use of an oblique approach vector as a plane normal. The original final position was outside the leaf; expanded physical checks independently enforce complete closure.
- Replaced unsupported P15 upper court-bridge curtain glazing with the photographed blank stone face/course joints.
- Preserved integrated Arabic RTL UI; corrected the obsolete English tour mention of courtyard palms.
- Added bounded regressions, full continuous journey, complete-width walking/rays, swept-capsule edge-route checks and strict actual-pixel/VSync capture verification.

## Executed verification
**17/17 suites; 317/317 assertions** (includes inherited/base assertions, not a unique-test count).

| Suite | Passed |
|---|---|
| Validate | 54/54 |
| V5Ground | 5/5 |
| V5Gates | 12/12 |
| V5Academic | 27/27 |
| V5Dormitory | 4/4 |
| V6Academic | 32/32 |
| V6Dormitory | 12/12 |
| V5Journey | 1/1 |
| V6Journey | 1/1 |
| V8Gates | 27/27 |
| V8Entries | 9/9 |
| V10AdminEntry | 23/23 |
| V11Gates | 37/37 |
| V11GateCoverage | 18/18 |
| V11PerimeterSeal | 12/12 |
| V11FullJourney | 2/2 |
| V11Ui | 41/41 |

Source checks 24/24; V8 source checks 30/30; game-asset checks 15/15; 113 unique source meshes validate without repair/nonfinite vertices.
Gate coverage: 1,392 frontage rays at 0.5 m intervals in both directions; 380 real walking trials with valid starting side, collision enabled, open/closed states and edge attempts. Swept player-capsule flood finds no closed route and a valid open route at all six gates within the tested frontage bounds.
The full outside-G1 → approach → Administration landing → Academic A → BOTH major stairs/hall/bridge → court ramp → rear → dormitory journey uses one initial placement, no later teleport/fly/jump, zero floor losses (maximum measured floor gap 0.189 m).
UI: 41 contracts + 56 rendered/native-display checks; actual captures at 1920×1080, 1280×720, 1366×768 and 2560×1440. Arabic menu, E operation/flight suppression, pause/resume/photo suppression, settings persistence and tour/location controls verified.
Actual Blender MCP reopened final source after saving the prior dirty live state; actual Godot MCP inspected editor/runtime, captured the menu, clicked Start and captured exploration. Only owned Godot verification processes were stopped.

## Performance (RTX 4070, actual 1920×1080 High)
10 identical stored poses, FOV 84.25; 90 warmup + 180 measured frames/view; VSync verified OFF after native settings, max FPS 0. No other task GPU job during final measurements.

| Metric | V10 | V11 |
|---|---:|---:|
| Aggregate FPS from measured mean frame times | 234.1 | 273.7 |
| Arithmetic mean of per-view FPS | 240.3 | 277.1 |
| Slowest view FPS | 162.4 | 215.1 |
| Worst view p99 (ms) | 6.97 | 5.27 |
| Draw-call range | [329.0, 1491.0] | [357.0, 1552.0] |
| Engine rendered-primitive range | [3757070.0, 4762886.0] | [3996579.0, 5033999.0] |
| Campus load + prepare (single warm run, ms) | 1634 + 25 | 2043 + 39 |

p50/p95 per-view ranges and all raw measurements: `output/validation/v11/final/performance_v10_v11.json` and HD capture reports. V11 passes 60 FPS at every measured view; loading and geometry/draw counts increased despite better measured FPS here. Results apply to this workstation/method, not all hardware/views. Packaged capped sample is separate from this uncapped comparison.

## Terrain and remaining architecture
Fresh audit: exposed-terrain clusters 85 → 11; 0 missing surfaces, 0 floating slabs, 0 tree trunks on paving; one connected paved component. Sliver metric 5,003 → 7199; height-step clusters 1007; curb kinks 29. These regressions remain recorded; mesh validity and traversal pass, but this is not a claim that every curb/aesthetic defect is fixed.
Owner issues: {'FIXED': 7, 'PARTIAL': 8, 'BLOCKED': 2, 'NOT DONE': 0}. Full source/validation/before-after/uncertainty entries: `output/validation/v11/final/OWNER_ISSUE_REVIEW.md` and `owner_issues_00_16.json`.
Remaining: residual sand shoulder/curb appearance (03/15), facade/sign scales and some entrance/bridge proportions (07/09/10/13/16), uncalibrated wing extents (11), incomplete facade response and uncertain original location for issue 12. The inherited O12 camera inside a wall is rejected; replacement candidate views are labelled. Dome cap is visible from the upper terrace, still hidden from the forecourt; heights were not reduced further without evidence.
Dormitory six-row facade, recessed windows, green hedges and branching garden paths are present and traversable; no additional dormitory redesign was invented during recovery. Geographic candidate identity and precise proportions remain unverified. G2–G6 architecture/operation is estimated. G2's external ~25 m sand gap remains UNRESOLVED and unextended. No survey-grade accuracy claim.
Seven Texture RID shutdown warnings persist on rendered Godot exits (previously documented); no script/runtime errors occurred in final acceptance runs. No human playtest or fresh independent human architectural acceptance is claimed.

## Delivery and preservation
- **Tested Windows executable:** `releases/ZewailCityExplorer_Windows/ZewailCityExplorer.exe` — 11.0.0 PE/app/manifest, 37/37 packaged checks, exit 0, no control ports even with `--mcp-bridge`; SHA-256 `b0f0cef1dcbbc156a76a6296687b857f9ee7db84016c2e07f9fcd3c6b390601a`.
- Authoritative scene: `output/Zewail_City_3D.blend`; game GLB: `output/game_ready/campus_full.glb`; game copy and manifest hashes match. Full source GLB re-exported/reimported, camera paths re-exported.
- Fresh **60 matched 1080p comparison boards + 12 gate state boards:** `output/validation/v11/final/comparisons/` (matching camera/FOV/preset and actual image pixels checked).
- **New guided tour:** `output/validation/v11/final/tour/v11_guided.mp4` — 1920×1080, 30 FPS, 4559 frames, 151.967 s; full decode passes and sampled frames visually inspected. Recording throughput is not an exploration benchmark.
- Recovery source checkpoint: `output/validation/v11/recovery_20261108/unfinished_v11_source.zip`; original gate failure retained there. Prior dirty live Blender state: `output/validation/v11/final/mcp/live_before_reopen.blend`.
- V10 backup `backups/v10_pre_v11_20261108T105635Z/`: **1,356/1,356 SHA-256 matches**, 3,951,608,517 bytes; untouched. Historical comparison images preserved. Benchmark uses a bounded 244 MB working resource copy, not another multi-GB historical backup.
- Rejected early timing/capture runs and first failed candidates remain in final evidence/iterations; only `final/hd` and `final/benchmark_v10/hd` supply final performance/capture acceptance.
- Cross-artifact acceptance: `output/validation/v11/final/delivery_verification.json`.

**Readiness:** playable, technically verified V11 Windows delivery; overall V11 remains PARTIAL because the architectural/visual issues above are not fully resolved.
