#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo"
image=${MD2XWIKI_IMAGE:-md2xwiki:local-test}
action=publish
run_dir=
build=true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --image) image=${2:?--image needs a tag or digest}; build=false; shift 2 ;;
    --resume|--cleanup) action=${1#--}; run_dir=${2:?Specify the run directory}; build=false; shift 2 ;;
    --help)
      echo "Usage: bash scripts/test-xwiki.sh [--image IMAGE]"
      echo "       bash scripts/test-xwiki.sh --resume|--cleanup .md2xwiki/tests/md2xwiki-test-UUID [--image IMAGE]"
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done
docker info >/dev/null
if [[ "$build" == true ]]; then
  docker build --tag "$image" --file md2xwiki/Dockerfile md2xwiki
fi
if [[ -z "${XWIKI_USERNAME:-}" ]]; then
  read -r -p "XWiki service account: " XWIKI_USERNAME
  export XWIKI_USERNAME
fi
if [[ -z "${XWIKI_PASSWORD:-}" ]]; then
  read -r -s -p "XWiki password: " XWIKI_PASSWORD
  printf '\n'
  export XWIKI_PASSWORD
fi
if [[ "$action" == publish ]]; then
  mkdir -p .md2xwiki/tests
  # Offline preparation: one copied sample and a unique recovery directory, without credentials.
  prepared=$(docker run --rm --user "$(id -u):$(id -g)" \
    --mount "type=bind,source=$repo,target=/workspace,readonly" \
    --mount "type=bind,source=$repo/.md2xwiki/tests,target=/tests" \
    "$image" prepare-test --output /tests \
    --fixture /workspace/md2xwiki/tests/fixtures/smoke)
  name=$(basename "$prepared")
  run_dir=".md2xwiki/tests/$name"
fi
if [[ ! "$run_dir" =~ ^\.md2xwiki/tests/md2xwiki-test-[0-9a-f]{32}$ ]]; then
  echo "Run directory must be the UUID directory printed by this script" >&2
  exit 2
fi
if [[ "$action" == cleanup ]]; then
  [[ -d "$repo/$run_dir/output" ]] || { echo "Missing recovery output directory" >&2; exit 2; }
  MD2XWIKI_COMMAND=cleanup bash scripts/run-xwiki.sh \
    "$image" "$run_dir/xwiki.toml" "$run_dir/output"
else
  echo "Run directory: $run_dir"
  target=$(docker run --rm --user "$(id -u):$(id -g)" \
    --mount "type=bind,source=$repo,target=/workspace,readonly" \
    "$image" target --config "/workspace/$run_dir/xwiki.toml")
  echo "Target: $target"
  echo "This writes only the temporary page and its attachments; it leaves it for inspection."
  echo "Rerun: bash scripts/test-xwiki.sh --resume $run_dir --image $image"
  echo "Cleanup: bash scripts/test-xwiki.sh --cleanup $run_dir --image $image"
  bash scripts/run-xwiki.sh "$image" "$run_dir/xwiki.toml" "$run_dir/output"
fi
