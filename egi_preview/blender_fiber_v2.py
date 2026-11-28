"""Original step-index fiber cutaway. Geometric ray illustration, not wave simulation.
Blender 4.5 LTS / CPU Cycles / native 1080x1920 at 30fps. R&D only.
"""
import bpy, math, os, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import time, statistics
from math import sin, cos, pi

bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene
S.render.engine='CYCLES'
S.cycles.device='CPU'
S.cycles.samples=32
S.cycles.use_adaptive_sampling=True
S.cycles.adaptive_threshold=.035
S.cycles.use_denoising=True
S.cycles.denoiser='OPENIMAGEDENOISE'
S.cycles.denoising_input_passes='RGB_ALBEDO_NORMAL'
S.render.use_persistent_data=True
bpy.context.preferences.edit.keyframe_new_interpolation_type='LINEAR'
S.cycles.max_bounces=4
S.render.resolution_x=1080
S.render.resolution_y=1920
S.render.resolution_percentage=100
FPS=30
N=24*FPS
S.render.fps=FPS
S.frame_start=1
S.frame_end=N
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


# Original connected optical communication bench, from source to receiver.
jacket=mat('Protective orange jacket',(.85,.23,.045),0,.32)
clad=mat('Lower index glass cut section',(.12,.48,.72),.25,.24)
core=mat('Higher index glass cut section',(.11,.32,.40),.15,.28)
gold=mat('Gold contacts',(.82,.54,.13),.85,.25)
signal=mat('Optical pulse',(.14,.88,1),0,.2,8)
ray=mat('Illustrated guided ray',(.06,.75,1),0,.32,4.5)
interface=mat('Core boundary teaching highlight',(.15,.64,.80),.12,.27,.4)
lensmat=mat('Lens schematic',(.24,.62,.76),.25,.14)
z=.95
cube('Backdrop',(0,0,-.82),(17,24,.22),bg,0)
cube('Machined optical bench',(0,0,-.42),(5.8,13,.48),case,.18)
for y in (-5.7,5.7):
    for x in (-2.55,2.55):cyl('Bench fastener',(x,y,-.12),.12,.12,steel,verts=24)
def ring_y(name,y,r0,r1,length,m,start=0,end=2*pi,n=72):
    # Ring section, axis Y; top half removed to reveal the optical path.
    vs=[];fs=[]
    for i in range(n+1):
        a=start+(end-start)*i/n
        for rr,yy in ((r0,y-length/2),(r1,y-length/2),(r1,y+length/2),(r0,y+length/2)):
            vs.append((rr*cos(a),yy,z+rr*sin(a)))
    for i in range(n):
        k=4*i
        for j in range(4):fs.append((k+j,k+(j+1)%4,k+4+(j+1)%4,k+4+j))
    fs.extend([(0,1,2,3),(4*n+3,4*n+2,4*n+1,4*n)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],fs);mesh.update()
    o=bpy.data.objects.new(name,mesh);S.collection.objects.link(o);o.data.materials.append(m)
    import bmesh
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
    return o
def cy(name,y,r,depth,m):
    return cyl(name,(0,y,z),r,depth,m,(pi/2,0,0),64)
# Two visibly distinct circuit modules and their optical ferrules.
for y,side in [(4.85,'TX'),(-4.85,'RX')]:
    cube(side+' aluminum base',(0,y,.08),(3.7,2.05,.38),steel,.12)
    cube(side+' circuit board',(0,y,.34),(3.44,1.84,.12),board,.08)
    for j in range(8):
        x=-1.25+.35*j
        cube(side+' SMD pad',(x,y+.65,.43),(.19,.12,.055),gold,.016)
        cube(side+' SMD component',(x,y-.63,.49),(.19,.24,.13),rubber,.022)
        for k in (-1,1):
            cube(side+' SMD terminal',(x,y-.63+k*.115,.46),(.19,.05,.045),steel,.005)
    for x in (-1.36,1.36):
        for dy in (-.69,.69):cyl(side+' screw',(x,y+dy,.45),.065,.08,steel,verts=16)
    for j in range(4):
        x=-1.18+j*.77
        tube(side+' PCB trace',[(x,y+.55,.425),(x,y+.25,.425),(x*.44,y+.25,.425),(x*.44,y,.425)],gold,.018)
    cube(side+' device enclosure',(0,y,.62),(1.16,.75,.48),darksteel,.075)
    cy(side+' optical package',y,.44,.50,steel)
    cy(side+' optical face',y+(-.29 if y>0 else .29),.26,.08,lensmat)
    cy(side+' luminous active area',y+(-.34 if y>0 else .34),.09,.035,signal if y>0 else lensmat)
for y in (3.89,-3.89):
    ring_y('Machined connector ferrule',y,.30,.66,.80,steel)
    ring_y('Connector strain relief',y+(.47 if y>0 else -.47),.27,.71,.25,rubber)
    for k in range(5):
        ring_y('Connector rib',y-.31+k*.155,.64,.72,.08,case)
