# Usage: python3 -I mannequin.py <Xbot.glb> <poses.json> <outdir>
# poses.json: {"view":[-250,360,150], "look":[0,-20,125], "ortho":2.5, "res":640,
#   "frames":[{"name":"1","grip":[x,y,z],"dir":[x,y,z],"lean":deg,"twist":deg,"drop":cm,
#              "rfoot":[x,y,z],"lfoot":[x,y,z],"elbow":"out|down"}]}
# Armature space (cm): +Z up, -Y = character front, +X = character LEFT. Grip = sword handle center.
# Right hand sits toward the guard, left hand toward the pommel.
import bpy, sys, math, json
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
from PIL import Image, ImageDraw

GLB, SPEC, OUT = sys.argv[-3:]
spec = json.load(open(SPEC))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB, bone_heuristic='TEMPERANCE')  # default makes every bone point straight up
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.parent is None: bpy.data.objects.remove(o)  # Icosphere
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.animation_data_clear()
P = arm.pose.bones
def B(n): return P['mixamorig:' + n]
def upd(): bpy.context.view_layer.update()
def aim(pb, pt):
    upd(); M = pb.matrix.copy(); h = M.translation.copy()
    q = (pb.tail - pb.head).normalized().rotation_difference((Vector(pt) - h).normalized())
    N = (q.to_matrix() @ M.to_3x3()).to_4x4(); N.translation = h; pb.matrix = N; upd()
def two_bone(up, lo, tgt, pole):
    upd(); S = up.head.copy(); T = Vector(tgt); L1, L2 = up.length, lo.length
    u = T - S; d = min(u.length, (L1 + L2) * 0.999); u.normalize()
    a = (L1*L1 - L2*L2 + d*d) / (2*d); h = math.sqrt(max(L1*L1 - a*a, 0))
    v = Vector(pole) - S; v = (v - u * v.dot(u)).normalized()
    aim(up, S + u*a + v*h); aim(lo, S + u*d)
def rot_about(pb, axis, ang, pivot):
    upd(); pb.matrix = (Matrix.Translation(pivot) @ Matrix.Rotation(ang, 4, axis)
                        @ Matrix.Translation(-pivot)) @ pb.matrix; upd()

def mat(name, col):
    m = bpy.data.materials.new(name); m.diffuse_color = col; return m
dark, steel = mat('dark', (0.05, 0.05, 0.06, 1)), mat('steel', (0.75, 0.78, 0.85, 1))
sword = bpy.data.objects.new('Sword', None); sc.collection.objects.link(sword); sword.parent = arm
for nm, size, z, m in (('handle', (3, 3, 24), -2, dark), ('tsuba', (8, 8, 1), 10.5, dark),
                       ('blade', (1, 3.2, 74), 48, steel)):
    bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.active_object
    o.scale, o.location, o.parent = size, (0, 0, z), sword; o.data.materials.append(m)

W = arm.matrix_world
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam)
cam.data.type = 'ORTHO'; cam.data.ortho_scale = spec.get('ortho', 2.5); sc.camera = cam
eye, tgt = W @ Vector(spec.get('view', (-250, 360, 150))), W @ Vector(spec.get('look', (0, -20, 125)))
cam.location = eye; cam.rotation_euler = (tgt - eye).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'BLENDER_WORKBENCH'
sc.render.resolution_x = sc.render.resolution_y = spec.get('res', 640)
sc.world = bpy.data.worlds.new('w'); sc.world.color = (1, 1, 1)
sc.view_settings.view_transform = 'Standard'
sh = sc.display.shading

BONES = [('Head', 'Neck'), ('Neck', 'RightArm'), ('Neck', 'LeftArm'), ('RightArm', 'RightForeArm'),
         ('RightForeArm', 'RightHand'), ('LeftArm', 'LeftForeArm'), ('LeftForeArm', 'LeftHand'),
         ('Neck', 'Hips'), ('Hips', 'RightUpLeg'), ('Hips', 'LeftUpLeg'), ('RightUpLeg', 'RightLeg'),
         ('RightLeg', 'RightFoot'), ('LeftUpLeg', 'LeftLeg'), ('LeftLeg', 'LeftFoot')]
COLS = [(255,0,0),(255,85,0),(255,170,0),(255,255,0),(170,255,0),(85,255,0),(0,255,0),
        (0,255,85),(0,255,170),(0,255,255),(0,170,255),(0,85,255),(0,0,255),(85,0,255)]
def px(p):
    v = world_to_camera_view(sc, cam, W @ p); r = sc.render.resolution_x
    return (v.x * r, (1 - v.y) * r)

