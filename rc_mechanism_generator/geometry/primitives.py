from __future__ import annotations

import math

import bmesh
from mathutils import Matrix, Vector


def _matrix_from_direction(direction: Vector, midpoint: Vector) -> Matrix:
    quat = direction.normalized().to_track_quat("Z", "Y")
    matrix = quat.to_matrix().to_4x4()
    matrix.translation = midpoint
    return matrix


def add_cylinder_between(
    bm: bmesh.types.BMesh,
    start: Vector,
    end: Vector,
    radius: float,
    segments: int = 16,
    cap_ends: bool = True,
) -> None:
    vec = end - start
    length = vec.length
    if length <= 1.0e-8:
        return
    matrix = _matrix_from_direction(vec, (start + end) * 0.5)
    bmesh.ops.create_cone(
        bm,
        cap_ends=cap_ends,
        cap_tris=False,
        segments=max(8, segments),
        radius1=radius,
        radius2=radius,
        depth=length,
        matrix=matrix,
    )


def add_sphere(bm: bmesh.types.BMesh, center: Vector, radius: float, segments: int = 12) -> None:
    matrix = Matrix.Translation(center)
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=max(8, segments),
        v_segments=max(6, segments // 2),
        radius=radius,
        matrix=matrix,
    )


def add_box_between(
    bm: bmesh.types.BMesh,
    start: Vector,
    end: Vector,
    width: float,
    height: float,
) -> None:
    vec = end - start
    length = vec.length
    if length <= 1.0e-8:
        return
    matrix = _matrix_from_direction(vec, (start + end) * 0.5)
    bmesh.ops.create_cube(bm, size=1.0, matrix=matrix)
    bmesh.ops.scale(
        bm,
        vec=Vector((width, height, length)),
        verts=bm.verts[-8:],
        space=Matrix.Identity(4),
    )


def add_helix_spring(
    bm: bmesh.types.BMesh,
    start: Vector,
    end: Vector,
    coil_radius: float,
    wire_radius: float,
    turns: float,
    radial_segments: int,
    path_steps_per_turn: int = 18,
    cap_ends: bool = True,
) -> None:
    axis = end - start
    length = axis.length
    if length <= 1.0e-8:
        return
    z_axis = axis.normalized()
    fallback = Vector((0.0, 1.0, 0.0)) if abs(z_axis.z) > 0.95 else Vector((0.0, 0.0, 1.0))
    x_axis = z_axis.cross(fallback).normalized()
    y_axis = z_axis.cross(x_axis).normalized()
    basis = Matrix((x_axis, y_axis, z_axis)).transposed()
    steps = max(12, int(path_steps_per_turn * turns))
    rings: list[list[bmesh.types.BMVert]] = []
    for i in range(steps + 1):
        t = i / steps
        ang = t * turns * math.tau
        center_local = Vector((math.cos(ang) * coil_radius, math.sin(ang) * coil_radius, t * length))
        tangent_local = Vector(
            (
                -math.sin(ang) * coil_radius * turns * math.tau,
                math.cos(ang) * coil_radius * turns * math.tau,
                length,
            )
        ).normalized()
        tangent = basis @ tangent_local
        normal = tangent.cross(z_axis).normalized()
        binormal = tangent.cross(normal).normalized()
        center_world = start + (basis @ center_local)
        ring = []
        for j in range(radial_segments):
            a = j / radial_segments * math.tau
            p = center_world + (math.cos(a) * normal + math.sin(a) * binormal) * wire_radius
            ring.append(bm.verts.new(p))
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    for i in range(len(rings) - 1):
        r1 = rings[i]
        r2 = rings[i + 1]
        for j in range(radial_segments):
            n = (j + 1) % radial_segments
            face_verts = (r1[j], r1[n], r2[n], r2[j])
            try:
                bm.faces.new(face_verts)
            except ValueError:
                pass
    if cap_ends and rings:
        try:
            bm.faces.new(tuple(reversed(rings[0])))
        except ValueError:
            pass
        try:
            bm.faces.new(tuple(rings[-1]))
        except ValueError:
            pass
