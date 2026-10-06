#!/usr/bin/env bash
set -euo pipefail

# Both CI and the local smoke test invoke this exact container pipeline.
if [[ $# -lt 3 ]]; then
  echo "Usage: bash scripts/run-xwiki.sh IMAGE CONFIG OUTPUT [--prune] [--overwrite]" >&2
  exit 2
fi
image=$1
config=$2
output=$3
shift 3
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
case "$config" in
  /*|*../*|../*) echo "CONFIG must be a repo-relative path without traversal" >&2; exit 2 ;;
esac
case "$output" in
  /*|*../*|../*) echo "OUTPUT must be a repo-relative path without traversal" >&2; exit 2 ;;
esac
[[ -f "$repo/$config" ]] || { echo "Configuration not found: $config" >&2; exit 2; }
: "${XWIKI_USERNAME:?Set XWIKI_USERNAME}"
: "${XWIKI_PASSWORD:?Set XWIKI_PASSWORD}"
mkdir -p "$repo/$output"
command=${MD2XWIKI_COMMAND:-pipeline}
case "$command" in
  pipeline|cleanup) ;;
  *) echo "Unsupported container command: $command" >&2; exit 2 ;;
esac
docker run --rm --user "$(id -u):$(id -g)" \
  --mount "type=bind,source=$repo,target=/workspace,readonly" \
  --mount "type=bind,source=$repo/$output,target=/output" \
  --env XWIKI_USERNAME --env XWIKI_PASSWORD --env XWIKI_EXPECTED_USER \
  "$image" "$command" --config "/workspace/$config" --output /output "$@"
