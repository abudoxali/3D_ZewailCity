# Licenses and attribution

- Campus source code and authored geometry remain under the project owner's control. This maintenance freeze does not grant a new blanket license.
- Poly Haven PBR surfaces, HDRI, Pachira, iceplant, Gazania and Shrub 01: recorded CC0 provenance and file hashes in `game/godot/assets/pbr/manifest.json` and `references/assets/**/manifest.json` / `SOURCE_AND_LICENSE.json`.
- Innerscene detailed and mature date palms: recorded CC0 source/license statements in their `references/assets/innerscene_*/manifest.json`.
- ambientCG reference/evaluated surfaces: provenance retained in the PBR manifests. Source inputs are retained for reproducibility; not every retained map is active in the final scene.
- Noto Sans Arabic: SIL Open Font License; full notice in `licenses/NotoSansArabic-OFL.txt`.
- Shapely 2.2.0 / GEOS: included upstream notices in `licenses/` and `tools/vendor/shapely-2.2.0.dist-info/licenses/`. The vendored wheel targets Windows x64 / CPython 3.13. Other platforms need a compatible Shapely installation in Blender's Python.
- Optional Godot MCP bridge: MIT, copyright 2025 slangwald; full notice in `licenses/Godot-MCP-MIT.txt`. No MCP server is required to open, build or play the project.
- Godot 4.6.2 is MIT-licensed. Exact engine license and third-party notices exported from the installed engine are included in `licenses/Godot-Engine-License.txt` and `licenses/Godot-Third-Party-Notices.json`. Blender is a separately installed GPL application and is not bundled.
- Original OSM/geospatial/photographic source attribution and uncertainty are retained in `references/SOURCE_EVIDENCE.md`, `references/geodata/`, and asset manifests. OSM data remains subject to its source attribution/ODbL terms.
- Owner photographs, third-party reference photographs, brochure and video in `references/` are local reference evidence, **not licensed for public redistribution**. Exclude them from public releases unless separately authorized. Public reuse rights for textures/models do not grant rights to these references or campus branding.
- Microsoft fonts are not redistributed. Existing Windows fonts are used when available; a bundled OFL Noto font is the rebuild fallback. The frozen master already contains the rendered text meshes.
