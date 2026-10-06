---
pageName: "Technology Option 2"
---
# TECH-02: Speaker assistance and caregiver alerts

| Field | Description |
| --- | --- |
| ID | TECH-02 |
| Name | Speaker assistance and caregiver alerts |
| Status | In Progress |
| Evidence basis | The breakdown pattern in [SA-01](../operational-demands/activities/SA-01.md), general technology literature, and the existing wiki's selected-technology record; provisional. |
| Category | Sensing, automation and socially assistive interaction. |
| Capabilities | A kitchen-based companion connected to appliance sensors can offer spoken reminders when a prepared meal appears untouched. A suitable consumption check would stop reminders after eating. Unresolved meal situations can alert Sarah ([ST-03](../operational-demands/stakeholders/ST-03.md)), with non-urgent summaries for her visits. |
| Limitations | Appliance activity is not confirmed consumption. Camera use raises privacy concerns. Enough suitable prepared food must be available; sensing alone does not establish that requirement. |
| Maturity and feasibility | Medium to high for available smart-home components; integration, decision logic and meal-consumption accuracy remain project work. |
| Failure and fallback behaviour | Dead batteries or disconnection can cause false alerts or silent failure. Sensor-health checks are needed; a fault missed between Sarah's visits can remain undetected for days. |
| Benefits | Intended support for the goal in [SA-01](../operational-demands/activities/SA-01.md) and security ([HV-01](../human-factors/human-values/HV-01.md)), with better visibility of unresolved meals between visits. These are proposed benefits, not evaluated outcomes. |
| Drawbacks | Autonomy/privacy versus safety; alert fatigue and extra on-call demands on Sarah. [VT-01](../human-factors/value-tensions/VT-01.md) records the core trade-off. |
| Selected or rejected | Selected, as recorded on the existing wiki page; the DOCX left this field open. |

## Research link

Hofstede, B. M., et al. (2025).
[A field study to explore user experiences with socially assistive robots for older adults: emphasizing the need for more interactivity and personalisation](https://doi.org/10.3389/frobt.2025.1537272).

This supports discussion of interactivity and personalisation in older-adult
robot use, not a claim that the proposed meal sensor is accurate. [RP-01](../../2-specification/personas/robot/RP-01.md) describes
Echo's intended profile; [AT-01](../../3-evaluation/artifacts/AT-01.md) states which parts the current build can address.
