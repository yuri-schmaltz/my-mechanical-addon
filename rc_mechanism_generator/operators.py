from __future__ import annotations

import csv
import json
import math
import os
from datetime import datetime

import bmesh
import bpy
from bpy.props import StringProperty
from mathutils import Matrix, Vector

from .dfm import interface_specs, run_printability_checks
from .geometry import (
    build_knuckle_mesh,
    build_link_mesh,
    build_servo_horn_dual_mesh,
    build_shock_body_mesh,
    build_shock_rod_mesh,
    build_spring_mesh,
    build_wishbone_mesh,
)
from .utils import (
    bbox_intersects,
    chassis_axes,
    delete_object_if_exists,
    ensure_collection_path,
    ensure_dir,
    ensure_empty,
    ensure_mesh_object,
    list_generated_mesh_objects,
    missing_required_hardpoints,
    missing_required_references,
    mm_to_m,
    object_center,
    parent_keep_world,
    parse_metadata_params,
    point_inside_bbox_world,
    set_metadata,
    tire_dimensions_local,
    validate_scene_for_shocks,
    validate_scene_for_steering,
    validate_scene_for_suspension,
)
from .utils.constants import SIDES
from .utils.math_utils import axis_vector_from_enum, lerp, midpoint, side_sign

_AUTO_REF_NAME_MAP = {
    "chassis_obj": ("chassis",),
    "wheel_l_obj": ("wheel_l", "wheel.l", "wheel-l"),
    "wheel_r_obj": ("wheel_r", "wheel.r", "wheel-r"),
    "servo_obj": ("servo",),
    "tire_l_obj": ("tire_l", "tire.l", "tire-l"),
    "tire_r_obj": ("tire_r", "tire.r", "tire-r"),
    "wheelwell_l_obj": ("wheelwell_l", "wheelwell.l", "wheelwell-l"),
    "wheelwell_r_obj": ("wheelwell_r", "wheelwell.r", "wheelwell-r"),
    "hub_l_obj": ("hub_l", "hub.l", "hub-l"),
    "hub_r_obj": ("hub_r", "hub.r", "hub-r"),
    "upright_l_obj": ("upright_l", "upright.l", "upright-l"),
    "upright_r_obj": ("upright_r", "upright.r", "upright-r"),
    "servo_horn_obj": ("servohorn", "servo_horn", "servo-horn"),
    "rear_axle_center": ("rear_axle_center", "rearaxlecenter"),
}

_AUTO_HP_NAME_MAP = {
    "lca_in_front_l": ("lca_in_front_l", "lcainfrontl"),
    "lca_in_rear_l": ("lca_in_rear_l", "lcainrearl"),
    "lca_out_l": ("lca_out_l", "lcaoutl"),
    "uca_in_front_l": ("uca_in_front_l", "ucainfrontl"),
    "uca_in_rear_l": ("uca_in_rear_l", "ucainrearl"),
    "uca_out_l": ("uca_out_l", "ucaoutl"),
    "steering_arm_point_l": ("steeringarm_point_l", "steeringarmpointl"),
    "lca_in_front_r": ("lca_in_front_r", "lcainfrontr"),
    "lca_in_rear_r": ("lca_in_rear_r", "lcainrearr"),
    "lca_out_r": ("lca_out_r", "lcaoutr"),
    "uca_in_front_r": ("uca_in_front_r", "ucainfrontr"),
    "uca_in_rear_r": ("uca_in_rear_r", "ucainrearr"),
    "uca_out_r": ("uca_out_r", "ucaoutr"),
    "steering_arm_point_r": ("steeringarm_point_r", "steeringarmpointr"),
    "shock_top_l": ("shocktop_l", "shock_top_l"),
    "shock_bottom_l": ("shockbottom_l", "shock_bottom_l"),
    "shock_top_r": ("shocktop_r", "shock_top_r"),
    "shock_bottom_r": ("shockbottom_r", "shock_bottom_r"),
}


def _loc(obj: bpy.types.Object | None) -> Vector | None:
    if obj is None:
        return None
    return obj.matrix_world.translation.copy()


def _hp_loc(refs: bpy.types.PropertyGroup, key: str, side: str) -> Vector | None:
    obj = getattr(refs, f"{key}_{side.lower()}", None)
    return _loc(obj)


def _ensure_collections(scene: bpy.types.Scene) -> dict[str, bpy.types.Collection]:
    return {
        "root": ensure_collection_path(scene, ("RC_GEN",)),
        "front": ensure_collection_path(scene, ("RC_GEN", "FrontAxle")),
        "steering": ensure_collection_path(scene, ("RC_GEN", "Steering")),
        "shocks": ensure_collection_path(scene, ("RC_GEN", "Shocks")),
        "debug": ensure_collection_path(scene, ("RC_GEN", "Debug")),
    }


def _warn_report(operator: bpy.types.Operator, warnings: list[str]) -> None:
    for item in warnings:
        operator.report({"WARNING"}, item)


def _get_rear_axle_reference(scene: bpy.types.Scene) -> Vector:
    refs = scene.rcgen_refs
    settings = scene.rcgen_settings
    _, forward, _ = chassis_axes(refs.chassis_obj)
    front_center = midpoint(object_center(refs, "L"), object_center(refs, "R"))
    if settings.ackermann_mode == "AUTO" and refs.rear_axle_center is not None:
        return refs.rear_axle_center.matrix_world.translation.copy()
    return front_center - forward * mm_to_m(settings.wheelbase_mm)


def _select_only(context: bpy.types.Context, obj: bpy.types.Object) -> tuple[list[bpy.types.Object], bpy.types.Object | None]:
    prev_selected = list(context.selected_objects)
    prev_active = context.view_layer.objects.active
    for item in prev_selected:
        item.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
    return prev_selected, prev_active


def _restore_selection(context: bpy.types.Context, selected: list[bpy.types.Object], active: bpy.types.Object | None) -> None:
    for obj in context.selected_objects:
        obj.select_set(False)
    for obj in selected:
        if obj.name in bpy.data.objects:
            obj.select_set(True)
    if active is not None and active.name in bpy.data.objects:
        context.view_layer.objects.active = active


def _norm_name(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum() or ch == "_")


def _resolve_capture_collections(context: bpy.types.Context, scope: str) -> set[bpy.types.Collection] | None:
    if scope == "ALL":
        return None
    if scope == "SELECTED":
        selected_cols: set[bpy.types.Collection] = set()
        for obj in context.selected_objects:
            for col in obj.users_collection:
                selected_cols.add(col)
        return selected_cols if selected_cols else None
    if context.view_layer.active_layer_collection is not None:
        return {context.view_layer.active_layer_collection.collection}
    return None


