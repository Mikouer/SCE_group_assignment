---
pageName: UC01-F2-PR2
---
# UC01-F2-PR2: Bounded and accurate reminder sequence

| Field | Description |
| --- | --- |
| ID | UC01-F2-PR2 |
| Function | [F2](F2.md). |
| Evaluation Method(s) / Measure(s) | [EM-04](../../../1-foundation/human-factors/evaluation-methods/EM-04.md) and [M-04](../../../1-foundation/human-factors/measures/M-04.md) in the current cycle; a later log-based run would use [EM-03](../../../1-foundation/human-factors/evaluation-methods/EM-03.md). |
| Verification Criteria | In every scripted scenario ([M-04](../../../1-foundation/human-factors/measures/M-04.md)): Echo gives no more than three reminders at the configured interval and without raised volume; one postponement restarts the sequence from the first reminder and a second postponement does not; kitchen activity alone is never logged as eaten (it is logged as unconfirmed or uncertain); the camera stays off until kitchen activity occurs, then stays on until the meal is complete (Cleber says he is done, or the camera detects the end of consumption) and while the escalation sequence is happening; Cleber saying he is done is recorded as done, though he is never required to say it; when there is no kitchen activity the camera stays off and the sequence continues. The properties concerned are correctness, timing and conformity to the specified interaction behaviour ([IDP-01](../../interaction-design-patterns/IDP-01.md)). In the cognitive walkthrough only the human-facing steps (steps 4 and 5) are judged: the evaluators' answers to the four questions show whether the step works as specified for the persona. |
| Action Sequence step(s) | [UC01](UC01.md), steps 3-5. |
| Assessment | Not assessed; a formative walkthrough is planned in [ER-01](../../../3-evaluation/reports/ER-01.md). |
