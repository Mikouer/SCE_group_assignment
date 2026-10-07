# md2xwiki

Compile Markdown to native `xwiki/2.1` and publish it to explicit XWiki
destinations. The core publisher has no hardcoded Foundation/Main mapping or
course-section names. The [course documentation](../docs/README.md) uses the
existing wiki destinations and separate case pages.

## Markdown page names

Every page file needs YAML front matter:

```markdown
---
pageName: "a. Artifacts"
---
# Artifacts

This is the page content.
```

The complete header is metadata and is **never published**. For tree publishing,
`pageName` is the exact raw XWiki space name, including spaces and literal dots.
The filename and folder name do not determine the destination.

A file containing only its header, with an empty/whitespace body, preserves the
existing page's content, syntax and title. If that page is missing, it is created
empty. Do not omit the file: a header-only file supplies the page's name even
when there is no replacement content.
Its owned attachments are retained too, even with pruning enabled.

Existing titles are preserved when replacing a body. Newly created pages use
`pageName` as their title. Objects, ACLs, comments, translations and parent
metadata are never included in page PUT bodies.

## Tree hierarchy

Each node folder must contain `index.yaml`:

```yaml
pageText: Overview.md
children:
  - Artifacts.md
  - Prototype
```

`pageText` points to the Markdown file for that node. `children` is a list of
Markdown leaf files and/or folders. Each listed folder has its own mandatory
`index.yaml`, with the same format. Only declared pages are published; unlisted
files/folders are not discovered automatically. Paths are relative to the
index's folder, cannot escape the source tree, and cannot use symlinks.

For example:

```text
3-evaluation/
  index.yaml               # pageText: Overview.md; children: [Artifacts.md, Prototype]
  Overview.md              # pageName: "3. Evaluation"
  Artifacts.md             # pageName: "a. Artifacts"
  Prototype/
    index.yaml             # pageText: Overview.md; children: [AT-01.md]
    Overview.md            # pageName: "a. Prototype"; header only to preserve its body
    AT-01.md               # pageName: "a.1.Artifact AT-01"
```

These pages map beneath `/view/3.%20Evaluation/`, not beneath `/Main/`.
If the Foundation root is the wiki's Main page, put `pageName: Main` in that
root's Markdown header. That is a source-data choice, not a code special case.

## Push a tree or file

Install locally:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e "md2xwiki[test]"
```

Publish a tree beneath a project root:

```bash
.venv/bin/md2xwiki push-tree \
  --root path/to/self-contained-tree \
  --project-root https://xwiki.ewi.tudelft.nl/xwiki/wiki/sce2026group05/view
```

Publish one file to an exact page URL:

```bash
.venv/bin/md2xwiki push-file \
  --file path/to/standalone.md \
  --destination 'https://xwiki.ewi.tudelft.nl/xwiki/wiki/sce2026group05/view/3.%20Evaluation/a.%20Prototype/a.1.Artifact%20AT-01/'
