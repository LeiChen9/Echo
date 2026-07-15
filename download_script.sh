#!/usr/bin/env bash
set -euo pipefail

rclone copy --progress --ignore-existing --exclude "_success/**" --exclude "_fails/**" r2:bonfire/script/ asset/script
echo "Done"