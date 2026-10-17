#!/usr/bin/env bash
# Browser capture bytes may be JPEG even when the requested filename ends .png.
# Re-encode only; no crop, resize, color treatment or fabricated chart contents.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v sips >/dev/null || { echo 'This optional capture-normalization helper requires macOS sips.' >&2; exit 1; }
for SCREENSHOT_PATH in docs/screenshots/*.png; do
    TEMP_SCREENSHOT_DIR=$(mktemp -d "${TMPDIR:-/tmp}/portfolio-capture.XXXXXX")
    sips -s format png "$SCREENSHOT_PATH" --out "$TEMP_SCREENSHOT_DIR/capture.png" >/dev/null
    mv "$TEMP_SCREENSHOT_DIR/capture.png" "$SCREENSHOT_PATH"
    rmdir "$TEMP_SCREENSHOT_DIR"
done
