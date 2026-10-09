---
pageName: "Technology Option 1"
---
# TECH-01: Social robot mealtime companion

| Field | Description |
| --- | --- |
| ID | TECH-01 |
| Name | Social robot mealtime companion |
| Status | In Progress |
| Evidence basis | Social-robot literature and the project's rationale; provisional, with no direct trial with Cleber. |
| Category | Social robot. |
| Capabilities | A physically present device can orient towards Cleber, speak meal reminders, ask whether he has eaten, and contact Sarah ([ST-03](../operational-demands/stakeholders/ST-03.md)) if bounded support is unsuccessful. It can retain a simple meal-status summary for her visits and provide a companion presence. |
| Limitations | Cost and acceptance risk; reminders may not reach a sleeping person. Sarah is not guaranteed to be immediately available outside visits. |
| Maturity and feasibility | Low to medium at the project's scope: commercially available capabilities do not establish long-term reliability in Cleber's home. |
| Failure and fallback behaviour | Hardware/software failure or rejection of the device may stop reminders. Sarah's next visit, normally every two to three days, offers an eventual human fallback, not immediate fault detection. |
| Benefits | Intended support for regular meals, achievement ([HV-02](../human-factors/human-values/HV-02.md)) and continuity between Sarah's visits. These effects remain unvalidated. |
| Drawbacks | Dignity/self-image and acceptance concerns, cost, and extra responsibility shifted to Sarah. [VT-01](../human-factors/value-tensions/VT-01.md) describes the support/independence trade-off. |
| Selected or rejected | Rejected as a stand-alone solution. A robot that follows Cleber would solve the reach problem of the alarms and notes in [SA-01](../operational-demands/activities/SA-01.md), but at a high price. A device that trails him through his home all day is a constant presence, which risks feeling like being watched rather than supported and works against his independence ([HV-02](../human-factors/human-values/HV-02.md), [VT-01](../human-factors/value-tensions/VT-01.md)). A moving robot in a home also adds cost, maintenance and a collision or trip hazard for someone who may be unsteady, and if he rejects the device, all support stops. Following him still does not tell the system whether he ate, so Sarah ([ST-03](../operational-demands/stakeholders/ST-03.md)) would be alerted on unreliable information or not alerted when needed. Fixed speakers in every room and kitchen sensing reach him in each room with much less intrusion and cost. The embodied, calm check-in is still valuable, so it is kept as Echo's interaction layer ([RP-01](../../2-specification/personas/robot/RP-01.md)) on top of the room-wide speakers and kitchen sensing selected in [TECH-02](TECH-02.md). |

## Research links

- Moharana, S., Panduro, A. E., Lee, H. R., and Riek, L. D. (2019).
  [Robots for Joy, Robots for Sorrow: Community Based Robot Design for Dementia Caregivers](https://doi.org/10.1109/HRI.2019.8673206).
- Hofstede, B. M., et al. (2025).
  [A field study to explore user experiences with socially assistive robots for older adults: emphasizing the need for more interactivity and personalisation](https://doi.org/10.3389/frobt.2025.1537272).

The chosen approach is recorded in [TECH-02](TECH-02.md) and [RP-01](../../2-specification/personas/robot/RP-01.md). General robot studies
are not evidence that the particular meal-support claims have been validated.