# Step-index longitudinal cutaway. The core/cladding boundary is at x=+/- .24.
# Outer jacket is a separate protective layer, not a reflecting mirror.
ring_y('Outer protective jacket',0,.60,.76,6.90,jacket,pi,2*pi)
ring_y('Lower-index cladding',0,.24,.60,7.24,clad,pi,2*pi)
ring_y('Higher-index core',0,0,.24,7.40,core,pi,2*pi)
# Thin illuminated boundary rails make the two cut surfaces easy to identify.
for x in (-.24,.24):
    tube('Core interface',[(x,3.7,z),(x,-3.7,z)],interface,.023)
for x in (-.60,.60):
    tube('Cladding cut edge',[(x,3.45,z),(x,-3.45,z)],steel,.019)
for y in (2.8,0,-2.8):
    for x in (-1.22,1.22):
        cube('Cable saddle',(x,y,-.02),(.67,.50,.28),darksteel,.07)
        cyl('Saddle fastener',(x,y,.16),.085,.09,steel,verts=16)
# A meridional ray in a straight step-index fiber. n1=1.48, n2=1.46.
# slope = 0.15 -> incidence ~81.47 degrees > critical ~80.57 degrees.
n1,n2=1.48,1.46
slope=.15
critical=math.degrees(math.asin(n2/n1))
incidence=90-math.degrees(math.atan(slope))
assert incidence>critical
pts=[(0,3.70,z+.012),(.24,2.10,z+.012),(-.24,-1.10,z+.012),(.15,-3.70,z+.012)]
# Endpoint transitions to module faces are simplified coupling, not a fiber model.
route=[(0,4.51,z+.012)]+pts+[(0,-4.51,z+.012)]
rayparts=[]
for a,b in zip(pts,pts[1:]):
    o=tube('Guided ray segment',[a,b],ray,.043);rayparts.append(o)
    for f in (1,240,241,N):
        o.hide_render=f<241;o.keyframe_insert(data_path='hide_render',frame=f)
def along(points,t):
    vs=[Vector(x) for x in points];ls=[(b-a).length for a,b in zip(vs,vs[1:])]
    d=max(0,min(1,t))*sum(ls)
    for a,b,l in zip(vs,vs[1:],ls):
        if d<=l:return a.lerp(b,d/l)
        d-=l
    return vs[-1]
def travel_fraction(points,i):
    ls=[(Vector(b)-Vector(a)).length for a,b in zip(points,points[1:])]
    return sum(ls[:i])/sum(ls)
# Slow schematic teaching pulse, then four information pulses; arrivals and reflections share one timeline.
DEMO_START,DEMO_TIME=8.15,4.65
DATA_START,DATA_TIME,SPACING=12.3,5.7,.82
def reflection_strength(t,j):
    hits=[DEMO_START+DEMO_TIME*travel_fraction(pts,j+1)]
    hits.extend(DATA_START+i*SPACING+DATA_TIME*travel_fraction(route,j+2) for i in range(4))
    return max(math.exp(-((t-hit)/.22)**2) for hit in hits)
for j,p in enumerate(pts[1:-1]):
    o=sphere('Reflection point',p,.090,signal)
    for f in range(1,N+1):
        t=(f-1)/FPS
        q=reflection_strength(t,j)
        o.scale=(q,q,q);o.keyframe_insert(data_path='scale',frame=f)
demo=sphere('Slow teaching light pulse',pts[0],.092,signal)
for f in range(1,N+1):
    t=(f-1)/FPS
    q=(t-DEMO_START)/DEMO_TIME
    demo.location=along(pts,q)
    demo.scale=(1,1.35,1) if 0<=q<=1 else (0,0,0)
    demo.keyframe_insert(data_path='location',frame=f)
    demo.keyframe_insert(data_path='scale',frame=f)
for i in range(4):
    pulse=sphere('Optical data pulse '+str(i),route[0],.093,signal)
    for f in range(1,N+1):
        t=(f-1)/FPS
        q=(t-DATA_START-i*SPACING)/DATA_TIME
        if 0<=q<=1:
            pulse.location=along(route,q);pulse.scale=(1,1.5,1)
        elif i==0 and 0<=t<4:
            pulse.location=along(route,min(.12,(t%1.2)*.10));pulse.scale=(.8,.8,.8)
        else:pulse.scale=(0,0,0)
        pulse.keyframe_insert(data_path='location',frame=f)
        pulse.keyframe_insert(data_path='scale',frame=f)
# Keep the last completed receiver state visible during the closing overview.
for i in range(4):
    x=-.87+i*.58
    o=cube('Receiver output indicator',(x,-5.22,.51),(.28,.19,.09),green,.035)
    for f in range(1,N+1):
        t=(f-1)/FPS
        q=1 if t>=DATA_START+DATA_TIME+i*SPACING else .12
        o.scale=(q,1,1);o.keyframe_insert(data_path='scale',frame=f)
