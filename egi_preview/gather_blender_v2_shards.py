"""Validate all eight lossless frame shards before any final encode."""
import hashlib, json, shutil, sys
from pathlib import Path
from PIL import Image
ROOT=Path('shards')
OUT=Path('frames')
N=480
def sha(p):
    return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
def main():
    OUT.mkdir(exist_ok=True)
    assert not list(OUT.iterdir()), 'frames dir not empty'
    seen=set()
    records=[]
    for i in range(8):
        base=ROOT/f'egi-v2-shard-{i}'
        manifest=json.loads((base/'manifest.json').read_text())
        lo=i*60+1;hi=lo+59
        assert (manifest['shard'],manifest['start'],manifest['end'])==(i,lo,hi),manifest
        assert manifest['commit']==sys.argv[1],manifest
        expected={f'f_{j:04d}.png' for j in range(lo,hi+1)}
        assert set(manifest['sha256'])==expected,manifest
        assert {p.name for p in (base/'frames').glob('*.png')}==expected
        for name in sorted(expected):
            assert name not in seen,name
            p=base/'frames'/name
            assert sha(p)==manifest['sha256'][name],name
            with Image.open(p) as im:
                assert im.size==(1080,1920),(name,im.size)
                im.verify()
            shutil.move(p,OUT/name)
            seen.add(name)
        records.append(manifest)
    assert seen=={f'f_{j:04d}.png' for j in range(1,N+1)}
    Path('preview').mkdir(exist_ok=True)
    Path('preview/shard-manifests.json').write_text(json.dumps(records,indent=2))
    print('SHARD_QA_PASS: exactly 480 unique native Full HD PNG frames')
if __name__=='__main__':main()
