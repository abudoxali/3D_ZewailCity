"""Owner photos 6/7/16/17 (20-28-31): paired timber pergolas in a housing garden.

Form is photo-supported. All placement, dimensions and seating are ESTIMATED;
live Maps/Earth review supports the eastern housing association, not a survey.
The two distinct shade plazas are visible together in photos 6 and 16. Geometry uses
the housing root's local .21 m paving datum; the campus pass moves the root once.
"""
from shapely.geometry import box, LineString
from shapely import union_all

PERGOLAS = ({'center': (409., -608.), 'width': 12., 'depth': 8.,
             'plaza': (401., -614., 417., -602.),
             'connection': ((409., -608.), (424., -608.))},
            {'center': (371., -594.), 'width': 12., 'depth': 8.,
             'plaza': (363., -600., 379., -588.),
             'connection': ((371., -594.), (371., -582.))})
PAVING_Z = .21
SOURCE = 'Owner photo_6/7/16/17_2026-11-10_20-28-31; two pergolas photo-supported; all metric layout ESTIMATED; eastern housing association supported by live GIS review, not surveyed'


def garden_layout(garden, shell, original_path):
    """Reserve plaza and a broad link before deriving planting/hedges/trees."""
    plazas = union_all([box(*s['plaza']) for s in PERGOLAS])
    links = union_all([LineString(s['connection']).buffer(1.8, cap_style='flat')
                       for s in PERGOLAS])
    addition = plazas.union(links).intersection(garden).difference(shell.buffer(1.2))
    return original_path.union(addition), plazas, links.intersection(garden)


def furniture_footprints(spec):
    """Actual projected support/bench envelopes for spatial verification."""
    x, y = spec['center']
    posts = [box(x + dx - .16, y + dy - .16, x + dx + .16, y + dy + .16)
             for dx in (-5.4, -1.8, 1.8, 5.4) for dy in (-3.2, 3.2)]
    benches = [box(x + dx - 1.5, y + dy - .30, x + dx + 1.5, y + dy + .30)
               for dx in (-3.1, 3.1) for dy in (-2.35, 2.35)]
    return posts, benches


def build(M, collection, root):
    from .geometry import MeshBuilder, parent_keep
    root['zc_identity'] = 'Eastern housing pair; geographic association supported by live Maps/Earth review; exact footprint, garden and camera alignment ESTIMATED'
    root['zc_photo_sources'] = 'Owner photo_6/7/10/16/17_2026-11-10_20-28-31 + photo_6_2026-11-10_20-26-04; LIVE_GIS_REVIEW.md'
    root['zc_garden'] = 'Southern housing court; two photo-supported timber pergolas; paths, dimensions, furniture count and metric placement ESTIMATED'
    for i, spec in enumerate(PERGOLAS, 1):
        x, y = spec['center']
        z = PAVING_Z
        timber = MeshBuilder()
        # Eight slender square posts, open sides, longitudinal beams and a
        # permeable rectangular timber lattice: no invented solid pavilion roof.
        for dx in (-5.4, -1.8, 1.8, 5.4):
            for dy in (-3.2, 3.2):
                timber.box(M['wood'], x+dx-.16, y+dy-.16, z,
                           x+dx+.16, y+dy+.16, z+3.35)
        for dy in (-3.2, 3.2):
            timber.box(M['wood'], x-6.1, y+dy-.12, z+3.18,
                       x+6.1, y+dy+.12, z+3.50)
        for k in range(25):
            dx = -6.0 + k*.5
            timber.box(M['wood'], x+dx-.06, y-4., z+3.50,
                       x+dx+.06, y+4., z+3.68)
        for k in range(9):
            dy = -4.0 + k
            timber.box(M['wood'], x-6.1, y+dy-.045, z+3.68,
                       x+6.1, y+dy+.045, z+3.76)
        obj = timber.to_object(f'Dorm_Photo_Pergola_{i}', collection)
        parent_keep(obj, root)
        obj['zc_collision'] = True
        obj['zc_evidence'] = SOURCE
        obj['zc_floor_local_m'] = PAVING_Z

        seats = MeshBuilder()
        # Seating is an explicitly estimated amenity under the photographed
        # shade structure. Both ends and a >4 m central aisle remain open.
        for dx in (-3.1, 3.1):
            for dy in (-2.35, 2.35):
                for lx in (-1.1, 1.1):
                    seats.box(M['metal'], x+dx+lx-.06, y+dy-.22, z,
                              x+dx+lx+.06, y+dy+.22, z+.42)
                for slat in range(4):
                    yy = y+dy-.28+slat*.15
                    seats.box(M['wood'], x+dx-1.5, yy, z+.42,
                              x+dx+1.5, yy+.12, z+.48)
                by = y+dy+(.25 if dy > 0 else -.30)
                seats.box(M['wood'], x+dx-1.5, by, z+.58,
                          x+dx+1.5, by+.05, z+.85)
        obj = seats.to_object(f'Dorm_Photo_Shaded_Seating_{i}', collection)
        parent_keep(obj, root)
        obj['zc_collision'] = True
        obj['zc_evidence'] = SOURCE + '; bench count/design ESTIMATED'
        obj['zc_floor_local_m'] = PAVING_Z
