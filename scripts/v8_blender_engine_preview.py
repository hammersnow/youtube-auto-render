#!/usr/bin/env python3
"""V8 Blender CPU proof-of-concept: original schematic 3D four-stroke engine.

No assets, internet access, YouTube credentials, or production writes.
Blender 4.0+ (bpy) with Cycles CPU. Real 3D meshes, not a sprite/video filter.
The gas particles are illustrative paths, NOT CFD.
Mechanics: crank 720 degrees in one four-stroke cycle; cam / valves 360 degrees.
"""
import bpy
import math
import sys
import argparse
from mathutils import Vector

parser = argparse.ArgumentParser()
parser.add_argument("--output", default="outputs/v8_blender_preview/frames")
parser.add_argument("--width", type=int, default=360)
parser.add_argument("--height", type=int, default=640)
parser.add_argument("--fps", type=int, default=12)
parser.add_argument("--seconds", type=float, default=6.0)
parser.add_argument("--samples", type=int, default=12)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = args.samples
scene.cycles.use_denoising = False
scene.render.resolution_x = args.width
scene.render.resolution_y = args.height
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = args.output
scene.render.fps = args.fps
scene.render.fps_base = 1
scene.frame_start = 1
scene.frame_end = max(4, round(args.fps * args.seconds))
scene.render.threads_mode = "FIXED"
scene.render.threads = 2
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "Medium High Contrast"
scene.render.image_settings.color_mode = "RGBA"
scene.world.color = (0.018, 0.03, 0.07)
scene.render.use_file_extension = True
scene.camera = None

