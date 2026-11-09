# Geodata used by the V4 reconstruction

| File | What | Licence |
|---|---|---|
| `campus_area_osm.json` | Overpass extract, every way and node in 29.928–29.952 N, 31.050–31.082 E (`out body geom`), taken 2026-11-06 | ODbL 1.0, © OpenStreetMap contributors |
| `core_meta.json`, `zewail_named.json`, `unis.json` | Edit metadata (dates, versions, users) and name searches used to find and date the campus features | ODbL 1.0 |
| `osm_axis_frame.json` | The extract converted to the campus axis frame by `tools/geo/osm_to_axis.js` | ODbL 1.0 (derived) |
| `s2_search.json`, `s2_20260916_*_meta.json` | STAC search result and crop metadata for Sentinel-2 L2A `S2A_36RUU_20260916` | Copernicus open data |
| `s2_20260916_B04.u16`, `s2_20260916_B08.u16` | 181 × 181 px crops (10 m) of the red and NIR bands, raw uint16 after a 15-byte header | Copernicus open data ("contains modified Copernicus Sentinel data 2026") |
| `s2_20260916_campus_x6.png` | True-colour crop, north up, upscaled ×6 for viewing | as above |
| `s2_20260916_axis.png`, `s2_20260916_axis_osm_overlay.png` | True colour resampled into the axis frame (1 px = 1 m, x −560…560, axis y −560…640), without and with the OSM lines | as above + ODbL |
| `ndvi_s2_20260916_blender_frame.png` | Preview of the NDVI grid stored in `src/utilities/data/ndvi_s2_20260916.json` | as above |
| `osm_*.png` | OSM rasters for inspection (overview, axis frame, approach and front zooms) | ODbL |

Regenerate everything with the scripts in `tools/geo/` (Node.js, no extra packages):

```bash
node tools/geo/osm_to_axis.js references/geodata/campus_area_osm.json references/geodata/osm_axis_frame.json
```

```bash
node tools/geo/export_osm_campus.js references/geodata/osm_axis_frame.json src/utilities/data/osm_campus.json
```

```bash
node tools/geo/s2_crop.js <TCI url> 29.9415 31.0665 900 crop.ppm meta.json
```

```bash
node tools/geo/ndvi_to_blender.js B04.u16 B08.u16 meta.json osm_axis_frame.json 246.1 src/utilities/data/ndvi_s2_20260916.json preview.ppm
```
