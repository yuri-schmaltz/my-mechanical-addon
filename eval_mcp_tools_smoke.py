import bpy, addon_utils, os, zipfile
repo = r'c:\Users\u60897\Documents\my-mechanical-addon'
zip_path = os.path.join(repo, 'dist', 'RC_Mechanism_Generator.zip')
src = os.path.join(repo, 'rc_mechanism_generator')
if os.path.exists(zip_path):
    os.remove(zip_path)
with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(src):
        for fn in files:
            p = os.path.join(root, fn)
            zf.write(p, os.path.relpath(p, repo))

bpy.ops.preferences.addon_install(filepath=zip_path, overwrite=True)
bpy.ops.preferences.addon_enable(module='rc_mechanism_generator')
scene = bpy.context.scene
s = scene.rcgen_settings
print('enabled', addon_utils.check('rc_mechanism_generator')[1])
print('has_call_op', hasattr(bpy.ops.rcgen, 'call_mcp_tool'))
print('tool_props', hasattr(s, 'mcp_tool_name'), hasattr(s, 'mcp_tool_args_json'), hasattr(s, 'mcp_last_tool_result'))
