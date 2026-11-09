"""V10 Administration & Cultural Building: central block and principal entrance.

Single-owner module (V10 ownership matrix: Codex CLI). Replaces the V9 solid
central block with a bounded entrance shell. Uses the shared Parts accumulator;
geometry still lands in AB_Administration_Cultural_Building(_Glass/_Details).

Evidence: A02 (Hassan Allam front elevation), A01, A04; A03 palette only. Metric
dimensions are estimates unless stated.
"""
from . import site_plan as SP
from .architecture import GROUND
from .geometry import Edge, rect_poly

G = GROUND
# Functional ESTIMATES, not a surveyed interior (A02 obscures the doors).
LOBBY_HALF_WIDTH = 11.6
LOBBY_DEPTH = 12.0
LOBBY_CLEAR_HEIGHT = 4.2
SCREEN_RECESS = 2.5
DOORWAYS = ((-1.1, 1.1), (1.9, 4.1))
DOOR_CLEAR_HEIGHT = 2.8


def _xr(a, b):
    return (min(a, b), max(a, b))


def face_py(x0, x1, y):
    """Facade facing +Y between x0..x1; arc length s = x_hi - x."""
    lo, hi = _xr(x0, x1)
    return Edge((hi, y), (lo, y)), hi


def build(P, M):
    st, band = M['stone'], M['band']
    yF = SP.ADMIN['front_y']            # 21.4
    yPo = SP.ADMIN['portico_front_y']   # 29.8
    deck = G + 3 * .17
    back = yF - LOBBY_DEPTH
    ceiling = deck + LOBBY_CLEAR_HEIGHT
    w = LOBBY_HALF_WIDTH
    # Closed outward-facing prisms around an actual void; no facade/block face
    # crosses the axis. The back block bounds the unfinished public vestibule.
    P.rblock(-18, -16, 18, back, G, 18.0)
    P.rblock(-18, back, -w, yF, G, ceiling + .12)
    P.rblock(w, back, 18, yF, G, ceiling + .12)
    P.shell.box(M['plaster'], -w, back, ceiling, w, yF, ceiling + .12)  # V10 integration: matte ceiling
    P.rblock(-18, back, 18, yF, ceiling + .12, 18.0)
    P.parapet(rect_poly(-18, -16, 18, yF), 18.0)

    # A02: stout square stone supports, not the palm trunks/round V9 columns.
    # Keep the inherited projecting frame and upper silhouette (A01).
    P.shell.box(st, -13.2, yF, 8.2, 13.2, yPo, 10.6)
    P.det.box(band, -8.0, yPo, 8.9, 8.0, yPo + 0.06, 10.1)          # name-sign fascia
    P.det.box(M['roof'], -13.0, yF + 0.2, 10.6, 13.0, yPo - 0.2, 10.65)
    for sx in (-1, 1):
        lo, hi = _xr(sx * 12.0, sx * 13.2)
        P.shell.box(st, lo, yPo - 4.2, G, hi, yPo, 8.2)              # solid stone cheek legs
        P.det.box(band, lo - 0.02, yPo - 4.2, 0.6, hi + 0.02, yPo + 0.02, 0.9)
    for x in (-7.0, 7.0):
        P.shell.box(st, x - .7, yPo - 1.4, deck, x + .7, yPo, 8.2)
    # Plain soffit panel; no unsupported lighting fixtures.
    P.det.box(M['metal_light'], -11.6, yF + 0.6, 8.12, 11.6, yPo - 0.6, 8.2)
    # Recessed ground glazing: two actual gaps in BOTH glass and collision.
    screen = yF - SCREEN_RECESS
    door_top = deck + DOOR_CLEAR_HEIGHT
    metal = M['metal']
    panels = ((-w, DOORWAYS[0][0]), (DOORWAYS[0][1], DOORWAYS[1][0]),
              (DOORWAYS[1][1], w))
    for a, b in panels:
        # Codex independent review (V10, High): glazing in P.glass is not part of the
        # game collider, so the 2 m spans between posts were walk-through. The fixed
        # lower panels are emitted into the shell (same glass material), so they
        # render identically and block the player; the doorways stay open.
        P.shell.box(M['lobby_glass'], a + .10, screen, deck + .05, b - .10, screen + .06, door_top)
        for x0, x1 in ((a, a + .10), (b - .10, b)):
            P.shell.box(metal, x0, screen, deck, x1, screen + .14, door_top)
        P.det.box(metal, a, screen, deck, b, screen + .14, deck + .05)
        n = max(1, round((b - a) / 2.1))
        for i in range(1, n):
            x = a + (b - a) * i / n
            P.det.box(metal, x - .045, screen + .04, deck, x + .045, screen + .14, door_top)
    P.shell.box(metal, -w, screen, door_top, w, screen + .14, door_top + .10)
    P.glass.box(M['lobby_glass'], -w, screen, door_top + .10, w, screen + .06, ceiling - .10)
    P.shell.box(metal, -w, screen, ceiling - .10, w, screen + .14, ceiling)
    # V8: the three steps previously ended at +0.72 with no matching landing.
    # Retain their rise; carry the surface back to the existing facade. A 1.8 m
    # side ramp (~6.5% estimated engineering interpretation) occupies a cut channel
    # in the steps, never an overlapping ramp laid over the stair geometry.
    P.steps(Edge((10.1,yPo),(-14,yPo)),12.05,24.1,n=3)
    P.steps(Edge((14,yPo),(11.9,yPo)),1.05,2.1,n=3)
    # One slab spans landing, threshold and lobby: no overlapping floor/deck
    # top faces. Face-domain tag survives Parts.finish for later interior work.
    tag = P.shell.bm.faces.layers.int.get('v10_admin_vestibule_floor')
    if tag is None:
        tag = P.shell.bm.faces.layers.int.new('v10_admin_vestibule_floor')
    # Allocate custom data before remembering BMesh elements: adding a layer
    # can invalidate existing face wrappers in Blender.
    floor_faces = set(P.shell.bm.faces)
    P.shell.box(M['plaza_light'], -w, back, G, 11.9, yPo, deck)
    for face in set(P.shell.bm.faces) - floor_faces:
        face[tag] = 1
    # Integration review (Claude, V10): Codex's isolated harness had no site, so it
    # added a plaza-level apron (top 0.21) in front of the steps. In the full scene
    # Plaza_Paving already provides that 0.21 m surface (live MCP ray probe at
    # (0,32), (-8,33), (5,34.2): Plaza_Paving z=0.21), so the apron would be
    # coplanar with it (z-fighting). It is omitted; the harness keeps its own
    # stand-in floor for the stair start.
    x0,x1=10.1,11.9;ya,yb=yPo,yPo+10.2
    foot=.06  # Road_Network_Internal surface, confirmed by V8 source ray probe.
    P.shell.raw(st,[(x0,ya,deck),(x1,ya,deck),(x1,yb,foot),(x0,yb,foot),
                    (x0,ya,-.15),(x1,ya,-.15),(x1,yb,-.15),(x0,yb,-.15)],
                   [(0,1,2,3),(7,6,5,4),(4,5,1,0),(5,6,2,1),(6,7,3,2),(7,4,0,3)])
    for x in (x0+.05,x1-.05):
        for k in range(7):
            t=k/6;y=ya+(yb-ya)*t;z=deck+(foot-deck)*t
            P.det.cylinder(M['metal_light'],(x,y),z,z+1.02,.025,segs=8)
        for rise in (.56,1.02):
            vertices=[(xx,yy,zz) for xx in (x-.025,x+.025) for yy,zz in
                      [(ya,deck+rise-.025),(yb,foot+rise-.025),(yb,foot+rise+.025),(ya,deck+rise+.025)]]
            P.det.raw(M['metal_light'],vertices,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)])
    # central upper curtain wall, stone band, dark band
    e, hi = face_py(-13, 13, yF)
    # The solid storey above the vestibule retains the dark glazed facade read;
    # only the ground-floor screen moves behind yF.
    P.curtain(e, hi - w, hi + w, ceiling + .20, 8.12, mull=1.6, transom=3.0)
    P.curtain(e, hi - 13, hi + 13, 10.4, 14.6, mull=1.6, transom=2.1)
    P.band(e, hi - 18, hi + 18, 16.0, 17.2)
    # Retained stone tower piers flanking the centre; no new metric photo fit.
    for sx in (-1, 1):
        lo, hi2 = _xr(sx * 13, sx * 18)
        P.det.box(st, lo, yF, G, hi2, yF + 1.3, 18.0)
        P.det.box(band, lo, yF + 1.3, 16.0, hi2, yF + 1.36, 17.2)
