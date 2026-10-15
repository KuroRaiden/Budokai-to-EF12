import bpy,pathlib,json,mathutils,os
base=pathlib.Path(os.environ.get('DBZ_WORKSPACE',str(pathlib.Path(__file__).resolve().parents[2])))
folder=pathlib.Path(os.environ.get('STUDIO_MODEL_DIR',str(base/'work/ef12/pilot_v2')))
bpy.ops.wm.open_mainfile(filepath=str(folder/'Goku_EF12_G6Lite.blend'))
data=json.loads((folder/'Goku_geometry.json').read_text())
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
arm.animation_data_clear()
for bone in arm.data.bones:bone.use_deform=True
for pb in arm.pose.bones:
 pb.location=(0,0,0);pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.scale=(1,1,1)
for record in data['meshes']:
 obj=bpy.context.scene.objects[record['name']]
 obj.data.use_auto_smooth=True
 obj.data.normals_split_custom_set([tuple(n) for n in record['normals']])
 for i,name in enumerate(record['materials']):
  mat=obj.data.materials[i];info=data['materials'][name];mat.use_nodes=True
  nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
  out=nodes.new('ShaderNodeOutputMaterial');bsdf=nodes.new('ShaderNodeBsdfPrincipled')
  bsdf.inputs['Roughness'].default_value=.85;bsdf.inputs['Specular IOR Level'].default_value=.1
  links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
  if info['texture']:
   image=bpy.data.images.load(str(folder/info['texture']),check_existing=True);image.pack()
   tex=nodes.new('ShaderNodeTexImage');tex.image=image;links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
  else:bsdf.inputs['Base Color'].default_value=info['color']
bpy.context.scene.render.fps=60
if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'model_review.blend' if os.environ.get('STUDIO_MODEL_DIR') else base/'outputs/Goku_Corrected_Review.blend'))
points=[o.matrix_world@mathutils.Vector(v) for o in bpy.context.scene.objects if o.type=='MESH' for v in o.bound_box]
lo=mathutils.Vector([min(p[i] for p in points) for i in range(3)]);hi=mathutils.Vector([max(p[i] for p in points) for i in range(3)]);center=(lo+hi)/2
bpy.ops.object.camera_add(location=center+mathutils.Vector((20,50,4)))
cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=max(hi-lo)*1.2;bpy.context.scene.camera=cam
for delta,power in [((10,30,40),50000),((-30,10,20),35000)]:
 bpy.ops.object.light_add(type='AREA',location=center+mathutils.Vector(delta));light=bpy.context.object;light.data.energy=power;light.data.size=40;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.world.color=(.1,.1,.1);scene.view_settings.view_transform='Standard';scene.render.filepath=str(folder/'thumbnail.png' if os.environ.get('STUDIO_MODEL_DIR') else base/'outputs/Goku_Corrected_Review.png');bpy.ops.render.render(write_still=True)
print('MODERN_REVIEW_READY')
