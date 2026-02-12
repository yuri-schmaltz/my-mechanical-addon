# Referencia de Propriedades

Fonte de verdade: `rc_mechanism_generator/properties.py`.

## Onde as propriedades vivem

- `scene.rcgen_refs` (`RCGEN_References`)
- `scene.rcgen_tolerances` (`RCGEN_Tolerances`)
- `scene.rcgen_settings` (`RCGEN_Settings`)

## RCGEN_References

### Referencias obrigatorias

- `chassis_obj`
- `wheel_l_obj`
- `wheel_r_obj`
- `servo_obj`

### Referencias opcionais

- `tire_l_obj`, `tire_r_obj`
- `wheelwell_l_obj`, `wheelwell_r_obj`
- `hub_l_obj`, `hub_r_obj`
- `upright_l_obj`, `upright_r_obj`
- `servo_horn_obj`
- `rear_axle_center` (empty, usado em Ackermann auto)

### Hardpoints obrigatorios

Lado L:
- `lca_in_front_l`
- `lca_in_rear_l`
- `lca_out_l`
- `uca_in_front_l`
- `uca_in_rear_l`
- `uca_out_l`
- `steering_arm_point_l`

Lado R:
- `lca_in_front_r`
- `lca_in_rear_r`
- `lca_out_r`
- `uca_in_front_r`
- `uca_in_rear_r`
- `uca_out_r`
- `steering_arm_point_r`

### Hardpoints manuais de shock

- `shock_top_l`, `shock_bottom_l`
- `shock_top_r`, `shock_bottom_r`

## RCGEN_Tolerances

- `clearance_sliding_mm`
- `clearance_press_mm`
- `hole_oversize_mm`
- `nut_trap_clearance_mm`
- `insert_pocket_clearance_mm`

## RCGEN_Settings

## Identificacao

- `rcgen_id`

## Projeto e impressao

- `project_scale`
- `wheelbase_mm`
- `default_hardware` (`M2`, `M3`, `M4`)
- `print_volume_x_mm`
- `print_volume_y_mm`
- `print_volume_z_mm`
- `nozzle_mm`
- `layer_height_mm`
- `wheel_spin_axis` (`X`, `Y`, `Z`)
- `tire_diameter_mm_manual`
- `tire_width_mm_manual`
- `servo_axis` (`X`, `Y`, `Z`)
- `segments`

## Suspensao

- `arm_section` (`ROUND`, `RECT`, `OVAL`)
- `arm_rod_diameter_mm`
- `arm_bushing_diameter_mm`
- `min_wall_mm`
- `min_feature_mm`
- `add_ribs`
- `use_chamfer_radius`
- `generate_knuckle_when_missing`
- `use_boolean_holes`
- `hole_diameter_mm`

## Direcao

- `servo_horn_length_mm`
- `servo_horn_diameter_mm`
- `tie_rod_diameter_mm`
- `tie_rod_terminal_diameter_mm`
- `ackermann_mode` (`MANUAL`, `AUTO`)
- `max_steer_angle_deg`
- `steering_min_length_mm`

## Shocks e mola

- `use_manual_shock_mounts`
- `bottom_mount_ratio`
- `bottom_inboard_offset_mm`
- `bottom_vertical_offset_mm`
- `bottom_fore_aft_offset_mm`
- `top_height_from_wheel_center_mm`
- `top_fore_aft_offset_mm`
- `top_inboard_offset_mm`
- `shock_total_length_mm`
- `shock_stroke_mm`
- `shock_body_diameter_mm`
- `shock_rod_diameter_mm`
- `shock_eyelet_diameter_mm`
- `generate_spring`
- `spring_outer_diameter_mm`
- `spring_wire_diameter_mm`
- `spring_turns`
- `spring_resolution`

## DFM e split/export

- `overhang_warn_deg`
- `min_edge_hole_margin_mm`
- `auto_split_large_parts`
- `split_key_diameter_mm`
- `split_key_profile` (`ROUND`, `HEX`, `D`)
- `split_orientation_bias` (`AUTO`, `CHASSIS_FORWARD`, `CHASSIS_RIGHT`)
- `split_clearance_mm`
- `auto_capture_prefix`
- `auto_capture_scope` (`ALL`, `SELECTED`, `ACTIVE`)
- `export_dir`
- `export_stl`
- `export_3mf`

## Estado de UI

- `ui_show_project`
- `ui_show_tolerances`
- `ui_show_refs`
- `ui_show_hardpoints`
- `ui_show_suspension`
- `ui_show_steering`
- `ui_show_shocks`
- `ui_show_dfm_export`

## Notas de uso

- Mudancas em `rcgen_settings` impactam diretamente os operadores de geracao e export.
- `rcgen_id` separa conjuntos de geracao e export.
- `export_dir` usa path Blender e pode ser relativo (`//...`) ou absoluto.

