---
pageName: "d. Verification and Validation Summary"
---
# Verification and validation summary

**Status:** Finalized for the formative cycle. Evidence so far comes from one report, [ER-01](reports/ER-01.md): the cognitive walkthrough on build B1 and a follow-up check of the log and summary on build B1.1. The planned summative test ([ER-02](reports/ER-02.md)) will add to it.

Verification asks whether a Function works as specified (Premises). Validation asks whether it has the intended effect (Claims). The two are rolled up separately below, and a Premise or Claim no report has addressed is marked untested.

## Evidence

| Evidence | Bears on | Assessed against criteria | Verdict |
| --- | --- | --- | --- |
| [EV-01](evidence/EV-01.md) | PR1 | Met | Supports |
| [EV-02](evidence/EV-02.md) | PR2 | Met | Supports |
| [EV-03](evidence/EV-03.md) | PR3 | Partly met | Qualifies |
| [EV-04](evidence/EV-04.md) | CL3 | Not assessed | Qualifies |
| [EV-05](evidence/EV-05.md) | PR4 | Partly met | Qualifies |

## Verification (Premises)

| Premise | Evidence | Roll-up | Notes |
| --- | --- | --- | --- |
| [UC01-F1-PR1](../2-specification/use-cases/uc01/UC01-F1-PR1.md) Initial reminder | [EV-01](evidence/EV-01.md): met, supports | **Supported** | The reminder logic and wording worked as specified in the scripted prototype. The sensing it depends on is assumed, not verified. |
| [UC01-F2-PR2](../2-specification/use-cases/uc01/UC01-F2-PR2.md) Bounded reminders and postponement | [EV-02](evidence/EV-02.md): met, supports | **Supported** | The bounded sequence and single postponement worked as specified in B1. The announced delay and the five-reminder limit were added later. |
| [UC01-F3-PR3](../2-specification/use-cases/uc01/UC01-F3-PR3.md) Escalation and closure | [EV-03](evidence/EV-03.md): partly met, qualifies | **Qualified** | Cleber's ending step and the scripted escalation log passed. Sarah's responses, the Gilbert path and real delivery were not exercised. |
| [UC01-F4-PR4](../2-specification/use-cases/uc01/UC01-F4-PR4.md) Log and summary | [EV-05](evidence/EV-05.md): partly met, qualifies | **Qualified** | The prototype's log check passed and the summary worked as specified on B1.1. Plate, sensor and data-gap behaviour depend on real sensing and are planned for [ER-02](reports/ER-02.md) (Session 1). |
| [UC01-F2-PR5](../2-specification/use-cases/uc01/UC01-F2-PR5.md) Eating confirmation | None | **Untested** | Added after the walkthrough; to be checked against ground truth ([M-06](../1-foundation/human-factors/measures/M-06.md)) in [ER-02](reports/ER-02.md). |

## Validation (Claims)

| Claim | Evidence | Roll-up | Notes |
| --- | --- | --- | --- |
| [UC01-F1-CL1](../2-specification/use-cases/uc01/UC01-F1-CL1.md) Reminder works | None | **Untested** | Needs measured responses ([M-02](../1-foundation/human-factors/measures/M-02.md)); planned for [ER-02](reports/ER-02.md). |
| [UC01-F2-CL2](../2-specification/use-cases/uc01/UC01-F2-CL2.md) Follow-ups help | None | **Untested** | As CL1. |
| [UC01-F2-CL3](../2-specification/use-cases/uc01/UC01-F2-CL3.md) Retained perceived autonomy | [EV-04](evidence/EV-04.md): not assessed, qualifies | **Qualified** | Rests entirely on evaluators' answers to open questions; the Likert criterion has not been applied. |
| [UC01-F3-CL4](../2-specification/use-cases/uc01/UC01-F3-CL4.md) Alert understood by Sarah | None | **Untested** | Nobody played Sarah. |
| [UC01-F4-CL5](../2-specification/use-cases/uc01/UC01-F4-CL5.md) Summary understood by Sarah | None | **Untested** | Nobody played Sarah. |

## Weighting and what the verdicts mean

- **No conflicts between Evidence entries.** Each Premise or Claim has at most one entry, so each roll-up is that entry's verdict.
- **Not assessed.** The only verdict resting entirely on criteria that were not applied is CL3 ([EV-04](evidence/EV-04.md)). It is a judgement from two evaluators, not a result against the 4 out of 5 threshold.
- **Build.** EV-01 to EV-04 concern build B1. B1.1 has since added the chime and light, the announced postponement delay and the eating-confirmation rule, in response to the findings. The verdicts stand as recorded for B1 and are repeated on the build used in [ER-02](reports/ER-02.md).
- **Verification and validation are different findings.** The walkthrough suggests the reminder and postponement logic works as specified (verification, in a scripted setting). Whether it helps Cleber eat, or whether Sarah can use the alert and summary, is not known (validation, untested except the first look at CL3).
