# SCE_group_assignment

The course documentation lives in [`docs/xwiki/`](docs/xwiki) and is published
to the group XWiki using the converter in [`md2xwiki/`](md2xwiki/README.md).
Edit the Markdown files here rather than editing managed page bodies directly
in the wiki. The publisher detects conflicting wiki edits instead of silently
overwriting them.

## Working on the documentation

| Location | Purpose |
| --- | --- |
| `docs/xwiki/1-foundation/` | Foundation, published beneath the wiki's `Main` page |
| `docs/xwiki/2-specification/` | Specification |
| `docs/xwiki/3-evaluation/` | Evaluation |
| `xwiki.toml` | Selects the published root folders and the destination wiki |

### How the tree works

Each page-tree folder has an **`index.yaml`** defining its own page and children.
For example, `docs/xwiki/3-evaluation/reports/index.yaml` currently contains:

```yaml
pageText: EvaluationReports.md
children:
  - ER-01.md
```

`pageText` is the Markdown file for the folder's page. Each entry in `children`
is either a Markdown file (a leaf page) or a folder with its own `index.yaml`
(a page with children). Paths are relative to that index's folder. Only pages
listed in these indexes are published; adding a file alone is not enough.
Use `children: []` for a folder page without children.

Every page file starts with YAML front matter:

```markdown
---
pageName: "ER-02: Follow-up evaluation"
---
# Follow-up evaluation

Write the page content here.
```

**`pageName` defines the wiki path segment, not the filename, folder name, or
heading.** Write it as plain text, not URL-encoded text. The parent indexes
determine where that segment sits in the hierarchy. The header is not uploaded.

Keep existing `pageName` values unchanged: some wiki technical names differ
from the displayed titles, such as Foundation's `Main`. Renaming a `pageName`
or moving a page to another parent changes its destination; it does not move
or delete the old wiki page.

When a file has content after the header, publishing replaces that page's
body while retaining its existing title. A **header-only file preserves the
existing body, title, and syntax**; if its destination is missing, an empty page
is created. This is how existing overview/template pages are left untouched.
Removing the body is therefore not a way to clear a wiki page.

### Adding a page

1. Create the Markdown file in the appropriate existing folder, with a unique
   `pageName` and the page content. Follow a similar existing case's structure.
2. Add its filename to that folder's `index.yaml` under `children`. For example,
   add `- ER-02.md` alongside `- ER-01.md` in the reports index.
3. Link related records to the new file and compile the complete tree locally
   before submitting the change.

### Adding a subsection with its own children

Create a new folder beneath the intended parent. For example:

```text
docs/xwiki/3-evaluation/follow-up/
  index.yaml
  FollowUp.md
  Study01.md
```

The new folder's `index.yaml` could contain:

```yaml
pageText: FollowUp.md
children:
  - Study01.md
```

Give `FollowUp.md` a header such as `pageName: "g. Follow-up Studies"`.
Give `Study01.md` its own header and content. Then append `- follow-up` to
`docs/xwiki/3-evaluation/index.yaml` under `children`, retaining its existing
entries. This creates a subsection beneath Evaluation and a study page beneath
that subsection. Repeat the same folder/index pattern for deeper nesting.

For an entirely new **top-level section**, create its tree under `docs/xwiki/`
and register it in `xwiki.toml`. For example, a `4-results/` folder with an
index and a root page named `pageName: "4. Results"` needs:

```toml
[[roots]]
source = "4-results"
```

Append this to the existing configuration; do not replace the other roots.
Subsections within an existing root do not need changes to `xwiki.toml`.

### Links and attachments

Use relative Markdown links to source files for references, including record
codes, rather than plain identifiers or guessed wiki URLs:

```markdown
[ER-01](ER-01.md)
[ST-04](../../1-foundation/operational-demands/stakeholders/ST-04.md)
```

These examples are relative to a file in `docs/xwiki/3-evaluation/reports/`.
The converter resolves them to the actual wiki destinations. Heading links such
as `[build history](../artifacts/AT-01.md#builds)` are supported too.

Store images or supporting files near their page, for example in an `assets/`
folder, and reference them with relative Markdown links. Referenced local files
are uploaded as attachments; the assets folder does not need an `index.yaml`.
Use ordinary HTTPS links for external sources. When renaming a source file,
update its index entry and all links that refer to it.

## Local compilation and publishing

From the repository root, install the converter once:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e "md2xwiki[test]"
```

Compile all configured sections together:

```bash
.venv/bin/md2xwiki build --config xwiki.toml --output build/xwiki
```

This is offline, requires no wiki credentials, and checks the metadata,
destinations, links, and supported Markdown. Generated output stays in `build/`;
edit the source files, not that output. Compile the full configuration because
cross-section links cannot be resolved by publishing a single isolated file.

Changes to the documentation on `main` trigger the GitHub workflow: it builds
and pushes the Docker image, then publishes all configured trees when
`XWIKI_PUBLISH_ENABLED=true`. Pull requests do not publish or run validation;
compile locally before merging. Missing pages are created automatically.
Removing a page from an index stops publishing it but does **not** delete its
existing wiki page by default; deletion requires deliberate, guarded pruning.
Update any links to removed pages so the remaining documentation still compiles.

See the [course documentation guide](docs/README.md) for the existing wiki
mapping and the [publisher guide](md2xwiki/README.md) for workflow settings,
supported syntax, recovery, and pruning.

## Test

To test the publisher on the real wiki without publishing the course trees,
use the small sample at `/view/test/`:

```bash
bash scripts/test-xwiki.sh
```

Start Docker and ensure you can reach the course wiki first. The script prompts
for credentials and leaves the sample page for inspection. It writes to the
shared `test` page, so coordinate with others before running it. The script
prints the page URL and the guarded cleanup command.