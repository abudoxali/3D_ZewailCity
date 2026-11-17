"""Owner-marked Administration circulation, 2026-11-10.

Retains the mapped dome/wing anchors and existing roof silhouette. Ground-level
voids follow the owner's marked routes; clearances, column grid and floor datum
are functional ESTIMATES, not an as-built interior plan. No offices/basements.
"""
from .architecture import GROUND
from .geometry import Edge

DECK = GROUND + .51
CLEAR = 5.0


def circulation(P, M):
    st = M['stone']
    # One flat, uninterrupted ground-floor plaza below the retained roof.
    # Meets the V10 vestibule exactly at y=9.42; no coplanar overlap.
    P.shell.box(M['plaza_light'], -23.4, -36, -.18, 23.4, 9.42, DECK)
    P.shell.box(M['plaza_light'], -16, -94, -.18, 16, -36, DECK)
    # Rear galleries: retain the wing slabs above and the rooms' outer masses.
    # These strips are part of the supported open circulation, not new rooms.
    for sx in (-1, 1):
        a, b = sorted((sx * 16, sx * 22))
        P.shell.box(M['plaza_light'], a, -88, -.18, b, -36, DECK)
        a, b = sorted((sx * 23.4, sx * 28.9))
        P.shell.box(M['plaza_light'], a, -16, -.18, b, 21.42, DECK)
        # Entrance threshold ramps occupy the open bays, with no stair overlaid.
        ramp(P, st, a, b, 21.42, 29.8, DECK, GROUND)
        # Return through exterior side courts into the roofed plaza.
        # A level slab and a real graded landing make the route continuous.
        a, b = sorted((sx * 23.4, sx * 28.9))
        P.shell.box(M['plaza_light'], a, -36, -.18, b, -16, DECK)
        # Support grid remains outside the axis and side passage clear widths.
        for x in (sx * 15.1,):
            for y in (-22., -34., -47., -61., -75., -89.):
                P.shell.box(st, x-.45, y-.45, DECK, x+.45, y+.45, CLEAR)
                P.det.box(M['band'], x-.46, y-.46, DECK, x+.46, y+.46, DECK+.15)
        # Concrete bearing piers visibly connect the central slab to the floor.
        for y in (-22., -33.):
            x = sx * 22.5
            P.shell.box(st, x-.4, y-.4, DECK, x+.4, y+.4, CLEAR)
        # Rear side openings flank the retained central glazed bay.
        ramp(P, st, *sorted((sx*8.5, sx*14.5)), -94., -104., DECK, GROUND)
    # Central rear glazed screen has a physical collider; the two side openings
    # are true gaps in both visible and collision meshes.
    P.shell.box(M['lobby_glass'], -5., -94.08, DECK, 5., -94.02, CLEAR)
    for x in (-5.1, 5.1):
        P.shell.box(M['metal'], x-.06, -94.12, DECK, x+.06, -93.98, CLEAR)
    # Narrow transverse structural ribs; no false lower ceilings or fixtures.
    for y in (-22., -34., -47., -61., -75., -89.):
        P.shell.box(st, -15.55, y-.35, CLEAR-.35, 15.55, y+.35, CLEAR)


def ramp(P, mat, a, b, ya, yb, za, zb):
    """Closed wedge, outward winding for either direction along the campus axis."""
    verts=[(a,ya,za),(b,ya,za),(b,yb,zb),(a,yb,zb),
           (a,ya,-.18),(b,ya,-.18),(b,yb,-.18),(a,yb,-.18)]
    faces=[(0,1,2,3),(7,6,5,4),(4,5,1,0),(5,6,2,1),
           (6,7,3,2),(7,4,0,3)]
    if yb < ya:
        faces=[tuple(reversed(f)) for f in faces]
    P.shell.raw(mat,verts,faces)
