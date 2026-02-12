bl_info = {
    "name": "RC Mechanism Generator",
    "author": "Codex",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > RC",
    "description": "Gera suspensao double wishbone, estercamento e coilover parametricos para RC.",
    "category": "Add Mesh",
}

from . import operators, properties, ui


def register():
    properties.register()
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()
