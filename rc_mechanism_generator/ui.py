from __future__ import annotations

import bpy

from .utils.constants import SIDES


def _draw_pointer_capture(layout, refs, prop_name: str, label: str, icon: str = "EMPTY_AXIS", required: bool = False):
    row = layout.row(align=True)
    row.alert = required and getattr(refs, prop_name, None) is None
    row.prop(refs, prop_name, text=label, icon=icon)
    op = row.operator("rcgen.capture_selected", text="", icon="EYEDROPPER")
    op.target_path = f"refs.{prop_name}"


def _draw_section_toggle(box, settings, prop_name: str, label: str, icon: str):
    row = box.row(align=True)
    row.scale_y = 1.05
    row.prop(
        settings,
        prop_name,
        text=label,
        icon="TRIA_DOWN" if getattr(settings, prop_name) else "TRIA_RIGHT",
        emboss=False,
    )
    row.label(text="", icon=icon)


def _draw_card_title(layout, title: str, icon: str, subtitle: str = ""):
    header = layout.row(align=True)
    header.label(text=title, icon=icon)
    if subtitle:
        header.label(text=subtitle)


def _count_core_references(refs) -> int:
    core = ("chassis_obj", "wheel_l_obj", "wheel_r_obj", "servo_obj")
    return sum(1 for prop in core if getattr(refs, prop, None) is not None)


