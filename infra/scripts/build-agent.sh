#!/usr/bin/env bash
set -euo pipefail

agent_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../cloud/agent" && pwd)"
package_dir="$agent_dir/deployment_package"
archive="$agent_dir/runtime.zip"

mkdir -p "$package_dir"
find "$package_dir" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +

python3 -m pip install \
  --platform manylinux2014_aarch64 \
  --python-version 3.13 \
  --implementation cp \
  --only-binary=:all: \
  --target "$package_dir" \
  --requirement "$agent_dir/requirements.txt"

cp "$agent_dir/main.py" "$package_dir/main.py"
cp "$agent_dir/deduplication.py" "$package_dir/deduplication.py"
find "$package_dir" -type d -name __pycache__ -prune -exec rm -rf -- {} +
find "$package_dir" -type f -exec chmod 0644 {} +
find "$package_dir" -type d -exec chmod 0755 {} +
(cd "$package_dir" && zip -q -r "$archive" .)
sha256sum "$archive"
