"""EGI isolated ManimCE comparison pilot. Schematic, not a vehicle design."""
from manim import *
import numpy as np

config.pixel_width = 1080
config.pixel_height = 1920
config.frame_rate = 24
config.frame_width = 9
config.frame_height = 16
config.background_color = "#091523"

CY = "#57DFE6"
AM = "#FFC078"
GR = "#70E6AE"
STEEL = "#8199AF"
DARK = "#192E42"
WHITE = "#EEF6FB"
DIM = "#A5B6C7"
RED = "#FF7585"

def label(s, size=29, color=WHITE):
    return Text(s, font="DejaVu Sans", font_size=size, color=color)

def ring(r, color, width=5):
    return Circle(radius=r, color=color, stroke_width=width)

def plate(w,h,center,color=DARK):
    return RoundedRectangle(width=w,height=h,corner_radius=.16,
                            fill_color=color,fill_opacity=1,
                            stroke_color=STEEL,stroke_width=1.5).move_to(center)

def wire(points,color,width=4):
    return VMobject().set_points_as_corners(points).set_stroke(color,width=width)

class RegenPilot(MovingCameraScene):
    def construct(self):
        self.camera.frame.save_state()
        title=label("BRAKING THAT RECHARGES",38).move_to(UP*6.5)
        brand=label("EGI  /  CURIOSITY IN MOTION",22,CY).move_to(UP*7.13)
        foot=label("SIMPLIFIED SCHEMATIC   •   EGI",18,DIM).move_to(DOWN*7.05)
        grid=VGroup(*[Line([-4.05,y,0],[4.05,y,0],stroke_width=.6,color="#172C3D")
                      for y in np.arange(-5.8,5.8,.38)])
        deck=RoundedRectangle(width=7.65,height=9.9,corner_radius=.25,
             stroke_color="#29445B",stroke_width=1.5,
             fill_color="#102235",fill_opacity=.65).move_to(DOWN*.35)
        self.add(grid,deck,brand,title,foot)

        wc=np.array([-2.0,2.8,0])
        mc=np.array([1.37,2.8,0])
        wheel=VGroup(ring(1.21,"#3E5268",17),ring(1.04,STEEL,3),
                     Circle(.89,stroke_color="#374C5E",fill_color="#152638",fill_opacity=1))
        for k in range(12):
            a=k*TAU/12
            v=np.array([np.cos(a),np.sin(a),0])
            wheel.add(Line(.28*v,.86*v,stroke_width=7,color=STEEL))
            wheel.add(Line(1.06*v,1.19*v,stroke_width=3,color=DIM))
        wheel.add(Circle(.28,fill_color=STEEL,fill_opacity=1,stroke_color=WHITE),
                  Circle(.09,fill_color=DARK,fill_opacity=1,stroke_width=0))
        wheel.move_to(wc)
        shaft=VGroup(Line(wc+RIGHT*.26,mc,stroke_width=19,color="#3B536B"),
                     Line(wc+RIGHT*.26+UP*.045,mc+UP*.045,stroke_width=5,color=STEEL))
        housing=VGroup(Circle(1.40,fill_color="#253A50",fill_opacity=1,stroke_color=STEEL,stroke_width=4),
                       ring(1.20,"#52697B",3)).move_to(mc)
        coils=VGroup()
        for k in range(12):
            a=k*TAU/12
            p=mc+1.06*np.array([np.cos(a),np.sin(a),0])
            c=RoundedRectangle(width=.32,height=.46,corner_radius=.08,
                     stroke_color=AM,stroke_width=2,fill_color="#9D6239",fill_opacity=1)
            c.rotate(a-PI/2).move_to(p)
            coils.add(c)
            housing.add(Dot(mc+1.31*np.array([np.cos(a),np.sin(a),0]),radius=.035,color=WHITE))
        rotor=VGroup(Circle(.79,stroke_color=STEEL,stroke_width=3,
                          fill_color="#364C61",fill_opacity=1))
        for k in range(6):
            a=k*TAU/6
            p=.55*np.array([np.cos(a),np.sin(a),0])
            rotor.add(RoundedRectangle(width=.32,height=.40,corner_radius=.04,
                 stroke_width=0,fill_color=RED if k%2==0 else CY,fill_opacity=1)
                 .rotate(a-PI/2).move_to(p))
        rotor.add(Circle(.18,stroke_color=WHITE,stroke_width=2,fill_color=STEEL,fill_opacity=1))
        rotor.move_to(mc)
        self.add(shaft,wheel,housing,coils,rotor)
        self.add(label("WHEEL",24).move_to(wc+DOWN*1.55),
                 label("MOTOR CUTAWAY",24).move_to(mc+DOWN*1.65))
        # Continuous motion derives from one shared angular state.
        angle=ValueTracker(0)
        wheel0=wheel.copy()
        rotor0=rotor.copy()
        wheel.add_updater(lambda m: m.become(wheel0.copy().rotate(angle.get_value(),about_point=wc)))
        rotor.add_updater(lambda m: m.become(rotor0.copy().rotate(angle.get_value(),about_point=mc)))
        torque=CurvedArrow(mc+RIGHT*.8+UP*.9,mc+LEFT*.75+UP*.9,angle=-PI/2,color=AM,stroke_width=5)
        torque_note=label("OPPOSING TORQUE",20,AM).move_to(mc+UP*1.77)
        # The same power path remains visible throughout; no repeated slide cards.
        inv_center=np.array([.35,-.65,0])
        battery_center=np.array([.35,-3.8,0])
        inverter=plate(5.05,1.65,inv_center)
        battery=plate(5.05,1.65,battery_center)
        inv_title=label("POWER ELECTRONICS",23).move_to(inv_center+UP*.59)
        bat_title=label("BATTERY PACK",23).move_to(battery_center+UP*.59)
        phases=VGroup()
        phase_colors=[CY,AM,"#B7A7FF"]
        for i,c in enumerate(phase_colors):
            x=mc[0]+(i-1)*.24
            phases.add(wire([[x,1.5,0],[x,.68+i*.12,0],
                            [-1.47+i*.24,.68+i*.12,0],[-1.47+i*.24,.18,0]],c))
        ac=VGroup()
        for i,c in enumerate(phase_colors):
            pts=[[x,-.64+.20*np.sin(7*(x+1.63)+i*TAU/3),0]
                 for x in np.linspace(-1.63,-.35,80)]
            ac.add(wire(pts,c,2.7))
        bridge=VGroup(*[Square(.20,stroke_color=STEEL,stroke_width=2,
                     fill_color="#37536A",fill_opacity=1)
                     .move_to([.03+(k%3)*.33,-.49-(k//3)*.33,0]) for k in range(6)])
        dc=VGroup(Line([1.14,-.49,0],[2.17,-.49,0],color=GR,stroke_width=4),
                  Line([1.14,-.80,0],[2.17,-.80,0],color=GR,stroke_width=4))
        dcwire=VGroup(wire([[1.69,-1.48,0],[1.69,-2.19,0],[1.40,-2.19,0],[1.40,-2.98,0]],GR),
                      wire([[2.00,-1.48,0],[2.00,-2.39,0],[1.71,-2.39,0],[1.71,-2.98,0]],"#557C70"))
        cells=VGroup()
        fill=VGroup()
        for i in range(6):
            p=battery_center+RIGHT*((i-2.5)*.72)+DOWN*.12
            cells.add(RoundedRectangle(width=.59,height=.76,corner_radius=.06,
                    stroke_color=STEEL,stroke_width=2,fill_color="#203A48",fill_opacity=1).move_to(p))
            fill.add(Rectangle(width=.46,height=.18,stroke_width=0,
                    fill_color=GR,fill_opacity=.8).move_to(p+DOWN*.23))
        self.add(phases,inverter,inv_title,ac,bridge,dc,dcwire,battery,bat_title,cells,fill)
        self.add(label("AC",19,CY).move_to([-1.0,-1.22,0]),
                 label("DC",19,GR).move_to([1.68,-1.22,0]))
        meter=label("ENERGY RECOVERED",21,DIM).move_to(DOWN*5.05)
        bar=RoundedRectangle(width=4.45,height=.16,corner_radius=.08,
                         stroke_width=0,fill_color="#2C4254",fill_opacity=1).move_to(DOWN*5.42)
        progress=Rectangle(width=.05,height=.16,stroke_width=0,fill_color=GR,fill_opacity=1)
        progress.align_to(bar,LEFT).set_y(bar.get_y())
        self.add(meter,bar,progress)
        caption=label("Wheels are turning.",30).move_to(DOWN*6.12)
        self.add(caption)
        # 0–3: moving wheel and shaft, close shot with readable labels.
        self.play(angle.animate.set_value(-2*TAU),self.camera.frame.animate.scale(.94).shift(UP*.28),
                  run_time=3,rate_func=linear)
        # 3–6: braking torque opposes rotation; speed decreases.
        self.play(Transform(caption,label("Motor becomes a generator.",30).move_to(caption)),
                  FadeIn(torque),FadeIn(torque_note),run_time=.4)
        self.play(angle.animate.set_value(-3.5*TAU),run_time=2.6,rate_func=rush_from)
        # 6–10: light fixed stator coils in a phased sequence.
        self.play(Transform(caption,label("Rotating field induces AC.",30).move_to(caption)),
                  self.camera.frame.animate.shift(DOWN*.22),run_time=.5)
        def energize(m):
            a=angle.get_value()
            for k,c in enumerate(m):
                strength=.35+.65*abs(np.sin(a+k*TAU/12))
                c.set_fill(interpolate_color(ManimColor("#855232"),ManimColor(AM),strength),opacity=1)
        coils.add_updater(energize)
        self.play(angle.animate.set_value(-4.6*TAU),
                  LaggedStart(*[ShowPassingFlash(p.copy().set_stroke(WHITE,7),time_width=.45)
                                for p in phases],lag_ratio=.22),
                  run_time=3.5,rate_func=linear)
        # 10–13: power electronics converts AC into DC.
        self.play(Transform(caption,label("Inverter converts AC to DC.",30).move_to(caption)),
                  self.camera.frame.animate.shift(DOWN*.18),run_time=.5)
        self.play(angle.animate.set_value(-5.2*TAU),
                  LaggedStart(*[Indicate(b,color=CY,scale_factor=1.12) for b in bridge],lag_ratio=.12),
                  run_time=2.5,rate_func=linear)
        # 13–16: recovered energy enters battery; not all kinetic energy is recovered.
        self.play(Transform(caption,label("Some energy returns to the battery.",27).move_to(caption)),
                  self.camera.frame.animate.move_to(ORIGIN).scale(1/.94),run_time=.5)
        targets=[Rectangle(width=.46,height=.60,stroke_width=0,fill_color=GR,fill_opacity=.8)
                 .move_to(c.get_center()+UP*.21) for c in fill]
        targetbar=Rectangle(width=3.18,height=.16,stroke_width=0,fill_color=GR,fill_opacity=1)
        targetbar.align_to(bar,LEFT).set_y(bar.get_y())
        self.play(angle.animate.set_value(-5.55*TAU),
                  *[Transform(c,q) for c,q in zip(fill,targets)],
                  Transform(progress,targetbar),
                  ShowPassingFlash(dcwire[0].copy().set_stroke(WHITE,7),time_width=.5),
                  run_time=2.5,rate_func=linear)
        wheel.clear_updaters()
        rotor.clear_updaters()
        coils.clear_updaters()
