# SCE_group_assignment

The Markdown-to-XWiki publisher lives in [`md2xwiki/`](md2xwiki/README.md).
Pages use YAML front matter with `pageName`; mandatory `index.yaml` files
describe the tree hierarchy. `push-file` takes an exact page URL and `push-tree`
takes the source root folder and project URL.
The [course documentation](docs/README.md) is imported from `SCE_Group5.docx`
and mapped to the existing wiki hierarchy. Production publishing remains opt-in.

Test the sample at `/view/test/`, using the same container pipeline
as GitHub Actions:

```bash
bash scripts/test-xwiki.sh
```

Start Docker and ensure you can reach the course wiki first. The script prompts
for credentials, prints the temporary page URL, and leaves the page for
inspection. See the [publisher guide](md2xwiki/README.md) for guarded cleanup,
workflow/environment setup and the `docs/xwiki` layout.