def _find_object_by_candidates(
    scene: bpy.types.Scene,
    candidates: tuple[str, ...],
    require_empty: bool = False,
    prefix: str = "",
    collections: set[bpy.types.Collection] | None = None,
) -> bpy.types.Object | None:
    prefix_norm = _norm_name(prefix)
    candidate_set = {_norm_name(item) for item in candidates}
    if prefix_norm:
        candidate_set.update({f"{prefix_norm}{item}" for item in list(candidate_set)})
    for obj in scene.objects:
        if collections is not None:
            if not any(col in collections for col in obj.users_collection):
                continue
        name = _norm_name(obj.name)
        starts_like = any(name.startswith(f"{item}_") for item in candidate_set)
        if (name in candidate_set or starts_like) and (not require_empty or obj.type == "EMPTY"):
            return obj
    return None


def _autofill_refs_and_hardpoints(
    scene: bpy.types.Scene,
    prefix: str = "",
    collections: set[bpy.types.Collection] | None = None,
) -> tuple[int, list[str]]:
    refs = scene.rcgen_refs
    assigned = 0
    missing: list[str] = []

    for attr, candidates in _AUTO_REF_NAME_MAP.items():
        current = getattr(refs, attr, None)
        if current is not None:
            continue
        found = _find_object_by_candidates(
            scene,
            candidates,
            require_empty=(attr == "rear_axle_center"),
            prefix=prefix,
            collections=collections,
        )
        if found is not None:
            setattr(refs, attr, found)
            assigned += 1
        else:
            missing.append(attr)

    for attr, candidates in _AUTO_HP_NAME_MAP.items():
        current = getattr(refs, attr, None)
        if current is not None:
            continue
        found = _find_object_by_candidates(
            scene,
            candidates,
            require_empty=True,
            prefix=prefix,
            collections=collections,
        )
        if found is not None:
            setattr(refs, attr, found)
            assigned += 1
        else:
            if not attr.startswith("shock_"):
                missing.append(attr)

    return assigned, missing


def infer_shock_mounts(scene: bpy.types.Scene, force_rebuild: bool = False) -> tuple[dict[str, tuple[Vector, Vector]], list[str]]:
    refs = scene.rcgen_refs
    settings = scene.rcgen_settings
    collections = _ensure_collections(scene)
    right, forward, up = chassis_axes(refs.chassis_obj)
    warnings: list[str] = []
    result: dict[str, tuple[Vector, Vector]] = {}

    for side in SIDES:
        lca_in_front = _hp_loc(refs, "lca_in_front", side)
        lca_in_rear = _hp_loc(refs, "lca_in_rear", side)
        lca_out = _hp_loc(refs, "lca_out", side)
        if not all((lca_in_front, lca_in_rear, lca_out)):
            continue

        in_mid = midpoint(lca_in_front, lca_in_rear)
        bottom = lerp(lca_out, in_mid, settings.bottom_mount_ratio)
        inboard = right * (-side_sign(side))
        bottom += inboard * mm_to_m(settings.bottom_inboard_offset_mm)
        bottom += up * mm_to_m(settings.bottom_vertical_offset_mm)
        bottom += forward * mm_to_m(settings.bottom_fore_aft_offset_mm)

        wheel_center = object_center(refs, side)
        tire_obj = getattr(refs, f"tire_{side.lower()}_obj", None)
        if tire_obj is not None:
            tire_diameter_m, _ = tire_dimensions_local(tire_obj, settings.wheel_spin_axis)
        else:
            tire_diameter_m = mm_to_m(settings.tire_diameter_mm_manual)

        top_height_mm = settings.top_height_from_wheel_center_mm
        if top_height_mm <= 0.0:
            top_height_mm = (tire_diameter_m * 1000.0) * 0.35

        top = wheel_center
        top += up * mm_to_m(top_height_mm)
        top += forward * mm_to_m(settings.top_fore_aft_offset_mm)
        top += inboard * mm_to_m(settings.top_inboard_offset_mm)

        wheelwell = getattr(refs, f"wheelwell_{side.lower()}_obj", None)
        if wheelwell is not None:
            iter_limit = 20
            step = mm_to_m(2.0)
            outboard = right * side_sign(side)
            while point_inside_bbox_world(wheelwell, top) and iter_limit > 0:
                top += outboard * step
                iter_limit -= 1
            if iter_limit == 0:
                warnings.append(f"RC_ShockTop_{side}: wheel well escape did not converge (bbox).")

        top_name = f"RC_ShockTop_{side}"
        bottom_name = f"RC_ShockBottom_{side}"
        if force_rebuild:
            delete_object_if_exists(top_name)
            delete_object_if_exists(bottom_name)

        top_empty = ensure_empty(scene, top_name, top, collections["debug"], size=mm_to_m(10.0))
        bottom_empty = ensure_empty(scene, bottom_name, bottom, collections["debug"], size=mm_to_m(10.0))
        set_metadata(top_empty, settings.rcgen_id, side, "shock", {"kind": "SHOCK_TOP_INFERRED"})
        set_metadata(bottom_empty, settings.rcgen_id, side, "shock", {"kind": "SHOCK_BOTTOM_INFERRED"})
        result[side] = (top, bottom)

    return result, warnings


def _effective_shock_mounts(scene: bpy.types.Scene, inferred: dict[str, tuple[Vector, Vector]]) -> tuple[dict[str, tuple[Vector, Vector]], list[str]]:
    refs = scene.rcgen_refs
    settings = scene.rcgen_settings
    warnings = []
    result: dict[str, tuple[Vector, Vector]] = {}
    for side in SIDES:
        manual_top = getattr(refs, f"shock_top_{side.lower()}", None)
        manual_bottom = getattr(refs, f"shock_bottom_{side.lower()}", None)
        if settings.use_manual_shock_mounts and manual_top and manual_bottom:
            result[side] = (
                manual_top.matrix_world.translation.copy(),
                manual_bottom.matrix_world.translation.copy(),
            )
        else:
            if settings.use_manual_shock_mounts and (manual_top is None or manual_bottom is None):
                warnings.append(f"Manual shock mounts incomplete on {side}; using inferred mounts.")
            if side in inferred:
                result[side] = inferred[side]
    return result, warnings


def _write_obj(name: str, mesh: bpy.types.Mesh, collection: bpy.types.Collection, parent: bpy.types.Object | None, rcgen_id: str, side: str, module: str, params: dict) -> bpy.types.Object:
    obj = ensure_mesh_object(name, mesh, collection)
    obj.matrix_world = Matrix.Identity(4)
    if parent is not None:
        parent_keep_world(obj, parent)
    set_metadata(obj, rcgen_id=rcgen_id, side=side, module=module, params=params)
    return obj