# Studio framing: continuous moves within the same apparatus.
def light(name,loc,energy,size,color):
    d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color
    o=bpy.data.objects.new(name,d);S.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
light('Cool key',(-6,5,11),2300,7,(.92,.96,1))
light('Warm fill',(6,-2,7),1600,6,(1,.82,.64))
light('Blue rim',(0,8,5),1800,5,(.60,.82,1))
d=bpy.data.cameras.new('Studio camera');cam=bpy.data.objects.new('Studio camera',d);S.collection.objects.link(cam);S.camera=cam
d.type='ORTHO';d.sensor_fit='VERTICAL'
shots=[(0,(0,4.15,.5),8.5),(4,(0,2.20,.65),6.6),(8,(0,.48,.65),5.9),(13,(0,-.7,.65),11.2),(17,(0,-4.15,.5),8.5),(21,(0,0,.5),17.4)]
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def shot_index(t):return max(i for i,(a,*_) in enumerate(shots) if a<=t)
def camera_pose(t):
    i=shot_index(t);start,p,scale=shots[i]
    if i and t-start<.72:
        _,prev,old=shots[i-1];q=smooth((t-start)/.72)
        p=Vector(prev).lerp(Vector(p),q);scale=old+(scale-old)*q
    else:p=Vector(p)
    cam.location=p+Vector((1.10+.07*sin(t*.48),-2.5,24))
    cam.rotation_euler=(p-cam.location).to_track_quat('-Z','Y').to_euler();d.ortho_scale=scale
for f in range(1,N+1):
    camera_pose((f-1)/FPS)
    cam.keyframe_insert(data_path='location',frame=f);cam.keyframe_insert(data_path='rotation_euler',frame=f);d.keyframe_insert(data_path='ortho_scale',frame=f)
anchors=[
    [('LASER DIODE',(0,4.51,z)),('OPTICAL CONNECTOR',(.50,3.9,z))],
    [('GLASS CORE',(.03,2.0,z)),('CLADDING',(.45,2.6,z))],
    [('CORE INTERFACE',(.24,2.10,z)),('GUIDED RAY',(-.14,-.44,z))],
    [('LIGHT PULSES',(0,-.7,z)),('PROTECTIVE JACKET',(.72,-2.6,z))],
    [('PHOTODIODE',(0,-4.51,z)),('ELECTRICAL OUTPUT',(.29,-5.22,.51))],
    [('LIGHT IN',(0,4.51,z)),('DATA OUT',(0,-4.51,z))]
]
focus=[
    [(-1.9,3.25,.0),(1.9,5.9,1.6)],
    [(-.9,1.2,.1),(.9,3.4,1.5)],
    [(-.85,-1.4,.1),(.85,2.6,1.5)],
    [(-.95,-3.7,.1),(.95,3.7,1.5)],
    [(-1.9,-5.9,.0),(1.9,-3.25,1.6)],
    [(-2.0,-5.9,.0),(2.0,5.9,1.6)]
]
def project(p):
    q=world_to_camera_view(S,cam,Vector(p));return [round(q.x*1080,2),round((1-q.y)*1920,2)]
os.makedirs('frames',exist_ok=True);os.makedirs('preview',exist_ok=True)
data={}
for f in range(1,N+1):
    t=(f-1)/FPS;S.frame_set(f);bpy.context.view_layer.update();i=shot_index(t)
    lo,hi=focus[i];cs=[project((x,y,z)) for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])]
    labels=[{'text':name,'point':project(p)} for name,p in anchors[i]]
    settled=i==0 or t-shots[i][0]>=.72
    flashes=[{'point':project(p),'strength':reflection_strength(t,j)} for j,p in enumerate(pts[1:-1]) if reflection_strength(t,j)>.04]
    data[str(f)]={'t':t,'shot':i,'settled':settled,'labels':labels,'flashes':flashes,'focus':[min(p[0] for p in cs),min(p[1] for p in cs),max(p[0] for p in cs),max(p[1] for p in cs)]}
    if settled:
        for a in labels:
            x,y=a['point'];assert 24<x<1056 and 180<y<1530,(f,a)
with open('preview/anchors.json','w') as f:json.dump(data,f)
assert sum(o.type=='MESH' for o in S.objects)>100
assert all(len(o.data.vertices)>0 and len(o.data.polygons)>0 for o in S.objects if o.type=='MESH')
with open('preview/geometry.json','w') as f:json.dump({'blender':bpy.app.version_string,'meshes':sum(o.type=='MESH' for o in S.objects),'objects':len(S.objects),'native':[1080,1920,FPS],'frames':N,'samples':S.cycles.samples,'denoise':S.cycles.denoiser,'critical_deg':critical,'incidence_deg':incidence,'scope':'schematic step-index meridional ray; no wave/velocity simulation'},f,indent=2)
S.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('preview/egi_fiber_v2.blend'))
print('SCENE_PREPARED: native 1080x1920, 30fps, 32 samples, OIDN')