```

For `push-file`, the destination URL is authoritative even if the source filename
or `pageName` differs; the header still supplies the initial title. Both commands
create missing pages and use the same compiler, guarded sync and read-back logic.
Targets are nested/nonterminal `WebHome` documents; a final `/WebHome` in the
destination URL is optional.
They accept `--dry-run`, `--output`, `--deployment-id` and explicit `--overwrite`.
Only `push-tree` accepts `--prune`. Normal file publishing cannot delete children.

Default deployment IDs are stable per operation/destination. Tree and standalone
file deployments use different IDs; a root already owned by a different
deployment is a conflict, not silently reassigned. To intentionally share
ownership, pass the same `--deployment-id`; file pushes still retain tree children.

For CI, `xwiki.toml` selects the three source root folders and their shared
project URL. It derives destinations from their Markdown headers. Every folder
and metadata file must exist before enabling production publishing.
The imported course pages have cross-root links: compile/publish them together
with this configuration. A single-file or single-root invocation does not
discover other roots' link targets.
Older `layout = "markdown"` configurations remain readable for compatibility,
but new trees use `layout = "yaml"`.

## Sample test on the real wiki

Start Docker (or a Docker-compatible engine) and run:

```bash
bash scripts/test-xwiki.sh
```

The script builds the standard `python:3.12-slim` Dockerfile and prompts securely
for the service account and password. With Podman selected through Docker:

```bash
DOCKER_CONTEXT=podman bash scripts/test-xwiki.sh
```

It copies **only** `tests/fixtures/smoke/index.md` and its two small sample
attachments, not a README or the real course trees. It targets exactly:

```text
https://xwiki.ewi.tudelft.nl/xwiki/wiki/sce2026group05/view/test/
```

This destination belongs to the test script/configuration only; it is not a
special destination in `push-file` or `push-tree`. Local and workflow tests call
the same `scripts/run-xwiki.sh` container pipeline: offline compilation,
authenticated preflight/dry-run plan, publishing with read-back, and a required
zero-write unchanged rerun. Front matter is excluded from the sample output.

The test leaves the page for inspection. Its UUID identifies the ignored local
run directory and ownership manifest, **not the wiki page name**. For subsequent
tests, use the printed `--resume` command with that directory; a fresh run cannot
take over another run's manifest on the same `test` page.

```bash
bash scripts/test-xwiki.sh --resume .md2xwiki/tests/md2xwiki-test-UUID
bash scripts/test-xwiki.sh --cleanup .md2xwiki/tests/md2xwiki-test-UUID
```

Replace `UUID` with the printed value. Cleanup deletes only a page created by
that run, still unchanged, without unrelated attachments/descendants/annotations.
If `test` already existed (for example, you created it to assign permissions),
it is backed up before replacement and cleanup refuses to delete it. Retain
the original backup and reuse the run directory. Normal deletion leaves
recycle-bin/history/audit traces.

Use `--image IMAGE` to skip building and run a prebuilt image. Rebuild without
that option after changing the publisher. Old UUID pages under Main can still
be resumed/cleaned using their original run configurations; they are not moved
implicitly. Retain output after failures for bootstrap recovery and backups.

## Authentication and permissions

Supply `XWIKI_USERNAME` and `XWIKI_PASSWORD` only as runtime environment variables
or secure prompts, never build arguments, source files or command-line passwords.
Enter the real account name (`scegroup5_sa`, not Markdown-escaped `scegroup5\_sa`).
The account needs view/edit/create/attachment rights at the supplied destination;
cleanup and pruning also need delete rights.

The probe discovers public server metadata separately, then verifies the
`xwiki-user` header on the **target wiki's** REST endpoint. The old server-root
check could see an unrelated Main-wiki/Guest context. Guest requests have no
`xwiki-user` header. The new error distinguishes missing authentication from
a real but unexpected user and shows the returned reference for mismatches.
Missing authentication still aborts before publishing writes.

If the reported authenticated reference genuinely belongs to your service
account but differs from its login identifier, set `XWIKI_EXPECTED_USER` to that
exact reference. This cannot turn Guest into an authenticated user.
`md2xwiki probe --config PATH` is read-only and prints the verified identity.
TLS verification stays enabled; no work proxy/mirror/CA settings are configured.

## GitHub Actions

Tests run locally; the workflow has no validation job or pull-request trigger.
Pushes to `main` and manual runs use your component:
`axillusion/build-tools/.github/workflows/docker-build-and-push.yml@main`.
It builds `md2xwiki/Dockerfile` with context `md2xwiki`, pushes amd64/arm64 to
`ghcr.io/mikouer/sce_group_assignment/md2xwiki`, and receives only
`registry_token: GITHUB_TOKEN`. `version` is the commit SHA; publishing uses that
tag rather than `latest`. Wiki credentials never enter image builds.

No second Git repository is needed: GHCR stores the image as a package associated
with this repository. GitHub supplies `GITHUB_TOKEN` automatically; do not create
a registry token secret. After the image build/push succeeds, the publishing job
pulls that exact image and publishes the trees from `xwiki.toml`.

The publishing job uses the `xwiki` environment. Configure:

| Setting | Where | Purpose |
| --- | --- | --- |
| `XWIKI_USERNAME`, `XWIKI_PASSWORD` | Repository or `xwiki` environment secrets | Publisher account |
| `XWIKI_EXPECTED_USER` (optional) | Repository or `xwiki` environment variable | Exact authenticated reference |
| `XWIKI_PUBLISH_ENABLED` | Repository variable | Leave unset until docs are ready; then `true` |

Publishing runs on GitHub-hosted `ubuntu-latest`, which includes Docker; no
self-hosted runner or runner-label variable is needed. The course wiki must be
reachable from that runner. For manual publishing, select target `production`.
Publishing needs the default branch and the enabled variable. Pruning is off
unless explicitly selected for manual production deployment. Enable repository
Actions access to the GHCR package if needed.

Runs are serialized with `cancel-in-progress: false`. REST has no multi-page
transaction or verified compare-and-swap: coordinate local runs and human edits
too. A remaining race exists between the last drift check and a human write.
Artifacts retain compiled output, configuration, backups and summaries without
credentials; backups can contain private wiki content and need restricted access.

## Safety and supported syntax

Page reads and ownership hashes use REST `rawTitle`, not the rendered `title`.
Rendered titles can contain HTML entities or be derived from a heading when the
stored title is empty. Sending them back as titles causes double escaping and
read-back failures. Raw titles and content are compared exactly; no HTML
unescaping or relaxed content verification is applied.

If an older image failed after saving an escaped title, retain the failure
artifacts and run the updated image with the same configuration/deployment ID.
The pending write is recovered only when the stored page matches its journaled
hash. This prevents another escape layer but does not undo an already-stored
literal `&amp;` title; review the original title in the backup/wiki history
before correcting it. Header-only pages retain empty raw titles, and their
ownership baselines are refreshed without rewriting page content.

All selected pages, links, headers and hierarchy are validated before publishing.
Relative Markdown links use the complete declared source-to-destination map;
directory links resolve to their YAML node. Heading fragments have explicit
GitHub-style anchors. Local images/files become path-hashed attachments; remote
images remain remote. HTTP/HTTPS/mailto links are allowed; unsafe schemes fail.

CommonMark formatting, reference links, tables, nested lists, blockquotes and code
are supported. Bare `<br>`, `<br/>` and `<br />` tags (case-insensitive) become
native XWiki line breaks, including inside table cells; consecutive tags retain
consecutive breaks. This applies to `push-file`, `push-tree` and configured
publishing alike. They are not passed through as HTML. Tags with attributes,
other HTML, and Mermaid/math extensions remain explicit errors. Line-break tags
in code or escaped Markdown remain literal. Literal XWiki-looking text is
escaped; macro-looking code uses safe verbatim blocks.

Reserved per-root manifests retain ownership hashes and pending operations.
Adopted existing content is backed up before replacement. Drift on replaceable
managed content fails unless deliberately overridden; header-only pages never
replace human content. Corrupt/out-of-scope/foreign manifests fail closed.
Interrupted operations reconcile by read-back, with local bootstrap journals
before creating roots. Unchanged reruns do not mutate resources or ownership.
Pruning touches only unchanged, owned removed resources, never roots or pages
with unrelated descendants/attachments/objects/comments/translations.

```bash
.venv/bin/python -m pytest md2xwiki/tests
.venv/bin/md2xwiki build --config xwiki.toml --output build/xwiki
.venv/bin/md2xwiki check --config xwiki.toml
.venv/bin/md2xwiki sync --config xwiki.toml --dry-run
```
