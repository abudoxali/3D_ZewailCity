# V15 final visual QA (V14 left vs V15 right, 29 boards reviewed by eye)

## Per-view verdicts
- G1_exterior_eye: BETTER. Modular kerb units with joints replace the smooth ribbon kerb, and the sand/island edge is cleaner. Gate, cacti island and asphalt are unchanged.
- O02_G1_inside: SAME/slightly WORSE. Kerb is modular, but a pale diagonal streak and a lighter patch now run across the lawn (right half, about x1430-1700,y360-500). The lawn is also darker and more saturated.
- V15_g1_inside_kerbs: SAME. Almost identical. The lawn edge strip is slightly more broken.
- V14_g1_gate_sand: BETTER. The diagonal glint/streak on the sand-paver boundary is gone and the edge is softer. A straight hard line remains where the paver meets the sand.
- V14_g1_median_nose: BETTER. The kerb is modular and the lawn kerb reads crisper. A hard-edged sand wedge sits at bottom-left (x960-1050,y400-580).
- V15_crossover_bands_eye: BETTER. The blobs on the pavement are gone and the right bed is brown soil with groundcover. The dark crossover band is only a faint brown strip (x1290-1560,y330-345), much weaker than C02.
- V15_median_eye: BETTER. The large blob shrubs standing on the pavement (V14 bottom-left) are removed, and the median lawn is a flat worn strip. It is a bit flat and pale-green.
- main_approach_road: BETTER vs V14 blobs, but the bed is the weak point. It is a large bare brown field with sparse, oversized leaf sprigs. It reads as a weed or seedling patch, not the dense low groundcover rows in C02.
- V12_approach_close: BETTER in structure (kerbed bed, no blobs). Leaf clumps are about 40-80 cm large and sparse, with flat dark soil.
- V15_verge_bed_close: BETTER, with the same bed-realism caveat. The kerb is continuous and tidy.
- V15_kerb_close: BETTER. Plants sit in a bed behind a kerb. The kerb has a visible end or gap near x1390-1420,y320-335 (first unit stops short), and the bluish-grey strip beside the paver edge (x965-1390,y340-500) looks flat and overly blue.
- V15_ring_junction_kerbs: BETTER. Blobs are gone and the bed is kerbed. Same sparse-leaf issue.
- V12_junction_dropoff_eye: SAME/mixed. The hard soil edge becomes a feathered sand fringe, which is more natural. The lawn is slightly more washed-out, and the sand reads as a pale band.
- junction_dropoff_ring: SAME/mixed. The kerbed brown beds are visible and plausible. Ground patches are now smudgy and blurry, and the lawn is desaturated.
- V13_approach_aerial: SAME/mixed. The approach has believable brown beds and G1 is intact. The soft ground reads hazy and smudgy, and the sand patches look washed out.
- admin_entrance_axis: BETTER. The forecourt edge now has a segmented precast kerb, where V14 had a smooth slab.
- drone_overview: SAME/WORSE. The corridor beds read as thin brown strips. Terrain patches are now blurry grey-brown smears, which looks like a low-quality blend.

## Defects in V15
1. HIGH: Large ground changes outside the corridor (see Q4). Soft-feathered terrain patches in drone_overview, V13_approach_aerial and junction_dropoff_ring look smudged and muddy. The brief said views outside the corridor should be unchanged.
2. MEDIUM: Groundcover scale and density are wrong in the bed boards, and the bed is mostly bare soil. The sprigs are oversized and sparsely scattered, and the repetition is visible at x1160-1700,y380-560 in V12_approach_close. C02 shows dense low planting rows.
3. MEDIUM: O02_G1_inside has a diagonal pale seam or feather-decal band across the lawn (right half, x1430-1700,y360-500).
4. MEDIUM: V15_kerb_close shows a kerb unit gap or ragged start near x1400,y325. The bluish kerb footing strip looks off-colour (x965-1390,y340-500).
5. MEDIUM: Crossover dark bands are barely visible (V15_crossover_bands_eye), so the requested feature is under-delivered.
6. LOW: A hard-edged sand wedge remains at V14_g1_median_nose bottom-left and a straight sand-paver line in V14_g1_gate_sand.
7. LOW: A tan vertical streak across the asphalt (about x230-300,y380-540) persists in V12_G1_close and O03_G1_paving_curb. It is the same in V14, so not new.
8. LOW: Median lawn is thin and flat, with no worn-grass variation. Median palms are unchanged, and there are still no young trees in the beds as in C02.
9. LOW: Lawn colour/saturation shifted slightly in several boards (O02, V12_junction_dropoff_eye).