def render(path, mode):
    if mode == 'color':
        sh.light, sh.color_type = 'STUDIO', 'MATERIAL'
    else:
        sh.light, sh.color_type, sh.single_color = 'FLAT', 'SINGLE', (0, 0, 0)
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)

side = Vector((1, 0, 0))
for f in spec['frames']:
    for pb in P: pb.matrix_basis = Matrix()
    upd()
    hips = B('Hips')
    upd(); M = hips.matrix.copy(); M.translation.z -= f.get('drop', 0); hips.matrix = M; upd()
    piv = B('Spine').head.copy()
    rot_about(B('Spine'), 'Z', math.radians(f.get('twist', 0)), piv)
    # lean: positive = forward (toward -Y)
    rot_about(B('Spine1'), 'X', math.radians(f.get('lean', 0)) * 0.5, B('Spine1').head.copy())
    rot_about(B('Spine2'), 'X', math.radians(f.get('lean', 0)) * 0.5, B('Spine2').head.copy())
    two_bone(B('RightUpLeg'), B('RightLeg'), f.get('rfoot', (-12, -20, 10)), (-12, -90, 50))
    two_bone(B('LeftUpLeg'), B('LeftLeg'), f.get('lfoot', (12, 22, 12)), (12, -90, 50))
    g, d = Vector(f['grip']), Vector(f['dir']).normalized()
    eo = 25 if f.get('elbow', 'out') == 'out' else -25
    two_bone(B('RightArm'), B('RightForeArm'), g + d*6 - side*2, (-70, 15, 140 + eo))
    two_bone(B('LeftArm'), B('LeftForeArm'), g - d*8 + side*2, (70, 15, 140 + eo))
    aim(B('RightHand'), g + d*30); aim(B('LeftHand'), g + d*30)
    # feet: sole flat on the floor, toes splayed outward by toe_out deg. "rheel"/"lheel": cm heel lift (rear foot push-off)
    for sd, s in (('Right', -1), ('Left', 1)):
        ft, toe = B(sd + 'Foot'), B(sd + 'ToeBase')
        ang = math.radians(f.get('toe_out', 12)) * s
        fwd = Vector((math.sin(ang), -math.cos(ang), 0))
        lift = f.get(sd[0].lower() + 'heel', 0)
        a = ft.head.copy()
        aim(ft, a + fwd * 10.7 + Vector((0, 0, -8.7 - lift)))
        aim(toe, toe.head + fwd * 8)
    sword.location = g; sword.rotation_euler = d.to_track_quat('Z', 'X').to_euler(); upd()
    base = f"{OUT}/{f['name']}"
    render(base + '_color.png', 'color'); render(base + '_sil.png', 'sil')
    r = sc.render.resolution_x; im = Image.new('RGB', (r, r), 'black'); dr = ImageDraw.Draw(im)
    for (a, b), c in zip(BONES, COLS):
        dr.line([px(B(a).head), px(B(b).head)], fill=c, width=6)
    for n in ('Head', 'Neck', 'RightArm', 'RightForeArm', 'RightHand', 'LeftArm', 'LeftForeArm',
              'LeftHand', 'Hips', 'RightUpLeg', 'RightLeg', 'RightFoot', 'LeftUpLeg', 'LeftLeg', 'LeftFoot'):
        x, y = px(B(n).head); dr.ellipse([x-5, y-5, x+5, y+5], fill='white')
    dr.line([px(g - d*14), px(g + d*85)], fill=(200, 200, 200), width=4)  # sword
    im.save(base + '_pose.png')
    print('FRAME', f['name'], 'head', [round(x) for x in B('Head').head])

# contact sheet: rows = color / silhouette / pose
names = [f['name'] for f in spec['frames']]
tiles = [[Image.open(f'{OUT}/{n}_{k}.png').convert('RGB') for n in names] for k in ('color', 'sil', 'pose')]
r = tiles[0][0].size[0]; sheet = Image.new('RGB', (r * len(names), r * 3), 'white')
for j, row in enumerate(tiles):
    for i, t in enumerate(row): sheet.paste(t, (i * r, j * r))
sheet.save(f'{OUT}/sheet.png'); print('SHEET', f'{OUT}/sheet.png')
# small copy for Claude's own check (saves image tokens); send sheet.png to the user, Read check.png yourself
k = min(1.0, 900 / sheet.size[0], 900 / sheet.size[1])
sheet.resize((int(sheet.size[0] * k), int(sheet.size[1] * k))).save(f'{OUT}/check.png'); print('CHECK', f'{OUT}/check.png')
