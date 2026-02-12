from __future__ import annotations

import bpy

from .constants import (
    HARDPOINT_LABELS,
    MANDATORY_HARDPOINT_TEMPLATES,
    MANDATORY_REFERENCE_KEYS,
    REFERENCE_LABELS,
    SIDES,
)


def missing_required_references(scene: bpy.types.Scene) -> list[str]:
    refs = scene.rcgen_refs
    missing = []
    for key in MANDATORY_REFERENCE_KEYS:
        if getattr(refs, key, None) is None:
            missing.append(REFERENCE_LABELS.get(key, key))
    return missing


def missing_required_hardpoints(scene: bpy.types.Scene) -> list[str]:
    refs = scene.rcgen_refs
    missing = []
    for side in SIDES:
        for template in MANDATORY_HARDPOINT_TEMPLATES:
            prop_name = template.format(side=side.lower())
            if getattr(refs, prop_name, None) is None:
                base = template.replace("_{side}", "")
                label = HARDPOINT_LABELS.get(base, template)
                missing.append(label.format(side=side))
    return missing


def validate_scene_for_suspension(scene: bpy.types.Scene) -> tuple[bool, list[str]]:
    errors = []
    missing_refs = missing_required_references(scene)
    missing_hp = missing_required_hardpoints(scene)
    if missing_refs:
        errors.append(f"Referencias obrigatorias ausentes: {', '.join(missing_refs)}")
    if missing_hp:
        errors.append(f"Hardpoints obrigatorios ausentes: {', '.join(missing_hp)}")
    return (not errors), errors


def validate_scene_for_steering(scene: bpy.types.Scene) -> tuple[bool, list[str]]:
    ok, errors = validate_scene_for_suspension(scene)
    return ok, errors


def validate_scene_for_shocks(scene: bpy.types.Scene) -> tuple[bool, list[str], list[str]]:
    ok, errors = validate_scene_for_suspension(scene)
    warnings = []
    refs = scene.rcgen_refs
    settings = scene.rcgen_settings
    if settings.use_manual_shock_mounts:
        for side in SIDES:
            top = getattr(refs, f"shock_top_{side.lower()}", None)
            bottom = getattr(refs, f"shock_bottom_{side.lower()}", None)
            if top is None or bottom is None:
                warnings.append(f"ShockTop_{side}/ShockBottom_{side} incompleto; usando inferencia.")
    return ok, errors, warnings
