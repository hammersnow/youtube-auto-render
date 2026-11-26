#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends ffmpeg espeak-ng libsndfile1 fonts-dejavu-core libx11-6 libxi6 libxrender1 libxxf86vm1 libxfixes3 libgl1 libsm6 libxkbcommon0 libegl1 libgomp1
version=4.5.16
archive="blender-$version-linux-x64.tar.xz"
base=https://download.blender.org/release/Blender4.5
mkdir -p /tmp/egi-blender
cd /tmp
curl --fail --location --retry 3 -o "$archive" "$base/$archive"
curl --fail --location --retry 3 -o blender.sha256 "$base/blender-$version.sha256"
grep -F "$archive" blender.sha256 | sha256sum --check -
tar -xJf "$archive" -C /tmp/egi-blender --strip-components=1
/tmp/egi-blender/blender --version
cd "$GITHUB_WORKSPACE"
python -m venv .venv
. .venv/bin/activate
python -m pip install --index-url https://download.pytorch.org/whl/cpu 'torch==2.6.0'
python -m pip install 'kokoro==0.9.4' soundfile pillow
python -m py_compile egi_preview/blender_regen_v2.py egi_preview/blender_kokoro_v2.py
