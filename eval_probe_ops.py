import bpy
print('has export_mesh.stl', hasattr(bpy.ops.export_mesh, 'stl'))
print('has wm.stl_export', hasattr(bpy.ops.wm, 'stl_export'))
print('has export_mesh.threemf', hasattr(bpy.ops.export_mesh, 'threemf'))
print('has wm.obj_export', hasattr(bpy.ops.wm, 'obj_export'))
