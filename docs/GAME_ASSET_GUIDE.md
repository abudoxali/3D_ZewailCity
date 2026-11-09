# Game asset guide (V6)

V6 retains the existing pipeline/coordinate conventions below. Its manifest records
26 generator hashes, 14 spawns, 18 landmarks, six perimeter gates and two separate
qualified C/F building entrances. The editable Academic source has dedicated
facade, stair, roof/bridge, courtyard and internal-entry collections. Residential
identity remains unverified; never promote its marker based on design similarity.

New procedural/baked slab materials, dark inlays, 0.22 × 0.11 m garden pavers,
warm stone cladding and framed glazing use physical scale and UVs. Original owner
photographs remain internal references and are not shipped as facade textures.
The optimized GLB has 1,101,460 render triangles and 420,509 collision triangles
(86.91 MB). Garden lighting is 32 bounded, shadowless lights with distance fade;
daylight is still the default, with an optional Graphics-menu evening toggle.

Large stairs keep visible real treads and rails. `stair_collision_parts` in the
exporter derives a local-frame walking incline from their source metadata and
stone vertices. Maximum visual/proxy discrepancy is one estimated 0.15 m riser.
The original player has a small grounded/descending floor-contact correction;
it preserves jump, fly, speeds, capsule and bindings. Continuous scripted tests
exercise both stairs up/down, court/ramp, rear soil and all garden branches.

The new `CIN_V6_Photo_Walkthrough` is a continuous 173.8667-second scripted camera
path; the long outdoor connection is explicitly accelerated. Existing cinematic
paths remain. Regenerate paths after editing source keyframes. V6 comparisons and
game captures live in `output/validation/v6/`; rerun `tools/verify_delivery_v6.py`
only after the current engine, Windows, performance and movie reports exist.

This guide covers how the campus moves from Blender to real-time use, and the conventions to keep when you extend it with NPCs, doors, interiors, vehicles or multiplayer.

## 1. Ownership

| Layer | Owner | File(s) | Edited by |
|---|---|---|---|
| Architecture, site, materials | Blender generator | `src/build_scene.py`, `src/utilities/*.py` → `output/Zewail_City_3D.blend` | Python (or by hand in Blender, then copied back into the generator) |
| Cinematic and tour paths | Blender | `Cinematic_Paths` collection in the authoritative .blend (`src/utilities/cinematics.py` seeds it) | Blender keyframes |
| Spawn points and landmarks | Python data | `src/utilities/game_points.py` | Python |
| Game-ready optimisation | Build script | `src/build_game_assets.py` → `output/game_ready/` | Never by hand; re-run the script |
| Gameplay, UI, camera, collision layers | Godot | `game/godot/` | Godot / GDScript |

The authoritative scene is `output/Zewail_City_3D.blend`. `build_game_assets.py` opens it read-only, makes every change in memory, and saves a **separate** `output/game_ready/Zewail_City_Game.blend`. Nothing in the game layer writes back to the architectural scene.

The game code never edits imported meshes. It instances `campus_full.glb` and adds behaviour around it (batching, collision layers, spawns). Re-exporting from Blender therefore never conflicts with gameplay code.

## 2. Pipeline

```bash
# 1. Architecture. Can also run live through Blender MCP; see README.
blender -b --python src/build_scene.py
# 2. Game-ready assets + copy into the Godot project (includes texture baking/cache)
blender -b output/Zewail_City_3D.blend --python src/build_game_assets.py
# 3. Camera / tour paths -> JSON (a few seconds; run after editing paths only)
blender -b output/Zewail_City_3D.blend --python src/export_camera_paths.py
# 4. Godot re-import (first open of the editor does this too)
godot --headless --path game/godot --import
```

## 3. Collections and naming

| Collection (and root node in the GLB) | Prefix | Contents |
|---|---|---|
| `Game_Terrain` | `TER_` | V5 graded desert/campus partition, NDVI ground cover, planted soil and estimated earth path |
| `Game_Roads` | `RD_` | Carriageways, medians, markings, parking (sidewalk faces removed) |
| `Game_Sidewalks` | `SW_` | Sidewalks and curbs split from each road, plus plazas and forecourts |
| `Game_Administration` | `BLD_` | `BLD_Administration_Cultural` |
| `Game_Academic` | `BLD_` | `BLD_Academic` |
| `Game_Institutes` | `BLD_` | `BLD_Helmy_Institute`, `BLD_East_Research_Institute`, `BLD_East_Residential_Estimated` (V4, low-detail, identity unconfirmed) |
| `Game_Gate` | `BLD_` | Main gate, perimeter wall, five separately labelled provisional gate markers; see six-gate inventory |
| `Game_Vegetation` | `VEG_` | Palms, trees, shrubs (shared meshes), static flower beds |
| `Game_Props` | `PROP_` | Lamps, cars, pergola |
| `Game_Collision` | `COL_…-colonly` | Collision-only proxies (no render mesh) |
| `Game_Landmarks` | `LM_` | Empties; label, radius, verified flag, evidence, linked spawn |
| `Game_Spawn_Points` | `SPAWN_NN_` | Empties; grounded at runtime by a downward ray |

Rules:

* Names are stable. Code looks objects up by name and prefix, so rename only together with the code that uses the name.
* The instance number on `VEG_<asset>_NNNN` / `PROP_<asset>_NNNN` is not stable; do not reference individual instances.
* Each `BLD_` object is one mesh: shell, glass and details merged, bevels applied. Its origin is at the footprint centre on the ground, and the institutes keep their rotation.
* `-colonly` is the Godot import hint for "collision only, trimesh". Use `-convcolonly` for convex hulls on new dynamic props.

## 4. Scale and coordinates