def mat(name, rgba, metallic=0, roughness=.3, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = rgba
        bsdf.inputs["Emission Strength"].default_value = emission
    return m

titanium = mat("Brushed titanium", (.28, .39, .48, 1), .75, .28)
dark = mat("Engine iron", (.08, .12, .17, 1), .75, .36)
gold = mat("Crank warm metal", (.94, .54, .13, 1), .55, .25)
piston_mat = mat("Piston aluminum", (.75, .85, .93, 1), .72, .17)
blue = mat("Intake electric blue", (.05, .62, 1, 1), .25, .24, 1.8)
red = mat("Exhaust hot orange", (1, .19, .055, 1), .2, .28, 1.5)
spark = mat("Ignition yellow", (1, .77, .16, 1), .0, .17, 2.0)
lime = mat("Valves polished green", (.24, .94, .56, 1), .48, .25)

def assign(obj, material):
    obj.data.materials.append(material)
    return obj

def cube(name, loc, scale, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new("Smooth bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        o.modifiers.new("Weighted normal", "WEIGHTED_NORMAL")
    assign(o, material)
    return o

def sphere(name, loc, radius, material, segments=16, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=loc)
    o = bpy.context.object
    o.name = name
    bpy.ops.object.shade_smooth()
    assign(o, material)
    return o

def cyl(name, loc, radius, depth, material, vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    bpy.ops.object.shade_smooth()
    assign(o, material)
    return o

def link(name, a, b, radius, material):
    a, b = Vector(a), Vector(b)
    d = b - a
    o = cyl(name, (a+b)/2, radius, max(.005, d.length), material, vertices=12)
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return o

def put_link(o, a, b):
    a, b = Vector(a), Vector(b)
    d = b - a
    o.location = (a+b)/2
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    # Cylinder was created with 1-unit depth, scaling length ratio is safe.
    o.scale.z = d.length / o.dimensions.z if o.dimensions.z else 1

def path(name, pts, material, radius=.04):
    curve = bpy.data.curves.new(name + " curve", type="CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    spline.points.add(len(pts)-1)
    for p, xyz in zip(spline.points, pts):
        p.co = tuple(xyz) + (1.0,)
    o = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(o)
    assign(o, material)
    return o

# Stationary engineering geometry: cylinder has NO front wall, so all motion remains legible.
# Back shell spans semicircle y>0; viewer camera y<0.
r_shell = .63
verts, faces = [], []
for idx in range(27):
    a = math.pi * idx / 26
    x,y = r_shell * math.cos(a), r_shell * math.sin(a)
    verts.extend([(x,y,.32),(x,y,1.83)])
for idx in range(26):
    j = 2 * idx
    faces.append((j,j+2,j+3,j+1))
mesh = bpy.data.meshes.new("Cutaway cylinder geometry")
mesh.from_pydata(verts,[],faces)
mesh.update()
shell = bpy.data.objects.new("Half-cylinder cutaway shell", mesh)
bpy.context.collection.objects.link(shell)
assign(shell, dark)

for x in (-.66, .66):
    cube("Open front edge of cylinder", (x,-.03,1.08),(.046,.08,1.52), titanium, .012)
for z in (.35,1.81):
    path("Cylinder rim",[(r_shell*math.cos(a*math.pi/28),r_shell*math.sin(a*math.pi/28),z) for a in range(29)],titanium,.025)

cube("Cutaway cylinder head", (0,.10,1.92),(1.42,.68,.16),titanium,.055)
cube("Open crankcase base", (0,.11,-.14),(1.38,.72,.18),dark,.04)
cyl("Crankshaft axis", (0,0,0), .14, .72, titanium).rotation_euler[0]=math.pi/2
cyl("Crank journal dark hub",(0,-.41,0),.19,.16,dark).rotation_euler[0]=math.pi/2

piston = cyl("Visible piston", (0,0,1.2), .51, .31, piston_mat, 40)
piston.scale.y = .91
ring_a = cyl("Piston upper ring", (0,0,1.2), .514,.022,dark,40)
ring_b = cyl("Piston lower ring", (0,0,1.2), .514,.022,dark,40)
for x, name, color in [(-.34,"INTAKE",blue),(.34,"EXHAUST",red)]:
    valve_head = cyl(name + " poppet head", (x,0,1.75), .155,.043,color,20)
    valve_stem = cyl(name + " stem",(x,0,1.96),.047,.36,titanium,14)
    if x<0:
        intake_head,intake_stem=valve_head,valve_stem
    else:
        exhaust_head,exhaust_stem=valve_head,valve_stem

# Visible outer pathways. Intake and exhaust separated by color.
path("Blue air enters via intake", [(-1.36,.14,2.18),(-.77,.14,2.18),(-.34,.14,1.94)],blue,.085)
path("Orange exhaust flows out",[(.34,.14,1.94),(.77,.14,2.18),(1.36,.14,2.18)],red,.085)
for xx,mm in [(-.32,blue),(.32,red)]:
    cyl("Valve top indicator", (xx,-.05,2.08),.075,.03,mm)

# Animated true slider crank and connecting rod, not approximated linear piston motion.
crank_radius = .42
rod_length = 1.13
rod = link("Connecting rod", (0,0,0), (0,0,rod_length), .077, gold)
arm = link("Crankshaft throw", (0,-.18,0), (.04,-.18,.4), .105, gold)
pin = sphere("Rotating crank pin", (.01,-.18,.42), .135, piston_mat, 20,12)
piston_pin = sphere("Piston pin",(0,-.22,1.2),.09,gold)
spark_flame = sphere("Ignition spark", (0,-.17,1.71), .12, spark)

air_particles = [sphere("Air packet %d"%i, (-1.30,.04,2.15), .042, blue) for i in range(7)]
gas_particles = [sphere("Exhaust packet %d"%i, (.40,.04,1.95), .044, red) for i in range(7)]
# Supporting geometry: subtle pedestal, lights, and camera.
cube("Presentation plinth", (0,.30,-.49),(2.55,1.6,.12),dark,.06)
cube("Dark rear backdrop", (0,1.55,1.0),(3.8,.08,4.6),dark,.015)

bpy.ops.object.camera_add(location=(3.6,-6.7,3.4))
camera=bpy.context.object
target=Vector((0,.12,1.05))
camera.rotation_euler=(target-camera.location).to_track_quat("-Z","Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = 4.25
scene.camera=camera

def area(name, location, power, size, color):
    bpy.ops.object.light_add(type="AREA",location=location)
    o=bpy.context.object
    o.name=name
    o.data.energy=power
    o.data.shape="DISK"
    o.data.size=size
    o.data.color=color
    o.rotation_euler=(target-o.location).to_track_quat("-Z","Y").to_euler()

area("Softbox", (1.0,-3.0,4.4),500,4.5,(.82,.91,1))
area("Orange rim",(-2.2,1.5,2.8),370,3,(1,.63,.35))
area("Blue fill", (3,1,1.6),260,3,(.42,.77,1))

def key(obj, frame, props=("location",)):
    for p in props:
        obj.keyframe_insert(data_path=p, frame=frame)

frames=scene.frame_end
for frame in range(1,frames+1):
    t=(frame-1)/max(1,frames-1)
    theta=t*(4*math.pi)
    stroke=min(3, int(t*4))
    phase=(t*4)%1
    cp=(crank_radius*math.sin(theta),-.18,crank_radius*math.cos(theta))
    z=crank_radius*math.cos(theta)+math.sqrt(rod_length**2-crank_radius**2*math.sin(theta)**2)
    piston.location.z=z
    ring_a.location.z=z+.115
    ring_b.location.z=z-.105
    piston_pin.location=(0,-.22,z)
    key(piston,frame); key(ring_a,frame); key(ring_b,frame); key(piston_pin,frame)
    # The rod cylinder was originally built with base depth L, so scale using that initial depth.
    pt0,pt1=Vector(cp),Vector((0,-.18,z))
    diff=pt1-pt0
    rod.location=(pt0+pt1)/2
    rod.rotation_euler=diff.to_track_quat("Z","Y").to_euler()
    rod.scale.z=diff.length / rod_length
    key(rod,frame,("location","rotation_euler","scale"))
    a0=Vector((0,-.18,0)); a1=Vector(cp)
    arm.location=(a0+a1)/2
    arm.rotation_euler=(a1-a0).to_track_quat("Z","Y").to_euler()
    arm.scale.z=1
    pin.location=cp
    key(arm,frame,("location","rotation_euler"))
    key(pin,frame)
    # Valve opening: intake on first stroke, exhaust on fourth. Rising/downward
    # motion is simplified; valves are closed throughout compression and power.
    intake_lift=.19*(math.sin(math.pi*phase)**2) if stroke==0 else 0
    exhaust_lift=.19*(math.sin(math.pi*phase)**2) if stroke==3 else 0
    intake_head.location.z=1.75-intake_lift
    intake_stem.location.z=1.96-intake_lift
    exhaust_head.location.z=1.75-exhaust_lift
    exhaust_stem.location.z=1.96-exhaust_lift
    for o in (intake_head,intake_stem,exhaust_head,exhaust_stem):
        key(o,frame)
    # Gas flow is illustrative. Only one stage shows each flow.
    for i,o in enumerate(air_particles):
        u=(phase+i/len(air_particles))%1
        o.location=(-1.33+1.03*u,-.08,2.16-.25*u)
        s=.9 if stroke==0 else 0.0001
        o.scale=(s,s,s)
        key(o,frame,("location","scale"))
    for i,o in enumerate(gas_particles):
        u=(phase+i/len(gas_particles))%1
        o.location=(.34+1.02*u,-.08,1.93+.24*u)
        s=.9 if stroke==3 else .0001
        o.scale=(s,s,s)
        key(o,frame,("location","scale"))
    # Flash near TDC at the start of power; no constant fake fire.
    lit=stroke==2 and phase<.20
    s=(.85+1.8*math.sin(math.pi*phase/.20)) if lit else .0001
    spark_flame.scale=(s,s,s)
    key(spark_flame,frame,("scale",))

# Linear speed between dense physical simulation keys. No extrapolated eased piston motion.
for obj in (piston,ring_a,ring_b,piston_pin,rod,arm,pin,intake_head,intake_stem,exhaust_head,exhaust_stem,spark_flame,*air_particles,*gas_particles):
    if obj.animation_data and obj.animation_data.action:
        action=obj.animation_data.action
        try:
            fcurves=action.fcurves
        except AttributeError:
            fcurves=[]
        for c in fcurves:
            for p in c.keyframe_points:
                p.interpolation="LINEAR"

bpy.ops.wm.save_as_mainfile(filepath="outputs/v8_blender_preview/engine_test.blend")
bpy.ops.render.render(animation=True)
print("V8_BLENDER_OK",frames,args.width,args.height,args.samples)
