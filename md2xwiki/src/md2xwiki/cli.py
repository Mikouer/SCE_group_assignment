import argparse
import json
import sys
import uuid
from pathlib import Path

from .client import Client
from .config import load_config
from .destinations import file_config, tree_config
from .errors import PublishError
from .model import Build, digest
from .renderer import compile_tree
from .sync import Publisher, encode, write_artifact


def build_artifacts(build: Build, output: Path) -> None:
    pages = []
    for page in build.pages:
        filename = digest(page.reference.document.encode()) + ".xwiki"
        write_artifact(output / "pages" / filename, page.content.encode())
        assets = []
        for attachment in page.attachments.values():
            write_artifact(output / "attachments" / attachment.name, attachment.data)
            assets.append({"name": attachment.name, "source": attachment.source.as_posix(),
                           "hash": attachment.hash, "mime": attachment.mime})
        pages.append({"source": page.source.as_posix(), "document": page.reference.document,
                      "spaces": list(page.reference.spaces), "title": page.title,
                      "preserve_content": page.preserve_content,
                      "preserve_title": page.preserve_title,
                      "hash": page.hash, "file": "pages/" + filename, "attachments": assets})
    write_artifact(output / "build.json", encode({"schema": 1, "pages": pages}))


def report(data: dict) -> None:
    for operation in data["operations"]:
        suffix = "@" + operation["name"] if operation["name"] else ""
        print(f"{operation['action']:9} {operation['document']}{suffix}")
    print(f"{len(data['operations'])} operation(s), {len(data['unchanged'])} unchanged item(s), "
          f"{len(data['pending_removals'])} pending removal(s)")
    for item in data["pending_removals"]:
        print(f"pending removal: {item}")


def prepare_test(output: Path, fixture: Path, base_url: str) -> None:
    output = output.resolve()
    if not fixture.is_dir() or not (fixture / "index.md").is_file():
        raise PublishError(f"Missing smoke fixture: {fixture}")
    name = "md2xwiki-test-" + uuid.uuid4().hex
    run = output / name
    run.mkdir(parents=True, exist_ok=False)
    # A copied fixture makes later retries/cleanup independent of source edits.
    import shutil
    shutil.copytree(fixture, run / "source")
    config = (
        "[xwiki]\n"
        f"destination = {json.dumps(base_url + '/wiki/sce2026group05/view/test/')}\n"
        'source = "source"\nsyntax = "xwiki/2.1"\nlayout = "file"\nfile = "index.md"\n'
        f'deployment_id = "{name}"\nmode = "temporary"\n\n'
    )
    write_artifact(run / "xwiki.toml", config.encode())
    load_config(run / "xwiki.toml")
    write_artifact(output / "latest-test.txt", (str(run) + "\n").encode())
    print(run)


def main() -> int:
    parser = argparse.ArgumentParser(prog="md2xwiki")
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "check", "sync", "pipeline", "cleanup", "target", "probe"):
        command = subcommands.add_parser(name)
        command.add_argument("--config", type=Path, default=Path("xwiki.toml"))
        command.add_argument("--output", type=Path, default=Path("build/xwiki"))
        if name in {"sync", "pipeline"}:
            command.add_argument("--prune", action="store_true")
            command.add_argument("--overwrite", action="store_true",
                                 help="Explicitly replace reviewed drift, with local backups")
        if name == "sync":
            command.add_argument("--dry-run", action="store_true")
    for name in ("push-tree", "push-file"):
        command = subcommands.add_parser(name)
        command.add_argument("--root" if name == "push-tree" else "--file", type=Path, required=True)
        command.add_argument("--project-root" if name == "push-tree" else "--destination", required=True)
        command.add_argument("--output", type=Path, default=Path("build/xwiki"))
        command.add_argument("--deployment-id")
        command.add_argument("--dry-run", action="store_true")
        if name == "push-tree":
            command.add_argument("--prune", action="store_true")
        command.add_argument("--overwrite", action="store_true")
    prepare = subcommands.add_parser("prepare-test")
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--fixture", type=Path, required=True)
    prepare.add_argument("--base-url", default="https://xwiki.ewi.tudelft.nl/xwiki")
    args = parser.parse_args()
    client = None
    try:
        if args.command in {"sync", "pipeline", "push-tree", "push-file"} and not getattr(args, "dry_run", False):
            write_artifact(args.output / "summary.json", encode({"status": "in_progress"}))
        if args.command == "prepare-test":
            prepare_test(args.output, args.fixture, args.base_url)
            return 0
        if args.command == "push-tree":
            config = tree_config(args.root, args.project_root, args.deployment_id)
        elif args.command == "push-file":
            config = file_config(args.file, args.destination, args.deployment_id)
        else:
            config = load_config(args.config)
        if args.command == "target":
            for root in config.roots:
                print(root.reference.view_url(config.base_url))
            return 0
        build = Build(config, []) if args.command in {"cleanup", "probe"} else compile_tree(config)
        if args.command in {"build", "pipeline", "push-tree", "push-file"}:
            build_artifacts(build, args.output)
            print(f"Compiled {len(build.pages)} page(s) offline")
        if args.command == "build":
            return 0
        client = Client(config)
        print(f"Authenticated REST probe: XWiki {client.probe()}")
        if args.command == "probe":
            print(f"Authenticated xwiki-user: {client.identity}")
            return 0
        publisher = Publisher(build, client, args.output)
        if args.command == "cleanup":
            publisher.cleanup()
            print("Temporary page removed (normal recycle-bin deletion)")
            return 0
        plan = publisher.preflight(prune=getattr(args, "prune", False),
                                   overwrite=getattr(args, "overwrite", False))
        report(plan.json())
        write_artifact(args.output / "plan.json", encode(plan.json()))
        if args.command == "check" or getattr(args, "dry_run", False):
            return 0
        publisher.apply(plan)
        verification = publisher.preflight(prune=getattr(args, "prune", False))
        if verification.operations or any(state.dirty for state in verification.states.values()):
            raise PublishError("Post-publish verification/idempotence check did not converge")
        write_artifact(args.output / "summary.json", encode({
            "status": "verified", "deployment_id": config.deployment_id,
            "applied": plan.json(), "verification": verification.json(),
        }))
        print("Published resources verified; an unchanged rerun requires no writes")
        if config.temporary:
            root = config.roots[0].reference
            print("Temporary page: " + root.view_url(config.base_url))
        return 0
    except (PublishError, OSError, UnicodeError) as exc:
        if args.command in {"sync", "pipeline", "push-tree", "push-file"} and not getattr(args, "dry_run", False):
            try:
                write_artifact(args.output / "summary.json",
                               encode({"status": "failed", "error": str(exc)}))
            except OSError as artifact_error:
                print(f"md2xwiki: Cannot persist failure summary: {artifact_error}", file=sys.stderr)
        print(f"md2xwiki: {exc}", file=sys.stderr)
        print("Deployment not completed. Retain the output directory for backups/recovery.",
              file=sys.stderr)
        return 1
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    sys.exit(main())