* 1 unit = 1 metre everywhere.
* Blender: origin = dome centre, +Y = toward the north gate, Z up.
* glTF / Godot: Y up. **Godot (x, y, z) = Blender (x, z, −y).** The manifest stores both.
* V5 uses the estimated datum in `utilities/ground_system.py`: soil +0.012 m, roads +0.060 m, paving up to +0.210 m and curbs +0.230 m. Level building pads use a 0.210 m floor. Transitions taper; no measured elevation claim is made.

## 5. Collision

| Proxy | Built from | Notes |
|---|---|---|
| `COL_Ground` | Terrain + roads + sidewalks + plazas + flower beds, minus road markings | Walkable; curbs and planters keep their real heights |
| `COL_BLD_*` (incl. `COL_BLD_Main_Gate`: frame legs, gatehouse, gate bars and posts, door frames) | Un-bevelled shell + detail parts that start near the ground (columns, piers, frame legs) + bulky upper parts (dome bands, drum, canopies, glass-box frames, rooftop plant) | Thin mullions, fins and glass are skipped |
| `COL_Vegetation_Trunks` | Hexagonal prism per palm or tree (r ≈ 0.22 m × scale, 3 m tall) | Shrubs have no collision |
| `COL_Props` | Lamp poles (prisms), cars (oriented boxes), pergola posts and beams | |

Physics layers (also named in `project.godot`):

| Layer | Name | Used by |
|---|---|---|
| 1 | world_static | All `COL_` proxies (`campus_loader.gd` sets this) |
| 2 | player | The player capsule (mask = 1) |
| 3 | dynamic_props | Reserved |
| 4 | npc | Reserved |
| 5 | vehicles | Reserved |
| 6 | interactables | Reserved: doors, info points |
| 7 | triggers | Reserved: landmark areas |
| 8 | validation_only | Render-geometry colliders built by the test suite only |

## 6. Materials and textures

Blender's procedural materials are baked to tiling textures in `output/game_ready/textures/`:

* **Albedo** is baked through an emission shortcut, so the colour is independent of metallic and lighting.
* **Normal** maps are baked in tangent space from the bump nodes.
* **Roughness** maps retain the source node variation. `textures/bake_cache.json` reuses a bake only when both the material graph fingerprint and PNG SHA-256 hashes match.
* **UVs** are world-scale box projections: each face uses the axis its normal is closest to, divided by the material's tile size (stored in `GM_*["zc_tile_m"]`). Stone panels repeat every 4.8 m (4 × 1.2 m panels by 8 × 0.6 m rows), and paving every 3.6 m or 4.8 m. These tiles are seamless by construction. Noise-based tiles (asphalt, grass, sand and others) are made seamless after baking.
* Glass becomes an opaque, low-roughness, slightly metallic dark material, which reads better in real time than transmission.
* Flat materials (metals, car paint, lamp lenses) keep their colour, roughness and metallic values. Lamp lenses keep their emission.

To change a material, change it in `src/utilities/materials.py`, rebuild the scene, then re-run `build_game_assets.py`.

V5 collision includes every ground region (including lawns, whose old underlying
plane is now cut out), the two 28-riser Academic stairs, the covered passage
ceiling, and simplified vegetation/prop obstacles. The first seven spawn indices
are preserved; gates append 8–12, Academic courtyard 13, dormitory candidate 14.
Grounded spawn searches may move a point by a small offset to avoid a wall.
Gate IDs G1–G6 are project identifiers, not verified official campus gate numbers.

The manifest records the authoritative blend SHA-256 and generator hashes.
`validate_v5_assets.py` checks these, UV coverage, material resources, normals,
metre scale, Academic bounds and byte-identical Godot copies. These checks prove
technical consistency, not architectural or identity accuracy.

## 7. Performance features

* **Instancing.** The glTF keeps one mesh per vegetation or prop asset (18 meshes for about 1,450 instances). At load, `campus_loader.gd` converts them into `MultiMeshInstance3D` batches, one per mesh per 160 m cell, so frustum culling and visibility ranges still work.
* **Visibility ranges** depend on the graphics preset. Shrubs fade at half the tree distance and cast no shadows.
* **LOD.** Godot generates mesh LODs on import (the default `meshes/generate_lods`). The preset sets `mesh_lod_threshold`.
* **No triangle reduction on landmarks.** The admin building keeps its full 20.6k triangles, and the dome keeps its bands and ribs.

## 8. Extending

| Future feature | Where it goes | Hook already in place |
|---|---|---|
| Third-person character | New `CharacterBody3D` scene; reuse `campus_loader.safe_spawn_position()` | Spawns are data; the capsule shape is a parameter |
| NPC students and pedestrians | NPC scenes on layer 4; a `NavigationRegion3D` baked from `COL_Ground` + `COL_BLD_*` | Collision proxies are simple and separate from the render meshes |
| Interactable doors | Door scenes on layer 6, placed by new `DOOR_*` empties added to `game_points.py` | Marker pattern (empties + manifest) |
| Interiors | Separate scenes, loaded through a door trigger | Each building is a standalone GLB in `output/game_ready/buildings/` |
| Vehicles and parking | `VehicleBody3D` on layer 5; the parking lots are `RD_Parking_Lots` | Roads and sidewalks are separate objects |
| Multiplayer | Use spawns from the manifest as server-authoritative spawn slots | Spawns are grounded and validated at runtime |
| Other engines | `campus_full.glb` + `campus_manifest.json` | Standard glTF 2.0 with PBR textures |

## 9. Evidence rules for new content

Follow `references/SOURCE_EVIDENCE.md`. Do not add buildings or names without a source. Unverified masterplan buildings stay out of the game build: `Unverified_Masterplan_Proposals` is dropped by `build_game_assets.py`. When a landmark's identity is uncertain, set `verified=False` in `game_points.py`. The HUD then says so.
