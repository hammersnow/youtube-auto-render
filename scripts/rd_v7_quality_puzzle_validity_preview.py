#!/usr/bin/env python3
"""Smoke-test versioned production puzzle families without publishing anything."""
from pathlib import Path
import cv2
import numpy as np
import render_premium_v7 as v
import render_v7_puzzle_quality as quality
import render_v7_puzzle_quality_v2 as v2

OUT = Path("outputs/rd_v7_quality_puzzle_validity")
OUT.mkdir(parents=True, exist_ok=True)


def save(name, frame):
    assert frame.shape == (v.H, v.W, 3)
    assert frame.dtype == np.uint8
    path = OUT / name
    assert cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 94])
    assert path.stat().st_size > 30000
    return path


def pair(name, fn, seed, duration, reveal, solve_t):
    v.set_timing(duration, reveal)
    solve = fn(solve_t, seed, int(solve_t * v.FPS), v)
    reveal_frame = fn(min(duration - .2, reveal + .35), seed, int((reveal + .35) * v.FPS), v)
    save(name + "_solve.jpg", solve)
    save(name + "_reveal.jpg", reveal_frame)
    assert float(np.mean(cv2.absdiff(solve, reveal_frame))) > 4.0
    return solve, reveal_frame


def main():
    quality.quality_self_test()
    v2.quality_self_test()

    # User-reported weak families: all must have deterministic validity tests
    # plus decodable solve/reveal previews at full production resolution.
    pair("spot_v2", v2.spot_difference_v2, 20261031, 9.6, 7.25, 2.8)
    pair("portal_v2", v2.portal_path_v2, 20261101, 9.5, 7.20, 3.8)
    pair("signal_v2", v2.signal_core_v2, 20261102, 9.5, 7.20, 4.2)
    pair("laser_v2", quality.laser_core, 20261103, 9.4, 7.10, 3.4)

    # Portal topology must visibly differ across seeds, not only change answer text.
    v.set_timing(9.5, 7.2)
    p1 = v2.portal_path_v2(3.6, 20261101, 108, v)
    p2 = v2.portal_path_v2(3.6, 20261102, 108, v)
    assert float(np.mean(cv2.absdiff(p1, p2))) > 3.0
    save("portal_v2_alt_seed.jpg", p2)

    print("puzzle_validity_preview=v3-PASS")


if __name__ == "__main__":
    main()
