MANDATORY_REFERENCE_KEYS = (
    "chassis_obj",
    "wheel_l_obj",
    "wheel_r_obj",
    "servo_obj",
)

REFERENCE_LABELS = {
    "chassis_obj": "Chassis",
    "wheel_l_obj": "Wheel_L",
    "wheel_r_obj": "Wheel_R",
    "servo_obj": "Servo",
}

OPTIONAL_REFERENCE_KEYS = (
    "tire_l_obj",
    "tire_r_obj",
    "wheelwell_l_obj",
    "wheelwell_r_obj",
    "hub_l_obj",
    "hub_r_obj",
    "upright_l_obj",
    "upright_r_obj",
    "servo_horn_obj",
)

SIDES = ("L", "R")

MANDATORY_HARDPOINT_TEMPLATES = (
    "lca_in_front_{side}",
    "lca_in_rear_{side}",
    "lca_out_{side}",
    "uca_in_front_{side}",
    "uca_in_rear_{side}",
    "uca_out_{side}",
    "steering_arm_point_{side}",
)

HARDPOINT_LABELS = {
    "lca_in_front": "LCA_In_Front_{side}",
    "lca_in_rear": "LCA_In_Rear_{side}",
    "lca_out": "LCA_Out_{side}",
    "uca_in_front": "UCA_In_Front_{side}",
    "uca_in_rear": "UCA_In_Rear_{side}",
    "uca_out": "UCA_Out_{side}",
    "steering_arm_point": "SteeringArm_Point_{side}",
}

MANUAL_SHOCK_MOUNT_TEMPLATES = (
    "shock_top_{side}",
    "shock_bottom_{side}",
)

GENERATED_PREFIX = "RC_"