def _generate_suspension(scene: bpy.types.Scene, operator: bpy.types.Operator) -> bool:
    ok, errors = validate_scene_for_suspension(scene)
    if not ok:
        for err in errors:
            operator.report({"ERROR"}, err)
        return False

    refs = scene.rcgen_refs
    settings = scene.rcgen_settings
    tol = scene.rcgen_tolerances
    cols = _ensure_collections(scene)

    iface = interface_specs(settings, tol)
    rod_radius = max(mm_to_m(settings.arm_rod_diameter_mm) * 0.5, mm_to_m(settings.min_wall_mm) * 0.5)
    bushing_radius = mm_to_m(settings.arm_bushing_diameter_mm) * 0.5 + iface["sliding_clearance_m"]

    warnings = []
    for side in SIDES:
        lca_mesh = build_wishbone_mesh(
            f"RC_LCA_{side}_MESH",
            _hp_loc(refs, "lca_in_front", side),
            _hp_loc(refs, "lca_in_rear", side),
            _hp_loc(refs, "lca_out", side),
            rod_radius=rod_radius,
            bushing_radius=bushing_radius,
            segments=settings.segments,
            add_rib=settings.add_ribs,
            section=settings.arm_section,
        )
        lca_obj = _write_obj(
            f"RC_LCA_{side}",
            lca_mesh,
            cols["front"],
            refs.chassis_obj,
            settings.rcgen_id,
            side,
            "suspension",
            {
                "kind": "LCA",
                "hardware": settings.default_hardware,
                "hole_dia_mm": round(iface["hole_m"] * 1000.0, 3),
                "arm_section": settings.arm_section,
            },
        )

        uca_mesh = build_wishbone_mesh(
            f"RC_UCA_{side}_MESH",
            _hp_loc(refs, "uca_in_front", side),
            _hp_loc(refs, "uca_in_rear", side),
            _hp_loc(refs, "uca_out", side),
            rod_radius=rod_radius * 0.9,
            bushing_radius=bushing_radius * 0.9,
            segments=settings.segments,
            add_rib=settings.add_ribs,
            section=settings.arm_section,
        )
        uca_obj = _write_obj(
            f"RC_UCA_{side}",
            uca_mesh,
            cols["front"],
            refs.chassis_obj,
            settings.rcgen_id,
            side,
            "suspension",
            {
                "kind": "UCA",
                "hardware": settings.default_hardware,
                "hole_dia_mm": round(iface["hole_m"] * 1000.0, 3),
                "arm_section": settings.arm_section,
            },
        )

        upright = getattr(refs, f"upright_{side.lower()}_obj", None)
        knuckle_obj = None
        if upright is None and settings.generate_knuckle_when_missing:
            center = object_center(refs, side)
            knuckle_mesh = build_knuckle_mesh(
                f"RC_KNUCKLE_{side}_MESH",
                center=center,
                lca_out=_hp_loc(refs, "lca_out", side),
                uca_out=_hp_loc(refs, "uca_out", side),
                steering_point=_hp_loc(refs, "steering_arm_point", side),
                core_radius=mm_to_m(7.0),
                arm_radius=mm_to_m(3.0),
                segments=settings.segments,
            )
            knuckle_obj = _write_obj(
                f"RC_Knuckle_{side}",
                knuckle_mesh,
                cols["front"],
                refs.chassis_obj,
                settings.rcgen_id,
                side,
                "suspension",
                {"kind": "KNUCKLE", "hardware": settings.default_hardware},
            )

        wheelwell = getattr(refs, f"wheelwell_{side.lower()}_obj", None)
        if wheelwell is not None:
            if bbox_intersects(lca_obj, wheelwell):
                warnings.append(f"{side}: LCA intersects WheelWell (bbox).")
            if bbox_intersects(uca_obj, wheelwell):
                warnings.append(f"{side}: UCA intersects WheelWell (bbox).")
            if knuckle_obj is not None and bbox_intersects(knuckle_obj, wheelwell):
                warnings.append(f"{side}: Knuckle intersects WheelWell (bbox).")

    _warn_report(operator, warnings)
    operator.report({"INFO"}, "Suspension generated/updated.")
    return True


def _generate_steering(scene: bpy.types.Scene, operator: bpy.types.Operator) -> bool:
    ok, errors = validate_scene_for_steering(scene)
    if not ok:
        for err in errors:
            operator.report({"ERROR"}, err)
        return False

    refs = scene.rcgen_refs
    settings = scene.rcgen_settings
    tol = scene.rcgen_tolerances
    cols = _ensure_collections(scene)

    right, _, _ = chassis_axes(refs.chassis_obj)
    half_horn = mm_to_m(settings.servo_horn_length_mm) * 0.5
    horn_center = refs.servo_obj.matrix_world.translation.copy()
    horn_left = horn_center - right * half_horn
    horn_right = horn_center + right * half_horn
    servo_axis = (refs.servo_obj.matrix_world.to_3x3() @ axis_vector_from_enum(settings.servo_axis)).normalized()

    iface = interface_specs(settings, tol)

    if refs.servo_horn_obj is None:
        horn_mesh = build_servo_horn_dual_mesh(
            "RC_SERVO_HORN_MESH",
            origin=horn_center,
            tip_left=horn_left,
            tip_right=horn_right,
            axis_dir=servo_axis,
            hub_radius=mm_to_m(settings.servo_horn_diameter_mm) * 0.5,
            arm_radius=mm_to_m(settings.tie_rod_diameter_mm) * 0.6,
            thickness=mm_to_m(5.0),
            segments=settings.segments,
        )
        _write_obj(
            "RC_ServoHorn",
            horn_mesh,
            cols["steering"],
            refs.servo_obj,
            settings.rcgen_id,
            "C",
            "steering",
            {
                "kind": "SERVO_HORN",
                "length_mm": settings.servo_horn_length_mm,
                "hardware": settings.default_hardware,
                "hole_dia_mm": round(iface["hole_m"] * 1000.0, 3),
            },
        )
    else:
        delete_object_if_exists("RC_ServoHorn")

    rear_ref = _get_rear_axle_reference(scene)
    warnings = []

    for side in SIDES:
        steering_target = _hp_loc(refs, "steering_arm_point", side)
        start = horn_left if side == "L" else horn_right
        dist = (steering_target - start).length
        min_len = mm_to_m(settings.steering_min_length_mm)
        terminal_radius = mm_to_m(settings.tie_rod_terminal_diameter_mm) * 0.5 + iface["sliding_clearance_m"]

        if dist < max(min_len, terminal_radius * 2.0):
            operator.report({"ERROR"}, f"Tie rod {side} impossible: insufficient length.")
            return False

        mesh = build_link_mesh(
            f"RC_TIEROD_{side}_MESH",
            start=start,
            end=steering_target,
            rod_radius=mm_to_m(settings.tie_rod_diameter_mm) * 0.5,
            terminal_radius=terminal_radius,
            segments=settings.segments,
        )
        tie_obj = _write_obj(
            f"RC_TieRod_{side}",
            mesh,
            cols["steering"],
            refs.chassis_obj,
            settings.rcgen_id,
            side,
            "steering",
            {
                "kind": "TIE_ROD",
                "hardware": settings.default_hardware,
                "hole_dia_mm": round(iface["hole_m"] * 1000.0, 3),
            },
        )

        wheelwell = getattr(refs, f"wheelwell_{side.lower()}_obj", None)
        if wheelwell is not None and bbox_intersects(tie_obj, wheelwell):
            warnings.append(f"{side}: Tie rod intersects WheelWell (bbox).")

        wheel_center = object_center(refs, side)
        steer_vec = steering_target - wheel_center
        steer_vec.z = 0.0
        front_vec = refs.chassis_obj.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0))
        front_vec.z = 0.0

        if steer_vec.length > 1.0e-8 and front_vec.length > 1.0e-8:
            angle = math.degrees(steer_vec.normalized().angle(front_vec.normalized()))
            if angle > settings.max_steer_angle_deg:
                warnings.append(f"{side}: estimated steering angle {angle:.1f} deg exceeds {settings.max_steer_angle_deg:.1f} deg.")

        ack_target = rear_ref - wheel_center
        if ack_target.length > 1.0e-8 and steer_vec.length > 1.0e-8:
            ack_delta = math.degrees(steer_vec.normalized().angle(ack_target.normalized()))
            if ack_delta > 25.0:
                warnings.append(f"{side}: Ackermann discrepancy {ack_delta:.1f} deg (hardpoint kept fixed).")

    _warn_report(operator, warnings)
    operator.report({"INFO"}, "Steering generated/updated.")
    return True

