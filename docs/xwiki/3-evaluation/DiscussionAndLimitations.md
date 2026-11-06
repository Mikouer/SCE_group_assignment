---
pageName: "e. Discussion and Limitations"
---
# Discussion and limitations

This page interprets the formative cycle ([ER-01](reports/ER-01.md), build B1) and the planned summative test ([ER-02](reports/ER-02.md), build B2) in relation to [UC01](../2-specification/use-cases/uc01/UC01.md), its Stakeholders and the methods used. Verification (does the Function work as specified?) and Validation (does it have the intended effect?) are kept apart.

## What the formative cycle showed

**Verification.** For the human-facing steps, both evaluators answered yes throughout, and the prototype's scripted conformance check ([M-04](../1-foundation/human-factors/measures/M-04.md)) recorded no failure in 26 runs. This speaks for [PR1](../2-specification/use-cases/uc01/UC01-F1-PR1.md) and [PR2](../2-specification/use-cases/uc01/UC01-F2-PR2.md). [PR3](../2-specification/use-cases/uc01/UC01-F3-PR3.md) is qualified: Cleber's ending step worked, but Sarah's responses and the notification of Gilbert were not walked. [PR4](../2-specification/use-cases/uc01/UC01-F4-PR4.md) was not walked in the walkthrough; on build B1.1 the prototype's own log check and an inspection of the summary were positive ([ER-01](reports/ER-01.md)), so it is qualified, since sensing is simulated. All of this concerns the prototype's scripted logic and the evaluators' judgement, not real sensing, timing or delivery.

**Validation.** Only [CL3](../2-specification/use-cases/uc01/UC01-F2-CL3.md) received a first look. Neither evaluator reported pressure and both found it possible to refuse or postpone, so the claim is qualified rather than supported: no criterion was applied. [CL1](../2-specification/use-cases/uc01/UC01-F1-CL1.md), [CL2](../2-specification/use-cases/uc01/UC01-F2-CL2.md), [CL4](../2-specification/use-cases/uc01/UC01-F3-CL4.md) and [CL5](../2-specification/use-cases/uc01/UC01-F4-CL5.md) are untested.

So far the scripted interaction looked understandable and non-pressuring to two evaluators. Whether it helps anyone eat, or whether Sarah can use the alert and summary, is not known.

## Verdicts that rest on weak evidence

The CL3 verdict rests entirely on evaluators' answers to open questions, with no threshold applied. The verdicts for PR1 to PR3 rest on yes-answers and on a conformance check run on the prototype's own script. Every step answer was yes, which suggests the questions did not discriminate. These verdicts look more settled than they are and should carry little weight in the next iteration.

## Unexpected findings and what followed

Three findings did not map to any Premise or Claim: a voice with no visible source may startle or confuse Cleber, particularly when he is asleep; evaluators wanted to know when Echo would speak again after "not now"; and an empty plate may not mean the food was eaten. The first two led to a chime and light before speech and an announced 30-minute delay (build B1.1). The third led to the new Premise [PR5](../2-specification/use-cases/uc01/UC01-F2-PR5.md), added after the formative cycle and still untested. Sleep interruption and discarded food remain unresolved.

## Limitations of the formative cycle

- Two evaluators who only imagine the persona, which is hard for someone with dementia; a small sample.
- Nobody played Sarah, and the log and summary were not walked.
- The prototype is scripted: the facilitator supplies the meal-state events, so it says nothing about the accuracy of real sensors or the camera, speaker coverage across rooms, real timing, or any effect on a person. Appliance activity must not be treated as proof that food was consumed.

## Limitations of the planned study

- Small, exploratory sample; a short observation of days; not statistically powered.
- Assisted living, not a private home, with staff nearby who may change behaviour; a family caregiver stands in for the professional caregiver Sarah.
- Questionnaire-based measurement of autonomy ([M-03](../1-foundation/human-factors/measures/M-03.md)) may be hard for some residents, so it is read aloud and complemented by observation ([EM-02](../1-foundation/human-factors/evaluation-methods/EM-02.md)).
- Real long-term acceptance is not shown.

## Reasons for not eating

The current design does not distinguish forgetting, sleeping, lack of appetite and dissatisfaction with the food. These can all lead to the same reminder and escalation sequence, so Echo may intervene even when Cleber has chosen not to eat at that moment. This limits the interpretation of [M-02](../1-foundation/human-factors/measures/M-02.md): not eating after a prompt does not necessarily mean the reminder failed.

## Meal preferences

Sarah prepares meals several days in advance, so Cleber's preference when a meal is chosen may differ from what he wants when it is served. The design supports later changes in preference only in a limited way, so a refusal can be mistaken for a reminder failure when it is a mismatch with the food.

## Cognitive and emotional effects

Cleber may forget an earlier prompt or believe he has already eaten, so repeated reminders could feel confusing, corrective or repetitive despite their gentle wording. Whether repeated use causes frustration or reduces perceived autonomy is not established. [HFC-02](../1-foundation/human-factors/concepts/HFC-02.md) motivates preserving agency, but it does not show the effect of this particular sequence.

## Discussion

[TDP-01](../2-specification/team-design-patterns/TDP-01.md) and [IDP-01](../2-specification/interaction-design-patterns/IDP-01.md) balance regular meal support with independence by limiting gentle prompts before involving Sarah. Autonomy, however, depends on understanding why Cleber is not eating, not only on how polite a prompt is. The prototype is better suited to inspecting whether the reminder and escalation flow can operate than to establishing its effect on behaviour or autonomy. The formative cycle did not test escalation timing, so [VT-01](../1-foundation/human-factors/value-tensions/VT-01.md) remains open. Future work should consider context-sensitive responses rather than treating every unresolved meal as the same event.
