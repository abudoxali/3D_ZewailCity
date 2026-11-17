"""Idempotent photo-guided palette for the isolated V18 native scene.

Photos13/19/25/26 show neutral grey granite floors beside slightly warm stone
facades. Camera white balance, wetness and lighting differ; these are material
estimates, not colorimetrically measured reflectance or a 95% accuracy claim.
"""
import bpy

SURFACES={
 'plaza_light':((.25,.26,.26),(.34,.35,.34),(.15,.16,.16),.38),
 'plaza_grey':((.22,.23,.23),(.29,.30,.29),(.13,.14,.14),.36),
}
def apply(M):
 # Separate clear upper glazing preserves actual interior depth and gives the
 # upper screen its blue-grey reflection; no emissive window-image substitute.
 if 'upper_lobby_glass' not in M:
  g=bpy.data.materials.get('M_V18_Upper_Lobby_Glass') or M['lobby_glass'].copy()
  g.name='M_V18_Upper_Lobby_Glass';M['upper_lobby_glass']=g
  g.diffuse_color=(.07,.11,.16,1.)
  for node in g.node_tree.nodes:
   if node.type=='BSDF_PRINCIPLED':node.inputs['Base Color'].default_value=(.07,.11,.16,1.)
 M['upper_lobby_glass']['gltf_base_color']=[.07,.11,.16]
 from .materials import flat
 for key,name,color in (('lamp_neutral','M_V18_Lamp_Neutral',(1.,.95,.84)),('lamp_warm','M_V18_Lamp_Warm',(1.,.74,.38))):
  if key not in M:M[key]=bpy.data.materials.get(name) or flat(name,(.85,.82,.74),rough=.25,emission=color,strength=1.2)
 for key,alpha,transmission in (('lobby_glass',.22,.9),('upper_lobby_glass',.70,.65),('res_glass',.42,.7)):
  mat=M[key];mat.surface_render_method='DITHERED'
  for node in mat.node_tree.nodes:
   if node.type=='BSDF_PRINCIPLED':
    node.inputs['Alpha'].default_value=alpha
    node.inputs['Transmission Weight'].default_value=transmission
 # Make the new material keys survive the next native-source iteration.
 import json
 keys=json.loads(bpy.context.scene.get('zc_material_keys','{}'))
 keys.update({k:v.name for k,v in M.items()});bpy.context.scene['zc_material_keys']=json.dumps(keys)
 for key,(a,b,joint,rough) in SURFACES.items():
  mat=M[key]
  for node in mat.node_tree.nodes:
   if node.type=='TEX_BRICK':
    node.inputs['Color1'].default_value=(*a,1)
    node.inputs['Color2'].default_value=(*b,1)
    node.inputs['Mortar'].default_value=(*joint,1)
   elif node.type=='BSDF_PRINCIPLED':
    if not node.inputs['Roughness'].is_linked:node.inputs['Roughness'].default_value=rough
  mid=tuple((x+y)/2 for x,y in zip(a,b))
  mat.diffuse_color=(*mid,1);mat['gltf_base_color']=list(mid);mat.roughness=rough
  mat['zc_v18_palette']='Neutral grey granite; photo13/19/25/26 qualitative reference; color not surveyed'
 # Small leaf relief on existing clipped hedge forms. The old 0.8/m colour
 # noise alone looked like stretched lawn on vertical rectangular walls.
 for key in ('hedge','shrub'):
  mat=M[key];nt=mat.node_tree
  if nt.nodes.get('V18_Leaf_Relief'):continue
  b=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
  coord=nt.nodes.new('ShaderNodeNewGeometry');noise=nt.nodes.new('ShaderNodeTexNoise')
  noise.inputs['Scale'].default_value=42.;noise.inputs['Detail'].default_value=2.
  nt.links.new(coord.outputs['Position'],noise.inputs['Vector'])
  bump=nt.nodes.new('ShaderNodeBump');bump.name='V18_Leaf_Relief'
  bump.inputs['Strength'].default_value=.45;bump.inputs['Distance'].default_value=.018
  if b.inputs['Normal'].is_linked:nt.links.new(b.inputs['Normal'].links[0].from_socket,bump.inputs['Normal'])
  nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],b.inputs['Normal'])
 for light in bpy.data.lights:
  if light.type=='SUN':light.color=(1.,.985,.96)