def _generate_shocks(scene: bpy.types.Scene, operator: bpy.types.Operator) -> bool:
    ok, errors, base_warnings = validate_scene_for_shocks(scene)
    if not ok:
        for err in errors:
            operator.report({"ERROR"}, err)
        return False

    _warn_report(operator, base_warnings)
    refs = scene.rcgen_refs
    settings = scene.rcgen_settings
    tol = scene.rcgen_tolerances
    cols = _ensure_collections(scene)

    iface = interface_specs(settings, tol)
    inferred, infer_warnings = infer_shock_mounts(scene, force_rebuild=False)
    _warn_report(operator, infer_warnings)
    mounts, mount_warnings = _effective_shock_mounts(scene, inferred)
    _warn_report(operator, mount_warnings)

    total_length = mm_to_m(settings.shock_total_length_mm)
    stroke = mm_to_m(settings.shock_stroke_mm)
    if stroke > total_length:
        operator.report({"ERROR"}, "Shock stroke larger than total length.")
        return False

    warnings = []
    for side in SIDES:
        if side not in mounts:
            operator.report({"ERROR"}, f"Shock mounts missing for side {side}.")
            return False

        top, bottom = mounts[side]
        axis = top - bottom
        mount_dist = axis.length
        if mount_dist <= 1.0e-8:
            operator.report({"ERROR"}, f"Shock mounts coincide on side {side}.")
            return False

        axis.normalize()
        body_len = max(mount_dist - stroke, mount_dist * 0.55)
        body_start = top
        body_end = top - axis * body_len
        rod_start = bottom
        rod_end = body_end

        body_mesh = build_shock_body_mesh(
            f"RC_SHOCK_BODY_{side}_MESH",
            body_start=body_start,
            body_end=body_end,
            body_radius=mm_to_m(settings.shock_body_diameter_mm) * 0.5,
            eye_radius=mm_to_m(settings.shock_eyelet_diameter_mm) * 0.5,
            segments=settings.segments,
        )
        body_obj = _write_obj(
            f"RC_ShockBody_{side}",
            body_mesh,
            cols["shocks"],
            refs.chassis_obj,
            settings.rcgen_id,
            side,
            "shock",
            {
                "kind": "SHOCK_BODY",
                "hardware": settings.default_hardware,
                "hole_dia_mm": round(iface["hole_m"] * 1000.0, 3),
            },
        )

        rod_mesh = build_shock_rod_mesh(
            f"RC_SHOCK_ROD_{side}_MESH",
            rod_start=rod_start,
            rod_end=rod_end,
            rod_radius=mm_to_m(settings.shock_rod_diameter_mm) * 0.5,
            eye_radius=mm_to_m(settings.shock_eyelet_diameter_mm) * 0.45,
            segments=settings.segments,
        )
        rod_obj = _write_obj(
            f"RC_ShockRod_{side}",
            rod_mesh,
            cols["shocks"],
            refs.chassis_obj,
            settings.rcgen_id,
            side,
            "shock",
            {
                "kind": "SHOCK_ROD",
                "hardware": settings.default_hardware,
                "stroke_mm": settings.shock_stroke_mm,
            },
        )

        spring_obj = None
        if settings.generate_spring:
            spring_start = top - axis * (body_len * 0.12)
            spring_end = bottom + axis * (mount_dist * 0.12)
            spring_mesh = build_spring_mesh(
                f"RC_SPRING_{side}_MESH",
                start=spring_start,
                end=spring_end,
                outer_diameter=mm_to_m(settings.spring_outer_diameter_mm),
                wire_diameter=mm_to_m(settings.spring_wire_diameter_mm),
                turns=settings.spring_turns,
                radial_segments=settings.spring_resolution,
            )
            spring_obj = _write_obj(
                f"RC_Spring_{side}",
                spring_mesh,
                cols["shocks"],
                refs.chassis_obj,
                settings.rcgen_id,
                side,
                "shock",
                {"kind": "SPRING", "od_mm": settings.spring_outer_diameter_mm},
            )
        else:
            delete_object_if_exists(f"RC_Spring_{side}")

        if settings.spring_outer_diameter_mm <= settings.shock_body_diameter_mm:
            warnings.append(f"{side}: spring may collide with body (OD <= body dia).")

        wheelwell = getattr(refs, f"wheelwell_{side.lower()}_obj", None)
        if wheelwell is not None:
            if bbox_intersects(body_obj, wheelwell) or bbox_intersects(rod_obj, wheelwell):
                warnings.append(f"{side}: shock intersects WheelWell (bbox).")
            if spring_obj is not None and bbox_intersects(spring_obj, wheelwell):
                warnings.append(f"{side}: spring intersects WheelWell (bbox).")

    _warn_report(operator, warnings)
    operator.report({"INFO"}, "Shock/spring generated/updated.")
    return True


