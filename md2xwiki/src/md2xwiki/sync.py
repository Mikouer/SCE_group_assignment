import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .client import Client, RemotePage
from .config import MANIFEST, Config, Root, spaces
from .errors import PublishError
from .model import Attachment, Build, Page, digest
from .references import Reference, valid_segment

HASH = re.compile(r"[0-9a-f]{64}\Z")
Kind = Literal["page", "attachment"]


def hash_value(value: object, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not HASH.fullmatch(value):
        raise PublishError("Invalid hash in ownership manifest")
    return value


def encode(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def write_artifact(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


@dataclass
class Owned:
    reference: Reference
    hash: str | None
    attachments: dict[str, str] = field(default_factory=dict)

    def json(self) -> dict:
        return {"spaces": list(self.reference.spaces), "hash": self.hash,
                "attachments": self.attachments}


@dataclass(frozen=True)
class Operation:
    kind: Kind
    reference: Reference
    before: str | None
    after: str | None
    name: str | None = None
    page: Page | None = None
    attachment: Attachment | None = None

    @property
    def action(self) -> str:
        return "delete" if self.after is None else "create" if self.before is None else "update"

    def json(self) -> dict:
        return {"kind": self.kind, "spaces": list(self.reference.spaces),
                "name": self.name, "before": self.before, "after": self.after}


@dataclass
class State:
    root: Root
    pages: dict[Reference, Owned] = field(default_factory=dict)
    pending: Operation | None = None
    remote_hash: str | None = None
    dirty: bool = False
    created_root: bool = False

    def json(self, config: Config) -> dict:
        return {"schema": 1, "base_url": config.base_url, "wiki": config.wiki,
                "deployment_id": config.deployment_id,
                "root": list(self.root.reference.spaces),
                "created_root": self.created_root,
                "pages": [o.json() for _, o in sorted(
                    self.pages.items(), key=lambda item: item[0].document
                )],
                "pending": self.pending.json() if self.pending else None}

    def accept(self, operation: Operation) -> None:
        if operation.kind == "page":
            if operation.after is None:
                self.pages.pop(operation.reference, None)
            else:
                owned = self.pages.setdefault(operation.reference, Owned(operation.reference, None))
                owned.hash = operation.after
        else:
            owned = self.pages.get(operation.reference)
            if owned is None or owned.hash is None:
                raise PublishError("Attachment operation has no owned parent page")
            if operation.after is None:
                owned.attachments.pop(operation.name, None)
            else:
                owned.attachments[operation.name] = operation.after
        self.pending = None
        self.dirty = True


def load_state(config: Config, root: Root, raw: bytes | None) -> State:
    state = State(root, remote_hash=digest(raw) if raw is not None else None)
    if raw is None:
        return state
    try:
        data = json.loads(raw)
        if (data["schema"] != 1 or data["base_url"] != config.base_url
                or data["wiki"] != config.wiki or data["deployment_id"] != config.deployment_id
                or data["root"] != list(root.reference.spaces)):
            guidance = (" Resume the original test run directory, or use that run's guarded "
                        "cleanup before starting a new one.") if config.temporary else ""
            raise PublishError("Manifest identity mismatch; root migrations must be explicit."
                               + guidance)
        state.created_root = data.get("created_root", config.temporary and config.layout == "markdown")
        if not isinstance(state.created_root, bool):
            raise PublishError("Invalid root-creation flag in ownership manifest")
        for item in data["pages"]:
            reference = Reference(config.wiki, spaces(item["spaces"]))
            if config.root_for(reference) != root or reference in state.pages:
                raise PublishError("Manifest has duplicate or out-of-scope references")
            page_digest = hash_value(item["hash"])
            attachments = item["attachments"]
            if not isinstance(attachments, dict):
                raise PublishError("Invalid attachment ownership map")
            for name, value in attachments.items():
                valid_segment(name)
                if name == MANIFEST:
                    raise PublishError("Manifest cannot claim its own state attachment")
                hash_value(value)
            state.pages[reference] = Owned(reference, page_digest, dict(attachments))
        if data.get("pending") is not None:
            item = data["pending"]
            reference = Reference(config.wiki, spaces(item["spaces"]))
            if config.root_for(reference) != root or item["kind"] not in {"page", "attachment"}:
                raise PublishError("Pending operation outside ownership scope")
            name = item["name"]
            if item["kind"] == "attachment":
                valid_segment(name)
                if name == MANIFEST or reference not in state.pages:
                    raise PublishError("Invalid pending attachment operation")
            elif name is not None:
                raise PublishError("Invalid pending page operation")
            before = hash_value(item["before"], nullable=True)
            after = hash_value(item["after"], nullable=True)
            if before == after or (after is None and reference == root.reference and name is None):
                raise PublishError("Invalid pending operation or attempted root deletion")
            owned = state.pages.get(reference)
            baseline = (owned.hash if name is None else owned.attachments.get(name)) if owned else None
            if before != baseline and baseline is not None:
                # A deliberate overwrite records the observed drift as its before hash.
                if after is None:
                    raise PublishError("Pending delete disagrees with ownership baseline")
            state.pending = Operation(item["kind"], reference, before, after, name)
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise PublishError(f"Corrupt ownership manifest on {root.reference.document}") from exc
    return state


@dataclass
class Plan:
    build: Build
    states: dict[Reference, State]
    operations: list[Operation]
    unchanged: list[str]
    pending_removals: list[str]
    backups: dict[Reference, RemotePage]
    asset_backups: dict[tuple[Reference, str], bytes] = field(default_factory=dict)

    def json(self) -> dict:
        return {"deployment_id": self.build.config.deployment_id,
                "operations": [dict(op.json(), action=op.action, document=op.reference.document)
                               for op in self.operations],
                "unchanged": self.unchanged, "pending_removals": self.pending_removals,
                "recoveries": [s.root.reference.document for s in self.states.values() if s.dirty]}


class Publisher:
    def __init__(self, build: Build, client: Client, output: Path):
        self.build = build
        self.config = build.config
        self.client = client
        self.output = output

    def bootstrap_path(self, root: Root) -> Path:
        if len(self.config.roots) == 1:
            return self.output / "bootstrap.json"
        return self.output / "bootstrap" / (digest(root.reference.document.encode()) + ".json")

    def bootstrap_state(self, root: Root, remote: RemotePage | None) -> State | None:
        path = self.bootstrap_path(root)
        if not path.exists():
            return None
        try:
            saved = json.loads(path.read_bytes())
            state = load_state(self.config, root, encode(saved))
            pending = state.pending
            if (pending is None or pending.reference != root.reference
                    or pending.before is not None or pending.kind != "page"
                    or pending.after is None):
                raise PublishError("Invalid root bootstrap journal")
            if remote is None:
                return None
            if remote.hash != pending.after:
                raise PublishError("Bootstrap page changed; refusing ownership")
            state.accept(pending)
            state.remote_hash = None
            return state
        except (OSError, ValueError) as exc:
            raise PublishError("Cannot recover root bootstrap journal") from exc

    def recover(self, state: State) -> None:
        pending = state.pending
        if pending is None:
            return
        actual = self.resource_hash(pending)
        if actual == pending.after:
            state.accept(pending)
        elif actual == pending.before:
            state.pending = None
            state.dirty = True
        else:
            raise PublishError(f"Unresolved partial publish/manual drift: {pending.reference.document}")

    def resource_hash(self, operation: Operation) -> str | None:
        if operation.kind == "page":
            return self.client.page_hash(operation.reference)
        return self.client.attachment_hash(operation.reference, operation.name)

    def preflight(self, *, prune: bool = False, overwrite: bool = False) -> Plan:
        states = {}
        operations = []
        unchanged = []
        removals = []
        backups = {}
        asset_backups = {}
        for root in self.config.roots:
            remote = self.client.get_page(root.reference)
            raw = self.client.get_attachment(root.reference, MANIFEST) if remote else None
            state = load_state(self.config, root, raw)
            if raw is None:
                recovered = self.bootstrap_state(root, remote)
                if recovered:
                    state = recovered
                elif remote is None:
                    state.created_root = True
            elif remote is None:
                raise PublishError("Ownership root disappeared")
            self.recover(state)
            states[root.reference] = state
        desired = {p.reference: p for p in self.build.pages}
        for page in self.build.pages:
            root = self.config.root_for(page.reference)
            state = states[root.reference]
            owned = state.pages.get(page.reference)
            remote = self.client.get_page(page.reference)
            actual = remote.hash if remote else None
            if remote is not None:
                if page.preserve_title:
                    page.title = remote.title
                if page.preserve_content:
                    page.content = remote.content
                    page.syntax = remote.syntax
            if owned:
                if actual != owned.hash and not overwrite and not page.preserve_content:
                    raise PublishError(f"Manual edit or missing managed page: {page.reference.document}; "
                                       "use --overwrite only after reviewing the change")
            elif remote is not None:
                if (page.reference != root.reference or self.config.temporary) and not page.adopt_existing:
                    raise PublishError(f"Unmanaged existing page collision: {page.reference.document}")
                if not page.preserve_content:
                    backups[page.reference] = remote
            if remote is not None and owned and actual != owned.hash and overwrite and not page.preserve_content:
                backups[page.reference] = remote
            if actual != page.hash:
                operations.append(Operation("page", page.reference, actual, page.hash, page=page))
            elif owned is None:
                # Establish explicit ownership even if content already happens to match.
                state.pages[page.reference] = Owned(page.reference, page.hash)
                state.dirty = True
                unchanged.append(page.reference.document)
            else:
                if page.preserve_content and owned.hash != actual:
                    owned.hash = actual
                    state.dirty = True
                unchanged.append(page.reference.document)
            for name, attachment in page.attachments.items():
                actual_asset = self.client.attachment_hash(page.reference, name) if remote else None
                baseline = owned.attachments.get(name) if owned else None
                if baseline is None and actual_asset is not None:
                    raise PublishError(f"Unmanaged attachment collision: {page.reference.document}@{name}")
                if baseline is not None and actual_asset != baseline and not overwrite:
                    raise PublishError(f"Manual attachment edit: {page.reference.document}@{name}")
                if actual_asset != attachment.hash:
                    if baseline is not None and actual_asset != baseline and actual_asset is not None:
                        raw = self.client.get_attachment(page.reference, name)
                        if raw is None or digest(raw) != actual_asset:
                            raise PublishError(f"Attachment changed while backing up: {name}")
                        asset_backups[(page.reference, name)] = raw
                    operations.append(Operation("attachment", page.reference, actual_asset,
                                                attachment.hash, name, attachment=attachment))
                else:
                    unchanged.append(page.reference.document + "@" + name)
        for state in states.values():
            for reference, owned in list(state.pages.items()):
                page = desired.get(reference)
                stale_names = set() if page and page.preserve_content else (
                    set(owned.attachments) - (set(page.attachments) if page else set())
                )
                for name in sorted(stale_names):
                    label = reference.document + "@" + name
                    removals.append(label)
                    if prune:
                        actual = self.client.attachment_hash(reference, name)
                        if actual not in {None, owned.attachments[name]}:
                            raise PublishError(f"Modified stale attachment cannot be pruned: {label}")
                        operations.append(Operation("attachment", reference, actual, None, name))
                if page is None:
                    if reference == state.root.reference:
                        raise PublishError("Root migrations/deletions are not implicit")
                    removals.append(reference.document)
                    if prune:
                        actual = self.client.page_hash(reference)
                        if actual not in {None, owned.hash}:
                            raise PublishError(f"Modified stale page cannot be pruned: {reference.document}")
                        operations.append(Operation("page", reference, actual, None))
        writes = [op for op in operations if op.after is not None]
        deletes = [op for op in operations if op.after is None]
        deletes.sort(key=lambda op: (-len(op.reference.spaces), op.kind == "page",
                                     op.reference.document, op.name or ""))
        plan = Plan(self.build, states, writes + deletes, unchanged, removals, backups, asset_backups)
        if prune:
            for op in deletes:
                if op.kind == "page":
                    self.guard_delete(op.reference, plan)
        return plan

    def guard_delete(self, reference: Reference, plan: Plan, *, temporary_root: bool = False) -> None:
        root = self.config.root_for(reference)
        if reference == root.reference and not (temporary_root and self.config.temporary):
            raise PublishError("Production/managed roots cannot be deleted")
        deleted = {op.reference for op in plan.operations
                   if op.kind == "page" and op.after is None}
        todo = [reference]
        visited = set()
        while todo:
            parent = todo.pop()
            for child in self.client.children(parent):
                if child in visited:
                    raise PublishError("Cyclic/repeated nested-page inventory")
                visited.add(child)
                if child not in deleted:
                    raise PublishError(f"Unmanaged/retained descendant prevents deletion: {child.document}")
                todo.append(child)
        owned = plan.states[root.reference].pages.get(reference)
        if owned is None:
            raise PublishError("Cannot delete an unowned page")
        if self.client.get_page(reference) is not None and self.client.has_annotations(reference):
            raise PublishError(f"Objects/comments/translations/class prevent deletion: {reference.document}")
        allowed = set(owned.attachments)
        if reference == root.reference:
            allowed.add(MANIFEST)
        unmanaged = self.client.attachments(reference) - allowed
        if unmanaged:
            raise PublishError(f"Unmanaged attachments prevent page deletion: {reference.document}")
        for name, baseline in owned.attachments.items():
            actual = self.client.attachment_hash(reference, name)
            if actual not in {None, baseline}:
                raise PublishError(f"Modified attachment prevents page deletion: {name}")

    def save_state(self, state: State) -> None:
        raw = encode(state.json(self.config))
        self.client.put_attachment(state.root.reference, MANIFEST, raw, "application/json",
                                   state.remote_hash)
        state.remote_hash = digest(raw)
        state.dirty = False

    def apply(self, plan: Plan) -> None:
        for reference, remote in plan.backups.items():
            write_artifact(self.output / "backups" / (digest(reference.document.encode()) + ".xml"),
                           remote.body())
        for (reference, name), raw in plan.asset_backups.items():
            write_artifact(self.output / "backups" / (
                digest((reference.document + "@" + name).encode()) + ".bin"
            ), raw)
        for state in plan.states.values():
            if self.client.get_page(state.root.reference) is not None:
                if state.remote_hash is None or state.dirty:
                    self.save_state(state)
        for operation in plan.operations:
            state = plan.states[self.config.root_for(operation.reference).reference]
            if self.resource_hash(operation) != operation.before:
                raise PublishError(f"Remote changed after preflight: {operation.reference.document}")
            if operation.before is None and operation.after is None:
                state.accept(operation)
                self.save_state(state)
                continue
            if operation.after is None and operation.kind == "page":
                self.guard_delete(operation.reference, plan)
            state.pending = operation
            bootstrap = (
                operation.reference == state.root.reference and operation.kind == "page"
                and operation.before is None and state.remote_hash is None
            )
            if bootstrap:
                write_artifact(self.bootstrap_path(state.root), encode(state.json(self.config)))
            else:
                self.save_state(state)
            if operation.kind == "page":
                if operation.after is None:
                    if operation.before is not None:
                        self.client.delete_page(operation.reference, operation.before)
                else:
                    page = operation.page
                    if page is None:
                        raise PublishError("Page operation has no compiled payload")
                    self.client.put_page(operation.reference, RemotePage(
                        page.title, page.syntax, page.content
                    ), operation.before)
            elif operation.after is None:
                if operation.before is not None:
                    self.client.delete_attachment(operation.reference, operation.name, operation.before)
            else:
                attachment = operation.attachment
                if attachment is None or operation.name is None:
                    raise PublishError("Attachment operation has no compiled payload/name")
                self.client.put_attachment(operation.reference, operation.name, attachment.data,
                                           attachment.mime, operation.before)
            state.accept(operation)
            self.save_state(state)

    def cleanup(self) -> None:
        if not self.config.temporary:
            raise PublishError("cleanup is restricted to the UUID temporary-page configuration")
        root = self.config.roots[0]
        remote = self.client.get_page(root.reference)
        if remote is None:
            return
        raw = self.client.get_attachment(root.reference, MANIFEST)
        state = load_state(self.config, root, raw)
        if raw is None:
            state = self.bootstrap_state(root, remote)
            if state is None:
                raise PublishError("Temporary page has no verifiable ownership; clean it manually")
        self.recover(state)
        if not state.created_root:
            raise PublishError("The test page existed before this run; cleanup will not delete it. "
                               "Restore its original content from the backup if needed.")
        owned = state.pages.get(root.reference)
        if owned is None or len(state.pages) != 1 or remote.hash != owned.hash:
            raise PublishError("Temporary page has changed/unexpected ownership; clean it manually")
        plan = Plan(self.build, {root.reference: state}, [], [], [], {})
        self.guard_delete(root.reference, plan, temporary_root=True)
        if state.remote_hash is not None:
            if self.client.attachment_hash(root.reference, MANIFEST) != state.remote_hash:
                raise PublishError("Temporary ownership changed before cleanup")
        self.client.delete_page(root.reference, owned.hash)
