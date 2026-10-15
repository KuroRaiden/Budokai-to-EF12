import pathlib,json,xml.dom.minidom as M,os
root=pathlib.Path(os.environ.get('STUDIO_MODEL_DIR',str(pathlib.Path(__file__).resolve().parent/'pilot_v2')))
data=json.loads((root/'Goku_geometry.json').read_text())
records={r['name']:r for r in data['meshes']}
doc=M.parse(str(root/'Goku_EF12.dae'))
for geometry in doc.getElementsByTagName('geometry'):
 name=geometry.getAttribute('name').removesuffix('-mesh')
 normals=records[name]['normals']
 for array in geometry.getElementsByTagName('float_array'):
  if array.getAttribute('id').endswith('-normals-array'):
   assert int(array.getAttribute('count'))==len(normals)*3
   while array.firstChild:array.removeChild(array.firstChild)
   array.appendChild(doc.createTextNode(' '.join('%.7f %.7f %.7f'%(n[0],n[2],-n[1]) for n in normals)))
for param in doc.getElementsByTagName('setparam'):
 if param.getAttribute('ref')=='Bold':
  param.getElementsByTagName('float')[0].firstChild.data='0.0015'
 if param.getAttribute('ref')=='BorderColor':
  param.getElementsByTagName('float3')[0].firstChild.data='0.05 0.05 0.05'
(root/'Goku_EF12.dae').write_bytes(doc.toxml(encoding='UTF-8'))
print('Restored original corner normals for',len(records),'mesh parts.')