No floating objects, z-fighting or plants standing on pavement were seen in V15. The pavement blobs in V14 are gone.

## Answers
1. Clearly and substantially better in shape, surface quality and continuity? NO (partly). The kerbs, removal of blobs on pavement, and the G1 island and edges are real improvements. But the main visible gain is a bare brown bed with sparse oversized sprigs, and ground feathering looks smudgy. The overall step is moderate, not substantial.
2. Matches C02 better than V14? YES, modestly. Raised kerbed brown beds and modular kerbs are closer to C02. The dark crossover bands and dense low groundcover are not there, and the lawn median is less convincing.
3. New severe regression? NO. Nothing is broken or floating. The ground-feathering smudge outside the corridor is the nearest to a regression (high-severity scope issue, not a geometry failure).
4. Change visible outside the corridor? YES. Aerial boards (drone_overview, V13_approach_aerial, junction_dropoff_ring) show reblended terrain patches across the whole site. Ground-level non-corridor boards (O07_academic_front, dorm_garden_paths, academic_court_aerial, admin_lobby_threshold, P13_court_photo, ring_road_eye) look identical. The O07 sand patch differs only imperceptibly.
5. Recommendation: PARTIAL. Do not present as a clear owner win yet. Fix groundcover density/scale and the lawn seam, restrict the ground feather to the corridor mask, and strengthen the crossover bands before owner review.

---

# Round 2 (final3)

Reviewed by eye: the prioritised boards above, plus V15_median_eye, V12_junction_dropoff_eye and academic_court_aerial.

## Fixed
- Aerial smear is mostly gone. drone_overview now looks almost the same as V14, with only a slight softening at patch edges.
- The O02 lawn seam is gone. The median now has plausible tan worn patches.
- Groundcover is denser and smaller, with 0.7 m row structure now visible. It looks like young bed planting and is clearly closer to C02. It is still not C02's dense low carpet.
- V15_median_eye and V12_junction_dropoff_eye are as good as or better than round 1, and the ground edge is softer than in V14.

## Per-view verdicts vs V14
- **BETTER:** G1_exterior_eye, V14_g1_gate_sand, V14_g1_median_nose, V15_median_eye, main_approach_road, V12_approach_close, V15_verge_bed_close, V15_ring_junction_kerbs, admin_entrance_axis, V15_crossover_bands_eye.
- **BETTER, with a remaining flaw:** V15_kerb_close.
- **SAME or slightly better:** O02_G1_inside, V15_g1_inside_kerbs, V12_junction_dropoff_eye, junction_dropoff_ring. Smear is largely gone and kerbs and beds are an improvement.
- **SAME to slightly better:** V13_approach_aerial (faint soft mottling remains at left x1000-1250,y290-330) and drone_overview.

## Remaining defects
- **Medium:** The bed is still dominated by bare brown soil with sparse rosettes (main_approach_road, V12_approach_close). It reads as a seedling bed and falls short of C02's dense low rows.
- **Medium:** V15_kerb_close still shows the first kerb unit stopping short, with a flat bluish footing strip along the paver edge (x965-1390,y340-500). A hard kerb end is still visible near x1400,y325. The repair may not be visible here, or the crack was a different feature.
- **Medium:** Crossover bands are still only a faint brown strip (V15_crossover_bands_eye x1290-1560,y330-345). The requested darker bands are not obvious next to C02's dark transverse paver bands.
- **Low:** Faint soft ground mottling in the aerials, the sand wedge, the sand/paver line and the asphalt tan streak (the last three are inherited, unchanged from V14).
- **Low:** Median lawn is flat and light green, with no young trees in the beds.
- No floating objects, z-fighting or plants on pavement were seen.

## Answers
1. Clearly and substantially better in shape, surface quality and physical continuity of G1 and the approach? YES, narrowly. The lawn, aerial and groundcover regressions are fixed. Modular kerbs, kerbed beds and no blobs on pavement are a real step up, and there are no regressions. The beds and the kerb end/footing strip are still short of ideal.
2. Matches C02 better than V14? YES. Kerbed brown beds with row-planted groundcover match C02 more closely. Crossover bands and planting density are still short.
3. New severe regression? NO.
4. Change visible outside the corridor? NO for ground-level boards. In the aerials only slight soft patch-edge changes remain (drone_overview is near-identical, V13_approach_aerial has faint mottling). Treat as negligible.
5. Recommendation: READY FOR OWNER VISUAL REVIEW, with the known limits flagged (sparse bed density, faint crossover bands, kerb end/bluish footing strip in V15_kerb_close).
