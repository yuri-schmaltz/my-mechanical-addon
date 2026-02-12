from __future__ import annotations

from typing import Any


def _nominal_hole_mm(hardware: str) -> float:
    return {"M2": 2.0, "M3": 3.0, "M4": 4.0}.get(hardware, 3.0)


def _nut_flat_mm(hardware: str) -> float:
    return {"M2": 4.0, "M3": 5.5, "M4": 7.0}.get(hardware, 5.5)


def _insert_mm(hardware: str) -> float:
    return {"M2": 3.2, "M3": 4.6, "M4": 5.6}.get(hardware, 4.6)


def hardware_hole_diameter_m(hardware: str, hole_oversize_mm: float) -> float:
    return (_nominal_hole_mm(hardware) + hole_oversize_mm) / 1000.0


def hex_nut_flat_m(hardware: str, nut_trap_clearance_mm: float) -> float:
    return (_nut_flat_mm(hardware) + nut_trap_clearance_mm) / 1000.0


def insert_pocket_diameter_m(hardware: str, insert_pocket_clearance_mm: float) -> float:
    return (_insert_mm(hardware) + insert_pocket_clearance_mm) / 1000.0


def interface_specs(settings: Any, tolerances: Any) -> dict[str, float]:
    return {
        "hole_m": hardware_hole_diameter_m(settings.default_hardware, tolerances.hole_oversize_mm),
        "nut_flat_m": hex_nut_flat_m(settings.default_hardware, tolerances.nut_trap_clearance_mm),
        "insert_m": insert_pocket_diameter_m(settings.default_hardware, tolerances.insert_pocket_clearance_mm),
        "sliding_clearance_m": tolerances.clearance_sliding_mm / 1000.0,
        "press_clearance_m": tolerances.clearance_press_mm / 1000.0,
    }
