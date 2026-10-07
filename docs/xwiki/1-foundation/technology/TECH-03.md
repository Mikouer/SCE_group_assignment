---
pageName: "Technology Option 3"
---
# TECH-03: Monitoring camera system

| Field | Description |
| --- | --- |
| ID | TECH-03 |
| Name | Monitoring camera system |
| Status | Finalized |
| Evidence basis | General technology literature on home camera monitoring for older adults; provisional, no direct trial with Cleber. |
| Category | Sensing / continuous video surveillance. |
| Capabilities | Fixed cameras throughout the home (kitchen, living areas) continuously record and analyze activity, detecting whether Cleber has entered the kitchen, approached the fridge, or eaten, without requiring any reminder or check-in step. Footage would be reviewed by Sarah and meal missing with respect to meal times would be directly notified ([ST-03](../operational-demands/stakeholders/ST-03.md)) at any time, not just at scheduled visits. |
| Limitations | Captures more than what is needed, continuous visual coverage can feel pressuring. No limit to what is recorded. |
| Maturity and feasibility | High — commercial smart-home camera systems are mature and inexpensive to deploy; the technical barrier is low, but the social and ethical barrier is high. |
| Failure and fallback behaviour | Camera outage or obstruction (e.g. accidental coverage of unwanted recordings, out of frame) leads to silent monitoring gaps that are easy to miss, since there isn't a reminder mechanism prompting Cleber in the meantime. |
| Benefits | Sarah would be able to have a complete picture of Cleber's day and the data recorded can help personalize the tool or make mealtimes efficient, in principle. |
| Drawbacks | Strains [VT-01] (autonomy/dignity vs. safety) more severely than any other option considered. Continuous visual monitoring is associated with reduced dignity and a pressuring sense of surveillance rather than support in the literature. Additionally, a controlled study directly compares camera monitoring to robot monitoring and found that older adults tend to perform behaviour to avoid the surveilance as much as possible, more than with an embodied robot. |
| Selected or rejected | Rejected. A continuous camera system optimizes visibility but sacrifices Cleber's privacy creating a sense of being watched rather than supported. This goes against the "quiet companion, not a monitor" framing essential to Echo's design ([RP-01](../../2-specification/personas/robot/RP-01.md)). Task-scoped kitchen sensing (TECH-02) and an embodied, opt-in check-in (TECH-01) were judged to meet the same safety need with substantially less erosion of dignity. |

## Research link

Caine, K., Šabanović, S., & Carter, M. (2012).
[The effect of monitoring by cameras and robots on the privacy enhancing behaviors of older adults](https://doi.org/10.1145/2157689.2157807).
In *Proceedings of the 7th ACM/IEEE International Conference on Human-Robot Interaction (HRI '12)* (pp. 343–350).

This directly compared a camera, a stationary robot, and a mobile robot in older adults' homes and found camera monitoring produced the strongest privacy-protective behavioral response of the three, grounding the rejection in comparative evidence rather than assumption alone. [TECH-01](./TECH-01.md) and [TECH-02](./TECH-02.md) show the robot and task-scoped sensing alternatives this project selected instead.
