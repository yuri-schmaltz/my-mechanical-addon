import json
import os
import runpy
import bpy
import addon_utils

REPO = r'c:\Users\u60897\Documents\my-mechanical-addon'
OUT = os.path.join(REPO, 'eval_outputs', 'gui_complementary_results.json')
MOCK = os.path.join(REPO, 'examples', 'create_mock_scene.py')
MODULE = 'rc_mechanism_generator'
ZIP = os.path.join(REPO, 'dist', 'RC_Mechanism_Generator.zip')

os.makedirs(os.path.dirname(OUT), exist_ok=True)

res = {
    'blender_version': bpy.app.version_string,
    'undo_redo': {},
    'ui_scale_checks': {},
    'notes': [],
}

# install/enable
try:
    bpy.ops.preferences.addon_install(filepath=ZIP, overwrite=True)
except Exception:
    pass
if not addon_utils.check(MODULE)[1]:
    bpy.ops.preferences.addon_enable(module=MODULE)

# setup scene
runpy.run_path(MOCK, run_name='__main__')
scene = bpy.context.scene
settings = scene.rcgen_settings
settings.rcgen_id = 'EVAL_UNDO_01'
bpy.ops.rcgen.auto_capture_by_name()

# run op and test undo/redo
try:
    bpy.ops.rcgen.generate_all()
    count_after_generate = sum(1 for o in scene.objects if o.type == 'MESH' and 'rcgen_id' in o and o.get('rcgen_id') == 'EVAL_UNDO_01')

    # initialize undo stack in background
    bpy.ops.ed.undo_push(message='before_update_all')
    bpy.ops.rcgen.update_all()
    count_after_update = sum(1 for o in scene.objects if o.type == 'MESH' and 'rcgen_id' in o and o.get('rcgen_id') == 'EVAL_UNDO_01')

    undo_ok = False
    redo_ok = False
    undo_err = ''
    redo_err = ''

    try:
        r_undo = bpy.ops.ed.undo()
        undo_ok = 'FINISHED' in r_undo
    except Exception as e:
        undo_err = str(e)

    try:
        r_redo = bpy.ops.ed.redo()
        redo_ok = 'FINISHED' in r_redo
    except Exception as e:
        redo_err = str(e)

    count_after_undo_redo = sum(1 for o in scene.objects if o.type == 'MESH' and 'rcgen_id' in o and o.get('rcgen_id') == 'EVAL_UNDO_01')

    res['undo_redo'] = {
        'count_after_generate': count_after_generate,
        'count_after_update': count_after_update,
        'undo_ok': undo_ok,
        'redo_ok': redo_ok,
        'count_after_undo_redo': count_after_undo_redo,
        'undo_error': undo_err,
        'redo_error': redo_err,
    }
except Exception as e:
    res['undo_redo'] = {'fatal_error': str(e)}

# UI scaling: headless limitations
prefs = bpy.context.preferences.view
orig_scale = prefs.ui_scale
scales = [1.0, 1.25, 1.5]
for s in scales:
    try:
        prefs.ui_scale = s
        res['ui_scale_checks'][str(s)] = {
            'set_ok': True,
            'note': 'Headless mode: sem viewport para validar clipping/overflow visual.'
        }
    except Exception as e:
        res['ui_scale_checks'][str(s)] = {'set_ok': False, 'error': str(e)}
prefs.ui_scale = orig_scale

res['notes'].append('Validacao visual de clipping requer Blender GUI interativo.')

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(res, f, indent=2, ensure_ascii=False)

print('GUI_COMPLEMENTARY_RESULT', OUT)
print(json.dumps(res['undo_redo'], ensure_ascii=False))
