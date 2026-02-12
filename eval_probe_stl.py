import bpy, os, tempfile
bpy.ops.mesh.primitive_cube_add()
out = os.path.join(tempfile.gettempdir(), 'probe_cube.stl')
try:
    bpy.ops.export_mesh.stl(filepath=out, use_selection=True, check_existing=False, ascii=False)
    print('export_mesh.stl ok', out)
except Exception as e:
    print('export_mesh.stl fail', repr(e))
try:
    bpy.ops.wm.stl_export(filepath=out, export_selected_objects=True, check_existing=False)
    print('wm.stl_export ok', out)
except Exception as e:
    print('wm.stl_export fail', repr(e))
