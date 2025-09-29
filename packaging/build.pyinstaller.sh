#!/usr/bin/env bash
set -euo pipefail
APP=cli-audio-visualizer
ENTRY=visualizer.py
OUTDIR=dist

# Detect platform tag
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
CASE_TAG="${PLATFORM}-${ARCH}"

mkdir -p "$OUTDIR"

pyinstaller \
  --name "$APP" \
  --onefile \
  --clean \
  --strip \
  --add-data "README.md:." \
  --hidden-import sounddevice \
  "$ENTRY"

# Rename with platform suffix
if [ -f "dist/$APP" ]; then
  mv "dist/$APP" "dist/${APP}-${CASE_TAG}"
fi

echo "Built dist/${APP}-${CASE_TAG}"