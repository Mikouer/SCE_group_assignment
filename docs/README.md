# Course documentation

`xwiki/` contains the project content imported from `SCE_Group5.docx`, excluding
the example case and the removed neighbour stakeholders. Hanz is ST-04.
`review/` contains presentation feedback and source task notes; it is not a wiki
publishing input.

## Publishing layout

The Foundation, Specification and Evaluation hierarchy was read through XWiki
REST GET requests on 6 October 2026. The import preserves all 36 existing
destinations. Folder names below are convenient source names, not wiki names:

| Source branch beneath `docs/xwiki/` | Existing wiki path beneath `/view/` |
| --- | --- |
| `1-foundation/` | `Main/` |
| `1-foundation/operational-demands/` | `Main/sdf/` |
| `1-foundation/operational-demands/activities/` | `Main/sdf/Environments/` |
| `1-foundation/operational-demands/stakeholders/` | `Main/sdf/Stakeholders/` |
| `1-foundation/operational-demands/problem-scenarios/` | `Main/sdf/3.%20Problem%20Scenario/` |
| `1-foundation/human-factors/` | `Main/b.%20Human%20Factors/` |
| `1-foundation/human-factors/concepts/` | `Main/b.%20Human%20Factors/Music%20and%20Cognition/` |
| `1-foundation/technology/TECH-01.md` | `Main/c.%20Technology/Music%20Management/` |
| `2-specification/design-scenarios/` | `2.%20Specification/b.%20Design%20Scenario/` |
| `2-specification/personas/` | `2.%20Specification/a2.%20Personas/` |
| `2-specification/use-cases/` | `2.%20Specification/b.%20Use%20Cases/` |
| `2-specification/team-design-patterns/` | `2.%20Specification/Requirements/` |
| `2-specification/interaction-design-patterns/` | `2.%20Specification/Claims/` |
| `3-evaluation/artifacts/` | `3.%20Evaluation/a.%20Prototype/` |
| `3-evaluation/reports/` | `3.%20Evaluation/b.%20Test/` |
| `3-evaluation/evidence/` | `3.%20Evaluation/Evidence/` |

Every branch has mandatory `index.yaml` metadata, and each case has its own
Markdown page. Existing case destinations are reused; new records are added
as children of the corresponding existing template/category page. Functions,
premises and claims have separate pages beneath their use case.

The three missing evaluation pages use `d. Verification and Validation Summary`,
`e. Discussion and Limitations`, and `f. Next Iteration`. The traceability graph
is deliberately deferred.

Header-only overview/template files preserve their current wiki content and
titles. They do not import or duplicate template/example prose into this repo.
Nonempty case files replace their explicitly mapped page bodies when published.

## References

Artifact identifiers in prose and fields are relative Markdown links to the
actual case file, for example:

```markdown
[ST-04](ST-04.md)
[HV-01](../../human-factors/human-values/HV-01.md)
```

The publisher resolves these against the complete configured source map and
emits escaped XWiki document references. Do not change a link into a path derived
from a display title: several current technical paths differ from their titles.

Compile all three roots together, since there are cross-section links:

```bash
.venv/bin/md2xwiki build --config xwiki.toml --output build/xwiki
```

The shared container workflow uses this same configuration. A standalone
`push-file` or single-root `push-tree` cannot resolve references to pages absent
from its source map. No automatic publishing is enabled by adding these docs;
the existing protected environment and `XWIKI_PUBLISH_ENABLED` gate still apply.

## Corrections and outstanding evidence

- Hanz's record uses the existing ST-04 destination. Removed stakeholder
  references were deleted, not redirected to the doctor.
- Security is HV-01 and achievement is HV-02. Swapped references in the robot
  profile and objective story are corrected.
- Team-pattern claims now reference the actual follow-up, autonomy and
  escalation claim identifiers.
- Sarah's persona describes the alert recipient/caregiver role rather than
  incorrectly assigning her Cleber's meal-reminder interaction.
- The health value's missing holders are filled from its own situated meanings.
  Health is not misrepresented as an additional category in Schwartz's theory.
- DOI/PubMed metadata was checked. The citation-only HFC-02 entry is expanded
  from Dixon, Piper and Lazar's study, with its population and evidence limits.
  The institution-proxied link is replaced by public DOI/PubMed references.
- The live wiki supplies the technology selection left open in the DOCX:
  TECH-01 is rejected and TECH-02 selected.
- The source's travel draft reused kitchen/meal data; those unrelated fields
  remain explicitly unspecified. The health-checkup activity was only a title.
- The undefined `HVF1`, a validated autonomy instrument, numerical acceptance
  thresholds, a justified escalation interval, and exact build-specific
  wording evidence cannot be recovered from the supplied material.
- ER-01 is a draft plan, not a completed report. Verification/validation entries
  are **Not assessed**, and no evidence entity or measured outcome is invented.
  Next-iteration proposals are derived from the supplied limitations and feedback.

The source allocation sketch is retained as the team-pattern attachment.
Its activity/consumption ambiguity is explained next to the figure.
