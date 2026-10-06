import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import yaml

from md2xwiki.config import load_config
from md2xwiki.renderer import compile_tree


def test_local_script_uses_shared_pipeline_and_cleanup(tmp_path):
    repository = Path(__file__).parents[2]
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    shutil.copytree(repository / "scripts", workspace / "scripts")
    shutil.copytree(repository / "md2xwiki/tests/fixtures/smoke",
                    workspace / "md2xwiki/tests/fixtures/smoke")
    binaries = tmp_path / "bin"
    binaries.mkdir()
    log = tmp_path / "docker.jsonl"
    # Only Docker is replaced. The actual scripts and test-config generator run.
    docker = binaries / "docker"
    docker.write_text(f"""#!{sys.executable}
import json, os, sys
from pathlib import Path
from md2xwiki.cli import prepare_test
from md2xwiki.config import load_config
args = sys.argv[1:]
with open(os.environ["DOCKER_TEST_LOG"], "a") as stream:
    stream.write(json.dumps(args) + "\\n")
if "prepare-test" in args:
    repo = Path.cwd()
    prepare_test(repo / ".md2xwiki/tests",
                 repo / "md2xwiki/tests/fixtures/smoke",
                 "https://xwiki.ewi.tudelft.nl/xwiki")
if "target" in args:
    path = args[args.index("--config") + 1].replace("/workspace/", "")
    config = load_config(Path.cwd() / path)
    print(config.roots[0].reference.view_url(config.base_url))
""")
    docker.chmod(0o755)
    env = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ["PATH"],
               DOCKER_TEST_LOG=str(log), XWIKI_USERNAME="Publisher",
               XWIKI_PASSWORD="test-only-placeholder")
    subprocess.run(["bash", "scripts/test-xwiki.sh", "--image", "example:test"],
                   cwd=workspace, env=env, check=True, capture_output=True, text=True)
    runs = list((workspace / ".md2xwiki/tests").glob("md2xwiki-test-*"))
    assert len(runs) == 1
    config = load_config(runs[0] / "xwiki.toml")
    assert config.temporary
    assert len(compile_tree(config).pages) == 1
    assert config.roots[0].reference.spaces == ("test",)
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    pipeline = next(args for args in calls if "pipeline" in args)
    assert pipeline[pipeline.index("example:test") + 1] == "pipeline"
    assert "--output" in pipeline and "/output" in pipeline
    assert "XWIKI_PASSWORD" in pipeline
    assert "test-only-placeholder" not in " ".join(pipeline)
    assert "--prune" not in pipeline
    assert not any("PROXY" in arg or "proxy" in arg or "CA_BUNDLE" in arg for arg in pipeline)
    assert not any("build" in args for args in calls)
    relative = runs[0].relative_to(workspace).as_posix()
    subprocess.run(["bash", "scripts/test-xwiki.sh", "--cleanup", relative,
                    "--image", "example:test"], cwd=workspace, env=env, check=True,
                   capture_output=True, text=True)
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    cleanup = next(args for args in calls if "cleanup" in args)
    assert cleanup[cleanup.index("example:test") + 1] == "cleanup"
    assert "/output" in cleanup


def test_workflow_calls_requested_component_and_shared_scripts():
    workflow = (Path(__file__).parents[2] / ".github/workflows/publish-xwiki.yml").read_text()
    assert "uses: axillusion/build-tools/.github/workflows/docker-build-and-push.yml@main" in workflow
    assert 'context: "md2xwiki"' in workflow
    assert 'dockerfile: "md2xwiki/Dockerfile"' in workflow
    assert "version: ${{ github.sha }}" in workflow
    assert "registry_token: ${{ secrets.GITHUB_TOKEN }}" in workflow
    assert 'bash scripts/run-xwiki.sh "$IMAGE" xwiki.toml' in workflow
    assert "vars.XWIKI_PUBLISH_ENABLED == 'true'" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "pull_request_target" not in workflow


def test_workflow_builds_before_publishing_without_ci_validation():
    path = Path(__file__).parents[2] / ".github/workflows/publish-xwiki.yml"
    workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    assert set(workflow["on"]) == {"push", "workflow_dispatch"}
    assert workflow["on"]["push"]["branches"] == ["main"]
    jobs = workflow["jobs"]
    assert set(jobs) == {"metadata", "docker", "publish"}
    assert jobs["docker"]["needs"] == ["metadata"]
    assert jobs["docker"]["with"]["image"] == "${{ needs.metadata.outputs.image }}"
    assert jobs["docker"]["with"]["version"] == "${{ github.sha }}"
    assert jobs["publish"]["needs"] == ["metadata", "docker"]
    assert jobs["publish"]["runs-on"] == "ubuntu-latest"
    assert jobs["metadata"]["runs-on"] == "ubuntu-latest"
    assert "XWIKI_RUNNER_LABELS" not in path.read_text()
    publishing = next(step for step in jobs["publish"]["steps"] if "IMAGE" in step.get("env", {}))
    assert publishing["env"]["IMAGE"] == "${{ needs.metadata.outputs.image }}:${{ github.sha }}"
