#!/usr/bin/env bash
set -euo pipefail

rclone copy --progress --exclude "_success/**" --exclude "_fails/**" asset/script bonfire:script/
echo "Done"
