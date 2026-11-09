"""Unverified masterplan buildings, kept apart from the as-built campus.

These are simple blockouts of buildings drawn on the 2014 site plan (B04) whose
existence is NOT confirmed by any dated photograph available to this project.
Plan buildings 1 and 2 are contradicted by A01 (open land at their location).
The collection is excluded from the view layer and from rendering by default;
enable it in the outliner to compare the proposal with the as-built model.
"""
import math

import bpy

from . import site_plan as SP
from .geometry import MeshBuilder


def build_proposals(M, C):
    coll = C['proposals']
    objs = []
    for label, u, v, length, width, rot, h in SP.PROPOSED:
        cx, cy = SP.P(u, v)
        mb = MeshBuilder()
        mb.obox(M['proposal'], (0, 0, h / 2), (length, width, h))
        o = mb.to_object(label, coll, recenter=False)
        o.location = (cx, cy, 0.0)
        o.rotation_euler = (0, 0, math.radians(rot))
        o.display_type = 'WIRE'
        o["evidence"] = "B04 site plan only; not confirmed by photographs"
        objs.append(o)
    coll.hide_render = True
    for vl in bpy.context.scene.view_layers:
        lc = vl.layer_collection.children.get(coll.name)
        if lc:
            lc.exclude = True
    return objs
