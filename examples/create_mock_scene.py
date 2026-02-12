import bpy
import sys
from mathutils import Vector


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.curves, bpy.data.materials):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def add_cube(name, location, scale):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    return obj


def add_cylinder(name, location, radius, depth, rotation=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=radius,
        depth=depth,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.active_object
    obj.name = name
    return obj


def add_empty(name, location, size=0.012):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = size
    obj.location = Vector(location)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def build_mock():
    clear_scene()
    add_cube("chassis", (0.0, 0.0, 0.08), (0.08, 0.19, 0.03))
    add_cube("servo", (0.0, 0.09, 0.09), (0.02, 0.015, 0.02))
    add_empty("rear_axle_center", (0.0, -0.13, 0.06))

    wheel_y = 0.13
    wheel_z = 0.06
    half_track = 0.115

    for side, sign in (("L", -1.0), ("R", 1.0)):
        x = half_track * sign
        add_cylinder(
            f"wheel_{side}",
            (x, wheel_y, wheel_z),
            radius=0.028,
            depth=0.02,
            rotation=(1.5708, 0.0, 0.0),
        )
        add_cylinder(
            f"tire_{side}",
            (x, wheel_y, wheel_z),
            radius=0.043,
            depth=0.035,
            rotation=(1.5708, 0.0, 0.0),
        )
        add_empty(f"hub_{side}", (x, wheel_y, wheel_z))
        add_cube(f"wheelwell_{side}", (x, wheel_y, wheel_z + 0.03), (0.045, 0.045, 0.045))

        add_empty(f"LCA_In_Front_{side}", (x * 0.55, wheel_y - 0.03, wheel_z - 0.03))
        add_empty(f"LCA_In_Rear_{side}", (x * 0.55, wheel_y - 0.06, wheel_z - 0.03))
        add_empty(f"LCA_Out_{side}", (x * 0.92, wheel_y - 0.015, wheel_z - 0.02))

        add_empty(f"UCA_In_Front_{side}", (x * 0.52, wheel_y - 0.03, wheel_z + 0.035))
        add_empty(f"UCA_In_Rear_{side}", (x * 0.52, wheel_y - 0.06, wheel_z + 0.035))
        add_empty(f"UCA_Out_{side}", (x * 0.90, wheel_y - 0.02, wheel_z + 0.028))

        add_empty(f"SteeringArm_Point_{side}", (x * 0.88, wheel_y + 0.015, wheel_z - 0.005))

    for obj in bpy.data.objects:
        obj.select_set(False)
    bpy.context.view_layer.objects.active = None


def _arg_output_path():
    if "--" not in sys.argv:
        return None
    argv = sys.argv[sys.argv.index("--") + 1 :]
    return argv[0] if argv else None


if __name__ == "__main__":
    build_mock()
    output = _arg_output_path()
    if output:
        bpy.ops.wm.save_as_mainfile(filepath=output)
