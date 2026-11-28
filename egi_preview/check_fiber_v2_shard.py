"""Verify an individual native PNG shard and record immutable frame hashes."""
import hashlib,json,os,sys,struct
from pathlib import Path
idx,start,end=map(int,sys.argv[1:])
assert 0<=idx<8 and start==idx*90+1 and end==start+89
p=Path('frames')
names={f'f_{i:04d}.png' for i in range(start,end+1)}
assert {x.name for x in p.glob('*.png')}==names
hashes={}
for name in sorted(names):
    with (p/name).open('rb') as f:
        head=f.read(24)
        assert head[:8]==b'\x89PNG\r\n\x1a\n' and head[12:16]==b'IHDR',name
        assert struct.unpack('>II',head[16:24])==(1080,1920),name
        f.seek(0)
        hashes[name]=hashlib.file_digest(f,'sha256').hexdigest()
Path('manifest.json').write_text(json.dumps({'shard':idx,'start':start,'end':end,'commit':os.environ['GITHUB_SHA'],'sha256':hashes},indent=2))
print(f'SHARD_PASS {idx}: {start}..{end}')
