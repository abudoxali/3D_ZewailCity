# V11 architectural reconstruction — 2026-11-08

Recovery addendum (Codex, same day): shared source now makes pedestrian leaves participate in G1–G6
closure (19 total leaves). Secondary vehicle leaves overlap the pylon plane at local t=-1.20 m.
These operational details are engineering estimates, not photographed gate mechanisms. G3's original
walking failure used its oblique inward approach vector as a gate-plane normal; corrected measurement,
complete-width rays, real walking and swept-capsule edge-route verification are retained in
`output/validation/v11/final/`. The P15 upper court-bridge face is now blank stone with thin horizontal
joints instead of the draft's unsupported curtain glazing. Side windows and full bridge dimensions
remain estimated. Existing P16 dormitory improvements were inspected and retained; no new unverified
rooms or facade redesign were added. The 17 issue dispositions and remaining uncertainties are in
`output/validation/v11/final/OWNER_ISSUE_REVIEW.md`. Historical evidence below is preserved.

V11 keeps the coordinate frame, OSM footprints, gate IDs/positions and the V10 evidence classes:
**PHOTO VERIFIED** (PV), **OWNER CONFIRMED** (OC), **OWNER MARK** (OM: a red line/X on the V11
owner screenshots, interpreted — not a measurement), **MAP SUPPORTED** (MS), **ESTIMATED** (EST),
**UNVERIFIED** (UNV). Every new metric dimension is EST. The owner screenshots are in
`references/owner/v11/V11_OWNER_MARKUPS/`; Wave 0 audits are in `output/validation/v11/reviews/`.
This is an estimated reconstruction, not a surveyed digital twin.

| Element | V11 change (permanent source) | Evidence | Class |
|---|---|---|---|
| Academic core (between the prongs) | Rebuilt as a two-level system (`v11_academic.core`): enclosed ground-floor lobbies flank an open lower passage (|x| < 7 m); a 10 m deep open upper terrace at 4.41 m in front of the glazed core; a covered upper hall under the core block; a bridge projecting ~21 m into the court (|x| < 16.4 m) on stone piers; two railed voids (11.6 × 8 m and 11.6 × 31 m) look down into the passage. V10's 3 m deck strip, open 7 m hall and passage ceiling slab are removed | Owner (V11 brief): upper walking level reached by two large stairs, open terrace, void overlooking the ground floor with balustrades, main hall at this level; 11 red line ≈ 10 m in front of the core and court-side bracket ≈ 34 × 21 m; P09 camera stands on the central deck; P15 deep stone bridge/portal | OC + OM + PV (form); all dimensions EST |
| Great stairs | Two 12.5 m flights (|x| 7–19.5, V10 10.5 m) from the forecourt (foot y −208.9) to the terrace front edge (y −219), 28 × 0.15 m risers, 0.36 m treads, dark granite nosings, side + mid-flight rails; planters at the deck corners | Owner: stairs too small and misplaced, must reach the upper terrace; P09 rails and corner planters | OC + PV (rails/planters); size EST |
| Academic balustrades | Collidable 1.1 m metal balustrades around both voids, the terrace front between the stairs and the bridge edges | Owner: protective railings around real drop-offs | OC; layout EST |
| Gate (A) signage | Arabic sign enlarged to ~27 % of the core width (was 1.1 m text); "Gate (A)" 0.5 m letters on the lower fascia between the stairs | D05/P09 proportions | Name PV; size EST |
| Upper-level entrances | Glazed entrance doors on the solid prong walls that bound the covered hall (no walk-through glazing) | Owner: main entry/hall relationship at the upper level | OC; positions EST |
| Academic entrance registry | `references/academic_entrances_v11.json`: Gate (A) (front), Gate (C) (ring 225°), UST / Gate (F) (+X side-wing corner), an unnamed −X side entrance, an unnamed 315° entrance, the rear passage. Only photo-read names are written on the model | Owner: Gate A, Gate C + ~4 entrances, names to be confirmed; 11: five X marks around the ring; P12 (Gate C), P14 (UST/F, dome on the right) | Names PV (A, C, F only); positions OM + lettering hypothesis EST |
| Gate (C) | Moved from the rear aperture to the 225° X mark: P12-style 14 m tall glazed bay (~4 storeys, 3 bays), stone frame, two door pairs, sign on the glass, landing + 3 steps | P12 form; owner 10 | Form PV; position EST |
| UST / Gate (F) | Moved from the +X prong face to the +X side-wing corner (owner 13): flush black 6 × 23 m panel with "UST" and "Gate (F)", glass box toward the corner, 9 steps + rails | P14; owner 13 corner | Form PV; position OM + EST |
| Rear passage | Ring aperture (266–274°) kept open; blank tunnel walls replaced by glazed lobby returns and soffit downlights | Owner 09 (court connects to the rear area) | OC; dimensions EST |
| Admin rear blocks / dome sightline | Academic-facing rear block 25 → 18.0 m, link block 25 → 20.4 m so the drum and dome rise above it from the Academic deck (P09 vantage) | P09; owner 16 | PV (sightline from the deck); heights EST |
| Admin rooftop trellis | Removed | Owner 00 X; only a weak A01 aerial hint; A02/A03/P08/P09 show nothing above the parapet | OC + PV (absence) |
| Admin forecourt beds | Striped red/orange/hedge ribbons on the drop-off islands removed; arm beds are low pebble-edged red/orange strips; approach circle kept and restyled (pebble ring, red mulch, euphorbia) | Owner 00 X; A02 low flower rows; C02 circle | OC + PV |
| G1 main gate | Stone return walls from each lane post to the portal leg close the walk-around strip; both lane leaves are separate sliding objects (E closed, W open at start, as C02) with real colliders, operated with E | Owner 02; C01/C02/D02 | Form PV; return walls + travel EST |
| Perimeter at G1 | Connector walls join the gate-complex ends (x ±61.7, GY+2.4) to the staggered plot line, closing the 9 m (+x) and ~23 m (−x) leaks | Owner 04; QA flood fill | MS + EST |
| G2–G6 | Rebuilt in G1's language: stone pylons with the ledgestone inverted-U inlay, a lintel with the gate number, black lattice sliding leaves (start open; closing blocks the opening), framed pedestrian bay beyond the parked leaf, wing walls to the perimeter cut | Owner 06; no secondary-gate photograph | **Conceptually standardised design — EST/UNV as-built**; positions PROVISIONAL_MAP_CLUSTER |
| Ground partition | Sidewalks continue through junction zones (cut by carriageways); medians are curb rings around a planting bed (palms no longer on concrete); enclosed sand slivers < 3.5 m between hard surfaces become paving (morphological closing); footway ends within 12 m of a hard surface are joined; G1 lanes paved through the portal; desert sand graded up to raised apron edges; trees/palms on walks moved off or removed; approach trees 3 m outside the walk; gatehouse footing below the sand. Log: `output/validation/v11/ground_repairs_v11.json` | Owner 03/05/12/15; QA baseline | EST (engineering) |

Not changed and why: G2's ~25 m external sand gap stays UNRESOLVED (no evidence for a public road);
Academic wing ends/footprint stay on OSM 540106547 (owner 11 verticals were not read as a footprint change);
no interiors are invented behind the new doors.
# V10 architectural corrections — 2026-11-08

V10 keeps the coordinate frame, OSM footprints, building heights, six gate IDs and
positions, spawns and landmarks. Evidence classes: **PHOTO VERIFIED** (PV),
**OWNER CONFIRMED** (OC), **MAP SUPPORTED** (MS), **ESTIMATED** (EST),
**UNVERIFIED** (UNV). Every new metric dimension is EST unless stated. Reviewers:
`campus-evidence-auditor` and `campus-geometry-reviewer` (Claude subagents, read-only)
and Codex CLI (independent implementation of the Administration entrance and an
independent review). Their reports are in `output/validation/v10/reviews/` and
`output/validation/v10/codex/`.

