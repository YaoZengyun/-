#!/usr/bin/env bash
set -euo pipefail

# Build APK with Buildozer Docker image (no local SDK/NDK install required)
# Usage: ./build_with_docker.sh [debug|release]

PROFILE="${1:-debug}"
if [[ "$PROFILE" != "debug" && "$PROFILE" != "release" ]]; then
  echo "Usage: $0 [debug|release]" >&2
  exit 1
fi

IMG="kivy/buildozer"
echo "Pulling $IMG ..."
docker pull "$IMG"

mkdir -p "$HOME/.buildozer" "$HOME/.cache/pip"

docker run --rm -it \
  -v "$PWD":/home/user/app \
  -v "$HOME/.buildozer":/home/user/.buildozer \
  -v "$HOME/.cache/pip":/home/user/.cache/pip \
  -w /home/user/app \
  "$IMG" \
  buildozer android "$PROFILE"

echo "\nDone. Check bin/ directory for the APK."
