#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends ffmpeg espeak-ng libsndfile1 fonts-dejavu-core libx11-6 libxi6 libxrender1 libxxf86vm1 libxfixes3 libgl1 libsm6 libxkbcommon0 libegl1 libgomp1
mode=${EGI_INSTALL_MODE:-all}
case "$mode" in all|render|compose) ;; *) exit 2;; esac
if [ "$mode" != compose ]; then
version=4.5.16
archive="blender-$version-linux-x64.tar.xz"
bundle="$GITHUB_WORKSPACE/blender-dist"
mkdir -p /tmp/egi-blender "$bundle"
cd "$bundle"
if [ "${EGI_BLENDER_BUNDLE_ONLY:-0}" = 1 ]; then
  test -s "$archive" && test -s blender.sha256
else
  # Official mirror directory and listed university mirrors, same pinned version.
  # No fallback to a different Blender build or disabling denoise.
  bases=(
    https://mirror.blender.org/release/Blender4.5
    https://ftp.nluug.nl/graphics/blender/release/Blender4.5
    https://ftp.halifax.rwth-aachen.de/blender/release/Blender4.5
    https://download.blender.org/release/Blender4.5
  )
  fetch() {
    curl --fail --location --show-error --connect-timeout 15 --max-time 300 --retry 1 -o "$2" "$1"
  }
  ok=0
  for base in "${bases[@]}"; do
    echo "Checking Blender source: $base"
    rm -f "$archive.part" manifest.part blender.sha256
    if fetch "$base/blender-$version.sha256" manifest.part &&
       awk -v a="$archive" '$2==a || $2=="*"a {print $1 "  " a}' manifest.part > blender.sha256 &&
       grep -Eq '^[[:xdigit:]]{64}  blender-' blender.sha256 &&
       fetch "$base/$archive" "$archive.part"; then
      mv "$archive.part" "$archive"
      if sha256sum --check blender.sha256; then
        echo "BLENDER_DOWNLOAD_VERIFIED $base"
        ok=1
        break
      fi
    fi
    rm -f "$archive" blender.sha256 "$archive.part" manifest.part
  done
  [ "$ok" = 1 ] || { echo "BLOCKED_BLENDER_DOWNLOAD: all approved sources failed"; exit 22; }
  rm -f manifest.part
fi
sha256sum --check blender.sha256
tar -xJf "$archive" -C /tmp/egi-blender --strip-components=1
/tmp/egi-blender/blender --version
fi
cd "$GITHUB_WORKSPACE"
if [ "$mode" != render ]; then
python -m venv .venv
. .venv/bin/activate
python -m pip install --index-url https://download.pytorch.org/whl/cpu 'torch==2.6.0'
python -m pip install 'kokoro==0.9.4' soundfile pillow
python -m py_compile egi_preview/blender_regen_v2.py egi_preview/blender_kokoro_v2.py

fi