| Element | V10 change (permanent source) | Evidence | Class |
|---|---|---|---|
| Academic inner courtyard planting | The two palm beds at (±59.5, −253.5) and four benches beside them are removed (`academic_public.build_spaces`). No tree, palm, planter, kiosk or pergola remains in the court | Owner correction (V10 brief): no trees in the inner court; P13 shows open hardscape | OC + PV |
| Academic forecourt (between the prongs) | The six "D05" trees at x = ±13.5 and the two curbed red-shrub beds are removed (`site.build_vegetation`, `site.build_landscape`); the random stream is consumed identically so all other planting is unchanged | P09 shows the forecourt between the prongs as open paving with nested dark inlays (low planters appear only at the lower stair corners); D05 is a possibly enhanced image | PV |
| Academic forecourt arcades | Each prong's forecourt face is a real double-height arcade: ground storey set back 3.2 m under the upper floors, 1.8 m square stone piers at 5.6 m pitch on the facade line with dark inlay bands, recessed glazing, stone fascia and soffit, paved floor (`buildings.academic`, `ARC_*`). Stops 1 m before the great stairs | P09: stout square piers forming a covered colonnade under the wing ends. The glazing behind the piers is not visible in P09 | Pier colonnade PV; set-back depth, glazing, height and pier size EST |
| Academic upper glazed boxes (prong faces) | ~20 m wide (V9 12 m) with heavy dark frames dividing big panes into 4 × 3; slits only beside the box | P09 | Form PV; width EST |
| Academic inner court facade | Near-black reflective court glass; dark cantilever soffits; glazed recessed balcony bays (V9 showed blank white walls); 2 m deep cream crown fascia (V9 1 m strip) | P13 | PV + OC; proportions EST |
| Court tiers | The 150 mm intermediate tread is dark granite like the riser, so platform edges read as P13's dark curbs instead of grey stairs | P13 | PV; levels EST (unchanged V7 radii/levels) |
| Great stairs | Unchanged geometry and collision proxy; paving now extends under both flights (V9 right flight stood on graded soil); no arcade pier stands on a tread | P09; geometry audit M2 | PV / EST |
| Administration principal entrance | Five slender round columns replaced by two 1.4 × 1.4 m square stone piers at x = ±7 (Codex: A02 measured at 21.8 px/m); ground glazing recessed 2.5 m behind yF; two 2.2 × 2.8 m open doorways (functional estimate: A02's entrance is hidden by a palm, and the doors are not visible from the axis camera); lower glazing panels are collidable; V8 steps, 0.72 landing and side ramp retained (`v10_admin_entrance.py`) | A02 shows square supports under a stone band and a dark recessed ground floor; no round columns. Door count/positions are hidden by a palm | Supports PV; positions/sizes EST; doors EST |
| Administration lobby shell | Bounded vestibule: floor 0.72 continuous with the landing, 4.2 m ceiling, side walls, closed back wall 12 m behind yF; slab tagged `v10_admin_vestibule_floor` for future interior work. No rooms, floors or halls invented | Recess visible in A02; interior not photographed | Shell EST; interior UNV |
| Dormitory facade | 0.2 m stone skin of piers and spandrels: windows are recessed with reveals, projecting sills; stair cores carry one ~1.1 m window per landing and a glazed entrance door (V9 2.5 m glass strip) | P16, P10 | Form PV; dimensions EST; building identity UNV |
| Dormitory garden | Lawn/hedge compartments extended to the courtyard's convex enclosure (V9 left a bare soil wedge); bed shrubs green (V7 red/golden accents came from a lower-priority official image) | P16 (owner) over the official dorms image | PV; extents EST |
| Road junctions | Inside the existing junction zones the unified road outline is closed with a 4 m kerb radius (166 fills, 1,229 m²) and a 0.3 m curb return follows each new edge (151 m²); approach-median noses are rejected by rule (`ground_system.junction_fillets`, report `output/validation/v10/junction_fillets.json`) | Engineering practice; geometry audit M1 width mismatches | EST |
| Vehicles | All 159 cars moved to `Optional_Vehicles_Disabled` (excluded from the view layer, hidden from render, removed by both exporters) | No photograph shows parked or moving cars | Removal |
| Rendering | New optional Ultra preset (SDFGI + TAA); High/Medium/Low unchanged | Engine capability | — |

Not changed in V10 and why: G1–G6 gate architecture (no new gate evidence; G2–G6 stay
PROVISIONAL_MAP_CLUSTER, G2's ~25 m external sand gap stays UNRESOLVED); the Academic
outer curved facade and Gate C (P12 already matched at the V9 level of detail); the dome
(not re-measured in V10; the final audit notes that A02 reads as a larger ribbed dome on a glazed drum than the eye-level renders show, which should be checked in V11); external-road curbs (performance only).

# V9 ground, roads and environment realism — 2026-11-08

V9 keeps the coordinate frame, roads, building elevations, six gate IDs and
positions, spawns, landmarks and every evidence classification. No new
photograph, survey or DEM was found or used. Every new dimension below is an
**ESTIMATE** chosen to be conservative and physically coherent.

| Area | Permanent implementation | Evidence and limits |
|---|---|---|
| Ground material defect | V8's baked 6 m natural-ground tiles were near-uniform (desert-sand albedo s.d. 0.8 %, normal 0.5 %; asphalt 1.4 % / 0.5 %): tone at 20–80 m scale cannot appear inside one tile, grit used a narrow threshold, relief a 3 mm bump, and the half-offset seamless blend halved what remained | Measured from the V8 bakes with `tools/v9_material_lab.py` (`output/validation/v9/iterations/lab_stats.json`) |
| Natural ground | `src/utilities/v9_ground_materials.py`: sand, graded campus soil, compacted earth and planted soil sampled on a flat 4D (Clifford) torus so every bake is natively seamless; lag gravel and grit (flint-brown / tan / pale limestone), low wind ripples on sand/soil only, sparse irregular groundcover clumps on planted soil. Bake s.d. 3.3–4.3 % albedo, 2.6–3.7 % normal | Palette from the existing photo-derived V7 earth colours (P07/P12/P14, C01/C02/D02 surroundings). Gravel/ripple sizes are generic desert-surface estimates; no stains, cracks, tyre marks or debris are invented |
| Asphalt / lawn | Dense asphalt (2048 px, 4 m tile): dark binder with exposed light limestone aggregate (s.d. 5.9 %, normal 5.9 %). Lawn: blade/clump texture with a few sun-dried patches (s.d. 3.5 %) | Asphalt colour range kept at the V7 sun-faded value; aggregate scale generic. Lawn colour kept from V7 |
| Micro-relief | `ground_system.relief()`: inside the wall ≤ 0.11 m at ~38 m + 0.035 m at ~13 m; outside within 450 m ≤ 0.22 m at ~90 m + 0.065 m at ~30 m; sampled maximum 0.19 m. Fades to exactly 0 within 1.5 m of every road, paving, wall, building, bed and lawn edge (full beyond 12 m). Terrain meshed at 5 m (campus) / 10 m (near desert); planting follows it | **ESTIMATED, no DEM.** No hills, cuts or excavations. Known road, paving, building, wall and gate elevations are unchanged because relief is zero there |
| Road edges | Soil graded up to the finished road level at every road edge (V8: 4.8 cm below, no edge face, read as a floating slab); lawn/planting likewise (V8: 2.8 cm). 1.6 / 1.2 m smooth fade resolved by an inner edge ring | Standard flush shoulder; actual site grading unsurveyed |
| Ground mask | Per-vertex `ZC_Ground_Mask` (exported as glTF COLOR_0): R fine-sand drift within ~1.4 m of hard edges and ~0.9 m of road edges, G relief (crests slightly darker/gravellier), B contact occlusion within 1.2 m of building footprints and the perimeter wall | Wind-blown sand at kerbs and wall feet is typical of desert campuses; amounts are restrained estimates |
| Gate aprons G2–G6 | Rectangular V8 aprons replaced by the same area filleted (r 2.4 m) where they join the internal link and rounded (r 0.9 m) at outer corners; full opening width kept 1.2 m either side of the wall line; 0.2 m flush concrete edge restraint where aprons meet soil (27.8 m² total) | Shapes are engineering interpretations. **G2–G6 remain PROVISIONAL_MAP_CLUSTER.** G2's ~25 m external sand gap remains **UNRESOLVED** and was deliberately not filled |
| Gate supports | Projecting 0.55 m plinth course, thin stone cap slab over the dark band, flush 4 mm steel sliding-leaf track across the vehicle opening | Restrained family detail echoing G1 materials; not photographic copies of real secondary gates |
| G1 | Architecture, dimensions and cream-beige identity unchanged; surrounding ground materials only | C01/C02/D02/D03 unchanged |
| Stairs / entrances | Unchanged. A heuristic contact probe gives identical results on V8 and V9 sources (`contact_probe_v8/v9.json`); no defect was confirmed, so no geometry was modified | Runtime stair, passage, ramp and route tests pass |
| Lighting | Global day/evening rigs unchanged (no grading, bloom or fog change). Ground shader adds ambient-only contact occlusion from the mask (AO light affect 0.2) | Keeps V8/V9 differences attributable to geometry and materials |
| Mesh validity | V8 `Plaza_Paving` had 5,635 duplicate faces (skirts emitted on both sides of shared internal paving edges), 76 repeated-vertex and 100 zero-area faces; similar in `Plaza_Academic_Courtyard` and `Road_Curb_Edges`. V9 mesher emits skirts only on the outer footprint and drops degenerate/duplicate faces: 0 duplicates, `mesh.validate()` changes nothing. The glTF exporter validates in place: planar simplification of `COL_Ground` left 3 duplicate faces, now repaired and logged in `build_game_assets.py` before export; the final export prints no "not valid" warning (V8: 6) | Verified through Blender MCP on the reopened V8 and V9 sources and the export logs |
| Texture RID warning | "7 RIDs of type Texture were leaked" is produced by any ReflectionProbe in Godot 4.6.2, even in a minimal scene and even when the probe is freed before quitting; scenes without a probe print nothing. The count is fixed (atlas-level) and only at shutdown. No RenderingServer API releases the reflection atlas; the two V7 probes are kept | Reproduction: `game/godot/tests/V9LeakProbe.tscn` (`--mode=env_probe_box` vs `--mode=env_box`), logs in `output/validation/v9/leak_probe/` |

# V8 ground, frontage and gate assemblies — 2026-11-07

V8 retains the existing coordinate frame, six gate IDs/positions, fourteen spawns,
landmarks and evidence classifications. No secondary-gate photographs were found
in the existing reference set. G2–G6 are **PROVISIONAL_MAP_CLUSTER** and their new
architecture is an editable engineering interpretation, not a photographically
verified reconstruction. Open leaves express local explorer traversability, not
current operating status or verified public access.

| Area | Permanent implementation | Evidence and limits |
|---|---|---|
| G1 stone | Cream-beige linear albedo 0.64/0.595/0.50–0.72/0.675/0.58; roughness 0.70; 0.8 × 0.6 m panels, recessed 8 mm joints and baked normal response | C01, C02, D02; colour/roughness approximate, images not colour-calibrated |
| G1 portal | Original 33.4 m overall width, 4.8 m legs, 18.7 m height retained | Successful prior proportions retained; photo dimensions approximate |
| G1 frontage | Recessed campus-side masses 9.8 m, piers 10 m; lower C01 exterior pavilions retained; frontage boundary ~6 m | C02 supports taller campus-side silhouette; C01/C02 perspective/date conflict is NOT resolved by survey data |
| Perimeter | ≤3 m terrain-following runs, 0.42 m wall, 0.90 m footings embedded 0.45 m; pilasters and coping; remote wall height retains prior 3.5 m estimate | OSM boundary retained; construction dimensions, grading and unphotographed wall type ESTIMATED, no DEM |
| G2–G6 | Independent opening/orientation/support/frame/leaf/pedestrian/threshold/wall parameters in `src/utilities/v8_gates.py`; smaller masonry/steel assemblies, sliding leaves parked along flank walls clear of original diagonal approaches, nominal 1.7 m pedestrian bays; yellow floating marker meshes removed | Owner six-gate inventory + paired OSM nodes (~10.6–13.9 m spacing). Spacing constrains an envelope; it does NOT establish lane count, actual opening width, access class or appearance |
| Gate ground | Local 6 m deep aprons and bounded INTERNAL connectors enter the disjoint road/ground partition; no layered slab over existing road | Surface joins are engineering estimates; positions/geographic road alignment retained |
| G2 external | **UNRESOLVED.** Existing mapped branches still stop in sand ~25 m before external road. No connecting road added | Local crossing test is not through-access to the external road |
| Administration entrance | 0.72 m portico landing joins the existing three 0.17 m risers; 1.8 m wide, 10.2 m long nominal 6.5% side ramp in a cut stair channel; slender rails | Actual generator defect: steps previously ended above the forecourt without a matching landing. The ramp foot matches the confirmed 0.06 m internal-road surface. Exact deck/ramp arrangement is a provisional accessibility interpretation, not photo verification; facade stays closed |
| Academic stairs | Upper landing exposed outer-edge rails continue 2.95 m beyond last nosing; inner walkway connections stay open; existing 28 × 150 mm risers, 360 mm treads, 4.41 m landing and source-derived collision inclines retained | P09 + owner paired stairs; engineering dimensions estimated. Existing passage/court/ramp/rear route retained |
| Curbs | No global curb-height correction | Previous 2,832-location investigation found zero sidewalk samples >8 cm below adjacent curb tops; disproven defect was not used to modify curbs |

Current executed checks, measured gap distances, provenance, renders and matched
before/after camera sidecars are saved in `output/validation/v8/`. Historical V7
source and playable release remain in `backups/v7_pre_v8_20261107T195155Z/`;
all 1,926 files (3,911,244,142 bytes) were re-hashed successfully before edits.

Final executed V8 validation: 24 source, 30 V8 geometry, 14 asset, 135 Godot and
32 packaged Windows checks passed. All 15 cinematic paths retain clearance;
G3's original diagonal approach and the full upper-walkway journey pass. Final
39-view 1080p benchmark: 165–167 FPS on RTX 4070; packaged 5-second sample
165.2 FPS. Actual MCP editor/runtime/source inspections and fixed-pose camera
sidecars are retained. Earlier failed candidates are preserved under `iterations/`.
Exporter plaza-validity and Godot shutdown texture-RID warnings remain documented
in README and logs; final geometry re-import and gameplay checks pass.

---

# Source evidence register

## V7 environmental fidelity and architectural detail — 2026-11-07

V6 is preserved, SHA-256-verified file by file, at
`backups/v6_pre_v7_20261107T154441Z/` (1,506 files, 2,827,863,320 bytes;
`manifest.json`). V7 evidence lives in `output/validation/v7/`; V4–V6 results
are untouched. Labels: **VISIBLE** (photographed form), **OFFICIAL** (Zewail City
web page), **OWNER-CONFIRMED**, **ESTIMATED** (dimension, spacing or quantity
fitted without a survey), **UNVERIFIED** (identity or location).

### New source consulted in V7

| ID | Source | What it shows | Used for |
|---|---|---|---|
| D-DORMS | Official page `https://www.zewailcity.edu.eg/dorms` (read 2026-11-07 in a browser; image `zcadminpanel.zewailcity.edu.eg/uploads/222222222_1_dce6228fe6.png`, not downloaded) | Curved courtyard residence with **six window rows (ground + 5)**, glazed stair cores rising above the roof, a grey base plinth, paver paths, red-flowering and golden-green bed shrubs, black bollards. Text: dorms inaugurated 15 Sep 2018 (281 beds); additional building received 13 Mar 2021 (93 rooms); 241 rooms / 467 beds; a laundry room "for each building". | Storey count, plinth, cores, bed-shrub colours. The page does **not** locate the residence on the campus map. |

### Changes by area and their basis

| Area / source module | V7 change | Basis | Status |
|---|---|---|---|
| Ground materials `materials.py` | All unit paving and stone cladding: joints are now recessed (Blender's Brick *Factor* is the mortar mask; V6 bump-mapped every joint upward). Per-unit grain and rougher joints. | Blender manual (bundled `shader_nodes/textures/brick.rst`); P05/P09/P11/P13 surfaces | Material defect fixed |
| Asphalt, curbs, earth, sand | New aggregate shader: sun-faded asphalt albedo 0.09–0.14 with light limestone aggregate (V6 0.03–0.07 read as black plastic), concrete curbs with grit, earth/sand with pale grit and clods | C01/C02/D02 road photos; P07/P12/P14 earth | Tone and roughness ESTIMATED |
| Academic forecourt and court slabs | Light grey-beige honed granite (albedo ~0.44–0.61, roughness 0.46–0.50). V6's 0.22–0.28 / 0.32 reflected the blue sky as saturated blue paving. | P09, P13 at full resolution | VISIBLE tone; exact stone unknown |
| Ground topology `ground_system.py` | Flush 0.16 m concrete edge restraint wherever unit paving meets soil or planting (disjoint partition is kept). Graded shoulders: soil rises up to 0.16 m over 1.6 m, lawn/planting 0.14 m over 1.2 m, toward raised paving, curbs and building foundations (V6 left 0.18–0.20 m vertical faces). Road markings now sit 12 mm above asphalt (V6: 4 mm). | P07/P11 paving-to-earth edges; standard paving construction | ESTIMATED grading and edge detail |
| Rear desire line `dormitory.py` | Irregular worn edges (1.0–1.8 m half-width) instead of a ruler-straight ribbon | Owner: bare rear ground | Alignment remains an ESTIMATE, not a mapped road |
| Academic court `v6_academic.py` | Tiers are now concentric with the inner glazing (centre 0,−249; radii 62/51/40 m; tops 0.51/0.81/1.11 m) with dark polished granite risers and coping, stepped north faces and half-height treads (≤150 mm risers). The ramp is re-cut to x 9–12 m, y −312 → −285.5 m (3.4%). | P13: the dark-coped platform edge runs parallel to the curved glazing a few metres from a ground-level viewer; P15 terraced plaza | Form VISIBLE; radii, levels and ramp ESTIMATED |
| Court poles, seating, palms | 13 slender dark poles with small luminaire heads at a regular 9.5° rhythm on the platform (replacing 8 ad hoc poles); four low black granite seat blocks on the walkway; the two owner-described palm beds move to the open apron north of the platform | P13/P15 poles, P13 seat blocks; owner (palms) | Count and positions ESTIMATED; pole luminaire function ESTIMATED |
| Academic entrances and passage `v7_lighting.py` | Recessed downlight fixtures in the P15 portal soffit, the Gate (A) canopy and the P12 Gate (C) band; evening sources at each, plus a wall light at the P14 Gate (F) hypothesis | P15 portal / D05 canopy; fixtures themselves not photographed | Fixture count/spacing ESTIMATED |
| Dormitory candidate `dormitory.py` | **Six storeys** (ground + 5; V6 five); window pitch 3.3 m (V6 3.8 m); lighter sky-reflective two-pane glazing; curtains drawn to varied heights behind about two thirds of the windows; grey stone plinth; stair cores rise one storey above the roof with grey floor bands | P16 enlarged; D-DORMS | VISIBLE form. **Conflict:** the OSM candidate footprint is tagged `building:levels=5`. Geographic identity remains UNVERIFIED |
| Dormitory garden | Loose-stone border between paver paths and planting (V6 left exposed soil); hedges with a softened two-step crown; 327 low round bed shrubs in rows (green, red-flowering, golden-green) 1.75 m from the path edges | P11 (stone border), P04/P16 (shrub rows), D-DORMS (flower colours) | Plan, counts and species ESTIMATED |
| Vegetation `vegetation.py` | Broadleaf trees: trunk, four limbs and 13 crown clumps in two foliage tones (V6: six spheres on a pole). Date palms: 18 pinnate fronds with paired drooping leaflets. Shrubs: three-lobe clumps. No new tree or lawn positions on documented bare ground. | General botanical form; positions unchanged from V4–V6 evidence (NDVI, photos) | Species generic; positions unchanged |
| Evening lights | 63 street-lamp heads, 13 court poles, 13 entrance downlights, 32 garden bollards: shadowless, range-limited, distance-faded; emission on lamp lenses only in the evening | Modelled luminaires only | Brightness/colour ESTIMATED |
| Main gate | Geometry and position unchanged (V4 photo reconstruction retained). Stone panels gain recessed joints and grain; apron ground gains graded shoulders and edge restraints. | C01/C02/D02/D03 | No new dimensions |
| Provisional gates G2–G6 | Unchanged: provisional representations, separate from building entrances B-C/B-F | OSM node clusters, owner count | Architecture/access UNVERIFIED |

### Not changed, deliberately

* No classrooms, offices, dormitory rooms, laboratories or cafeteria were created.
  The cafeteria doorway and exterior access remain unresolved; the low-resolution
  sign visible in P13 is not reproduced.
* P09's large framed window bays at the wing ends near the upper landing are not
  remodelled in V7 (the existing double-height colonnade and slot windows remain).
* Survey-based road alignment (V4/V5) is unchanged. No road connections were added.

## V6 owner-photo corrections — 2026-11-07

The prior register below is retained. The detailed V6 mapping is
[`OWNER_PHOTO_EVIDENCE_V6.md`](OWNER_PHOTO_EVIDENCE_V6.md): all 16 original hashes,
photo clusters, model objects, approximate camera poses and explicit comparison links.
P09/P13/P15 replace the V5 generic Academic arc with projected glass volumes,
recessed balcony voids, light-stone bands, three semi-circular court levels and a
deep stone portal. Bilateral major stairs retain an estimated 28 × 0.15 m rise;
their fitted width is 10.5 m, with metal rails and a distinct upper landing.
Photographs do not establish those exact dimensions. P09 also corrects the
Academic-facing admin block/glazing; the P08 dome geometry is retained.

P04/P06/P10/P11/P16 support the five-storey curved residential design, two glazed
cores, framed windows and six branching garden paths, with modest evening lights.
The geographic identity of the OSM candidate pair remains **UNVERIFIED**. The
[official dormitory page](https://www.zewailcity.edu.eg/campus-services/dorms)
confirms campus accommodation, not this particular footprint's identity.
P03/P05 institute/pergola context is kept separate from P13's Academic court.
P07/P12/P14 support exposed soil without proving current construction status.

The owner explicitly confirms both Academic facade entrances and boundary-wall
gates. P12/P14 C/F labels belong to the **building entrance** layer. Their exact
rear-curve / outer-prong placement is a hypothesis and their minimap markers are
qualified. G1–G6 records and 14 spawns remain stable. Broad owner descriptions do
not turn project IDs into official gate numbers. Cafeteria entry remains unresolved.

Permanent generators produce the source, game exports and reference cameras.
Source-derived stair collision inclines support continuous sprint descent while
retaining all visible treads and solid rails. A small player floor-contact fix
resets downward motion when grounded and applies the existing floor snap while
descending; jump/fly controls, speeds and key bindings remain intact. This uses
the documented [Godot floor-snap behavior](https://docs.godotengine.org/en/4.6/classes/class_characterbody3d.html#class-characterbody3d-method-apply-floor-snap).
The continuous stairs → court → soil → dorm test records zero floor losses.

Actual V6 MCP operations include source inspection, permanent-generator rebuild,
render and source reopen through Blender; editor/resource inspection, run/state/
stop, runtime-tree, screenshot and Start-click through Godot. An ended Blender
session caused two failed final render/reopen attempts; retrying the same unchanged
installed add-on succeeded. The protocol-version warning remains; no upgrade was
performed. Native engine logs replace the unavailable MCP get_output log.

Final machine reports, game/Windows captures, comparisons, measured performance,
video probe and unresolved issues live in `output/validation/v6/`; the README is
the owner-facing entry point. V5's SHA-verified backup and historical evidence
remain intact. Test success establishes runtime behavior, not surveyed accuracy.

## V5 ground reconstruction — 2026-11-07

V4 evidence and historical registers below remain intact. V5 keeps the same OSM
coordinate transform, road centrelines, photo-supported interlocking campus roads,
external asphalt, and Sentinel-2 planting distribution. The modelled OSM plot is
675,794.5 m²; this is distinct from the brochure's 840,000 m² planned land parcel.
It is not a cadastral boundary or a new measured land survey.

No DEM, spot heights, road cross-sections or surveyed floor elevations are available.
The new shared datum is an **engineering estimate**, not recovered topography:
0.08% longitudinal grading and 0.02% crossfall, smoothly flattened at existing
building/gate pads. Ground, pavement, curbs, planting, furniture and collision use
that datum. Floor levels and building silhouettes are preserved. Building bases
extend 0.4 m below their 0.21 m floor datum to remove visible foundation gaps.

V5 unions all road footprints before meshing, trims raised beds off carriageways,
partitions paving/lawn/soil without overlapping their top surfaces, and retains
terrain beneath buildings. Footway curb transitions taper over 2.4 m. The short
connector from mapped footway (0,-117.88) to the academic apron, and the two
approach-to-ring footway connectors, are **estimated functional connections**,
not newly mapped paths. Exact ramp construction and road widths remain estimated.

Technical evidence is in `output/validation/v5/`: `ground_topology.json`,
`road_floor_samples.json`, `ground_runtime.json`, ground/road-only top-down renders,
an elevation render mapped from -0.70 m (blue) to +0.70 m (orange), and eye-height
renders. The runtime test queries the actual imported `COL_Ground` and drives the
existing player controller. It probes ±2 cm at numerical triangle/cap boundaries;
the report includes recovery counts and maximum error. These are scripted engine
tests, not a human play test or a positional-accuracy measurement.

Blender MCP was accessed using the already installed `blmcp` stdio server and
live local bridge at 127.0.0.1:9876. The initially discovered alternative server
used an incompatible protocol; no Blender add-on was replaced. Godot MCP uses
the project-local MIT `slangwald/godot-mcp` bridge, commit
`95532c4eb632d61c9a3c7a281f1a8a2925042345`, compatible with the installed 4.6.2.
After the original live session ended, the installed on-disk Blender bridge was
restarted without replacing it. Its protocol 14 supports the project-local Ahuja
MCP server's `execute_blender_code` calls used here, despite a protocol-15 upgrade
warning. A complete permanent-generator rebuild, source reopen and inspection
were executed through that real MCP connection. No upgrade-only feature is claimed.
Editor/runtime Godot ports are bound to 127.0.0.1:9500/9501. Runtime control is opt-in
with `--mcp-bridge` and is disabled for release builds. No other coding agent was run.

### V5 six-gate register

The owner confirms **six** perimeter entrances. The map has paired lane nodes,
which must not be counted as separate gates. `six_gate_inventory.json` groups
them into six entrances, excluding the two off-campus nodes near (-457,-184).
G1–G6 are **project IDs, not verified official campus gate numbers**. Inward
bearing is 143.46°; owner-right is -X (233.46°, SW), owner-left +X (53.46°, NE).

| ID / owner description | Model x,y metres | Evidence / model | Remaining uncertainty |
|---|---|---|---|
| G1 main/front | 0, 314.600 | C01/C02/D02/D03 + OSM; V4 monumental portal retained; V5 ground/material export improvements | Photo-scaled proportions, current details |
| G2 rear | 6.445, -638.674 | OSM 5225739664 / 5225739665; labelled provisional marker | Current existence/state, exact opening, architecture, access type |
| G3 right A | -270.917, 132.472 | OSM 5225739797 / 8478493617; provisional | As above; owner A/B association unconfirmed |
| G4 right B | -342.324, -238.001 | OSM 5225739800 / 6424866649; provisional | As above |
| G5 left A | 237.756, 76.165 | OSM 5225739729 / 8478493632; provisional | As above |
| G6 left B | 346.622, -236.753 | OSM 5225739801 / 8478493550; provisional | As above |

The five model positions are nearest boundary projections of map-node cluster
centres, displaced 1.63–5.57 m; the JSON preserves both coordinates and offsets.
Nominal 9 m clear markers, 2 m posts and 20 m wall gaps are **engineering
placeholders**, not reconstructed gate designs. Their open walking routes are
tested, but operational/public access in the real campus is not asserted. No
unsupported security equipment was added. Original spawn indices 1–7 remain;
these gates append 8–12 and have a distinct minimap identification layer.

### V5 Academic and rear-campus corrections

| Feature / reference | Previous issue | Implemented correction | Estimated / unresolved |
|---|---|---|---|
| Academic C footprint — OSM 540106547; owner courtyard description | Inner space bare and isolated by solid core/rear shell | Retained OSM-fit wings/curve; open inner court, central and rear pedestrian passages | Courtyard dimensions/configuration, roof/levels and circulation are functional estimates, not an architectural survey |
| Two substantial stairs — owner; D05 composition | 2.5 m wide generic stairs with 0.35 m risers | Two nominal 9 m stairs, 28 × 0.15 m risers, 0.36 m treads, 4.20 m rise to 4.41 m deck; plain estimated cheek guards | All stair dimensions, guard details, exact positions; D05 may be enhanced and is not a measurement source |
| Central passage — owner | Solid facade/core blocked the route | 11 m clear opening through the core, covered at about 4 m, split glazing and side walls, connected floor | Covered-passage versus lobby interpretation and precise opening configuration require current photos |
| Academic courtyard — owner confirms palms, seating/gathering | No usable public courtyard | Paving, six palm beds, twelve benches, clear centre axis, separate editable courtyard collection | Bed/plant/seat counts and placement are estimated; no invented shade structures or full academic interiors |
| Cafeteria — official dining page | No verified external location | Cafeteria is recorded as basement dining; surrounding public courtyard seating is modelled | Exact cafeteria door/access and exterior appearance **not reconstructed**; `academic_cafeteria_context.png` is context only, not a verified cafe image |
| Rear ground — owner + S2 | Risk of adding ornamental lawns | Retained bare graded sand/soil; estimated compacted-earth walking desire line | Grading/path exactness; no measured spot elevations |
| Dormitory — owner left/rear position; OSM 540106540/541 five floors; D01 | Unlabelled low-detail pair, identity uncertain | Explicitly labelled student-housing candidate, photo-informed estimated glazed entry bays and canopies, southern garden/path | **Identity is not confirmed.** D01 does not geolocate the blocks. No private interior or room layout is invented |
| Dormitory central garden — owner + S2 | No intentional garden | Southern C-block planted soil, three estimated trees, loop path and gently graded ingress | Layout, exact planting and which block is the owner's dormitory remain unconfirmed |

The sampled NDVI at (350,-460) is **0.064** (bare northern court), at (390,-603)
**0.2635** (southern planting, not proof of lawn), and at rear soil (0,-400),
(0,-500) **0.056 / 0.062**. V5 does not turn the whole rear or northern court green.
These 10 m pixels cannot resolve a garden's detailed design or species.

Official pages rechecked 2026-11-07:
* Dining: https://www.zewailcity.edu.eg/about/campus-services/dining — cafeteria in Academic basement.
* Dormitory: https://www.zewailcity.edu.eg/campus-services/dorms — confirms the dormitory service, not these coordinates.
* Visit: https://www.zewailcity.edu.eg/main/campus-services/transportations/visit-zewail-city — main-gate campus arrival, not a map of all six gates.

### V5 validation limits and corrected defects

Source/export provenance is checked by SHA-256, and runtime walking uses actual
Godot physics with simulated input. Floor loss and maximum foot-to-floor gap are
recorded throughout routes. No human-playtest, surveyed elevation, photogrammetric
accuracy percentage, or independently confirmed side-gate/dorm identity is claimed.

Final camera tests caught a misplaced separated Academic roof: its world matrix
had been copied before parenting evaluation completed. The generator now updates
the dependency graph before copying transforms. Added source and game bounds checks
guard against recurrence. This was a modelling-transform defect, not a reason to
change the established V4 camera trajectories.

Blender 5.2.3 also crashed inside dependency-graph rebuilding when changing render
visibility between views (`blender_depsgraph_crash.txt`). `tools/render_v5.ps1`
renders one view per fresh process; no factory reset, engine upgrade or add-on
replacement is used. A batch crash is not counted as completed visual validation.

The six technical composites in `output/validation/v5/comparisons/` retain the
original photographs and render aspect ratios. C01 compares the retained main
gate; D05 compares facade/major-stair composition; the courtyard sheet records
owner-described features without pretending to supply an independent reference.
The dormitory comparison explicitly does not identify the candidate building.
The Sentinel/OSM 50% overlay uses the same 1120 × 1200 metric map extent as the
V5 orthographic camera. None of these images supplies an accuracy percentage.

For measured capture, `--capture` sets a 1920 × 1080 viewport and keeps aspect,
so Windows' decorated-window fitting cannot silently change the render size.
Ordinary interactive window sizing is preserved. This uses Godot's documented
[viewport scaling](https://docs.godotengine.org/en/4.6/tutorials/rendering/multiple_resolutions.html).
The guided-tour performance sample now measures 60 actual seconds, rather than
assuming that 3,600 uncapped frames equals a minute. The initial MCP screenshot
session is retained separately as `performance_initial_mcp_capture.json`;
`output/validation/godot_performance.json` is the final exact-1080p measurement.
Godot MCP launch/state/stop calls succeeded. Its `get_output` tool could not open
the engine log; native project and executable logs provide the error evidence.

---

# V4 reconstruction register — 2026-11-06

This register lists every source used for the V4 campus, what each one supports, and the status of every modelled structure. The V2/V3 register follows below it as a historical record.

**Status labels**

| Label | Meaning |
|---|---|
| **AS-BUILT VERIFIED** | Dated photographs **and** dated map or imagery data agree on existence and position. |
| **ESTIMATED** | The structure exists, but its size, height or detail is inferred (photo scale, typical construction). |
| **HISTORICAL DESIGN** | Appears only in the 2014 masterplan, brochure or exhibition model. Hidden, excluded from every export. |
| **UNVERIFIED** | Cannot be supported. Not modelled. |

No positional accuracy percentage is claimed. Section 3 gives the measured residuals between independent sources instead.

## 1. Sources accessed in V4

Local copies live in `references/source_images/v4/` and `references/geodata/`. They are kept for private comparison only. Each file keeps its owner's licence.

| ID | Source | Date | Licence / terms | Used for |
|---|---|---|---|---|
| **OSM** | OpenStreetMap via Overpass API, bbox 29.928–29.952 N, 31.050–31.082 E (`geodata/campus_area_osm.json`) | Extract taken 2026-11-06. Campus service roads were edited on 2021-03-02 (user Eman_Mehrez); building outlines and gates on 2017-11-13. | ODbL 1.0, © OpenStreetMap contributors | Ring road, approach, slip roads, drop-off loop, perimeter loop, spurs, parking aisles, footways, bounding streets, plot outline, building footprints, gate nodes |
| **S2** | Copernicus Sentinel-2 L2A scene `S2A_36RUU_20260916`, read from the public AWS COGs (TCI, B04, B08) | 2026-09-16, 0.003 % cloud | Copernicus open data licence ("contains modified Copernicus Sentinel data 2026") | Independent dated orthophoto check of the OSM layout (10 m pixels). NDVI map of irrigated planting (`src/utilities/data/ndvi_s2_20260916.json`). |
| **WD** | Wikidata Q21062258 (P625) | — | CC0 | Campus location, 29.9395 N 31.0650 E |
| **C01** | Wikimedia Commons, "Zewail City Gates.jpg", by Tasneemalinaguib, 6000×3492 | 2017-11-18 10:46 (EXIF, Canon EOS 750D) | CC BY-SA 4.0 | Main gate from **outside**: portal frame and inlay, stepped gatehouse, medallion, slots, steel lane gate, pedestrian gate, gate buildings, cactus and agave beds |
| **C02** | Wikimedia Commons, "Zewail City.jpg", same author, 6000×3379 | 2017-11-18 14:55 (EXIF) | CC BY-SA 4.0 | Approach seen from the admin portico roof: frame size (photogrammetry), approach cross-section, median and strips, circular bed, flanking walls and palms |
| **D02** | zewailcity.edu.eg/campus-services, "Transportation" (`2021_637637593456796334_...jpeg`) | 2021, from the file name | © Zewail City; reference only | The same portal legs and stepped gatehouse seen from inside in 2021. Grey interlocking pavers. Bus livery with the same pyramid medallion. |
| **D03** | zewailcity.edu.eg/campus-services, "Landscape" (`Capture_354efd90fc.PNG`) | undated; same scene as C01 | © Zewail City | Confirms that C01 shows the official campus gate |
| **D01** | zewailcity.edu.eg/campus-services, "Dorms" | 2024-02-12, from the file name | © Zewail City | 5-storey residential blocks. Their location on campus is not stated. |
| **D05** | zewailcity.edu.eg/city-structure, "Academic Building Gate A" (`almbna_alakadymy_bwabt_A_...png`, 2117×743) | Server timestamp 2026-11-01; capture date unknown | © Zewail City | Internal Academic Building entrance "Gate (A)": courtyard between the prongs, glazed core, sign, colonnades. The image looks digitally enhanced, so it is used for composition only, not dimensions. |
| (excl.) | zewailcity.edu.eg/city-structure, "Research Institutes" and "Valley" images | — | — | **Not used.** The file names (`Gemini_Generated_Image_*`) show they are AI-generated. |
| A01–A05, B01–B04 | V2 register (below) | see below | see below | Admin, academic, institutes, historical masterplan |

**Requested but not usable:**
* The official home, campus-services and city-structure pages render their content client-side. They were read in a browser; their photo URLs are listed above.
* The SlideShare masterplan deck (B05) was not opened. It is a design document, and V4 does not need it for the as-built layout.
* No licensed high-resolution orthophoto (Maxar, Google, Esri or Bing) was downloaded or traced. OSM was traced by its contributors from imagery licensed for that purpose.

**Distinguishing the entrances:**
* The **external main gate** (C01, C02, D02, D03) is the stone portal frame with the gatehouse, on Ahmed Zewail Road at the end of the approach.
* **Gate (A)** (D05) is the entrance of the Academic Building inside the ring. It has no portal frame.
* No photograph of the **side gates** (OSM nodes on the W, E, NE, S spurs and the S boundary) was found. They are road openings only: **UNVERIFIED**, not modelled.

## 2. Coordinate transformation (documented, reproducible)

Scripts: `tools/geo/osm_to_axis.js`, `tools/geo/export_osm_campus.js`, `tools/geo/s2_to_axis.js`, `tools/geo/ndvi_to_blender.js`.

1. **WGS84 → local ENU metres** about 29.9410 N, 31.0670 E. Metres per degree come from the ellipsoid (111 069 m/° latitude, 96 543 m/° longitude). Sentinel-2 pixels are mapped through an exact UTM 36N forward projection.
2. **Axis frame:**
   * Origin: least-squares circle centre of the ring road (Kåsa fit, n = 184 vertices, rms 5.7 m).
   * +Y: unit vector to the midpoint of the two main-gate nodes (OSM 5225739523 and 5225739528), 560.7 m away.
   * +Y bearing: **N 36.5° W**. V3 assumed N 20° W from the brochure's north arrow.
3. **Blender frame = (x_axis, y_axis − 246.1).** 246.1 m is the dome's axis-frame Y. The 2017 admin outline (arm fronts 280 m, rear 148 m) was combined with the photographed admin massing (arms +33.9 m, rear −94 m from the dome). The two estimates differ by 4 m.
4. **2017 building outlines are shifted +3.0 m in x.** The admin, academic and institute outlines are centred 2.5–4 m west of the gate axis, which the 2021 road centrelines and gate nodes define. The shift is a systematic tracing offset; it is documented, not hidden.

**Control points.** These are independent features on the axis. A feature that lies on the axis should have x = 0.

| Feature (source) | x in axis frame (m) |
|---|---|
| Gate-node midpoint (OSM, defines the axis) | 0.0 |
| Ring centre, north half fit (OSM 912696913, rms 0.54 m) | +2.0 |
| Ring centre, south half fit (OSM 685373371, rms 0.36 m) | +1.9 |
| Approach centreline midpoint (OSM 685373372 / 912696914) | +0.4 |
| Admin 2017 outline bbox centre | −2.5 |
| Academic 2017 outline centre | −3.5 |
| Sentinel-2 vs OSM registration (ring, approach, buildings, by overlay) | consistent within 1 pixel (10 m) |

**Independent scale check.** In the C02 photograph the circular bed measures 875 px at the 38° horizontal field. That gives a radius of 7.6 m at the distance implied by the OSM positions; 7 m is modelled. The bed's image position (row 980 of 1126) also matches a camera on the admin portico roof at y ≈ 30 m. Two independent sources therefore agree on the bed position (y ≈ 82 m) to about 2 m.

## 3. V3 → V4 changes to positions (Blender frame, metres)

| Control | V3 (brochure plan) | V4 (survey) | Source |
|---|---|---|---|
| Main gate line y | 307.6 | 314.6 | OSM gate nodes |
| Ring road centre y | −245.0 | −237.6 | OSM ring (two halves) |
| Ring road radius | 302 × 298 (ellipse), dual carriageway | 301.2 (circle), one one-way carriageway | OSM ring |
| Academic prong front y | −158.3 | −169.0 | OSM 540106547 |
| Academic core front (Gate A) y | −207.0 | −229.0 | OSM 540106547, D05 |
| Academic rear y | −342.4 | −348.0 | OSM 540106547 |
| Helmy centre (x, y) | (−129.7, −61.3) | (−130.4, −69.3) | OSM 540106545 |
| Helmy size | 108 × 35 m, 40.9° | 103.5 × 29.8 m, 45.3° | OSM 540106545 |
| East institute centre (x, y) | (143.4, −60.1) | (146.8, −62.8) | OSM 540106546 |
| East institute size | 96 × 33 m | 77.3 × 36.6 m, 42.0° | OSM 540106546 |
| Circular bed y | 118 | 82 | OSM wedge geometry, C02 photogrammetry |
| Dome rise | 7.0 m | 5.5 m | A02 full resolution: rise / base = 104 / 380 px |

## 4. Structures and site elements (V4 status)

| Element | Status | Evidence | What is approximate |
|---|---|---|---|
| **Main gate portal frame** (`AB_Main_Gate_Complex`) | AS-BUILT VERIFIED (2017 and 2021 photos, OSM gate nodes) | C01, C02, D02, D03, OSM | Size from C02 photogrammetry: 33.4 × 18.7 m, legs 4.8 m, lintel 4.5 m (±8 %). The 4.8 m depth is not visible in any photo and is estimated. |
| Dark ledgestone inlay band (both faces) | VERIFIED | C01 (outside), C02 (inside) | Width 0.55 m, offset 1.9 m |
| Gatehouse with stepped blocks, three slots, medallion | VERIFIED | C01, D02, D03 | Block heights (9.4 / 8.1 / 6.5 m) from the C01 minibus scale. Its depth and its position ~10 m outside the frame come from the C01/C02 scale ratio (estimated). |
| Medallion "مدينة زويل / ZEWAIL CITY" with three pyramids | VERIFIED as of 2017 | C01; the same mark on the official bus in D02 | Whether it is still mounted today is not verified. Letterforms are approximated with Tahoma Bold / Arial Bold. |
| Steel sliding lane gates (lattice top, bars) | VERIFIED | C01, C02 | Open/closed state follows C02 (right lane closed, left lane open) |
| Pedestrian gates beside the legs, grid doors, ledgestone flanks | VERIFIED (west in close-up, east in C02) | C01, C02 | Doors are modelled open so the walking route works |
| Gate buildings (single-storey plaster, roof AC units) and stone pavilions | ESTIMATED | C01, C02; OSM 2017 stepped outline | Footprints follow the OSM steps. Heights 5.4 / 6.5 m come from C01. C02 suggests taller (~10 m) plastered wall volumes beside the gate. That discrepancy is unresolved. |
| Lattice screens / portals | VERIFIED (C01 right edge) | C01 | Pattern simplified to a square grid |
| Perimeter wall (3.5 m plaster, pilasters) | ESTIMATED | C02 near the gate; OSM 2017 outline | Wall type is photographed only near the gate and assumed to continue around the plot |
| Gate island beds (red mulch, white pebbles, agave, golden barrel cactus, red euphorbia, young date palms) | VERIFIED (2017) | C01 | Bed outlines and plant counts are estimated; 2017 planting may have changed |
| **Approach** (two one-way carriageways, palm median, planted strips, walkways) | VERIFIED | OSM, C02, A01 | Widths are estimated from C02 (7 m carriageways, 4.5 m median, 5 m strip, 4 m walkway). Median palms only near the gate, as in C02. |
| Gate lanes (5.1 m each side of the gatehouse) | VERIFIED | C02 photogrammetry | OSM centrelines (±5.2 m) are simplified at the gate; the photo is used |
| Perimeter service loop just inside the gate, side spurs, parking aisles | VERIFIED (position) | OSM 2021 | Widths are estimated (5.5–7.2 m) |
| **Ring road** | VERIFIED | OSM, S2, A01 | 8 m width is estimated |
| Slip roads in front of the ring; admin drop-off loop | VERIFIED | OSM 685373372 / 912696914 / 912696912; A01 | Widths are estimated |
| Bounding streets (Zewail St, Side Zewail St, W / E / S roads) | VERIFIED (position) | OSM | Widths and lane counts are estimated |
| **Octagonal road, four diagonals, E–W and S axes around the academic** | **HISTORICAL DESIGN.** Removed in V4. | B04 only. Absent from OSM and S2 2026. | — |
| V3 grove lobes (four green quadrants) | Removed | S2 NDVI 2026: the S half of the ring is bare | — |
| Irrigated planting distribution | VERIFIED (2026-09-16) | S2 NDVI | 10 m pixels: lawn edges are smoothed and strips narrower than ~20 m are blurred. Tree density follows NDVI; species are generic. |
| Circular bed and wedge lawn | VERIFIED | A01, A02, C02 | Radius 7 m (C02 gives 7.6 m) |
| Admin parterre (curved red / orange / hedge rows) | VERIFIED (qualitatively) | A01, A02 | Row geometry is approximate |
| **Administration & Cultural Building** | VERIFIED (V2/V3 massing) | A01–A04, OSM 540106548 | V4 changes: dome rise 5.5 m (A02 measurement); roof trellises lowered (A02). Position is consistent with the OSM outline within 4 m. The rear and the side elevations remain approximate. |
| **Academic Building** | VERIFIED (footprint and front), ESTIMATED (heights, rear) | OSM 540106547, A01, D05 | Re-fitted: semicircular rear ring (R 99 m) around an inner court, side wings, two prongs 35.5 m wide framing a 39.6 m Gate (A) court, glazed core with sign and canopy, double-height colonnade. Heights 22–24 m. |
| Academic sign "المبنى الأكاديمي" and "Gate (A)" | VERIFIED (official image) | D05 | Position on the facade approximate |
| **Helmy Institute** | VERIFIED | SIAC page, A05, OSM 540106545 | Height 20 m, facade rhythm from V3 |
| **East research institute** | ESTIMATED (identity unconfirmed) | OSM 540106546, A01 | Presumed NBE Nanosciences, not confirmed. The HUD says so. |
| **Five-storey pair east of the ring** (`AB_East_Residential_Pair_Estimated`) | ESTIMATED | OSM 540106540/541 (`building:levels=5`), S2 2026 | Identity unknown (possibly the dorms in D01). Low-detail massing, 18 m, no landmark label. |
| Plan buildings 1, 2, 3, 8-series, 9–13 | HISTORICAL DESIGN | B04 | Hidden collection, excluded from renders and exports |
| Side gates on the W / E / NE / S spurs | UNVERIFIED | OSM gate nodes only | Not modelled |
| Gatehouse interiors, guard posts, barriers, cameras | UNVERIFIED | — | Not modelled (no evidence) |

## 5. Remaining uncertainties

1. **No survey-grade data.** Positions rest on OSM tracing, typically ±3–5 m for buildings and ±2 m for roads, and on 10 m Sentinel-2 pixels. Widths, heights and the gatehouse depth are photo estimates.
2. **Dates differ between sources.** Gate and approach photos are from 2017 (C01, C02) and 2021 (D02). The planting distribution is from 2026 (S2). The admin and academic photos date from 2017–2025. Gate planting and signage may have changed since 2017.
3. **Gate flank heights:** C01 shows 5.4–6.5 m gate buildings; C02 suggests ~10 m plastered volumes. This is not reconciled.
4. **Admin rear and sides** are only seen in A01 and in the exhibition model.
5. **The east institute's identity and the identity of the 5-storey pair** are not confirmed.
6. **D05** appears digitally enhanced. It was used for composition only.
7. **The south half of the campus** is bare in S2 2026 and is modelled as graded ground. No building there is supported.

---

# Historical register: V2/V3 (kept for reference; superseded where V4 above differs)

## Source-to-building evidence register (v2 reconstruction)

This file lists, for each modelled structure and road, the evidence used and how confident that evidence is. Reference IDs (A01–A06, B01–B05) follow `correction_kit/Zewail_Architecture_Correction_Kit/REFERENCE_SOURCES.md`.

* **As-built (A):** dated photographs of the real campus. These are the primary evidence.
* **Design (B):** the 2014 masterplan, design brochure and exhibition scale model. These are secondary evidence: they record a design, and the campus may not have been built that way.

### 1. Sources actually accessed

Local copies are kept in `references/source_images/` for private comparison only. They must not be redistributed.

| ID | What was retrieved | Accessed via | Used for |
|---|---|---|---|
| A01 | Official campus aerial, 1280×719 (file name gives 2025-09-07) | zcadminpanel.zewailcity.edu.eg upload, linked from zewailcity.edu.eg | Building relationships, admin silhouette, approach fork, academic front blocks, institute facades |
| A02 | Hassan Allam photo of the administration building, 2560×1707 | cdn.hassanallam.com | Front elevation, dome/drum proportions, front lawn and circular bed |
| A02 page | Hassan Allam project page | WebFetch | 3 floors, 2 basements, 36,000 m² built-up area (BUA), year 2017. The page heading says "B8" while the URL slug says "B5"; this is not resolved here. |
| A03 | Official close-up of the admin building, 1000×878 | zcadminpanel upload | Dome banding, drum windows, stone panel cladding, dark granite bands, pergola |
| A04 | Official driveway view, 729×423 | zcadminpanel upload | Approach planting (fan palms, double-arm lamps), axial alignment |
| A05 | SIAC aerial of the Helmy building under construction, 800×450 | siac.com.eg | Helmy position relative to the admin and the curved academic ring |
| A05 page | SIAC project page | WebFetch | "Helmy Building for Medical Sciences", 12,200 m² total area, CEGMAN as engineer |
| B01 | Official photo of the exhibition scale model | zcadminpanel upload | Rear stepped roof, wing arrangement (design evidence) |
| B02 | Aura masterplan aerial and admin render, plus project page | squarespace CDN, WebFetch | 840,000 m² land plot, 190,000 m² BUA, phase-one building list |
| B03 | CEGMAN project page | WebFetch | No dimensions on the page; master planning scope only |
| B04 | Architecture brochure PDF (10.9 MB). Its 20 embedded images were extracted. | squarespace CDN | **Image 6, the site-plan drawing, is the layout base.** Images 13, 15 and 16 are construction photos used for floor counts. |
| (v1) | `IMG_4519.MOV`, video of the exhibition model | user supplied | Superseded as layout evidence by B04 and A01 |

**Not accessed:** satellite imagery (no licensed source was used), the B05 SlideShare deck, and any survey or CAD data.

### 2. Coordinate system and scale

* The site-plan drawing (B04 image 6) was digitised on pixel grids (`src/utilities/site_plan.py`).
* **Scale = 0.595 m per plan pixel.** The plan's dashed plot boundary encloses 2,369,158 px², and B02 states an 840,000 m² plot, so √(840000 / 2369158) = 0.595.
* **Cross-check:** the dome-drum diameter is 20.8 m on the plan at this scale and about 20 m from A02, which was scaled independently from an 18 m three-storey parapet.
* **Uncertainty:** the scale is plausible to roughly ±10%. The boundary may not be exactly the 840,000 m² parcel, and the drawing may not be perfectly orthographic.
* **Orientation:** +Y is the top of the drawing, which is the main gate and the admin front. The drawing's north arrow points about 20° clockwise from +Y.

### 3. Buildings modelled as built

| Object | Plan ref | Evidence | What is supported | What is approximate | Confidence |
|---|---|---|---|---|---|
| `AB_Administration_Cultural_Building` | 4 (4.a, 4.b) | A01, A02, A03, A04, B01, B04, A02 page | Symmetric rectilinear massing; flat entrance portico on slim columns with a name fascia; tall stone piers; dark curtain walls; lower lateral sections with framed glazing; tall dark-glass slots; open stone portal frames; low arms projecting toward the gate; end pavilions with bridges; stepped auditorium-like roof rising behind the dome; rear wings; white base, octagonal copper collar, copper drum with ~20 windows, banded shallow copper dome, flat top ring, thin mast; light marble panels with dark granite bands | All dimensions (plan footprint ±10%; heights scaled from A02: centre parapet 18 m, arms ~10.5 m, frames ~15.7 m, drum top ~26 m, dome apex ~33 m, mast ~40 m); drum window count; rear block heights; roof trellis positions | High for silhouette and composition; medium for dimensions |
| `AB_Academic_Building` | 7 | B04 plan; A01 (front blocks); A05 (curved ring); B04 construction photos | C-shaped ring around a courtyard; two forward arms and a central block facing the admin; framed stone-and-glass facades | Heights (ring 22 m, arms/core 28 m, inferred from A01 proportions and about 6 storeys in a construction photo); courtyard-side facades; exact arm footprints | Medium |
| `AB_Helmy_Institute_Medical_Sciences` | 5 | B04 plan; A05 (SIAC aerial); A01 right; A05 page | Long bar NW of the admin, its long side facing the admin axis; alternating blank stone panels and dark glass bays with a central glazed recess; about 3,800 m² footprint, consistent with 12,200 m² over 3–4 floors | Height 20 m; atrium; rear facade | Medium |
| `AB_East_Research_Institute_Nano` | 6 | B04 plan; A01 left; Wikipedia list of completed buildings ("Nano") | Long white block NE of the admin with grouped windows and dark glass strips; taller end block | **Which institute this is.** It is presumed to be the NBE Nanosciences institute but is not confirmed. Height, end block and facade are approximate. | Medium-low |

### 4. Structures removed from v1 (not supported)

| v1 element | Why removed |
|---|---|
| Curved colonnaded front with radial piers | Contradicted by A01, A02 and A04, which show a rectilinear front |
| White drum with a hemispherical dome, lantern and finial | Contradicted by A01–A03 (copper drum, shallow banded dome, mast) |
| Long ribbed "East Hall" attached to the dome block | No match in any photo or the plan |
| Eight generic white pavilions (portico hall, cube pavilion, north lab and others) | Invented to fill space; no supporting evidence |
| Rectangular ring road, curved interchange and southern avenue | The plan shows a circular ring and an orthogonal gate system |
| Three pergola courtyards, circular dark plaza and circular lawn | Not on the plan or in photos. One pergola beside the admin is kept, supported by A03. |
| ~730 palms on regular grids | Replaced with planting distributed per evidence (section 6) |

### 5. Plan buildings kept separate (unverified)

The collection `Unverified_Masterplan_Proposals` holds 18 wireframe blockouts. It is excluded from the view layer, from renders and from the GLB.

* **Plan buildings 1 and 2:** contradicted. A01 shows open land with saplings where the plan draws them.
* **Buildings 3, 8 (×10), 9, 10, 11, 12 and 13:** not visible in any dated photograph used here. Plan building 12 is student housing, rendered in B04 images 12 and 17. Some of these may exist, since Aura's phase one included a "one-stop shop" and an "engineering building", but their positions could not be confirmed.

### 6. Roads, plazas and landscape

| Element | Evidence | Status |
|---|---|---|
| Circular campus ring road (dual carriageway with planted median) | B04 plan; A01 (curved road with a planted median in front of the admin, cars) | Plan-anchored. Its shape is a 302 × 298 m ellipse because plan readings differ by about 5%. |
| North axial approach (dual) from the north gate | B04; A04 (straight driveway with fan palms and double lamps) | Plan-anchored |
| Approach fork with a lawn wedge and circular flower bed | A01 (two diverging arms, bed in the wedge); A02 (bed with white pebbles, dark gravel and marigold rings) | **Follows A01, not the plan.** The plan draws a narrow funnel. The bed's position (about 97 m in front of the facade) was inferred from A02's long-lens perspective. |
| Octagonal road and plaza around the academic complex | B04 | Plan only |
| Four diagonal roads; east–west axes to the side gates; south axis | B04 | Plan only |
| Parking: west lot, bus lot, east lot | B04 "P"; A01 (west lot full of cars) | West lot supported; others plan only |
| External streets around the plot | B04 (boundary roads); A01 background | Approximate offsets from the boundary |
| Admin forecourt paving, flower-bed rows, topiary | A01, A02, A03 | Supported qualitatively; layout approximate |
| Grove lobes (east and west of the academic complex) | B04 (tree grids) | Plan only; jittered young trees |
| Graded sandy ground with sparse planting elsewhere | A01 foreground, A05 | Supported qualitatively |
| Inner perimeter loop road, gatehouses, sports field, plan building 11 garden | B04 | **Not modelled** (unverified) |

### 7. Remaining uncertainties and sources still needed

1. **Survey-grade geometry:** a dated, licensed orthophoto or CAD site plan would replace the brochure-plan scale (±10%) and the photo-scaled heights.
2. **Admin rear and sides:** only B01 (the model) and the A01 roof view show them. The rear wings and auditorium are approximate.
3. **Academic complex:** no close photograph of its facades. Heights and the courtyard side are inferred.
4. **East institute identity and design:** NBE Nanosciences is presumed, not confirmed.
5. **Which plan buildings exist today** (8-series, 9, 11, 12, 13): a current aerial of the southern half of the campus is needed.
6. **Exact road widths, lane counts and junction geometry.**
7. **Contractor naming discrepancy:** B5 vs B8 for the admin building.
8. **Orientation:** the plan's north arrow is a sketch symbol, so the true bearing of the campus axis is approximate.

### 8. V3 changes (2026-11-06)

V3 uses no new sources. Every change addresses a mismatch already documented in `output/validation/MISMATCH_REPORT.md` against A01–A05.

| Change | Mismatch addressed | Source |
|---|---|---|
| Admin portico is a deeper box with solid stone cheek legs, a deeper fascia and five round columns | "The photo's portico frame is a deeper two-storey box" | A02 |
| Two adjacent full-height dark slots on each side volume (was one) | "The photo shows two adjacent tall dark slots on the side volume" | A03 |
| Drum window band 3.2 → 3.8 m (drum top 26.8 m, dome apex ~33.8 m, mast 40.4 m) | "The drum appears slightly taller relative to the dome" | A02 (drum:dome ratio ~0.82; model now ~0.83) |
| Dome: broad dark lower band, two thinner bands, 36 meridian standing-seam ribs | Banded dome with a fine panel grid | A02, A03 |
| Four slender roof masts | Masts visible above the central and outer blocks | A02 |
| Projecting framed glass box on each academic arm | "Their facades show glass 'boxes' that were not modelled" | A01 |
| Recessed glazing now renders (academic core front, Helmy centre bay) | V2 modelling bug: glass was inside the solid shell | A01, A05 |

**Still not modelled:**

* Gatehouses.
* The inner perimeter loop.
* "ZEWAIL" lawn lettering.
* Interiors.

None of these is supported by a dated photograph precise enough to model.

**Game build.** The game build drops `Unverified_Masterplan_Proposals` and keeps the evidence status of every landmark:

* The east institute is labelled "identity unconfirmed" in the explorer.
* Landmark labels, evidence and spawn links are defined in `src/utilities/game_points.py`.
