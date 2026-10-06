---
pageName: "e. Discussion and Limitations"
---
# Discussion and limitations

This discussion imports the source document's design analysis. No supporting
evaluation logs, result tables or completed report were supplied, so the
limitations below are not represented as newly verified empirical findings.

## Reasons for not eating

The current design does not adequately distinguish forgetting, sleeping,
lack of appetite, intentional postponement and dissatisfaction with the
available food. These can all lead to a similar reminder/escalation sequence.
Echo may therefore intervene even when Cleber has intentionally chosen not
to eat at that moment.

This limits the interpretation of [M-02](../1-foundation/human-factors/measures/M-02.md): not eating after a prompt does not
necessarily mean that the reminder failed.

## Meal preferences

Sarah prepares meals several days in advance. Cleber's preference when a meal
is selected may differ from what he wants when it is served. The design offers
limited support for later changes in preference, so refusal can be mistaken for
a reminder failure instead of a mismatch between food and current preference.

## Cognitive and emotional effects

Cleber may forget an earlier prompt or believe he has already eaten. Repeated
reminders could therefore feel confusing, corrective or repetitive despite
their gentle wording. The source does not establish whether repeated use causes
frustration or reduces perceived autonomy or competence.

[HFC-02](../1-foundation/human-factors/concepts/HFC-02.md) motivates preserving agency, but it does not establish the effect of this
particular sequence.

## Evaluation limitations

The described evaluation setup uses a tester acting as Cleber rather than
a representative person with dementia. Such a setup can inspect [UC01](../2-specification/use-cases/uc01/UC01.md)'s flow
but cannot reliably reproduce the intended population's cognitive or emotional
responses. Short, controlled interactions also cannot establish long-term
effectiveness or acceptance in everyday home life.

[AT-01](artifacts/AT-01.md)'s detection and simulation descriptions need clarification. Appliance
activity must not be treated as proof that food was consumed.

## Measuring autonomy

Questionnaire-based assessment may be difficult for some people with dementia.
[M-03](../1-foundation/human-factors/measures/M-03.md) remains unspecified and provisional; self-report would need appropriate
accessible interviews and behavioural observation, as proposed in [EM-02](../1-foundation/human-factors/evaluation-methods/EM-02.md).

## Discussion

[TDP-01](../2-specification/team-design-patterns/TDP-01.md) and [IDP-01](../2-specification/interaction-design-patterns/IDP-01.md) balance regular meal support with independence by limiting
gentle prompts before involving Sarah. However, autonomy depends on understanding
why Cleber is not eating, not only on the politeness of a prompt.

The prototype is better suited to inspecting whether the reminder/escalation
flow can operate than to establishing its effect on behaviour or autonomy.
Future work should consider context-sensitive responses rather than treating
every unresolved meal as the same event. [VT-01](../1-foundation/human-factors/value-tensions/VT-01.md) remains open.
