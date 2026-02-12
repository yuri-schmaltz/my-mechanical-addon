from __future__ import annotations

from mathutils import Matrix, Vector


def midpoint(a: Vector, b: Vector) -> Vector:
    return (a + b) * 0.5


def lerp(a: Vector, b: Vector, t: float) -> Vector:
    return a.lerp(b, t)


def safe_normalized(v: Vector, fallback: Vector | None = None) -> Vector:
    if v.length > 1.0e-8:
        return v.normalized()
    if fallback is not None and fallback.length > 1.0e-8:
        return fallback.normalized()
    return Vector((0.0, 0.0, 1.0))


def axis_vector_from_enum(axis_enum: str) -> Vector:
    mapping = {
        "X": Vector((1.0, 0.0, 0.0)),
        "Y": Vector((0.0, 1.0, 0.0)),
        "Z": Vector((0.0, 0.0, 1.0)),
    }
    return mapping.get(axis_enum, Vector((0.0, 1.0, 0.0)))


def basis_from_forward_up(forward: Vector, up_hint: Vector) -> Matrix:
    x_axis = safe_normalized(forward, Vector((1.0, 0.0, 0.0)))
    z_axis = safe_normalized(up_hint)
    y_axis = safe_normalized(z_axis.cross(x_axis), Vector((0.0, 1.0, 0.0)))
    z_axis = safe_normalized(x_axis.cross(y_axis), Vector((0.0, 0.0, 1.0)))
    return Matrix((x_axis, y_axis, z_axis)).transposed()


def side_sign(side: str) -> float:
    return -1.0 if side == "L" else 1.0
