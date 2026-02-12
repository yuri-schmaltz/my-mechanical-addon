from __future__ import annotations

import bpy

from .utils.constants import SIDES


def _draw_pointer_capture(layout, refs, prop_name: str, label: str):
    row = layout.row(align=True)
    row.prop(refs, prop_name, text=label)
    op = row.operator("rcgen.capture_selected", text="", icon="EYEDROPPER")
    op.target_path = f"refs.{prop_name}"


class RCGEN_PT_MainPanel(bpy.types.Panel):
    bl_label = "RC Mechanism Generator"
    bl_idname = "RCGEN_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RC"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        scene = context.scene
        refs = scene.rcgen_refs
        settings = scene.rcgen_settings
        tol = scene.rcgen_tolerances

        layout.prop(settings, "rcgen_id")

        row = layout.row(align=True)
        row.operator("rcgen.generate_all", icon="MOD_BUILD")
        row.operator("rcgen.update_all", icon="FILE_REFRESH")

        self._draw_project(layout, settings)
        self._draw_tolerances(layout, tol, settings)
        self._draw_refs(layout, refs, settings)
        self._draw_hardpoints(layout, refs, settings)
        self._draw_suspension(layout, settings)
        self._draw_steering(layout, refs, settings)
        self._draw_shocks(layout, refs, settings)
        self._draw_dfm_export(layout, settings)

    def _draw_project(self, layout, settings):
        box = layout.box()
        box.prop(
            settings,
            "ui_show_project",
            text="Projeto",
            icon="TRIA_DOWN" if settings.ui_show_project else "TRIA_RIGHT",
            emboss=False,
        )
        if not settings.ui_show_project:
            return
        box.prop(settings, "project_scale")
        box.prop(settings, "wheelbase_mm")
        box.prop(settings, "default_hardware")
        box.prop(settings, "wheel_spin_axis")
        box.prop(settings, "servo_axis")
        box.prop(settings, "segments")
        row = box.row(align=True)
        row.prop(settings, "print_volume_x_mm")
        row.prop(settings, "print_volume_y_mm")
        row.prop(settings, "print_volume_z_mm")
        row2 = box.row(align=True)
        row2.prop(settings, "nozzle_mm")
        row2.prop(settings, "layer_height_mm")
        tire = box.row(align=True)
        tire.prop(settings, "tire_diameter_mm_manual")
        tire.prop(settings, "tire_width_mm_manual")

    def _draw_tolerances(self, layout, tol, settings):
        box = layout.box()
        box.prop(
            settings,
            "ui_show_tolerances",
            text="Tolerancias",
            icon="TRIA_DOWN" if settings.ui_show_tolerances else "TRIA_RIGHT",
            emboss=False,
        )
        if not settings.ui_show_tolerances:
            return
        box.prop(tol, "clearance_sliding_mm")
        box.prop(tol, "clearance_press_mm")
        box.prop(tol, "hole_oversize_mm")
        box.prop(tol, "nut_trap_clearance_mm")
        box.prop(tol, "insert_pocket_clearance_mm")

    def _draw_refs(self, layout, refs, settings):
        box = layout.box()
        box.prop(
            settings,
            "ui_show_refs",
            text="Referencias",
            icon="TRIA_DOWN" if settings.ui_show_refs else "TRIA_RIGHT",
            emboss=False,
        )
        if not settings.ui_show_refs:
            return
        _draw_pointer_capture(box, refs, "chassis_obj", "Chassis")
        _draw_pointer_capture(box, refs, "wheel_l_obj", "Wheel L")
        _draw_pointer_capture(box, refs, "wheel_r_obj", "Wheel R")
        _draw_pointer_capture(box, refs, "servo_obj", "Servo")
        box.separator()
        _draw_pointer_capture(box, refs, "tire_l_obj", "Tire L (opt)")
        _draw_pointer_capture(box, refs, "tire_r_obj", "Tire R (opt)")
        _draw_pointer_capture(box, refs, "wheelwell_l_obj", "WheelWell L (opt)")
        _draw_pointer_capture(box, refs, "wheelwell_r_obj", "WheelWell R (opt)")
        _draw_pointer_capture(box, refs, "hub_l_obj", "Hub L (opt)")
        _draw_pointer_capture(box, refs, "hub_r_obj", "Hub R (opt)")
        _draw_pointer_capture(box, refs, "upright_l_obj", "Upright L (opt)")
        _draw_pointer_capture(box, refs, "upright_r_obj", "Upright R (opt)")
        _draw_pointer_capture(box, refs, "servo_horn_obj", "ServoHorn (opt)")
        _draw_pointer_capture(box, refs, "rear_axle_center", "Rear Axle Center (opt)")
        box.prop(settings, "auto_capture_prefix")
        box.prop(settings, "auto_capture_scope")
        row = box.row(align=True)
        row.operator("rcgen.auto_capture_by_name", icon="VIEWZOOM")
        row.operator("rcgen.validate_references", icon="CHECKMARK")

    def _draw_hardpoints(self, layout, refs, settings):
        box = layout.box()
        box.prop(
            settings,
            "ui_show_hardpoints",
            text="Hardpoints",
            icon="TRIA_DOWN" if settings.ui_show_hardpoints else "TRIA_RIGHT",
            emboss=False,
        )
        if not settings.ui_show_hardpoints:
            return
        for side in SIDES:
            side_lower = side.lower()
            sub = box.box()
            sub.label(text=f"Lado {side}")
            _draw_pointer_capture(sub, refs, f"lca_in_front_{side_lower}", "LCA In Front")
            _draw_pointer_capture(sub, refs, f"lca_in_rear_{side_lower}", "LCA In Rear")
            _draw_pointer_capture(sub, refs, f"lca_out_{side_lower}", "LCA Out")
            _draw_pointer_capture(sub, refs, f"uca_in_front_{side_lower}", "UCA In Front")
            _draw_pointer_capture(sub, refs, f"uca_in_rear_{side_lower}", "UCA In Rear")
            _draw_pointer_capture(sub, refs, f"uca_out_{side_lower}", "UCA Out")
            _draw_pointer_capture(sub, refs, f"steering_arm_point_{side_lower}", "Steering Arm Point")
        row = box.row(align=True)
        row.operator("rcgen.validate_hardpoints", icon="CHECKMARK")
        row.operator("rcgen.validate_all", icon="INFO")

    def _draw_suspension(self, layout, settings):
        box = layout.box()
        box.prop(
            settings,
            "ui_show_suspension",
            text="Suspensao",
            icon="TRIA_DOWN" if settings.ui_show_suspension else "TRIA_RIGHT",
            emboss=False,
        )
        if not settings.ui_show_suspension:
            return
        box.prop(settings, "arm_section")
        box.prop(settings, "arm_rod_diameter_mm")
        box.prop(settings, "arm_bushing_diameter_mm")
        box.prop(settings, "min_wall_mm")
        box.prop(settings, "min_feature_mm")
        box.prop(settings, "add_ribs")
        box.prop(settings, "use_chamfer_radius")
        box.prop(settings, "generate_knuckle_when_missing")
        box.prop(settings, "use_boolean_holes")
        box.prop(settings, "hole_diameter_mm")
        row = box.row(align=True)
        row.operator("rcgen.generate_suspension", icon="MOD_BUILD")
        row.operator("rcgen.update_suspension", icon="FILE_REFRESH")

    def _draw_steering(self, layout, refs, settings):
        box = layout.box()
        box.prop(
            settings,
            "ui_show_steering",
            text="Estercamento",
            icon="TRIA_DOWN" if settings.ui_show_steering else "TRIA_RIGHT",
            emboss=False,
        )
        if not settings.ui_show_steering:
            return
        box.prop(settings, "servo_horn_length_mm")
        box.prop(settings, "servo_horn_diameter_mm")
        box.prop(settings, "tie_rod_diameter_mm")
        box.prop(settings, "tie_rod_terminal_diameter_mm")
        box.prop(settings, "steering_min_length_mm")
        box.prop(settings, "max_steer_angle_deg")
        box.prop(settings, "ackermann_mode")
        box.prop(settings, "wheelbase_mm")
        if settings.ackermann_mode == "AUTO":
            _draw_pointer_capture(box, refs, "rear_axle_center", "Rear Axle (auto)")
        row = box.row(align=True)
        row.operator("rcgen.generate_steering", icon="MOD_BUILD")
        row.operator("rcgen.update_steering", icon="FILE_REFRESH")

    def _draw_shocks(self, layout, refs, settings):
        box = layout.box()
        box.prop(
            settings,
            "ui_show_shocks",
            text="Amortecedor/Mola",
            icon="TRIA_DOWN" if settings.ui_show_shocks else "TRIA_RIGHT",
            emboss=False,
        )
        if not settings.ui_show_shocks:
            return
        box.prop(settings, "use_manual_shock_mounts")
        if settings.use_manual_shock_mounts:
            for side in SIDES:
                side_lower = side.lower()
                sub = box.box()
                sub.label(text=f"Mounts Manuais {side}")
                _draw_pointer_capture(sub, refs, f"shock_top_{side_lower}", "Shock Top")
                _draw_pointer_capture(sub, refs, f"shock_bottom_{side_lower}", "Shock Bottom")
        box.label(text="Inferencia Mounts")
        box.prop(settings, "bottom_mount_ratio")
        box.prop(settings, "bottom_inboard_offset_mm")
        box.prop(settings, "bottom_vertical_offset_mm")
        box.prop(settings, "bottom_fore_aft_offset_mm")
        box.prop(settings, "top_height_from_wheel_center_mm")
        box.prop(settings, "top_fore_aft_offset_mm")
        box.prop(settings, "top_inboard_offset_mm")
        row = box.row(align=True)
        row.operator("rcgen.reinfer_shock_mounts", icon="DRIVER_DISTANCE")
        row.operator("rcgen.generate_shocks", icon="MOD_BUILD")
        row.operator("rcgen.update_shocks", icon="FILE_REFRESH")
        box.separator()
        box.label(text="Coilover")
        box.prop(settings, "shock_total_length_mm")
        box.prop(settings, "shock_stroke_mm")
        box.prop(settings, "shock_body_diameter_mm")
        box.prop(settings, "shock_rod_diameter_mm")
        box.prop(settings, "shock_eyelet_diameter_mm")
        box.prop(settings, "generate_spring")
        if settings.generate_spring:
            box.prop(settings, "spring_outer_diameter_mm")
            box.prop(settings, "spring_wire_diameter_mm")
            box.prop(settings, "spring_turns")
            box.prop(settings, "spring_resolution")

    def _draw_dfm_export(self, layout, settings):
        box = layout.box()
        box.prop(
            settings,
            "ui_show_dfm_export",
            text="DFM/Export",
            icon="TRIA_DOWN" if settings.ui_show_dfm_export else "TRIA_RIGHT",
            emboss=False,
        )
        if not settings.ui_show_dfm_export:
            return
        box.prop(settings, "overhang_warn_deg")
        box.prop(settings, "min_edge_hole_margin_mm")
        box.prop(settings, "auto_split_large_parts")
        box.prop(settings, "split_key_diameter_mm")
        box.prop(settings, "split_key_profile")
        box.prop(settings, "split_orientation_bias")
        box.prop(settings, "split_clearance_mm")
        box.prop(settings, "export_dir")
        row = box.row(align=True)
        row.prop(settings, "export_stl")
        row.prop(settings, "export_3mf")
        box.operator("rcgen.run_printability_checks", icon="CHECKMARK")
        box.operator("rcgen.export_manufacturing_pack", icon="EXPORT")
        box.operator("rcgen.organize_collections", icon="OUTLINER_COLLECTION")


classes = (RCGEN_PT_MainPanel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
