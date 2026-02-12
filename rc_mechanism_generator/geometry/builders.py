from __future__ import annotations

import bmesh
from mathutils import Vector

from .primitives import add_box_between, add_cylinder_between, add_helix_spring, add_sphere
from ..utils.blender_utils import mesh_from_bmesh
from ..utils.math_utils import midpoint


def build_wishbone_mesh(
    name: str,
    in_front: Vector,
    in_rear: Vector,
    out_point: Vector,
    rod_radius: float,
    bushing_radius: float,
    segments: int,
    add_rib: bool,
    section: str = "ROUND",
) -> object:
    bm = bmesh.new()
    if section == "RECT":
        add_box_between(bm, in_front, out_point, rod_radius * 2.0, rod_radius * 1.4)
        add_box_between(bm, in_rear, out_point, rod_radius * 2.0, rod_radius * 1.4)
        add_box_between(bm, in_front, in_rear, rod_radius * 1.8, rod_radius * 1.2)
    elif section == "OVAL":
        add_cylinder_between(bm, in_front, out_point, rod_radius * 1.1, segments)
        add_cylinder_between(bm, in_rear, out_point, rod_radius * 1.1, segments)
        add_cylinder_between(bm, in_front, in_rear, rod_radius, segments)
    else:
        add_cylinder_between(bm, in_front, out_point, rod_radius, segments)
        add_cylinder_between(bm, in_rear, out_point, rod_radius, segments)
        add_cylinder_between(bm, in_front, in_rear, rod_radius * 0.9, segments)
    if add_rib:
        in_mid = midpoint(in_front, in_rear)
        brace_mid = midpoint(in_mid, out_point)
        add_cylinder_between(bm, in_mid, brace_mid, rod_radius * 0.7, segments)
        add_cylinder_between(bm, brace_mid, out_point, rod_radius * 0.7, segments)
    add_sphere(bm, in_front, bushing_radius, segments)
    add_sphere(bm, in_rear, bushing_radius, segments)
    add_sphere(bm, out_point, bushing_radius, segments)
    return mesh_from_bmesh(name, bm)


def build_link_mesh(
    name: str,
    start: Vector,
    end: Vector,
    rod_radius: float,
    terminal_radius: float,
    segments: int,
) -> object:
    bm = bmesh.new()
    add_cylinder_between(bm, start, end, rod_radius, segments)
    add_sphere(bm, start, terminal_radius, segments)
    add_sphere(bm, end, terminal_radius, segments)
    return mesh_from_bmesh(name, bm)


def build_knuckle_mesh(
    name: str,
    center: Vector,
    lca_out: Vector,
    uca_out: Vector,
    steering_point: Vector,
    core_radius: float,
    arm_radius: float,
    segments: int,
) -> object:
    bm = bmesh.new()
    add_sphere(bm, center, core_radius, segments)
    add_cylinder_between(bm, center, lca_out, arm_radius, segments)
    add_cylinder_between(bm, center, uca_out, arm_radius, segments)
    add_cylinder_between(bm, center, steering_point, arm_radius * 0.9, segments)
    add_sphere(bm, lca_out, arm_radius * 1.1, segments)
    add_sphere(bm, uca_out, arm_radius * 1.1, segments)
    add_sphere(bm, steering_point, arm_radius * 1.1, segments)
    return mesh_from_bmesh(name, bm)


def build_servo_horn_mesh(
    name: str,
    origin: Vector,
    tip: Vector,
    axis_dir: Vector,
    hub_radius: float,
    arm_radius: float,
    thickness: float,
    segments: int,
) -> object:
    bm = bmesh.new()
    hub_top = origin + axis_dir.normalized() * (thickness * 0.5)
    hub_bottom = origin - axis_dir.normalized() * (thickness * 0.5)
    add_cylinder_between(bm, hub_bottom, hub_top, hub_radius, segments)
    add_cylinder_between(bm, origin, tip, arm_radius, segments)
    add_sphere(bm, tip, arm_radius * 1.3, segments)
    return mesh_from_bmesh(name, bm)


def build_servo_horn_dual_mesh(
    name: str,
    origin: Vector,
    tip_left: Vector,
    tip_right: Vector,
    axis_dir: Vector,
    hub_radius: float,
    arm_radius: float,
    thickness: float,
    segments: int,
) -> object:
    bm = bmesh.new()
    hub_top = origin + axis_dir.normalized() * (thickness * 0.5)
    hub_bottom = origin - axis_dir.normalized() * (thickness * 0.5)
    add_cylinder_between(bm, hub_bottom, hub_top, hub_radius, segments)
    add_cylinder_between(bm, tip_left, tip_right, arm_radius, segments)
    add_sphere(bm, tip_left, arm_radius * 1.3, segments)
    add_sphere(bm, tip_right, arm_radius * 1.3, segments)
    return mesh_from_bmesh(name, bm)


def build_shock_body_mesh(
    name: str,
    body_start: Vector,
    body_end: Vector,
    body_radius: float,
    eye_radius: float,
    segments: int,
) -> object:
    bm = bmesh.new()
    add_cylinder_between(bm, body_start, body_end, body_radius, segments)
    add_sphere(bm, body_start, eye_radius, segments)
    add_sphere(bm, body_end, eye_radius, segments)
    return mesh_from_bmesh(name, bm)


def build_shock_rod_mesh(
    name: str,
    rod_start: Vector,
    rod_end: Vector,
    rod_radius: float,
    eye_radius: float,
    segments: int,
) -> object:
    bm = bmesh.new()
    add_cylinder_between(bm, rod_start, rod_end, rod_radius, segments)
    add_sphere(bm, rod_start, eye_radius, segments)
    add_sphere(bm, rod_end, eye_radius, segments)
    return mesh_from_bmesh(name, bm)


def build_spring_mesh(
    name: str,
    start: Vector,
    end: Vector,
    outer_diameter: float,
    wire_diameter: float,
    turns: float,
    radial_segments: int,
) -> object:
    bm = bmesh.new()
    coil_radius = max((outer_diameter * 0.5) - (wire_diameter * 0.5), wire_diameter)
    add_helix_spring(
        bm,
        start,
        end,
        coil_radius=coil_radius,
        wire_radius=wire_diameter * 0.5,
        turns=turns,
        radial_segments=max(6, radial_segments),
    )
    return mesh_from_bmesh(name, bm)
