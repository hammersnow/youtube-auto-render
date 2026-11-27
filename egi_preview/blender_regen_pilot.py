"""Original schematic 3D comparison: not a vehicle design or electrical simulation.
Blender 4.x-compatible API, CPU Cycles. 12 native fps at 540x960 for R&D only.
"""
import bpy, math, os, json
from mathutils import Vector
from math import sin, cos, pi

bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene
S.render.engine='CYCLES'
S.cycles.device='CPU'
S.cycles.samples=8
# Ubuntu packaged Cycles was built without OpenImageDenoiser.
S.cycles.use_denoising=False
S.cycles.max_bounces=4
S.render.resolution_x=540
S.render.resolution_y=960
S.render.resolution_percentage=100
S.render.fps=12
S.frame_start=1
S.frame_end=192
S.render.image_settings.file_format='PNG'
S.render.filepath=os.path.abspath('frames/f_')
S.world=bpy.data.worlds.new('Studio')
S.world.use_nodes=True
S.world.node_tree.nodes.get('Background').inputs[0].default_value=(.065,.09,.13,1)
S.world.node_tree.nodes.get('Background').inputs[1].default_value=.4
S.view_settings.view_transform='AgX'

def mat(name,c,metal=0,rough=.35,em=0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    m.diffuse_color=(*c,1)
    n=m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value=(*c,1)
    n.inputs['Metallic'].default_value=metal
    n.inputs['Roughness'].default_value=rough
    if em:
        n.inputs['Emission Color'].default_value=(*c,1)
        n.inputs['Emission Strength'].default_value=em
    return m
steel=mat('Brushed alloy',(.53,.63,.74),1,.29)
darksteel=mat('Dark alloy',(.20,.27,.35),1,.35)
rubber=mat('Tyre rubber',(.023,.033,.047),0,.67)
copper=mat('Copper winding',(.79,.29,.075),1,.3)
board=mat('PCB',(.025,.16,.15),0,.49)
case=mat('Anodised blue',(.06,.13,.22),0,.38)
bg=mat('Studio navy',(.018,.038,.065),0,.6)
red=mat('North magnet',(.65,.045,.06),0,.29)
blue=mat('South magnet',(.025,.34,.63),0,.29)
green=mat('Charge indicator',(.05,.8,.35),0,.3,1.8)
phase=[mat('Phase A',(.05,.62,.82),0,.3,.25),mat('Phase B',(.86,.36,.06),0,.3,.25),mat('Phase C',(.41,.18,.79),0,.3,.25)]
glow=[mat('Signal '+str(i),c,0,.3,2) for i,c in enumerate([(.05,.9,1), (1,.5,.08),(.65,.3,1)])]

def use(obj,name,m):
    obj.name=name; obj.data.materials.append(m)
    return obj
def bevel(obj,w=.05,n=2):
    mod=obj.modifiers.new('Machined edges','BEVEL');mod.width=w;mod.segments=n
    return obj
def cube(name,loc,dim,m,w=.04):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    use(o,name,m)
    if w: bevel(o,w)
    return o
def cyl(name,loc,r,depth,m,rot=None,verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc,rotation=rot or (0,0,0))
    o=use(bpy.context.object,name,m);bevel(o,.018)
    for f in o.data.polygons:
        if len(f.vertices)==4: f.use_smooth=True
    return o
def torus(name,loc,r,minor,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(location=loc,rotation=rot,major_radius=r,minor_radius=minor,major_segments=48,minor_segments=10)
    o=use(bpy.context.object,name,m)
    for f in o.data.polygons:f.use_smooth=True
    return o
def annulus(name,center,r0,r1,z0,z1,m,start=0,end=2*pi,n=72):
    verts=[];faces=[]
    for k in range(n+1):
        a=start+(end-start)*k/n
        for r,z in [(r0,z0),(r1,z0),(r1,z1),(r0,z1)]:
            verts.append((center[0]+r*cos(a),center[1]+r*sin(a),z))
    for k in range(n):
        i=4*k
        for j in range(4):faces.append((i+j,i+(j+1)%4,i+4+(j+1)%4,i+4+j))
    faces.extend([(3,2,1,0),(4*n,4*n+1,4*n+2,4*n+3)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);S.collection.objects.link(obj);obj.data.materials.append(m)
    # Normalize winding; caps and curved faces remain explicit.
    import bmesh
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
    return obj
def tube(name,pts,m,r=.055):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=8;c.bevel_depth=r;c.bevel_resolution=3
    p=c.splines.new('POLY');p.points.add(len(pts)-1)
    for q,xyz in zip(p.points,pts):q.co=(*xyz,1)
    o=bpy.data.objects.new(name,c);S.collection.objects.link(o);o.data.materials.append(m);return o
def empty(name,loc):
    o=bpy.data.objects.new(name,None);S.collection.objects.link(o);o.location=loc;return o
def parent_keep(o,p):
    # Update matrices before parenting: retain the original world transform.
    bpy.context.view_layer.update()
    world=o.matrix_world.copy();o.parent=p;o.matrix_world=world
def radial_point(x,y,r,a,z):return (x+r*cos(a),y+r*sin(a),z)
def sphere(name,loc,r,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=r,location=loc)
    return use(bpy.context.object,name,m)

# One continuous cutaway test bench, not successive slides.
cube('Backdrop',(0,0,-.74),(17,24,.2),bg,.0)
cube('Machined plinth',(0,0,-.38),(7.6,11,.42),case,.16)
for x in (-3.4,3.4):
    for y in (-5,5):
        cyl('Plinth screw',(x,y,-.1),.08,.06,steel,verts=16)
wx,wy=-1.92,2.75;mx,my=1.55,2.75
wheel=empty('Wheel rotation',(wx,wy,.7))
parent_keep(torus('Rubber tyre',(wx,wy,.7),1.04,.24,rubber),wheel)
parent_keep(cyl('Alloy rim',(wx,wy,.7),.88,.55,darksteel),wheel)
parent_keep(annulus('Rim lip',(wx,wy),.74,.88,.96,1.04,steel),wheel)
for i in range(8):
    a=i*2*pi/8
    o=cube('Alloy spoke',radial_point(wx,wy,.49,a,1.025),(.79,.13,.13),steel)
    o.rotation_euler.z=a;parent_keep(o,wheel)
for i in range(32):
    a=i*2*pi/32
    o=cube('Tread block',radial_point(wx,wy,1.23,a,.79),(.12,.11,.34),rubber,.012)
    o.rotation_euler.z=a;parent_keep(o,wheel)
parent_keep(cyl('Wheel hub',(wx,wy,1.06),.26,.26,steel),wheel)
# Parallel-axis schematic coupling: a visible gear/belt path links the two axes.
for x in (wx,mx):
    cyl('Shaft bearing',(x,wy,.30),.31,.28,steel)
for y in (wy-.33,wy+.33):
    tube('Transmission belt',[(wx,y,.18),(mx,y,.18)],rubber,.11)
# Motor: stator backplate and incomplete side shell reveal wound teeth and rotor.
cyl('Motor back plate',(mx,my,.12),1.40,.32,darksteel)
annulus('Motor shell cutaway',(mx,my),1.29,1.45,.19,.91,steel,start=0.12*pi,end=1.55*pi,n=56)
annulus('Stator iron',(mx,my),1.03,1.27,.25,.73,darksteel)
for i in range(12):
    a=i*2*pi/12
    p=radial_point(mx,my,1.03,a,.61)
    o=cube('Stator tooth',p,(.33,.24,.48),steel,.018);o.rotation_euler.z=a
    # Visible copper winding turns around each tooth.
    for j in range(4):
        p=radial_point(mx,my,1.03+(j-1.5)*.065,a,.61)
        torus('Copper turn',p,.16,.032,copper,(0,pi/2,a))
    cyl('Housing fastener',radial_point(mx,my,1.36,a,.94),.055,.08,darksteel,verts=12)
rotor=empty('Rotor rotation',(mx,my,.49))
parent_keep(cyl('Rotor laminated core',(mx,my,.49),.79,.57,darksteel),rotor)
for i in range(6):
    a=i*2*pi/6
    o=cube('Permanent magnet',radial_point(mx,my,.61,a,.83),(.26,.40,.12),red if i%2==0 else blue,.025)
    o.rotation_euler.z=a;parent_keep(o,rotor)
parent_keep(cyl('Rotor shaft',(mx,my,.90),.20,.42,steel),rotor)

# Power-electronics board, six simplified switching packages, visible heat-sink fins.
iy=-.35;by=-3.45
cube('Inverter heat sink',(0,iy,.04),(4.9,1.50,.38),steel)
cube('Inverter PCB',(0,iy,.30),(4.7,1.34,.12),board)
for i in range(6):
    x=-1.8+.57*i
    cube('Switch package',(x,iy,.49),(.43,.55,.26),rubber,.03)
    for j in range(3):
        cube('Switch pin',(x+(j-1)*.11,iy-.34,.37),(.05,.21,.055),steel,.006)
for i in range(8):
    cube('Cooling fin',(1.56+(i%4)*.15,iy+(.23 if i<4 else -.23),.49),(.085,.39,.32),steel,.012)
for i in range(3):
    cyl('DC link capacitor',(1.21+i*.38,iy+.4,.55),.14,.36,darksteel)
# Battery module with actual 3D individual cells and bus bars.
cube('Battery tray',(0,by,.09),(4.9,1.85,.5),darksteel)
for i in range(6):
    x=-1.82+i*.73
    cube('Battery cell',(x,by,.57),(.60,1.25,.56),case,.07)
    cyl('Cell terminal +',(x,by+.42,.91),.09,.10,copper)
    cyl('Cell terminal -',(x,by-.42,.91),.09,.10,steel)
    if i<5:
        cube('Bus bar',(x+.365,by+.42,.99),(.76,.10,.05),copper,.015)
ind=[]
for i in range(6):
    x=-1.82+i*.73
    o=cube('Illustrative charge display',(x,by-.18,.87),(.38,.12,.045),green,.01)
    ind.append(o)
# Three AC routes are separated in depth and never lie on top of a caption.
paths=[]
for i in range(3):
    x=mx+(i-1)*.23
    pts=[(x,my-1.33,.57),(x,1.10,.57),(-1.8+i*.57,1.10-.19*i,.57),(-1.8+i*.57,iy+.69,.49)]
    paths.append(pts);tube('Three-phase lead '+str(i),pts,phase[i],.052)
dcpath=[(2.28,iy-.50,.48),(2.7,-1.45,.48),(2.7,-2.4,.48),(2.20,by+.77,.50)]
tube('DC positive',dcpath,phase[1],.065)
tube('DC return',[(2.02,iy-.55,.42),(2.4,-1.52,.42),(2.4,-2.4,.42),(1.92,by+.8,.48)],darksteel,.065)

def along(pts,t):
    vs=[Vector(x) for x in pts];lens=[(b-a).length for a,b in zip(vs,vs[1:])]
    d=max(0,min(1,t))*sum(lens)
    for a,b,l in zip(vs,vs[1:],lens):
        if d<=l:return a.lerp(b,d/l)
        d-=l
    return vs[-1]
def linear_keyframes(o):
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves:
            for p in fc.keyframe_points:p.interpolation='LINEAR'
# Integrate decreasing angular speed, then keyframes deterministic at each native frame.
for f in range(1,193):
    t=(f-1)/12
    if t<=3:turns=1.0*t
    else:
        dt=t-3;turns=3+dt-(.75/26)*dt*dt
    for o in (wheel,rotor):
        o.rotation_euler.z=-2*pi*turns
        o.keyframe_insert(data_path='rotation_euler',frame=f)
for o in (wheel,rotor):linear_keyframes(o)
# Moving luminous energy indicators (schematic, not charge-carrier velocity).
for i,pts in enumerate(paths):
    o=sphere('AC energy pulse '+str(i),pts[0],.083,glow[i])
    for f in range(1,193):
        t=(f-1)/12
        o.location=along(pts,((t*1.25+i/3)%1))
        o.scale=(1,1,1) if t>=6 else (0,0,0)
        o.keyframe_insert(data_path='location',frame=f);o.keyframe_insert(data_path='scale',frame=f)
    linear_keyframes(o)
o=sphere('DC energy pulse',dcpath[0],.09,green)
for f in range(1,193):
    t=(f-1)/12
    o.location=along(dcpath,(t*1.15)%1)
    o.scale=(1,1,1) if t>=10 else (0,0,0)
    o.keyframe_insert(data_path='location',frame=f);o.keyframe_insert(data_path='scale',frame=f)
linear_keyframes(o)
for i,o in enumerate(ind):
    for f in (1,145+i*3,168+i*3,192):
        s=.25 if f<168+i*3 else 1
        o.scale=(s,1,1);o.keyframe_insert(data_path='scale',frame=f)
# Studio area-light rig. Camera motion stays within the same scene.
def light(name,loc,energy,size,color):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=color
    obj=bpy.data.objects.new(name,data);S.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(-obj.location).to_track_quat('-Z','Y').to_euler()
light('Key',(-6,5,11),1700,7,(.82,.9,1))
light('Warm fill',(6,-2,7),1100,6,(1,.70,.48))
light('Rim',(0,8,5),1500,5,(.48,.75,1))
d=bpy.data.cameras.new('Studio camera');cam=bpy.data.objects.new('Studio camera',d);S.collection.objects.link(cam);S.camera=cam
d.type='ORTHO'
for f,loc,target,scale in [(1,(2.8,-3.6,24),(0,0,0),15.9),(36,(2.1,-2.8,24),(0,.25,0),15.3),(72,(1.2,-2.4,24),(0,.2,0),15.3),(120,(.5,-1.6,24),(0,-.15,0),15.3),(156,(-.7,-1.4,24),(0,-.25,0),15.3),(192,(1.6,-2.8,24),(0,0,0),15.9)]:
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=scale
    cam.keyframe_insert(data_path='location',frame=f);cam.keyframe_insert(data_path='rotation_euler',frame=f);d.keyframe_insert(data_path='ortho_scale',frame=f)
# Geometry sanity, not a collision/physical validation.
assert len([o for o in S.objects if o.type=='MESH'])>100
assert all(len(o.data.vertices)>0 and len(o.data.polygons)>0 for o in S.objects if o.type=='MESH')
os.makedirs('frames',exist_ok=True);os.makedirs('preview',exist_ok=True)
with open('preview/geometry.json','w') as f:json.dump({'blender':bpy.app.version_string,'meshes':sum(o.type=='MESH' for o in S.objects),'objects':len(S.objects),'native':[540,960,12],'frames':192,'scope':'geometry presence only; visual and physical QA pending'},f,indent=2)
S.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('preview/egi_regen_scene.blend'))
bpy.ops.render.render(animation=True)
