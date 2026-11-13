"""3D render-speed test: builds a small toy-style scene (character, house, press, cash) and
renders one frame. Run: blender -b --python render3d/bench.py -- ENGINE WIDTH HEIGHT SAMPLES OUT.png"""
import math
import sys
import time

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
ENGINE, W, H, SAMPLES, OUT = argv[0], int(argv[1]), int(argv[2]), int(argv[3]), argv[4]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def mat(name, rgb, rough=0.55, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


def obj_finish(o, m, bevel=0.0, subsurf=0):
    o.data.materials.append(m)
    if bevel:
        mod = o.modifiers.new("bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 4
    if subsurf:
        mod = o.modifiers.new("sub", "SUBSURF")
        mod.levels = subsurf
        mod.render_levels = subsurf
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def box(loc, size, m, bevel=0.06):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    return obj_finish(o, m, bevel)


def sphere(loc, r, m, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(location=loc, radius=r, segments=48, ring_count=24)
    o = bpy.context.object
    o.scale = scale
    return obj_finish(o, m)


def cyl(loc, r, depth, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(location=loc, radius=r, depth=depth, rotation=rot,
                                        vertices=40)
    return obj_finish(bpy.context.object, m, 0.04)


skin = mat("skin", (0.95, 0.70, 0.55), 0.6)
red = mat("plaid", (0.78, 0.12, 0.10), 0.7)
blue = mat("jeans", (0.20, 0.30, 0.55), 0.8)
beard = mat("beard", (0.45, 0.25, 0.12), 0.9)
white = mat("white", (0.95, 0.95, 0.92), 0.4)
black = mat("black", (0.03, 0.03, 0.03), 0.3)
wood = mat("wood", (0.55, 0.33, 0.17), 0.7)
roof = mat("roof", (0.55, 0.18, 0.12), 0.6)
grass = mat("grass", (0.32, 0.55, 0.20), 0.9)
money = mat("money", (0.45, 0.70, 0.40), 0.6)
steel = mat("steel", (0.35, 0.37, 0.42), 0.35)
glass = mat("glass", (0.6, 0.8, 0.9), 0.1)

# ground
bpy.ops.mesh.primitive_plane_add(size=60)
obj_finish(bpy.context.object, grass)

# Gus (toy proportions: big head, capsule body)
for x in (-0.22, 0.22):
    cyl((x, 0, 0.35), 0.14, 0.7, blue)
    sphere((x, 0.06, 0.04), 0.13, skin, (1, 1.5, 0.5))
body = sphere((0, 0, 1.15), 0.5, red, (1, 0.8, 1.05))
for x, ang in ((-0.55, -0.5), (0.55, 0.9)):
    cyl((x, 0, 1.15), 0.12, 0.7, red, (0, ang, 0))
    sphere((x * 1.35, 0, 1.15 - 0.25 + (0.5 if ang > 0 else 0)), 0.14, skin)
head = sphere((0, 0, 2.0), 0.48, skin)
sphere((0, -0.12, 1.78), 0.36, beard, (1.05, 0.8, 0.7))
sphere((0, 0, 2.28), 0.5, red, (1, 1, 0.62))
sphere((0, 0, 2.62), 0.12, white)
for x in (-0.17, 0.17):
    sphere((x, -0.43, 2.05), 0.075, white)
    sphere((x, -0.49, 2.05), 0.04, black)

# house
box((-3.2, 3.5, 1.6), (4, 3, 3.2), wood)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=3.2, depth=1.6, location=(-3.2, 3.5, 4.0),
                                rotation=(0, 0, math.pi / 4))
obj_finish(bpy.context.object, roof, 0.05)
box((-3.2, 1.95, 0.9), (0.9, 0.12, 1.8), mat("door", (0.3, 0.17, 0.09)))
for x in (-4.5, -1.9):
    box((x, 1.95, 2.1), (0.9, 0.1, 0.8), glass, 0.02)

# printing press + cash stacks
box((2.2, 0.8, 0.7), (1.4, 1.0, 1.4), steel)
cyl((3.05, 0.8, 1.0), 0.35, 0.2, steel, (0, math.pi / 2, 0))
for i in range(6):
    for j in range(3):
        box((1.2 + j * 0.5, -0.9 - (i % 2) * 0.3, 0.06 + i * 0.12), (0.45, 0.22, 0.1), money, 0.01)

# trees
for k, (x, y) in enumerate(((-7, 8), (5, 9), (8, 6), (-9, 4), (1, 12))):
    cyl((x, y, 0.8), 0.25, 1.6, wood)
    bpy.ops.mesh.primitive_cone_add(radius1=1.4, depth=3, location=(x, y, 3), vertices=24)
    obj_finish(bpy.context.object, mat(f"tree{k}", (0.15, 0.42, 0.2), 0.8), 0.08)

# lights + world
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), 0, math.radians(30)))
sun = bpy.context.object
sun.data.energy = 4
sun.data.angle = math.radians(8)
bpy.ops.object.light_add(type="AREA", location=(3, -6, 6))
fill = bpy.context.object
fill.data.energy = 600
fill.data.size = 6
fill.rotation_euler = (math.radians(55), 0, math.radians(25))
world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.75, 0.95, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.9

# camera (9:16)
bpy.ops.object.camera_add(location=(1.2, -9.5, 3.4), rotation=(math.radians(80), 0, math.radians(6)))
cam = bpy.context.object
cam.data.lens = 30
scene.camera = cam

scene.render.resolution_x, scene.render.resolution_y = W, H
scene.render.resolution_percentage = 100
scene.render.filepath = OUT
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX" if "AgX" in [
    t.identifier for t in bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items_static] else "Filmic"

if ENGINE == "CYCLES":
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.max_bounces = 4
elif ENGINE == "EEVEE":
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    try:
        scene.eevee.taa_render_samples = SAMPLES
    except AttributeError:
        pass
else:
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.render_aa = "16"

t0 = time.time()
bpy.ops.render.render(write_still=True)
print(f"BENCH {ENGINE} {W}x{H} samples={SAMPLES}: {time.time() - t0:.1f}s per frame")
