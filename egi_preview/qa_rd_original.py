#!/usr/bin/env python3
"""Fast R&D render boundary and event regression tests; zero publishing access."""
from PIL import Image, ImageDraw
from egi_rd_original_20261119 import (
    W, H, DURATION, FPS, ssd, heat, progress, one_callout
)

def main():
    for t in (0, 1e-7, 0.001, 0.01, 1 / FPS, 0.2, 4.5, DURATION-1/FPS, DURATION):
        im = Image.new("RGB", (W, H), "black")
        progress(ImageDraw.Draw(im), t)
        for kind, render_frame in (("ssd", ssd), ("heat", heat)):
            frame = render_frame(t)
            assert frame.mode == "RGB" and frame.size == (W, H), (kind,t)
    try:
        im = Image.new("RGB", (W, H), "black")
        one_callout(ImageDraw.Draw(im), 1, [(0,2,"A"),(.5,1.5,"B")])
    except AssertionError:
        pass
    else:
        raise AssertionError("Overlapping explanatory callouts were not rejected")
    print("EGI_RD_BOUNDARY_QA_PASS: t=0, subpixel, transitions, last frame, exclusive callouts")

if __name__ == "__main__":
    main()
