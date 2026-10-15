import bpy,os,sys,json
base=os.environ.get('DBZ_WORKSPACE',os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
out=os.environ.get('SHIN_OUT_DIR',os.path.join(base,'work','ef12','shin_motion'))
data=json.load(open(os.path.join(out,'retargeted_motion.json')))
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.environ.get('STUDIO_MODEL_DIR',os.path.join(base,'work','ef12','pilot_v2')),'Goku_EF12_G6Lite.blend'))
sys.path.insert(0,os.path.join(base,'work','ef12','motion_exporter'))
import ef12_motion_export
ef12_motion_export.register()
arm=bpy.data.objects['G6Lite_Rig']
for o in bpy.context.scene.objects:o.select=(o==arm)
bpy.context.scene.objects.active=arm
arm.animation_data_clear();arm.animation_data_create()
for pb in arm.pose.bones:
 pb.ef12.use_rotation=False;pb.rotation_mode='XYZ';pb.location=(0,0,0);pb.rotation_euler=(0,0,0);pb.scale=(1,1,1)
 for con in list(pb.constraints):pb.constraints.remove(con)
for name,frames in data.items():
 action=bpy.data.actions.new(name);action.use_fake_user=True;arm.animation_data.action=action
 for sample in frames:
  for bone,values in sample['bones'].items():
   pb=arm.pose.bones[bone];pb.rotation_mode='XYZ';pb.rotation_euler=values['rotation'];pb.location=values['location']
   pb.keyframe_insert(data_path='rotation_euler',frame=sample['frame']);pb.keyframe_insert(data_path='location',frame=sample['frame'])
 for curve in action.fcurves:
  for point in curve.keyframe_points:point.interpolation='BEZIER';point.handle_left_type='VECTOR';point.handle_right_type='VECTOR'
 bpy.context.scene.frame_start=0;bpy.context.scene.frame_end=frames[-1]['frame'];bpy.context.scene.frame_set(0)
 arm.data.bones.active=arm.data.bones['Waist']
 ef12_motion_export.write_motion_data(bpy.context,os.path.join(out,name+'.xsi'))
 print('EXPORTED_SHIN',name,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out,'Goku_Shin_Legacy.blend'))