def _hardware_bom(objects: list[bpy.types.Object], default_hw: str) -> dict[str, int]:
    counts: dict[str, int] = {f"Screw_{default_hw}": 0, f"Nut_{default_hw}": 0, f"Insert_{default_hw}": 0}
    for obj in objects:
        module = obj.get("rcgen_module", "")
        params = parse_metadata_params(obj)
        kind = params.get("kind", "")
        if module == "suspension" and kind in {"LCA", "UCA"}:
            counts[f"Screw_{default_hw}"] += 3
            counts[f"Nut_{default_hw}"] += 3
        elif module == "steering" and kind == "TIE_ROD":
            counts[f"Screw_{default_hw}"] += 2
            counts[f"Nut_{default_hw}"] += 2
        elif module == "shock" and kind in {"SHOCK_BODY", "SHOCK_ROD"}:
            counts[f"Screw_{default_hw}"] += 1
            counts[f"Nut_{default_hw}"] += 1
            counts[f"Insert_{default_hw}"] += 1
    return counts


def _exceeds_print_volume(obj: bpy.types.Object, settings: bpy.types.PropertyGroup) -> bool:
    max_x = settings.print_volume_x_mm / 1000.0
    max_y = settings.print_volume_y_mm / 1000.0
    max_z = settings.print_volume_z_mm / 1000.0
    return obj.dimensions.x > max_x or obj.dimensions.y > max_y or obj.dimensions.z > max_z


def _local_axis_for_longest_dimension(obj: bpy.types.Object) -> tuple[Vector, int]:
    bb = [Vector(corner) for corner in obj.bound_box]
    min_v = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    max_v = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    local_dims = max_v - min_v
    scale = obj.matrix_world.to_scale()
    dims = (
        abs(local_dims.x * scale.x),
        abs(local_dims.y * scale.y),
        abs(local_dims.z * scale.z),
    )
    if dims[0] >= dims[1] and dims[0] >= dims[2]:
        return obj.matrix_world.to_3x3() @ Vector((1.0, 0.0, 0.0)), 0
    if dims[1] >= dims[2]:
        return obj.matrix_world.to_3x3() @ Vector((0.0, 1.0, 0.0)), 1
    return obj.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0)), 2


def _estimated_effort_axis(obj: bpy.types.Object, split_axis_index: int) -> Vector:
    bb = [Vector(corner) for corner in obj.bound_box]
    min_v = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    max_v = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    local_dims = max_v - min_v
    scale = obj.matrix_world.to_scale()
    dims = [
        abs(local_dims.x * scale.x),
        abs(local_dims.y * scale.y),
        abs(local_dims.z * scale.z),
    ]
    candidates = [0, 1, 2]
    if split_axis_index in candidates:
        candidates.remove(split_axis_index)
    best = max(candidates, key=lambda idx: dims[idx])
    local_axis = Vector((1.0, 0.0, 0.0)) if best == 0 else Vector((0.0, 1.0, 0.0)) if best == 1 else Vector((0.0, 0.0, 1.0))
    return (obj.matrix_world.to_3x3() @ local_axis).normalized()


def _split_orientation_bias_axis(scene: bpy.types.Scene, settings: bpy.types.PropertyGroup) -> Vector | None:
    if settings.split_orientation_bias == "AUTO":
        return None
    chassis = scene.rcgen_refs.chassis_obj
    if chassis is None:
        return None
    rot = chassis.matrix_world.to_3x3()
    if settings.split_orientation_bias == "CHASSIS_FORWARD":
        return (rot @ Vector((0.0, 1.0, 0.0))).normalized()
    if settings.split_orientation_bias == "CHASSIS_RIGHT":
        return (rot @ Vector((1.0, 0.0, 0.0))).normalized()
    return None


def _basis_matrix_from_axis(axis: Vector, align_ref: Vector | None) -> Matrix:
    z_axis = axis.normalized()
    ref = align_ref.copy() if align_ref is not None else Vector((1.0, 0.0, 0.0))
    ref_proj = ref - z_axis * ref.dot(z_axis)
    if ref_proj.length < 1.0e-8:
        fallback = Vector((0.0, 1.0, 0.0))
        ref_proj = fallback - z_axis * fallback.dot(z_axis)
    x_axis = ref_proj.normalized()
    y_axis = z_axis.cross(x_axis).normalized()
    x_axis = y_axis.cross(z_axis).normalized()
    return Matrix((x_axis, y_axis, z_axis)).transposed()


def _split_mesh_part(
    source_obj: bpy.types.Object,
    plane_co: Vector,
    plane_no: Vector,
    keep_positive: bool,
    mesh_name: str,
) -> bpy.types.Mesh:
    tmp_mesh = source_obj.data.copy()
    bm = bmesh.new()
    bm.from_mesh(tmp_mesh)
    bmesh.ops.bisect_plane(
        bm,
        geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
        plane_co=plane_co,
        plane_no=plane_no,
        clear_outer=not keep_positive,
        clear_inner=keep_positive,
        use_snap_center=False,
        dist=0.00001,
    )
    out_mesh = bpy.data.meshes.new(mesh_name)
    bm.to_mesh(out_mesh)
    bm.free()
    bpy.data.meshes.remove(tmp_mesh)
    out_mesh.update()
    return out_mesh


def _build_key_mesh(
    name: str,
    center: Vector,
    axis: Vector,
    radius: float,
    depth: float,
    segments: int,
    profile: str,
    align_ref: Vector | None = None,
) -> bpy.types.Mesh:
    bm = bmesh.new()
    if profile == "HEX":
        segs = 6
    else:
        segs = max(8, segments)
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segs,
        radius1=radius,
        radius2=radius,
        depth=depth,
    )
    if profile == "D":
        bmesh.ops.bisect_plane(
            bm,
            geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            plane_co=Vector((radius * 0.45, 0.0, 0.0)),
            plane_no=Vector((1.0, 0.0, 0.0)),
            clear_outer=True,
            clear_inner=False,
            use_snap_center=False,
            dist=0.000001,
        )

    matrix = _basis_matrix_from_axis(axis, align_ref).to_4x4()
    matrix.translation = center
    bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return mesh


def _apply_boolean_difference(
    context: bpy.types.Context,
    target_obj: bpy.types.Object,
    cutter_obj: bpy.types.Object,
) -> bool:
    modifier = target_obj.modifiers.new(name="RC_SPLIT_SOCKET", type="BOOLEAN")
    modifier.object = cutter_obj
    modifier.operation = "DIFFERENCE"
    if hasattr(modifier, "solver"):
        modifier.solver = "EXACT"
    try:
        with context.temp_override(
            object=target_obj,
            active_object=target_obj,
            selected_editable_objects=[target_obj],
        ):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        return True
    except Exception:
        if modifier.name in target_obj.modifiers:
            target_obj.modifiers.remove(modifier)
        return False


