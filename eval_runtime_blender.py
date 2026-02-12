import os
import sys
import json
import time
import traceback
import statistics
import runpy

import bpy
import addon_utils

REPO = r"c:\Users\u60897\Documents\my-mechanical-addon"
ZIP_PATH = os.path.join(REPO, "dist", "RC_Mechanism_Generator.zip")
MOCK_SCRIPT = os.path.join(REPO, "examples", "create_mock_scene.py")
OUT_DIR = os.path.join(REPO, "eval_outputs")
os.makedirs(OUT_DIR, exist_ok=True)
RESULT_PATH = os.path.join(OUT_DIR, "runtime_eval_results.json")
EXPORT_DIR = os.path.join(OUT_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

MODULE = "rc_mechanism_generator"

results = {
    "environment": {
        "blender_version": bpy.app.version_string,
        "blender_binary": bpy.app.binary_path,
        "factory_startup": True,
    },
    "install_enable": {},
    "enable_disable_cycles": {},
    "e2e": {},
    "performance": {},
    "stability": {},
    "undo_redo": {},
    "persistence": {},
    "errors": [],
    "warnings": [],
}


def safe_call(label, fn):
    t0 = time.perf_counter()
    try:
        out = fn()
        dt = time.perf_counter() - t0
        return {"ok": True, "duration_s": dt, "result": str(out)}
    except Exception as e:
        dt = time.perf_counter() - t0
        tb = traceback.format_exc()
        results["errors"].append({"label": label, "error": str(e), "traceback": tb})
        return {"ok": False, "duration_s": dt, "error": str(e)}


def ensure_clean_addon_state():
    try:
        if addon_utils.check(MODULE)[1]:
            bpy.ops.preferences.addon_disable(module=MODULE)
    except Exception:
        pass


def install_and_enable():
    # Install from zip to test installation flow; then enable.
    bpy.ops.preferences.addon_install(filepath=ZIP_PATH, overwrite=True)
    bpy.ops.preferences.addon_enable(module=MODULE)
    enabled = addon_utils.check(MODULE)[1]
    return {"enabled": enabled}


def disable_addon():
    if addon_utils.check(MODULE)[1]:
        bpy.ops.preferences.addon_disable(module=MODULE)
    return {"enabled": addon_utils.check(MODULE)[1]}


def run_mock_scene():
    runpy.run_path(MOCK_SCRIPT, run_name="__main__")


def generated_objects_count():
    c = 0
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and "rcgen_id" in obj and "rcgen_module" in obj:
            c += 1
    return c


def setup_scene_and_refs():
    run_mock_scene()
    scene = bpy.context.scene
    s = scene.rcgen_settings
    s.rcgen_id = "EVAL_RUNTIME_01"
    s.export_dir = EXPORT_DIR
    s.export_stl = True
    s.export_3mf = False
    s.auto_split_large_parts = True
    s.auto_capture_scope = "ALL"
    s.auto_capture_prefix = ""

    res_auto = bpy.ops.rcgen.auto_capture_by_name()
    res_refs = bpy.ops.rcgen.validate_references()
    res_hp = bpy.ops.rcgen.validate_hardpoints()
    return {
        "auto_capture": str(res_auto),
        "validate_references": str(res_refs),
        "validate_hardpoints": str(res_hp),
    }


def op_time(op_callable, rounds=5):
    times = []
    for _ in range(rounds):
        t0 = time.perf_counter()
        op_callable()
        times.append(time.perf_counter() - t0)
    times_sorted = sorted(times)
    p50 = statistics.median(times_sorted)
    idx95 = max(0, min(len(times_sorted) - 1, int(round(0.95 * (len(times_sorted) - 1)))))
    return {
        "rounds": rounds,
        "times_s": times,
        "p50_s": p50,
        "p95_s": times_sorted[idx95],
        "min_s": min(times_sorted),
        "max_s": max(times_sorted),
    }


def add_heavy_scene_objects(n=400):
    mesh = bpy.data.meshes.new("EvalCubeMesh")
    verts = [(-0.01, -0.01, -0.01), (0.01, -0.01, -0.01), (0.01, 0.01, -0.01), (-0.01, 0.01, -0.01),
             (-0.01, -0.01, 0.01), (0.01, -0.01, 0.01), (0.01, 0.01, 0.01), (-0.01, 0.01, 0.01)]
    faces = [(0,1,2,3), (4,5,6,7), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    col = bpy.context.scene.collection
    for i in range(n):
        obj = bpy.data.objects.new(f"EVAL_DUMMY_{i}", mesh)
        obj.location = (i % 40) * 0.05, (i // 40) * 0.05, 0.0
        col.objects.link(obj)


# 1) Install + enable
ensure_clean_addon_state()
results["install_enable"]["install_enable"] = safe_call("install_enable", install_and_enable)

# 2) Enable/disable 10x
cycles = []
for i in range(10):
    r_dis = safe_call(f"disable_{i}", disable_addon)
    r_en = safe_call(f"enable_{i}", lambda: bpy.ops.preferences.addon_enable(module=MODULE))
    enabled_now = addon_utils.check(MODULE)[1]
    cycles.append({"cycle": i + 1, "disable": r_dis, "enable": r_en, "enabled_after": enabled_now})
results["enable_disable_cycles"] = {
    "cycles": cycles,
    "all_enabled_after": all(c["enabled_after"] for c in cycles),
}

# Ensure enabled for remaining tests
if not addon_utils.check(MODULE)[1]:
    bpy.ops.preferences.addon_enable(module=MODULE)

# 3) E2E setup + operators
results["e2e"]["setup"] = safe_call("setup_scene_and_refs", setup_scene_and_refs)

results["e2e"]["generate_all"] = safe_call("generate_all", lambda: bpy.ops.rcgen.generate_all())
count_after_generate = generated_objects_count()
results["e2e"]["generated_count_after_generate_all"] = count_after_generate

results["undo_redo"]["undo"] = safe_call("undo", lambda: bpy.ops.ed.undo())
results["undo_redo"]["redo"] = safe_call("redo", lambda: bpy.ops.ed.redo())

results["e2e"]["update_all"] = safe_call("update_all", lambda: bpy.ops.rcgen.update_all())
results["e2e"]["printability_checks"] = safe_call("run_printability_checks", lambda: bpy.ops.rcgen.run_printability_checks())
results["e2e"]["export_pack"] = safe_call("export_pack", lambda: bpy.ops.rcgen.export_manufacturing_pack())

set_dir = os.path.join(EXPORT_DIR, "EVAL_RUNTIME_01")
expected_files = [
    "BOM.csv",
    "BOM.json",
    "ASSEMBLY.md",
    "manifest.json",
]
file_status = {name: os.path.exists(os.path.join(set_dir, name)) for name in expected_files}
stl_count = 0
if os.path.isdir(set_dir):
    for name in os.listdir(set_dir):
        if name.lower().endswith(".stl"):
            stl_count += 1
results["e2e"]["export_artifacts"] = {
    "export_dir": set_dir,
    "expected_files": file_status,
    "stl_count": stl_count,
}

# 4) Performance (small)
results["performance"]["small_update_all"] = safe_call(
    "perf_small",
    lambda: op_time(lambda: bpy.ops.rcgen.update_all(), rounds=10),
)

# 5) Performance (large scene)
results["performance"]["add_heavy_scene"] = safe_call("add_heavy_scene", lambda: add_heavy_scene_objects(500))
results["performance"]["large_update_all"] = safe_call(
    "perf_large",
    lambda: op_time(lambda: bpy.ops.rcgen.update_all(), rounds=5),
)

# 6) Stability 100x update

def run_100x_updates():
    fails = 0
    t0 = time.perf_counter()
    for i in range(100):
        try:
            bpy.ops.rcgen.update_all()
        except Exception:
            fails += 1
    dt = time.perf_counter() - t0
    return {"rounds": 100, "fails": fails, "total_s": dt, "avg_s": dt / 100.0}

results["stability"]["update_all_100x"] = safe_call("update_100x", run_100x_updates)

# 7) Save/reopen persistence
blend_path = os.path.join(OUT_DIR, "runtime_eval_scene.blend")


def save_and_reopen():
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    before = generated_objects_count()
    bpy.ops.wm.open_mainfile(filepath=blend_path)
    after = generated_objects_count()
    return {"blend_path": blend_path, "generated_before": before, "generated_after": after}

results["persistence"]["save_reopen"] = safe_call("save_reopen", save_and_reopen)

# finalize
with open(RESULT_PATH, "w", encoding="utf-8") as fp:
    json.dump(results, fp, indent=2, ensure_ascii=False)

print("RUNTIME_EVAL_RESULT", RESULT_PATH)
print(json.dumps({
    "install_ok": results["install_enable"].get("install_enable", {}).get("ok", False),
    "generate_ok": results["e2e"].get("generate_all", {}).get("ok", False),
    "export_ok": results["e2e"].get("export_pack", {}).get("ok", False),
    "errors": len(results.get("errors", [])),
}, ensure_ascii=False))
