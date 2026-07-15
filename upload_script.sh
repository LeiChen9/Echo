#!/usr/bin/env bash
set -euo pipefail

rclone copy --progress --ignore-existing --exclude "_success/**" --exclude "_fails/**" asset/script r2:bonfire/script/
echo "Done"
