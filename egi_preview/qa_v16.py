#!/usr/bin/env python3
"""Read-only V16 invariants and representative frame tests. Never upload."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import egi_v16_rich_resources as v16

def main():
    v16.verify_timeline()
    assert v16.W == 1080 and v16.H == 1920
    assert v16.FPS == 30 and v16.DUR == 36
    specs = v16.RESOURCE_SPECS
    assert [s['name'] for s in specs] == ['HTML', 'CSS', 'JAVASCRIPT']
    assert {s['purpose'] for s in specs} == {'STRUCTURE', 'STYLING', 'BEHAVIOR'}
    assert specs[0]['start'] < specs[1]['start'] < specs[2]['start']
    assert all(s['end'] > s['start'] for s in specs)
    for mode in ('software', 'technology'):
        for t in (1.3, 8.8, 11.4, 21.0, 24.5, 29.9, 35.0):
            frame = v16.frame(mode, t)
            assert frame.size == (1080, 1920), (mode, t, frame.size)
            assert frame.mode == 'RGB'
    assert not any(key.startswith('YOUTUBE_') for key in os.environ), 'YouTube secrets must not reach preview job'
    print('EGI_V16_QA_PASS: events exclusive, named resources, full-frame smoke, no publishing secrets')

if __name__ == '__main__':
    main()
