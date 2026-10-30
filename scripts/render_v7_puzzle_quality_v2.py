#!/usr/bin/env python3
"""Human-perceptible V2 replacements for three weak V7 puzzle families."""
import math
import cv2
import numpy as np


def _smooth(x):
    x=max(0.0,min(1.0,float(x))); return x*x*(3.0-2.0*x)

# --- spot_difference_v2 ----------------------------------------------------
def _spot_motion(idx,t,bad=False):
    ph=idx*.71
    dx=9*math.sin(t*2.25+ph); dy=8*math.cos(t*1.95+ph)
    pulse=1+.06*math.sin(t*2.8+ph); rot=t*24+idx*11
    if not bad: return dx,dy,pulse,rot
    a=_smooth((t-.70)/.75)
    # Keep the opening identical, then force a sustained, phone-visible path
    # separation. Most of the anomaly is vertical so 4-column glyphs cannot
    # collide horizontally; row parity flips direction to avoid a fixed visual.
    sign=1.0 if (idx//4)%2==0 else -1.0
    dx2=26*math.sin(t*2.10+ph+.85)
    dy2=30*math.cos(t*2.55+ph-.55)+sign*55
    p2=1+.14*math.sin(t*3.25+ph+math.pi); r2=rot+38*math.sin(t*1.85+ph)
    return dx*(1-a)+dx2*a,dy*(1-a)+dy2*a,pulse*(1-a)+p2*a,rot*(1-a)+r2*a


def _spot_centers():
    l=[]; r=[]
    for row in range(4):
        for col in range(4):
            y=560+row*225; l.append((145+col*102,y)); r.append((645+col*102,y))
    return l,r


def spot_difference_v2(t,seed,frame_idx,v):
    im,accent,secondary=v.mesh_background(seed,3,t)
    im=v.header(im,"SPOT THE MOVING DIFFERENCE","One matching symbol follows a different path.")
    v.glass_panel(im,(70,355,510,1425),42,(22,27,42),.67,(160,148,112),.30)
    v.glass_panel(im,(570,355,1010,1425),42,(22,27,42),.67,(160,148,112),.30)
    left,right=_spot_centers(); rng=np.random.default_rng(seed+55)
    kinds=[int(rng.integers(0,4)) for _ in range(16)]; bad=seed%16
    for i in range(16):
        col=accent if i%3 else secondary
        a=_spot_motion(i,t,False); b=_spot_motion(i,t,i==bad)
        lx,ly=left[i]; rx,ry=right[i]
        v.draw_glyph(im,kinds[i],lx+a[0],ly+a[1],27*a[2],col,rot=a[3])
        v.draw_glyph(im,kinds[i],rx+b[0],ry+b[1],27*b[2],col,rot=b[3])
    if .6<t<v.ACTIVE_REVEAL:
        q=v.ease((t-.6)/max(.1,v.ACTIVE_REVEAL-.6)); y=int(430+880*q)
        v.glow_line(im,(92,y),(488,y),accent,2,.38); v.glow_line(im,(592,y),(988,y),accent,2,.38)
    if t>=v.ACTIVE_REVEAL:
        lx,ly=left[bad]; rx,ry=right[bad]
        for k in range(1,7):
            tt=max(0,t-.05*k); a=_spot_motion(bad,tt,False); b=_spot_motion(bad,tt,True)
            c=tuple(int(x*(.35+.08*k)) for x in (78,245,151))
            cv2.circle(im,(int(lx+a[0]),int(ly+a[1])),4+k,c,1,cv2.LINE_AA)
            cv2.circle(im,(int(rx+b[0]),int(ry+b[1])),4+k,c,1,cv2.LINE_AA)
        v.reveal_pulse(im,(rx,ry),t)
        cv2.rectangle(im,(lx-54,ly-54),(lx+54,ly+54),(95,190,220),3,cv2.LINE_AA)
        cv2.rectangle(im,(rx-58,ry-58),(rx+58,ry+58),(78,245,151),6,cv2.LINE_AA)
        im=v.footer_result(im,"RIGHT COPY TAKES A DIFFERENT PATH")
    v.timer(im,t,accent); return v.finish_frame(im,seed,frame_idx)

# --- portal_path_v2 --------------------------------------------------------
_LAYOUTS=[
 [(220,560),(520,500),(830,590),(255,1090),(575,1180),(850,1050)],
 [(250,520),(805,520),(520,700),(230,1160),(820,1170),(530,1030)],
 [(190,650),(520,500),(850,690),(310,1050),(690,1030),(520,1270)],
 [(260,580),(700,500),(850,900),(640,1210),(245,1150),(470,850)],
]


def _portal_plan(seed):
    rng=np.random.default_rng(seed+913); base=_LAYOUTS[seed%len(_LAYOUTS)]
    pts=[(x+int(rng.integers(-24,25)),y+int(rng.integers(-28,29))) for x,y in base]
    chain=list(map(int,rng.permutation(6)[:5]))
    if abs(pts[chain[1]][0]-pts[chain[0]][0])>520: chain[1],chain[2]=chain[2],chain[1]
    return pts,chain


def _portal_state(t,reveal,pts,chain):
    start=.45; hops=len(chain)-1; dur=max(.5,reveal-start-.35)/hops
    if t<=start: return chain[0],pts[chain[0]],0.0
    u=min(hops-1e-6,max(0,(t-start)/dur)); hop=int(u); local=u-hop
    src=pts[chain[hop]]; dst=pts[chain[hop+1]]
    if local<.48:
        ang=local/.48*math.tau; pos=(src[0]+26*math.cos(ang),src[1]+12*math.sin(ang)); alpha=1.0
    elif local<.64: pos=src; alpha=max(0,1-(local-.48)/.16)
    else:
        q=_smooth((local-.64)/.36); pos=(dst[0]-int(42*(1-q)),dst[1]-int(28*math.sin(math.pi*q))); alpha=q
    return chain[hop+(1 if local>=.64 else 0)],pos,alpha


def portal_path_v2(t,seed,frame_idx,v):
    im,accent,secondary=v.mesh_background(seed,2,t)
    im=v.header(im,"WHICH PORTAL DOES IT EXIT?","Track four warps — the layout changes every round.")
    v.glass_panel(im,(95,365,985,1425),48,(22,16,40),.55,(145,100,190),.30)
    pts,chain=_portal_plan(seed); colors=[accent,secondary,(255,186,84),(94,230,166),(126,154,255),(240,110,200)]
    current,orb,alpha=_portal_state(t,v.ACTIVE_REVEAL,pts,chain)
    for i,(x,y) in enumerate(pts):
        c=colors[i]; pulse=1+(.12*math.sin(t*8) if i==current and t<v.ACTIVE_REVEAL else 0)
        for rr,a in [(64,.28),(50,.5),(38,1.0)]: cv2.ellipse(im,(x,y),(int(rr*pulse),int(rr*.42*pulse)),0,0,360,c,max(2,int(5*a)),cv2.LINE_AA)
        im=v.pil_text(im,chr(65+i),(x,y+92),28,fill=(205,216,240),stroke=1)
    if t<.9:
        x,y=pts[chain[0]]; im=v.pil_text(im,"START",(x,y-92),24,fill=(78,245,151),stroke=1)
    if t<v.ACTIVE_REVEAL and alpha>.02: v.glow_circle(im,orb,23,(78,245,151),intensity=.65+.35*alpha)
    if t>=v.ACTIVE_REVEAL:
        exit_i=chain[-1]; x,y=pts[exit_i]; v.reveal_pulse(im,(x,y),t)
        cv2.ellipse(im,(x,y),(90,42),0,0,360,(78,245,151),8,cv2.LINE_AA)
        im=v.pil_text(im," → ".join(chr(65+i) for i in chain),(v.W//2,1370),30,fill=(180,244,212),stroke=2)
        im=v.footer_result(im,f"EXIT PORTAL {chr(65+exit_i)}")
    v.timer(im,t,accent); return v.finish_frame(im,seed,frame_idx)

# --- signal_core_v2 --------------------------------------------------------
def _signal_plan(seed):
    core=(850,900); good=seed%4; starts=[(145,540),(145,780),(145,1020),(145,1260)]
    ends=[(705,720),(705,840),(705,960),(705,1080)]; rng=np.random.default_rng(seed+1881); routes=[]
    for i,(sx,sy) in enumerate(starts):
        y1=sy+int(rng.integers(-80,81)); y2=sy+int(rng.integers(-105,106)); y3=int((y2+ends[i][1])/2+rng.integers(-55,56))
        routes.append([(sx,sy),(315,y1),(470,y2),(605,y3),ends[i]])
    bad=[i for i in range(4) if i!=good]; order=list(map(int,rng.permutation(3)))
    fails={bad[k]:order[k] for k in range(3)}; fails[good]=None
    return core,good,routes,fails


def signal_core_v2(t,seed,frame_idx,v):
    im,accent,secondary=v.mesh_background(seed,1,t)
    im=v.header(im,"WHICH SIGNAL REACHES THE CORE?","Each signal faces three timed gates.")
    v.glass_panel(im,(90,360,990,1430),46,(12,27,40),.57,(80,170,180),.28)
    core,good,routes,fails=_signal_plan(seed); colors=[accent,secondary,(255,190,95),(110,235,185)]
    q=_smooth((t-.55)/max(.2,v.ACTIVE_REVEAL-1.05))
    for i,pts in enumerate(routes):
        for a,b in zip(pts[:-1],pts[1:]): v.glow_line(im,a,b,(82,100,126),5,.12)
        im=v.pil_text(im,chr(65+i),(112,pts[0][1]),28,fill=(218,230,244),stroke=1); fail=fails[i]
        for g,node in enumerate(pts[1:4]):
            col=(105,128,150)
            if t>=.65 and q>=(g+1)/4.2: col=(78,245,151) if fail is None or g<fail else (110,126,145)
            cv2.circle(im,node,16,col,3,cv2.LINE_AA)
        cap=1.0 if fail is None else (fail+1)/4.0-.025; pq=min(q,cap); pos=v.poly_point(pts,pq)
        v.glow_circle(im,pos,14,colors[i],intensity=.75); v.glow_line(im,v.poly_point(pts,max(0,pq-.12)),pos,colors[i],4,.55)
        if fail is not None and q>cap+.04:
            gx,gy=pts[fail+1]; cv2.line(im,(gx-16,gy-16),(gx+16,gy+16),(70,90,120),4,cv2.LINE_AA); cv2.line(im,(gx-16,gy+16),(gx+16,gy-16),(70,90,120),4,cv2.LINE_AA)
    v.glow_circle(im,core,38,(75,241,174),core=(40,120,95),intensity=1.0); cv2.circle(im,core,68,(58,120,102),2,cv2.LINE_AA)
    end=routes[good][-1]
    if t<v.ACTIVE_REVEAL and q>.88:
        b=_smooth((q-.88)/.12); p=(int(end[0]+(core[0]-end[0])*b),int(end[1]+(core[1]-end[1])*b))
        v.glow_line(im,end,p,(78,245,151),6,.75); v.glow_circle(im,p,16,(78,245,151),intensity=.9)
    if t>=v.ACTIVE_REVEAL:
        for a,b in zip(routes[good][:-1],routes[good][1:]): v.glow_line(im,a,b,(78,245,151),9,1.0)
        v.glow_line(im,routes[good][-1],core,(78,245,151),9,1.0); v.reveal_pulse(im,core,t)
        im=v.footer_result(im,f"SIGNAL {chr(65+good)} SURVIVES ALL 3 GATES")
    v.timer(im,t,accent); return v.finish_frame(im,seed,frame_idx)


def quality_self_test():
    times=[1.55,2.25,3.05,4.10,5.20]
    for seed in range(64):
        bad=seed%16; ds=[]
        for t in times:
            a=_spot_motion(bad,t,False); b=_spot_motion(bad,t,True); ds.append(math.hypot(a[0]-b[0],a[1]-b[1]))
        assert min(ds)>=20 and max(ds)>=70 and sum(ds)/len(ds)>=45,("spot-too-subtle",seed,ds)
    sigs=set(); exits=set()
    for seed in range(32):
        pts,chain=_portal_plan(seed); assert len(chain)==5 and len(set(chain))==5
        sigs.add(tuple(chain)); exits.add(chain[-1]); assert all(150<=x<=900 and 430<=y<=1330 for x,y in pts)
    assert len(sigs)>=20 and len(exits)>=5,("portal-variety",len(sigs),exits)
    for seed in range(48):
        core,good,routes,fails=_signal_plan(seed); assert fails[good] is None
        assert sorted(v for k,v in fails.items() if k!=good)==[0,1,2]
        for i,path in enumerate(routes):
            d=math.hypot(path[-1][0]-core[0],path[-1][1]-core[1]); assert d>=140,("core-line-too-obvious",seed,i,d)
    print("puzzle_quality_v2_self_test=PASS")


if __name__=="__main__": quality_self_test()
