---
pageName: "f. Next Iteration"
---
# Next iteration

**Status:** In Progress.

**Goal.** Build B2 with real sensing and run the two-session summative test ([ER-02](reports/ER-02.md)): staged verification of the Premises first, then validation with residents and caregivers.

Each finding of the formative cycle ([ER-01](reports/ER-01.md)) is routed to the part of the report it changes.

| Finding or gap | Routed to | Change | Status |
| --- | --- | --- | --- |
| A voice with no visible source may startle or confuse Cleber. | Specification ([UC01](../2-specification/use-cases/uc01/UC01.md), [IDP-01](../2-specification/interaction-design-patterns/IDP-01.md), [RP-01](../2-specification/personas/robot/RP-01.md)); [AT-01](artifacts/AT-01.md) | A chime and a light precede each spoken reminder. B1.1 only logs them; B2 should play and show them. | Specified; B2 pending |
| Sleep interruption remains unresolved. | Specification | Detect whether Cleber is awake or in the living room, for example with a movement sensor, and tune Echo's reach across rooms. | Deferred |
| Postponement timing was unclear. | Specification ([UC01](../2-specification/use-cases/uc01/UC01.md), [TECH-02](../1-foundation/technology/TECH-02.md)); AT-01 | Echo announces the 30-minute delay. Let Cleber choose the delay if needed. | Announcement specified and in B1.1; choice deferred |
| An empty plate may not mean the food was eaten. | Specification ([PR5](../2-specification/use-cases/uc01/UC01-F2-PR5.md)); Foundation ([M-06](../1-foundation/human-factors/measures/M-06.md), [EM-05](../1-foundation/human-factors/evaluation-methods/EM-05.md)) | Define presence-detection rules and the conditions for "eating confirmed" from camera evidence; add checks for false positives. | PR5 and M-06 added; rules to define |
| The log needs fields the walkthrough did not exercise. | Foundation ([M-04](../1-foundation/human-factors/measures/M-04.md)); Specification ([F4](../2-specification/use-cases/uc01/F4.md), [PR4](../2-specification/use-cases/uc01/UC01-F4-PR4.md), TECH-02) | Record pre-speech cues, detection confidence and ground truth. | M-04 updated; the other pages to do |
| PR3 is qualified: Sarah's responses and Gilbert's notification were not walked. | Evaluation | Include Sarah's path and alert delivery ([M-07](../1-foundation/human-factors/measures/M-07.md)) in ER-02. | Planned |
| PR4 is untested: the log and summary were not walked. | Evaluation | Verify the system-generated log and summary in Session 1 on B2. | Planned |
| CL3 is qualified and its criterion was never applied; the criterion is testable. | Evaluation | Apply [M-03](../1-foundation/human-factors/measures/M-03.md) and the avoidance observation in [ER-02](reports/ER-02.md), Session 2. | Planned |
| CL1, CL2, CL4 and CL5 have no evidence. | Evaluation | Measure them in [ER-02](reports/ER-02.md), Session 2. | Planned |
| Evaluators suggested small talk and a post-meal exchange. | Artifact | Add an optional short post-meal prompt, kept optional to avoid burden. Small talk deferred. | Deferred |

## Later

- Switch the interaction from a screen to voice chat, so a person can speak to the robot.
- Tune the reminder windows and timings.
- Extend alerts to close contacts beyond Sarah.
- Add a check on whether Cleber enjoyed the meal.