def _split_object_for_export(
    context: bpy.types.Context,
    scene: bpy.types.Scene,
    source_obj: bpy.types.Object,
    settings: bpy.types.PropertyGroup,
    tol: bpy.types.PropertyGroup,
    collection: bpy.types.Collection,
) -> tuple[list[bpy.types.Object], list[bpy.types.Object], list[str]]:
    warnings: list[str] = []
    plane_axis, split_axis_idx = _local_axis_for_longest_dimension(source_obj)
    plane_no = plane_axis.normalized()
    effort_axis = _estimated_effort_axis(source_obj, split_axis_idx)
    bias_axis = _split_orientation_bias_axis(scene, settings)
    if bias_axis is not None:
        bias_proj = bias_axis - plane_no * bias_axis.dot(plane_no)
        if bias_proj.length > 1.0e-8:
            # Blend geometric effort with chassis bias to keep deterministic anti-rotation orientation.
            effort_axis = (effort_axis + bias_proj.normalized() * 1.25).normalized()
    plane_co = source_obj.matrix_world.translation.copy()

    left_mesh = _split_mesh_part(source_obj, plane_co, plane_no, keep_positive=False, mesh_name=f"{source_obj.name}_PART_A_MESH")
    right_mesh = _split_mesh_part(source_obj, plane_co, plane_no, keep_positive=True, mesh_name=f"{source_obj.name}_PART_B_MESH")
    if len(left_mesh.vertices) == 0 or len(right_mesh.vertices) == 0:
        if len(left_mesh.vertices) == 0:
            bpy.data.meshes.remove(left_mesh)
        if len(right_mesh.vertices) == 0:
            bpy.data.meshes.remove(right_mesh)
        return [], [], warnings

    part_a = bpy.data.objects.new(f"{source_obj.name}_PART_A", left_mesh)
    part_b = bpy.data.objects.new(f"{source_obj.name}_PART_B", right_mesh)
    part_a.matrix_world = source_obj.matrix_world.copy()
    part_b.matrix_world = source_obj.matrix_world.copy()
    collection.objects.link(part_a)
    collection.objects.link(part_b)

    pin_objs: list[bpy.types.Object] = []
    cutter_objs: list[bpy.types.Object] = []
    key_radius = mm_to_m(settings.split_key_diameter_mm) * 0.5
    key_profile = settings.split_key_profile
    key_length = max(mm_to_m(8.0), min(source_obj.dimensions) * 0.25)
    clearance = mm_to_m(settings.split_clearance_mm + max(0.0, tol.clearance_sliding_mm))

    ref = Vector((0.0, 0.0, 1.0))
    if abs(plane_no.dot(ref)) > 0.95:
        ref = Vector((0.0, 1.0, 0.0))
    tangent_u = plane_no.cross(ref).normalized()
    tangent_v = plane_no.cross(tangent_u).normalized()
    offset = max(key_radius * 2.5, mm_to_m(5.0))
    pin_centers = (plane_co + tangent_u * offset, plane_co - tangent_u * offset)

    for idx, center in enumerate(pin_centers, start=1):
        pin_mesh = _build_key_mesh(
            f"{source_obj.name}_PIN_{idx}_MESH",
            center=center,
            axis=plane_no,
            radius=max(0.0002, key_radius - clearance * 0.5),
            depth=key_length,
            segments=max(8, settings.segments // 2),
            profile=key_profile,
            align_ref=effort_axis,
        )
        pin_obj = bpy.data.objects.new(f"{source_obj.name}_PIN_{idx}", pin_mesh)
        collection.objects.link(pin_obj)
        pin_objs.append(pin_obj)

        cutter_mesh = _build_key_mesh(
            f"{source_obj.name}_SOCKET_{idx}_MESH",
            center=center,
            axis=plane_no,
            radius=key_radius + clearance,
            depth=key_length,
            segments=max(8, settings.segments // 2),
            profile=key_profile,
            align_ref=effort_axis,
        )
        cutter_obj = bpy.data.objects.new(f"{source_obj.name}_SOCKET_{idx}", cutter_mesh)
        collection.objects.link(cutter_obj)
        cutter_objs.append(cutter_obj)

    for part in (part_a, part_b):
        for cutter in cutter_objs:
            ok = _apply_boolean_difference(context, part, cutter)
            if not ok:
                warnings.append(f"{part.name}: failed to apply split socket boolean.")

    for cutter in cutter_objs:
        mesh = cutter.data if cutter.type == "MESH" else None
        bpy.data.objects.remove(cutter, do_unlink=True)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    return [part_a, part_b], pin_objs, warnings


def _write_manufacturing_pack(context: bpy.types.Context, scene: bpy.types.Scene, operator: bpy.types.Operator) -> bool:
    settings = scene.rcgen_settings
    tol = scene.rcgen_tolerances

    out_dir = ensure_dir(bpy.path.abspath(settings.export_dir))
    set_dir = ensure_dir(os.path.join(out_dir, settings.rcgen_id))

    objects = list_generated_mesh_objects(scene, settings.rcgen_id)
    if not objects:
        operator.report({"ERROR"}, "No generated RC objects found for export.")
        return False

    errors, warnings, orientations = run_printability_checks(scene)
    _warn_report(operator, warnings)
    for err in errors:
        operator.report({"ERROR"}, err)
    if errors:
        return False

    temp_collection = ensure_collection_path(scene, ("RC_GEN", "ExportTemp"))
    temp_objects: list[bpy.types.Object] = []
    split_notes: list[str] = []
    export_targets: list[bpy.types.Object] = []
    split_pin_count = 0

    for obj in objects:
        if settings.auto_split_large_parts and _exceeds_print_volume(obj, settings):
            parts, pins, split_warnings = _split_object_for_export(context, scene, obj, settings, tol, temp_collection)
            _warn_report(operator, split_warnings)
            if parts:
                export_targets.extend(parts)
                export_targets.extend(pins)
                temp_objects.extend(parts)
                temp_objects.extend(pins)
                split_pin_count += len(pins)
                split_notes.append(
                    f"{obj.name}: split into {parts[0].name} and {parts[1].name} "
                    f"with {settings.split_key_profile} keys "
                    f"(bias={settings.split_orientation_bias})"
                )
                continue
            operator.report({"WARNING"}, f"{obj.name}: split failed, exporting original mesh.")
        export_targets.append(obj)

    exported: list[dict[str, str]] = []
    prev_selected = list(context.selected_objects)
    prev_active = context.view_layer.objects.active

    try:
        for obj in export_targets:
            before_sel, before_active = _select_only(context, obj)
            base_path = os.path.join(set_dir, obj.name)
            if settings.export_stl:
                stl_path = base_path + ".stl"
                bpy.ops.export_mesh.stl(filepath=stl_path, use_selection=True, check_existing=False, ascii=False)
                exported.append({"object": obj.name, "format": "STL", "path": stl_path})
            if settings.export_3mf:
                if hasattr(bpy.ops.export_mesh, "threemf"):
                    path_3mf = base_path + ".3mf"
                    bpy.ops.export_mesh.threemf(filepath=path_3mf, use_selection=True, check_existing=False)
                    exported.append({"object": obj.name, "format": "3MF", "path": path_3mf})
                else:
                    operator.report({"WARNING"}, "3MF exporter not available in this Blender build.")
            _restore_selection(context, before_sel, before_active)
    finally:
        _restore_selection(context, prev_selected, prev_active)

    bom_counts = _hardware_bom(objects, settings.default_hardware)
    bom_rows = []
    for name, qty in bom_counts.items():
        if qty > 0:
            bom_rows.append({"item": name, "qty": qty, "notes": "Estimated by generator topology"})

    bom_rows.extend(
        {
            "item": obj.name,
            "qty": 1,
            "notes": f"module={obj.get('rcgen_module', '')}, side={obj.get('rcgen_side', '')}",
        }
        for obj in objects
    )
    if split_pin_count > 0:
        bom_rows.append(
            {
                "item": f"Split_Alignment_Pin_{settings.split_key_profile}",
                "qty": split_pin_count,
                "notes": "Generated split alignment pins",
            }
        )

    bom_json_path = os.path.join(set_dir, "BOM.json")
    with open(bom_json_path, "w", encoding="utf-8") as fp:
        json.dump(
            {
                "rcgen_id": settings.rcgen_id,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "hardware_default": settings.default_hardware,
                "rows": bom_rows,
            },
            fp,
            indent=2,
        )

    bom_csv_path = os.path.join(set_dir, "BOM.csv")
    with open(bom_csv_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["item", "qty", "notes"])
        writer.writeheader()
        for row in bom_rows:
            writer.writerow(row)

    assembly_path = os.path.join(set_dir, "ASSEMBLY.md")
    with open(assembly_path, "w", encoding="utf-8") as fp:
        fp.write("# RC Mechanism Generator - Manufacturing Pack\n\n")
        fp.write(f"- Set: `{settings.rcgen_id}`\n")
        fp.write(f"- Generated: {datetime.utcnow().isoformat()}Z\n")
        fp.write("\n## Recommended Sequence\n")
        fp.write("1. Print suspension arms and knuckles.\n")
        fp.write("2. Assemble chassis pivots with specified hardware.\n")
        fp.write("3. Install steering horn and tie rods.\n")
        fp.write("4. Install shock body, rod and spring.\n")
        fp.write("5. Re-check free movement and wheel-well clearance.\n")
        fp.write("\n## Project Tolerances\n")
        fp.write(f"- clearance_sliding_mm: {tol.clearance_sliding_mm:.3f}\n")
        fp.write(f"- clearance_press_mm: {tol.clearance_press_mm:.3f}\n")
        fp.write(f"- hole_oversize_mm: {tol.hole_oversize_mm:.3f}\n")
        fp.write(f"- nut_trap_clearance_mm: {tol.nut_trap_clearance_mm:.3f}\n")
        fp.write(f"- insert_pocket_clearance_mm: {tol.insert_pocket_clearance_mm:.3f}\n")
        fp.write("\n## Print Orientation (suggested)\n")
        for obj in export_targets:
            ori = orientations.get(obj.name, {"rx_rad": 0.0, "ry_rad": 0.0, "rz_rad": 0.0})
            fp.write(
                f"- {obj.name}: rotate rx={math.degrees(ori['rx_rad']):.1f}deg, "
                f"ry={math.degrees(ori['ry_rad']):.1f}deg, rz={math.degrees(ori['rz_rad']):.1f}deg\n"
            )
        if split_notes:
            fp.write("\n## Auto Split Notes\n")
            for note in split_notes:
                fp.write(f"- {note}\n")

    manifest_path = os.path.join(set_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fp:
        json.dump(
            {
                "exports": exported,
                "bom_csv": bom_csv_path,
                "bom_json": bom_json_path,
                "assembly": assembly_path,
                "split_notes": split_notes,
            },
            fp,
            indent=2,
        )

    for tmp_obj in temp_objects:
        mesh = tmp_obj.data if tmp_obj.type == "MESH" else None
        bpy.data.objects.remove(tmp_obj, do_unlink=True)
        if mesh is not None and mesh.users == 0:
            bpy.data.meshes.remove(mesh)

    operator.report({"INFO"}, f"Manufacturing pack exported to: {set_dir}")
    return True


class RCGEN_OT_CaptureSelected(bpy.types.Operator):
    bl_idname = "rcgen.capture_selected"
    bl_label = "Capture Selected"
    bl_description = "Assign active object to target pointer"

    target_path: StringProperty()

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if obj is None:
            self.report({"ERROR"}, "No active object.")
            return {"CANCELLED"}
        if not self.target_path.startswith("refs."):
            self.report({"ERROR"}, "Invalid target path.")
            return {"CANCELLED"}
        attr = self.target_path.split(".", 1)[1]
        setattr(context.scene.rcgen_refs, attr, obj)
        self.report({"INFO"}, f"{attr} <- {obj.name}")
        return {"FINISHED"}


class RCGEN_OT_AutoCaptureByName(bpy.types.Operator):
    bl_idname = "rcgen.auto_capture_by_name"
    bl_label = "Auto Capture By Name"
    bl_description = "Fill references and hardpoints by common object names"

    def execute(self, context: bpy.types.Context):
        settings = context.scene.rcgen_settings
        collections = _resolve_capture_collections(context, settings.auto_capture_scope)
        assigned, missing = _autofill_refs_and_hardpoints(
            context.scene,
            prefix=settings.auto_capture_prefix,
            collections=collections,
        )
        if assigned == 0:
            self.report({"WARNING"}, "No references/hardpoints auto-captured.")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Auto-captured {assigned} entries.")
        if missing:
            self.report({"WARNING"}, f"Still missing: {', '.join(missing)}")
        return {"FINISHED"}


class RCGEN_OT_ValidateReferences(bpy.types.Operator):
    bl_idname = "rcgen.validate_references"
    bl_label = "Validate References"

    def execute(self, context: bpy.types.Context):
        missing = missing_required_references(context.scene)
        if not missing:
            self.report({"INFO"}, "Required references OK.")
            return {"FINISHED"}
        self.report({"ERROR"}, f"Missing references: {', '.join(missing)}")
        return {"CANCELLED"}


class RCGEN_OT_ValidateHardpoints(bpy.types.Operator):
    bl_idname = "rcgen.validate_hardpoints"
    bl_label = "Validate Hardpoints"

    def execute(self, context: bpy.types.Context):
        missing = missing_required_hardpoints(context.scene)
        if not missing:
            self.report({"INFO"}, "Required hardpoints OK.")
            return {"FINISHED"}
        self.report({"ERROR"}, f"Missing hardpoints: {', '.join(missing)}")
        return {"CANCELLED"}


class RCGEN_OT_ValidateAll(bpy.types.Operator):
    bl_idname = "rcgen.validate_all"
    bl_label = "Validate All"

    def execute(self, context: bpy.types.Context):
        ok, errors = validate_scene_for_suspension(context.scene)
        if ok:
            self.report({"INFO"}, "Validation OK.")
            return {"FINISHED"}
        for err in errors:
            self.report({"ERROR"}, err)
        return {"CANCELLED"}


class RCGEN_OT_GenerateSuspension(bpy.types.Operator):
    bl_idname = "rcgen.generate_suspension"
    bl_label = "Generate Suspension"

    def execute(self, context: bpy.types.Context):
        return {"FINISHED"} if _generate_suspension(context.scene, self) else {"CANCELLED"}


class RCGEN_OT_UpdateSuspension(bpy.types.Operator):
    bl_idname = "rcgen.update_suspension"
    bl_label = "Update Suspension"

    def execute(self, context: bpy.types.Context):
        return {"FINISHED"} if _generate_suspension(context.scene, self) else {"CANCELLED"}


class RCGEN_OT_GenerateSteering(bpy.types.Operator):
    bl_idname = "rcgen.generate_steering"
    bl_label = "Generate Steering"

    def execute(self, context: bpy.types.Context):
        return {"FINISHED"} if _generate_steering(context.scene, self) else {"CANCELLED"}


class RCGEN_OT_UpdateSteering(bpy.types.Operator):
    bl_idname = "rcgen.update_steering"
    bl_label = "Update Steering"

    def execute(self, context: bpy.types.Context):
        return {"FINISHED"} if _generate_steering(context.scene, self) else {"CANCELLED"}

class RCGEN_OT_ReinferShockMounts(bpy.types.Operator):
    bl_idname = "rcgen.reinfer_shock_mounts"
    bl_label = "Reinfer Shock Mounts"

    def execute(self, context: bpy.types.Context):
        ok, errors = validate_scene_for_suspension(context.scene)
        if not ok:
            for err in errors:
                self.report({"ERROR"}, err)
            return {"CANCELLED"}
        _, warnings = infer_shock_mounts(context.scene, force_rebuild=True)
        _warn_report(self, warnings)
        self.report({"INFO"}, "Shock mounts reinferred.")
        return {"FINISHED"}


class RCGEN_OT_GenerateShocks(bpy.types.Operator):
    bl_idname = "rcgen.generate_shocks"
    bl_label = "Generate Shock/Spring"

    def execute(self, context: bpy.types.Context):
        return {"FINISHED"} if _generate_shocks(context.scene, self) else {"CANCELLED"}


class RCGEN_OT_UpdateShocks(bpy.types.Operator):
    bl_idname = "rcgen.update_shocks"
    bl_label = "Update Shock/Spring"

    def execute(self, context: bpy.types.Context):
        return {"FINISHED"} if _generate_shocks(context.scene, self) else {"CANCELLED"}


class RCGEN_OT_RunPrintabilityChecks(bpy.types.Operator):
    bl_idname = "rcgen.run_printability_checks"
    bl_label = "Run Printability Checks"

    def execute(self, context: bpy.types.Context):
        errors, warnings, _ = run_printability_checks(context.scene)
        _warn_report(self, warnings)
        if errors:
            for err in errors:
                self.report({"ERROR"}, err)
            return {"CANCELLED"}
        self.report({"INFO"}, "Printability checks passed.")
        return {"FINISHED"}


class RCGEN_OT_ExportManufacturingPack(bpy.types.Operator):
    bl_idname = "rcgen.export_manufacturing_pack"
    bl_label = "Export Manufacturing Pack"

    def execute(self, context: bpy.types.Context):
        return {"FINISHED"} if _write_manufacturing_pack(context, context.scene, self) else {"CANCELLED"}


class RCGEN_OT_GenerateAll(bpy.types.Operator):
    bl_idname = "rcgen.generate_all"
    bl_label = "Generate All"

    def execute(self, context: bpy.types.Context):
        if not _generate_suspension(context.scene, self):
            return {"CANCELLED"}
        if not _generate_steering(context.scene, self):
            return {"CANCELLED"}
        if not _generate_shocks(context.scene, self):
            return {"CANCELLED"}
        self.report({"INFO"}, "Full generation finished.")
        return {"FINISHED"}


class RCGEN_OT_UpdateAll(bpy.types.Operator):
    bl_idname = "rcgen.update_all"
    bl_label = "Update All"

    def execute(self, context: bpy.types.Context):
        if not _generate_suspension(context.scene, self):
            return {"CANCELLED"}
        if not _generate_steering(context.scene, self):
            return {"CANCELLED"}
        if not _generate_shocks(context.scene, self):
            return {"CANCELLED"}
        self.report({"INFO"}, "Full update finished.")
        return {"FINISHED"}


class RCGEN_OT_OrganizeCollections(bpy.types.Operator):
    bl_idname = "rcgen.organize_collections"
    bl_label = "Organize Collections"

    def execute(self, context: bpy.types.Context):
        _ensure_collections(context.scene)
        self.report({"INFO"}, "RC_GEN collections organized.")
        return {"FINISHED"}


classes = (
    RCGEN_OT_CaptureSelected,
    RCGEN_OT_AutoCaptureByName,
    RCGEN_OT_ValidateReferences,
    RCGEN_OT_ValidateHardpoints,
    RCGEN_OT_ValidateAll,
    RCGEN_OT_GenerateSuspension,
    RCGEN_OT_UpdateSuspension,
    RCGEN_OT_GenerateSteering,
    RCGEN_OT_UpdateSteering,
    RCGEN_OT_ReinferShockMounts,
    RCGEN_OT_GenerateShocks,
    RCGEN_OT_UpdateShocks,
    RCGEN_OT_RunPrintabilityChecks,
    RCGEN_OT_ExportManufacturingPack,
    RCGEN_OT_GenerateAll,
    RCGEN_OT_UpdateAll,
    RCGEN_OT_OrganizeCollections,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
