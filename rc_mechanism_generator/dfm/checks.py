from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector

from ..utils.blender_utils import bbox_intersects, world_bbox_bounds


def _generated_mesh_objects(scene: bpy.types.Scene) -> list[bpy.types.Object]:
    result = []
    for obj in scene.objects:
        if obj.type == "MESH" and "rcgen_id" in obj and "rcgen_module" in obj:
            result.append(obj)
    return result


def _manifold_check(obj: bpy.types.Object) -> tuple[bool, str]:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    non_manifold = [e for e in bm.edges if not e.is_manifold]
    bm.free()
    if non_manifold:
        return False, f"{obj.name}: non-manifold edges={len(non_manifold)}"
    return True, ""


def _min_dimension_m(obj: bpy.types.Object) -> float:
    dims = obj.dimensions
    return min(dims.x, dims.y, dims.z)


def _estimate_overhang_ratio(obj: bpy.types.Object, warn_deg: float) -> float:
    if obj.type != "MESH" or len(obj.data.polygons) == 0:
        return 0.0
    up = Vector((0.0, 0.0, 1.0))
    warn_rad = math.radians(warn_deg)
    total = 0
    bad = 0
    rot = obj.matrix_world.to_3x3()
    for poly in obj.data.polygons:
        total += 1
        n = (rot @ poly.normal).normalized()
        angle_from_up = n.angle(up)
        if angle_from_up > warn_rad and n.z < 0.2:
            bad += 1
    if total == 0:
        return 0.0
    return bad / total


def _hole_edge_warning(obj: bpy.types.Object, hole_diameter_mm: float, min_edge_hole_margin_mm: float) -> bool:
    hole_dia_m = hole_diameter_mm / 1000.0
    margin_m = min_edge_hole_margin_mm / 1000.0
    min_dim = _min_dimension_m(obj)
    return min_dim < (hole_dia_m + margin_m * 2.0)


def _oversize_warning(obj: bpy.types.Object, settings: bpy.types.PropertyGroup) -> bool:
    max_x = settings.print_volume_x_mm / 1000.0
    max_y = settings.print_volume_y_mm / 1000.0
    max_z = settings.print_volume_z_mm / 1000.0
    dims = obj.dimensions
    return dims.x > max_x or dims.y > max_y or dims.z > max_z


def _wheelwell_interference_warning(obj: bpy.types.Object, refs: bpy.types.PropertyGroup) -> list[str]:
    warnings = []
    for side in ("l", "r"):
        wheelwell = getattr(refs, f"wheelwell_{side}_obj", None)
        if wheelwell is not None and bbox_intersects(obj, wheelwell):
            warnings.append(f"{obj.name}: intersects WheelWell_{side.upper()} (bbox)")
    return warnings


def suggested_print_orientation(obj: bpy.types.Object) -> tuple[float, float, float]:
    min_v, max_v = world_bbox_bounds(obj)
    dims = max_v - min_v
    if dims.z <= dims.x and dims.z <= dims.y:
        return (0.0, 0.0, 0.0)
    if dims.x <= dims.y:
        return (0.0, math.radians(90.0), 0.0)
    return (math.radians(90.0), 0.0, 0.0)


def run_printability_checks(scene: bpy.types.Scene) -> tuple[list[str], list[str], dict[str, dict[str, float]]]:
    settings = scene.rcgen_settings
    refs = scene.rcgen_refs
    errors: list[str] = []
    warnings: list[str] = []
    orientations: dict[str, dict[str, float]] = {}
    objs = _generated_mesh_objects(scene)

    for obj in objs:
        ok, manifold_msg = _manifold_check(obj)
        if not ok:
            errors.append(manifold_msg)

        if _min_dimension_m(obj) < settings.min_wall_mm / 1000.0:
            errors.append(f"{obj.name}: below minimum wall {settings.min_wall_mm:.2f} mm")

        if _hole_edge_warning(obj, settings.hole_diameter_mm, settings.min_edge_hole_margin_mm):
            warnings.append(f"{obj.name}: hole too close to edge (approx)")

        ratio = _estimate_overhang_ratio(obj, settings.overhang_warn_deg)
        if ratio > 0.35:
            warnings.append(f"{obj.name}: overhang-heavy geometry ({ratio * 100.0:.0f}% faces)")

        if _oversize_warning(obj, settings):
            msg = f"{obj.name}: exceeds print volume {settings.print_volume_x_mm:.0f}x{settings.print_volume_y_mm:.0f}x{settings.print_volume_z_mm:.0f} mm"
            if settings.auto_split_large_parts:
                warnings.append(msg + "; split recommended")
            else:
                errors.append(msg)

        warnings.extend(_wheelwell_interference_warning(obj, refs))

        ori = suggested_print_orientation(obj)
        orientations[obj.name] = {"rx_rad": ori[0], "ry_rad": ori[1], "rz_rad": ori[2]}

    return errors, warnings, orientations