class RCGEN_PT_MainPanel(bpy.types.Panel):
    bl_label = "Gerador de Mecanismo RC"
    bl_idname = "RCGEN_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RC"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        scene = context.scene
        refs = scene.rcgen_refs
        settings = scene.rcgen_settings
        tol = scene.rcgen_tolerances

        self._draw_overview(layout, settings, refs)
        self._draw_quick_actions(layout)

        self._draw_project(layout, settings)
        self._draw_tolerances(layout, tol, settings)
        self._draw_refs(layout, refs, settings)
        self._draw_hardpoints(layout, refs, settings)
        self._draw_suspension(layout, settings)
        self._draw_steering(layout, refs, settings)
        self._draw_shocks(layout, refs, settings)
        self._draw_mcp(layout, settings)
        self._draw_dfm_export(layout, settings)

    def _draw_overview(self, layout, settings, refs):
        box = layout.box()
        _draw_card_title(box, "Visao Geral", "TOOL_SETTINGS")

        box.prop(settings, "rcgen_id", text="ID do Conjunto")

        status = box.row(align=True)
        core_count = _count_core_references(refs)
        status.alert = core_count < 4
        status.label(text=f"Referencias base: {core_count}/4", icon="CHECKMARK" if core_count == 4 else "ERROR")

        chips = box.row(align=True)
        chips.label(text=f"Escala {settings.project_scale:.2f}", icon="PREFERENCES")
        chips.label(text=f"Entre-eixos {settings.wheelbase_mm:.0f} mm", icon="DRIVER_DISTANCE")

    def _draw_quick_actions(self, layout):
        box = layout.box()
        _draw_card_title(box, "Acoes Rapidas", "PLAY")
        row = box.row(align=True)
        row.scale_y = 1.2
        row.operator("rcgen.generate_all", text="Gerar Tudo", icon="MOD_BUILD")
        row.operator("rcgen.update_all", text="Atualizar Tudo", icon="FILE_REFRESH")

    def _draw_project(self, layout, settings):
        box = layout.box()
        _draw_section_toggle(box, settings, "ui_show_project", "Projeto", "SCENE_DATA")
        if not settings.ui_show_project:
            return

        basics = box.column(align=True)
        basics.prop(settings, "project_scale", text="Escala")
        basics.prop(settings, "wheelbase_mm", text="Entre-eixos (mm)")
        basics.prop(settings, "default_hardware", text="Ferragem Padrao")
        basics.prop(settings, "wheel_spin_axis", text="Eixo de Giro da Roda")
        basics.prop(settings, "servo_axis", text="Eixo do Servo")
        basics.prop(settings, "segments", text="Segmentos")

        box.separator()
        box.label(text="Perfil de Impressao", icon="MOD_WIREFRAME")
        row = box.row(align=True)
        row.prop(settings, "print_volume_x_mm", text="Volume X")
        row.prop(settings, "print_volume_y_mm", text="Y")
        row.prop(settings, "print_volume_z_mm", text="Z")
        row2 = box.row(align=True)
        row2.prop(settings, "nozzle_mm", text="Bico (mm)")
        row2.prop(settings, "layer_height_mm", text="Altura de Camada (mm)")

        box.separator()
        box.label(text="Pneu (Entrada Rapida)", icon="MESH_CIRCLE")
        tire = box.row(align=True)
        tire.prop(settings, "tire_diameter_mm_manual", text="Diametro")
        tire.prop(settings, "tire_width_mm_manual", text="Largura")

    def _draw_tolerances(self, layout, tol, settings):
        box = layout.box()
        _draw_section_toggle(box, settings, "ui_show_tolerances", "Tolerancias", "MODIFIER")
        if not settings.ui_show_tolerances:
            return

        box.prop(tol, "clearance_sliding_mm", text="Folga Deslizante (mm)")
        box.prop(tol, "clearance_press_mm", text="Folga de Interferencia (mm)")
        box.prop(tol, "hole_oversize_mm", text="Sobredimensionamento de Furo (mm)")
        box.prop(tol, "nut_trap_clearance_mm", text="Folga do Alojamento de Porca (mm)")
        box.prop(tol, "insert_pocket_clearance_mm", text="Folga do Insert (mm)")

    def _draw_refs(self, layout, refs, settings):
        box = layout.box()
        _draw_section_toggle(box, settings, "ui_show_refs", "Referencias", "OUTLINER_OB_EMPTY")
        if not settings.ui_show_refs:
            return

        required = box.box()
        required.label(text="Obrigatorias", icon="CHECKMARK")
        _draw_pointer_capture(required, refs, "chassis_obj", "Chassi", icon="MESH_CUBE", required=True)
        _draw_pointer_capture(required, refs, "wheel_l_obj", "Roda E", icon="MESH_CIRCLE", required=True)
        _draw_pointer_capture(required, refs, "wheel_r_obj", "Roda D", icon="MESH_CIRCLE", required=True)
        _draw_pointer_capture(required, refs, "servo_obj", "Servo", icon="ARMATURE_DATA", required=True)

        optional = box.box()
        optional.label(text="Opcionais", icon="INFO")
        _draw_pointer_capture(optional, refs, "tire_l_obj", "Pneu E")
        _draw_pointer_capture(optional, refs, "tire_r_obj", "Pneu D")
        _draw_pointer_capture(optional, refs, "wheelwell_l_obj", "Paralama E")
        _draw_pointer_capture(optional, refs, "wheelwell_r_obj", "Paralama D")
        _draw_pointer_capture(optional, refs, "hub_l_obj", "Cubo E")
        _draw_pointer_capture(optional, refs, "hub_r_obj", "Cubo D")
        _draw_pointer_capture(optional, refs, "upright_l_obj", "Manga E")
        _draw_pointer_capture(optional, refs, "upright_r_obj", "Manga D")
        _draw_pointer_capture(optional, refs, "servo_horn_obj", "Braço do Servo")
        _draw_pointer_capture(optional, refs, "rear_axle_center", "Centro do Eixo Traseiro")

        box.separator()
        box.prop(settings, "auto_capture_prefix", text="Prefixo de Captura")
        box.prop(settings, "auto_capture_scope", text="Escopo")
        row = box.row(align=True)
        row.operator("rcgen.auto_capture_by_name", text="Captura Automatica", icon="VIEWZOOM")
        row.operator("rcgen.validate_references", text="Validar", icon="CHECKMARK")

    def _draw_hardpoints(self, layout, refs, settings):
        box = layout.box()
        _draw_section_toggle(box, settings, "ui_show_hardpoints", "Pontos de Fixacao", "OUTLINER_OB_EMPTY")
        if not settings.ui_show_hardpoints:
            return

        for side in SIDES:
            side_lower = side.lower()
            sub = box.box()
            sub.label(text=f"Lado {side}")
            _draw_pointer_capture(sub, refs, f"lca_in_front_{side_lower}", "Bandeja Inf. Interno Frontal")
            _draw_pointer_capture(sub, refs, f"lca_in_rear_{side_lower}", "Bandeja Inf. Interno Traseiro")
            _draw_pointer_capture(sub, refs, f"lca_out_{side_lower}", "Bandeja Inferior Externo")
            _draw_pointer_capture(sub, refs, f"uca_in_front_{side_lower}", "Bandeja Sup. Interno Frontal")
            _draw_pointer_capture(sub, refs, f"uca_in_rear_{side_lower}", "Bandeja Sup. Interno Traseiro")
            _draw_pointer_capture(sub, refs, f"uca_out_{side_lower}", "Bandeja Superior Externo")
            _draw_pointer_capture(sub, refs, f"steering_arm_point_{side_lower}", "Ponto do Braço de Direcao")
        row = box.row(align=True)
        row.operator("rcgen.validate_hardpoints", text="Validar Pontos", icon="CHECKMARK")
        row.operator("rcgen.validate_all", text="Validar Tudo", icon="INFO")

    def _draw_suspension(self, layout, settings):
        box = layout.box()
        _draw_section_toggle(box, settings, "ui_show_suspension", "Suspensao", "PHYSICS")
        if not settings.ui_show_suspension:
            return

        box.prop(settings, "arm_section", text="Secao do Braço")
        box.prop(settings, "arm_rod_diameter_mm", text="Diametro da Haste (mm)")
        box.prop(settings, "arm_bushing_diameter_mm", text="Diametro da Bucha (mm)")
        box.prop(settings, "min_wall_mm", text="Parede Minima (mm)")
        box.prop(settings, "min_feature_mm", text="Detalhe Minimo (mm)")
        box.prop(settings, "add_ribs", text="Adicionar Nervuras")
        box.prop(settings, "use_chamfer_radius", text="Usar Chanfro/Raio")
        box.prop(settings, "generate_knuckle_when_missing", text="Gerar Manga Automaticamente")
        box.prop(settings, "use_boolean_holes", text="Usar Furos por Boolean")
        box.prop(settings, "hole_diameter_mm", text="Diametro de Furo (mm)")
        row = box.row(align=True)
        row.operator("rcgen.generate_suspension", text="Gerar", icon="MOD_BUILD")
        row.operator("rcgen.update_suspension", text="Atualizar", icon="FILE_REFRESH")

    def _draw_steering(self, layout, refs, settings):
        box = layout.box()
        _draw_section_toggle(box, settings, "ui_show_steering", "Direcao", "DRIVER_DISTANCE")
        if not settings.ui_show_steering:
            return

        box.prop(settings, "servo_horn_length_mm", text="Comprimento do Braço de Servo (mm)")
        box.prop(settings, "servo_horn_diameter_mm", text="Diametro do Cubo do Braço (mm)")
        box.prop(settings, "tie_rod_diameter_mm", text="Diametro da Barra de Direcao (mm)")
        box.prop(settings, "tie_rod_terminal_diameter_mm", text="Diametro do Terminal (mm)")
        box.prop(settings, "steering_min_length_mm", text="Comprimento Min. da Barra (mm)")
        box.prop(settings, "max_steer_angle_deg", text="Angulo Maximo de Esterco (graus)")
        box.prop(settings, "ackermann_mode", text="Ackermann")
        box.prop(settings, "wheelbase_mm", text="Entre-eixos (mm)")
        if settings.ackermann_mode == "AUTO":
            _draw_pointer_capture(box, refs, "rear_axle_center", "Eixo Traseiro (auto)")
        row = box.row(align=True)
        row.operator("rcgen.generate_steering", text="Gerar", icon="MOD_BUILD")
        row.operator("rcgen.update_steering", text="Atualizar", icon="FILE_REFRESH")

    def _draw_shocks(self, layout, refs, settings):
        box = layout.box()
        _draw_section_toggle(box, settings, "ui_show_shocks", "Amortecedor / Mola", "PHYSICS")
        if not settings.ui_show_shocks:
            return

        box.prop(settings, "use_manual_shock_mounts", text="Usar Pontos Manuais de Amortecedor")
        if settings.use_manual_shock_mounts:
            for side in SIDES:
                side_lower = side.lower()
                sub = box.box()
                sub.label(text=f"Pontos Manuais {side}", icon="EMPTY_AXIS")
                _draw_pointer_capture(sub, refs, f"shock_top_{side_lower}", "Topo do Amortecedor")
                _draw_pointer_capture(sub, refs, f"shock_bottom_{side_lower}", "Base do Amortecedor")

        box.separator()
        box.label(text="Inferencia de Pontos", icon="OUTLINER_DATA_EMPTY")
        box.prop(settings, "bottom_mount_ratio", text="Razao do Ponto Inferior")
        box.prop(settings, "bottom_inboard_offset_mm", text="Offset Interno Inferior (mm)")
        box.prop(settings, "bottom_vertical_offset_mm", text="Offset Vertical Inferior (mm)")
        box.prop(settings, "bottom_fore_aft_offset_mm", text="Offset Longitudinal Inferior (mm)")
        box.prop(settings, "top_height_from_wheel_center_mm", text="Altura Superior ao Centro da Roda (mm)")
        box.prop(settings, "top_fore_aft_offset_mm", text="Offset Longitudinal Superior (mm)")
        box.prop(settings, "top_inboard_offset_mm", text="Offset Interno Superior (mm)")
        row = box.row(align=True)
        row.operator("rcgen.reinfer_shock_mounts", text="Reinferir", icon="DRIVER_DISTANCE")
        row.operator("rcgen.generate_shocks", text="Gerar", icon="MOD_BUILD")
        row.operator("rcgen.update_shocks", text="Atualizar", icon="FILE_REFRESH")

        box.separator()
        box.label(text="Coilover", icon="MOD_SCREW")
        box.prop(settings, "shock_total_length_mm", text="Comprimento do Amortecedor (mm)")
        box.prop(settings, "shock_stroke_mm", text="Curso (mm)")
        box.prop(settings, "shock_body_diameter_mm", text="Diametro do Corpo (mm)")
        box.prop(settings, "shock_rod_diameter_mm", text="Diametro da Haste (mm)")
        box.prop(settings, "shock_eyelet_diameter_mm", text="Diametro do Olhal (mm)")
        box.prop(settings, "generate_spring", text="Gerar Mola")
        if settings.generate_spring:
            box.prop(settings, "spring_outer_diameter_mm", text="Diametro Externo da Mola (mm)")
            box.prop(settings, "spring_wire_diameter_mm", text="Diametro do Arame (mm)")
            box.prop(settings, "spring_turns", text="Espiras")
            box.prop(settings, "spring_resolution", text="Resolucao da Mola")

    def _draw_dfm_export(self, layout, settings):
        box = layout.box()
        _draw_section_toggle(box, settings, "ui_show_dfm_export", "DFM / Exportacao", "EXPORT")
        if not settings.ui_show_dfm_export:
            return

        box.prop(settings, "overhang_warn_deg", text="Alerta de Overhang (graus)")
        box.prop(settings, "min_edge_hole_margin_mm", text="Margem Min. Borda-Furo (mm)")
        box.prop(settings, "auto_split_large_parts", text="Dividir Pecas Grandes Automaticamente")
        box.prop(settings, "split_key_diameter_mm", text="Diametro da Chave de Uniao (mm)")
        box.prop(settings, "split_key_profile", text="Perfil da Chave")
        box.prop(settings, "split_orientation_bias", text="Orientacao Preferencial de Corte")
        box.prop(settings, "split_clearance_mm", text="Folga de Encaixe da Divisao (mm)")
        box.prop(settings, "export_dir", text="Diretorio de Exportacao")
        row = box.row(align=True)
        row.prop(settings, "export_stl", text="Exportar STL")
        row.prop(settings, "export_3mf", text="Exportar 3MF")

        actions = box.column(align=True)
        actions.operator("rcgen.run_printability_checks", text="Rodar Verificacoes de Impressao", icon="CHECKMARK")
        actions.operator("rcgen.export_manufacturing_pack", text="Exportar Pacote de Fabricacao", icon="EXPORT")
        actions.operator("rcgen.organize_collections", text="Organizar Colecoes", icon="OUTLINER_COLLECTION")

    def _draw_mcp(self, layout, settings):
        box = layout.box()
        _draw_section_toggle(box, settings, "ui_show_mcp", "MCP", "URL")
        if not settings.ui_show_mcp:
            return

        box.prop(settings, "mcp_enabled", text="Ativar MCP")
        box.prop(settings, "mcp_transport", text="Transporte")
        if settings.mcp_transport == "STDIO":
            box.prop(settings, "mcp_stdio_command", text="Comando MCP")
            box.prop(settings, "mcp_stdio_cwd", text="Diretorio de Trabalho")
        else:
            box.prop(settings, "mcp_endpoint_url", text="Endpoint")
        box.prop(settings, "mcp_protocol_version", text="Protocol Version")
        box.prop(settings, "mcp_timeout_sec", text="Timeout (s)")

        row = box.row(align=True)
        row.operator("rcgen.test_mcp_connection", text="Testar Conexao MCP", icon="LINKED")

        status = box.row(align=True)
        text = settings.mcp_last_status.strip()
        if text.startswith("OK:"):
            status.label(text=text, icon="CHECKMARK")
        elif text.startswith("ERROR:"):
            status.alert = True
            status.label(text=text, icon="ERROR")
        else:
            status.label(text=f"Status: {text}", icon="INFO")

        box.separator()
        box.label(text="Tools/Call", icon="TOOL_SETTINGS")
        box.prop(settings, "mcp_tool_name", text="Nome da Tool")
        box.prop(settings, "mcp_tool_args_json", text="Args (JSON)")

        call_row = box.row(align=True)
        call_row.operator("rcgen.call_mcp_tool", text="Executar Tool MCP", icon="PLAY")

        tool_result = box.row(align=True)
        result_text = settings.mcp_last_tool_result.strip()
        if result_text.startswith("OK:"):
            tool_result.label(text=result_text, icon="CHECKMARK")
        elif result_text.startswith("ERROR:"):
            tool_result.alert = True
            tool_result.label(text=result_text, icon="ERROR")
        else:
            tool_result.label(text=result_text, icon="INFO")


classes = (RCGEN_PT_MainPanel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
