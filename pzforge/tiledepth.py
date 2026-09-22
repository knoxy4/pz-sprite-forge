"""B42 per-tile depth, ported from the game (zombie.tileDepth.TileGeometryUtils, 42.20).

Why a sprite needs this: a B42 tile draws through the ``tileWithDepth`` shader, which takes
each pixel's depth from the tile's depth texture and DISCARDS any pixel whose texel is
empty. A tile with no depth texture falls back to ``DEPTH_whole_tile`` -- the front faces
of a full-tile cube -- so a character standing on that square always draws behind it.

Scene space is tile-local: x east, y up, z south; one tile = 1.0, one floor = sqrt(6).
A depth cell is 128x256 (2x); the value is ``getNormalizedDepth`` of the nearest surface,
larger = farther. On disk (``<mod>/common/media/depthmaps/DEPTH_<tileset>.png``, eight
128x256 cells per row) a texel is alpha 0 for "no depth", else depth = blue / 255.
The game only scans a mod's ``depthmaps`` folder when ``common/media/tileGeometry.txt``
exists (TileDepthTextureManager.init).

Pure numpy, so Blender's bundled Python can import it.
"""
from __future__ import annotations

import math

import numpy as np

FLOOR = math.sqrt(6.0)
CELL_W, CELL_H = 128, 256


def _ortho(l, r, b, t, n, f):
    m = np.identity(4)
    m[0, 0] = 2 / (r - l); m[1, 1] = 2 / (t - b); m[2, 2] = 2 / (n - f)
    m[0, 3] = (r + l) / (l - r); m[1, 3] = (t + b) / (b - t); m[2, 3] = (f + n) / (n - f)
    return m


def _rot(axis: str, a: float):
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1.0]])
    if axis == "y":
        return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1.0]])
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])


def _trans(x, y, z):
    m = np.identity(4)
    m[0, 3], m[1, 3], m[2, 3] = x, y, z
    return m


# calcMatricesForSquare: ortho over one 1x2 tile view, camera pitched 30 deg, yawed 315 deg
_S2 = math.sqrt(2.0)
PROJ = _ortho(-_S2 / 2, _S2 / 2, -_S2, _S2, -2.0, 2.0) @ _trans(0, -2 * _S2 * 0.375, 0)
VIEW = _rot("x", math.radians(30)) @ _rot("y", math.radians(315))
MVP = PROJ @ VIEW
INV = np.linalg.inv(MVP)


def depth_of_points(p: np.ndarray) -> np.ndarray:
    """Raw depth (MVP z) of scene points, shape (3, n) -> (n,)."""
    return MVP[2, :3] @ p + MVP[2, 3]


_D_NW = abs(float(depth_of_points(np.array([[-0.5], [0.0], [-0.5]]))[0]))


def normalized(d):
    """getNormalizedDepth: the tile's back floor corner (NW) maps to 1.0."""
    return d * (0.25 / _D_NW) + 0.75


def pixel_rays():
    """Camera ray for every pixel centre of a 128x256 cell, as scene-space
    (origins (3, n), unit directions (3, n)), row-major from the top-left pixel."""
    ys, xs = np.mgrid[0:CELL_H, 0:CELL_W]
    ui_x = (xs.ravel() + 0.5) / 128.0
    ui_y = 2.0 - (ys.ravel() + 0.5) / 128.0
    ndc_x, ndc_y = ui_x * 2 - 1, ui_y - 1
    n = ndc_x.size
    near = INV @ np.stack([ndc_x, ndc_y, -np.ones(n), np.ones(n)])
    far = INV @ np.stack([ndc_x, ndc_y, np.ones(n), np.ones(n)])
    a, b = near[:3] / near[3], far[:3] / far[3]
    d = b - a
    return a, d / np.linalg.norm(d, axis=0)


def pixel_of_point(p):
    """Scene point -> (px, py) inside the 128x256 cell."""
    v = MVP @ np.array([p[0], p[1], p[2], 1.0])
    return (v[0] + 1) / 2 * 128.0, (1.0 - v[1]) * 128.0


def fill_to_mask(depth: np.ndarray, mask: np.ndarray, max_steps: int = 64):
    """Give every masked pixel a depth. Geometry misses inside the sprite's silhouette
    (contour strokes, grounding, antialiased rims) take the nearest hit, grown outward one
    4-neighbour ring per step, taking the NEARER (smaller) neighbour. Unmasked pixels are
    cleared. Returns (depth, filled_count, steps, unfilled_count)."""
    d = np.where(mask, depth, -1.0)
    known = d >= 0
    filled, steps = 0, 0
    while steps < max_steps:
        hole = mask & ~known
        if not hole.any():
            break
        pad = np.pad(np.where(known, d, np.inf), 1, constant_values=np.inf)
        nb = np.minimum.reduce([pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:]])
        grow = hole & np.isfinite(nb)
        if not grow.any():
            break
        d = np.where(grow, nb, d)
        known |= grow
        filled += int(grow.sum())
        steps += 1
    unfilled = int((mask & ~known).sum())
    return d, filled, steps, unfilled


def encode_cell(depth: np.ndarray) -> np.ndarray:
    """Float depth (-1 = none) -> RGBA uint8 cell, the layout TilesetDepthTexture.load reads."""
    out = np.zeros(depth.shape + (4,), dtype=np.uint8)
    has = depth >= 0
    v = np.clip(np.floor(np.minimum(depth, 1.0) * 255.0), 1, 255).astype(np.uint8)
    for c in range(3):
        out[..., c] = np.where(has, v, 0)
    out[..., 3] = np.where(has, 255, 0)
    return out


def geometry_box_block(lo, hi) -> str:
    """One tileGeometry.txt VERSION 2 box, axis-aligned, scene units x10000, in vanilla's
    own convention: translate = centre of the footprint at the box's bottom, min y = 0."""
    f = lambda v: "x".join(str(int(round(c * 10000))) for c in v)
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    hx, hz = (hi[0] - lo[0]) / 2, (hi[2] - lo[2]) / 2
    return ("            box\n            {\n"
            f"                translate = {f([cx, lo[1], cz])},\n"
            "                rotate = 0x0x0,\n"
            f"                min = {f([-hx, 0, -hz])},\n"
            f"                max = {f([hx, hi[1] - lo[1], hz])},\n"
            "            }\n")
