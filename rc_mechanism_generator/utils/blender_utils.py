from __future__ import annotations

import json
import os
from typing import Iterable

import bpy
import bmesh
from mathutils import Vector


def mm_to_m(value_mm: float) -> float:
    return value_mm / 1000.0


def ensure_collection(parent: bpy.types.Collection, name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    if collection.name not in [c.name for c in parent.children]:
        parent.children.link(collection)
    return collection


def ensure_collection_path(scene: bpy.types.Scene, names: Iterable[str]) -> bpy.types.Collection:
    collection = scene.collection
    for name in names:
        collection = ensure_collection(collection, name)
    return collection


def delete_object_if_exists(name: str) -> None:
    obj = bpy.data.objects.get(name)
    if obj is not None:
        mesh = obj.data if obj.type == "MESH" else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def ensure_empty(
    scene: bpy.types.Scene,
    name: str,
    location: Vector,
    collection: bpy.types.Collection,
    size: float = 0.01,
) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        obj.empty_display_type = "PLAIN_AXES"
        obj.empty_display_size = size
        collection.objects.link(obj)
    obj.location = location
    if obj.name not in [o.name for o in collection.objects]:
        collection.objects.link(obj)
    return obj


def mesh_from_bmesh(name: str, bm: bmesh.types.BMesh) -> bpy.types.Mesh:
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    mesh.update()
    bm.free()
    return mesh


def ensure_mesh_object(name: str, mesh: bpy.types.Mesh, collection: bpy.types.Collection) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
    else:
        old_mesh = obj.data if obj.type == "MESH" else None
        obj.data = mesh
        if old_mesh is not None and old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    if obj.name not in [o.name for o in collection.objects]:
        collection.objects.link(obj)
    return obj


def parent_keep_world(obj: bpy.types.Object, parent: bpy.types.Object | None) -> None:
    if parent is None:
        return
    current_world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = current_world


def set_metadata(obj: bpy.types.Object, rcgen_id: str, side: str, module: str, params: dict) -> None:
    obj["rcgen_id"] = rcgen_id
    obj["rcgen_side"] = side
    obj["rcgen_module"] = module
    obj["rcgen_params"] = json.dumps(params, sort_keys=True)


def parse_metadata_params(obj: bpy.types.Object) -> dict:
    raw = obj.get("rcgen_params", "{}")
    try:
        return json.loads(raw)
    except Exception:
        return {}


def world_bbox_bounds(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_v = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    max_v = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return min_v, max_v


def bbox_intersects(a: bpy.types.Object, b: bpy.types.Object) -> bool:
    a_min, a_max = world_bbox_bounds(a)
    b_min, b_max = world_bbox_bounds(b)
    return (
        a_min.x <= b_max.x
        and a_max.x >= b_min.x
        and a_min.y <= b_max.y
        and a_max.y >= b_min.y
        and a_min.z <= b_max.z
        and a_max.z >= b_min.z
    )


def point_inside_bbox_world(obj: bpy.types.Object, point: Vector) -> bool:
    min_v, max_v = world_bbox_bounds(obj)
    return min_v.x <= point.x <= max_v.x and min_v.y <= point.y <= max_v.y and min_v.z <= point.z <= max_v.z


def chassis_axes(chassis_obj: bpy.types.Object) -> tuple[Vector, Vector, Vector]:
    rot = chassis_obj.matrix_world.to_3x3()
    right = (rot @ Vector((1.0, 0.0, 0.0))).normalized()
    forward = (rot @ Vector((0.0, 1.0, 0.0))).normalized()
    up = (rot @ Vector((0.0, 0.0, 1.0))).normalized()
    return right, forward, up


def object_center(refs: bpy.types.PropertyGroup, side: str) -> Vector:
    hub = getattr(refs, f"hub_{side.lower()}_obj", None)
    wheel = getattr(refs, f"wheel_{side.lower()}_obj", None)
    source = hub or wheel
    if source is None:
        return Vector((0.0, 0.0, 0.0))
    return source.matrix_world.translation.copy()


def tire_dimensions_local(tire_obj: bpy.types.Object, spin_axis: str) -> tuple[float, float]:
    idx_map = {"X": 0, "Y": 1, "Z": 2}
    axis_idx = idx_map.get(spin_axis, 1)
    bb = [Vector(corner) for corner in tire_obj.bound_box]
    min_v = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    max_v = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    local_dims = max_v - min_v
    scale = tire_obj.matrix_world.to_scale()
    dims = Vector((abs(local_dims.x * scale.x), abs(local_dims.y * scale.y), abs(local_dims.z * scale.z)))
    width = dims[axis_idx]
    dia_axes = [0, 1, 2]
    dia_axes.remove(axis_idx)
    diameter = max(dims[dia_axes[0]], dims[dia_axes[1]])
    return diameter, width


def list_generated_mesh_objects(scene: bpy.types.Scene, rcgen_id: str | None = None) -> list[bpy.types.Object]:
    objs = []
    for obj in scene.objects:
        if obj.type != "MESH":
            continue
        if "rcgen_id" not in obj:
            continue
        if rcgen_id and obj.get("rcgen_id") != rcgen_id:
            continue
        objs.append(obj)
    return objs


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path
