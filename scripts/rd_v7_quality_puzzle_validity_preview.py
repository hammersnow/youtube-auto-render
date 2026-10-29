#!/usr/bin/env python3
"""Smoke-test the production puzzle-quality hotfix without publishing anything."""
from pathlib import Path
import cv2
import numpy as np
import render_premium_v7 as v
import render_v7_puzzle_quality as quality

OUT = Path("outputs/rd_v7_quality_puzzle_validity")
OUT.mkdir(parents=True, exist_ok=True)


def save(name, frame):
    assert frame.shape == (v.H, v.W, 3)
    assert frame.dtype == np.uint8
    path = OUT / name
    assert cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 94])
    assert path.stat().st_size > 30000
    return path


def main():
    quality.quality_self_test()

    # Exercise seeds that previously could choose rotation-invariant glyphs.
    v.set_timing(9.6, 7.25)
    spot_solve = quality.spot_difference(2.35, 20261029, 70, v)
    spot_reveal = quality.spot_difference(7.55, 20261029, 226, v)

    v.set_timing(9.4, 7.10)
    laser_solve = quality.laser_core(3.40, 20261030, 102, v)
    laser_reveal = quality.laser_core(7.38, 20261030, 221, v)

    paths = [
        save("spot_solve.jpg", spot_solve),
        save("spot_reveal.jpg", spot_reveal),
        save("laser_solve.jpg", laser_solve),
        save("laser_reveal.jpg", laser_reveal),
    ]

    # Solve/reveal frames must differ materially; a no-op renderer must fail CI.
    assert float(np.mean(cv2.absdiff(spot_solve, spot_reveal))) > 4.0
    assert float(np.mean(cv2.absdiff(laser_solve, laser_reveal))) > 4.0
    print("puzzle_validity_preview=PASS")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
