#!/usr/bin/env python3
"""R&D-only laser topology audit/preview. Does not modify production renderer."""
from pathlib import Path
import math, time
import cv2
import numpy as np

W,H=540,960
OUT=Path("outputs/rd_v7_laser_topology"); OUT.mkdir(parents=True,exist_ok=True)

def plan(seed):
    rng=np.random.default_rng(seed+61102)
    core=(440,450+int(rng.integers(-55,56)))
    ys=list(map(int,rng.permutation([285,450,615])))
    good=int(rng.integers(0,3)); paths=[]
    for i,y in enumerate(ys):
        p=[(70,y)]
        for x in (180,285,380):
            p.append((x,int(np.clip(y+rng.integers(-120,121),190,720))))
        if i==good: end=core
        else:
            miss_y=int(np.clip(core[1]+(-1 if i%2 else 1)*rng.integers(125,210),160,760))
            end=(470,miss_y)
        p.append(end); paths.append(p)
    return core,good,paths

def signature(paths):
    return tuple(tuple((int(x//20),int(y//20)) for x,y in p[1:4]) for p in paths)

def draw(seed):
    core,good,paths=plan(seed)
    im=np.zeros((H,W,3),np.uint8); im[:]=(13,17,28)
    cv2.putText(im,"LASER TOPOLOGY V3 R&D",(32,65),cv2.FONT_HERSHEY_SIMPLEX,.72,(235,240,248),2,cv2.LINE_AA)
    cv2.putText(im,f"seed {seed}  |  solve-frame preview",(32,98),cv2.FONT_HERSHEY_SIMPLEX,.48,(145,165,190),1,cv2.LINE_AA)
    cv2.circle(im,core,26,(90,235,170),3,cv2.LINE_AA)
    colors=[(255,165,80),(95,205,255),(210,110,245)]
    for i,p in enumerate(paths):
        cv2.putText(im,chr(65+i),(34,p[0][1]+7),cv2.FONT_HERSHEY_SIMPLEX,.62,colors[i],2,cv2.LINE_AA)
        cv2.circle(im,p[0],7,colors[i],-1,cv2.LINE_AA)
        # Solve preview exposes interaction points, never a complete route.
        for node in p[1:4]:
            cv2.circle(im,node,13,(165,180,205),2,cv2.LINE_AA)
            cv2.line(im,(node[0]-15,node[1]+8),(node[0]+15,node[1]-8),(205,220,235),3,cv2.LINE_AA)
    cv2.putText(im,"No pre-drawn answer path",(32,875),cv2.FONT_HERSHEY_SIMPLEX,.52,(130,210,175),1,cv2.LINE_AA)
    return im

def main():
    t0=time.perf_counter(); sigs=set(); winners=set(); min_miss=1e9
    for seed in range(64):
        core,good,paths=plan(seed); sigs.add(signature(paths)); winners.add(good)
        assert len(paths)==3 and all(len(p)==5 for p in paths)
        hits=[math.hypot(p[-1][0]-core[0],p[-1][1]-core[1])<8 for p in paths]
        assert sum(hits)==1 and hits[good]
        for i,p in enumerate(paths):
            if i!=good: min_miss=min(min_miss,math.hypot(p[-1][0]-core[0],p[-1][1]-core[1]))
    assert len(sigs)>=56,("insufficient topology diversity",len(sigs))
    assert winners=={0,1,2},winners
    assert min_miss>=125,min_miss
    frames=[]
    for seed in (7,29):
        im=draw(seed); cv2.imwrite(str(OUT/f"laser_seed_{seed}_solve.png"),im); frames.append(im)
    # Short two-seed MP4 for artifact review.
    vw=cv2.VideoWriter(str(OUT/"laser_topology_two_seed.mp4"),cv2.VideoWriter_fourcc(*"mp4v"),12,(W,H))
    assert vw.isOpened()
    for im in frames:
        for _ in range(18): vw.write(im)
    vw.release()
    ms=(time.perf_counter()-t0)*1000
    print(f"laser_topology_rd=PASS unique={len(sigs)}/64 winners={sorted(winners)} min_miss={min_miss:.1f}px benchmark_ms={ms:.1f}")

if __name__=="__main__": main()
