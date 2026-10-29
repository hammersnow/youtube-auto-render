#!/usr/bin/env python3
from pathlib import Path
import json
import os
import numpy as np
import render_premium_v7 as v
import render_v7_flow_field as flow_field
import render_v7_puzzle_quality as puzzle_quality

CFG_PATH = Path("config/strategy_v7.json")
PREVIOUS_MANIFEST = Path(os.environ.get("PREVIOUS_MANIFEST", "previous_manifest.json"))

# Production registration stays in the runtime layer so the base V7 engine remains stable.
v.FAMILIES["flow_field"] = (
    lambda t, seed, frame_idx=0: flow_field.render(t, seed, frame_idx, v),
    "Which Flow Breaks the Field? 🌊 #Shorts", 9.4, 7.1,
)

# Puzzle-quality hotfixes. These override only the affected families and keep
# the proven V7 base renderer unchanged for easy rollback.
v.FAMILIES["spot_difference"] = (
    lambda t, seed, frame_idx=0: puzzle_quality.spot_difference(t, seed, frame_idx, v),
    "Spot the Moving Difference 🔎 #Shorts", 9.6, 7.25,
)
v.FAMILIES["laser_core"] = (
    lambda t, seed, frame_idx=0: puzzle_quality.laser_core(t, seed, frame_idx, v),
    "Which Laser Hits the Core? 🔺 #Shorts", 9.4, 7.1,
)


def load_config():
    if not CFG_PATH.exists():
        return None
    cfg = json.loads(CFG_PATH.read_text(encoding="utf-8"))
    if cfg.get("daily_short_count") != 3:
        raise SystemExit("V7 currently requires daily_short_count=3")
    return cfg


def load_previous_families():
    if not PREVIOUS_MANIFEST.exists():
        return set()
    try:
        m = json.loads(PREVIOUS_MANIFEST.read_text(encoding="utf-8"))
        families = {x.get("family") for x in m.get("shorts", []) if x.get("family")}
        if families:
            print("Avoiding previous manifest families:", sorted(families))
        return families
    except Exception as exc:
        print("Previous manifest ignored:", exc)
        return set()


def weighted_choice_without_replacement(rng, weights, count, avoid=None):
    avoid = set(avoid or ())
    positive = [name for name, weight in weights.items() if float(weight) > 0]
    preferred = [name for name in positive if name not in avoid]
    names = preferred if len(preferred) >= count else positive
    if len(names) < count:
        raise SystemExit("Not enough positive-weight families in strategy config")
    vals = np.array([float(weights[name]) for name in names], dtype=np.float64)
    chosen = []
    pool = names[:]
    p = vals / vals.sum()
    for _ in range(count):
        idx = int(rng.choice(len(pool), p=p))
        chosen.append(pool.pop(idx))
        vals = np.delete(vals, idx)
        if pool:
            p = vals / vals.sum()
    return chosen


def config_selection(seed):
    cfg = load_config()
    if cfg is None:
        return v.daily_selection(seed)
    day_index = int(v.DAY.strftime("%j"))
    rng = np.random.default_rng(seed + day_index * 104729)
    previous = load_previous_families()
    proven = weighted_choice_without_replacement(rng, cfg["proven_weights"], 2, previous)
    experiment = weighted_choice_without_replacement(rng, cfg["experiment_weights"], 1, previous)
    order = proven + experiment
    shift = day_index % 3
    selected = order[shift:] + order[:shift]
    print("Selected V7 families:", selected)
    return selected


def annotate_manifest(cfg):
    path = Path("outputs/latest/manifest.json")
    if not path.exists() or not cfg:
        return
    m = json.loads(path.read_text(encoding="utf-8"))
    experiments = set(cfg.get("experiment_weights", {}))
    for item in m.get("shorts", []):
        item["strategy_bucket"] = "experiment" if item.get("family") in experiments else "proven"
        item["strategy_weight"] = float((cfg.get("experiment_weights", {}) if item["strategy_bucket"] == "experiment" else cfg.get("proven_weights", {})).get(item.get("family"), 0))
        if item.get("family") in {"spot_difference", "laser_core"}:
            item["puzzle_quality_gate"] = "v2-validity-guarded"
    m["experiment_tracking"] = {"enabled": True, "policy": cfg.get("selection_policy", "2-proven-1-experiment")}
    m["puzzle_quality_gate"] = {"enabled": True, "version": "v2"}
    path.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    original = v.daily_selection
    try:
        puzzle_quality.quality_self_test()
        v.daily_selection = config_selection
        cfg = load_config()
        if cfg:
            print("Loaded V7 strategy config:", json.dumps(cfg, ensure_ascii=False))
        v.main()
        annotate_manifest(cfg)
    finally:
        v.daily_selection = original


if __name__ == "__main__":
    main()
