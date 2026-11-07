---
pageName: "Technology Option 2"
---
# TECH-02: Speaker assistance and caregiver alerts
 
| Field | Description |
| --- | --- |
| ID | TECH-02 |
| Name | Speaker assistance and caregiver alerts |
| Status | Finalized |
| Evidence basis | The breakdown pattern in [SA-01](../operational-demands/activities/SA-01.md), general technology literature [1]–[6], provisional. |
| Category | Sensing, automation and socially assistive interaction. |
| Capabilities | **Reach:** speakers in every room play the spoken reminders, so a prompt does not depend on Cleber being in the kitchen. **Trigger:** appliance sensors detect when prepared meals are taken out of their location/that a prepared meal appears untouched; this starts the reminders and does not depend on the camera. **Confirmation:** a camera that only sees the table becomes active only after kitchen activity is detected, and records the meal event. If Cleber never comes to the kitchen there is no kitchen activity, so the camera stays off, eating stays unconfirmed and the reminder sequence continues as normal. Reminders stop after camera-observed consumption when the camera detects meal end or Cleber says he is done; finishing the plate is not required. The camera stays on until then or while escalation is happening. **Plate taken away:** the table camera sees when the plate leaves the table, and the system logs the time between the plate leaving and returning, for Sarah to review later. This is only logged: no reminders are sent while the plate is away. If the plate does not return, the log records that the food was taken and the plate has not returned, and nothing further is sent. **Postponing:** if Cleber does not want to eat, he can postpone once; the reminder sequence then restarts from the first notification, and a second postponement is not accepted. **Escalation:** after three unanswered reminders, Sarah ([ST-03](../operational-demands/stakeholders/ST-03.md)) is alerted (see the sequence below). **Reporting:** logs are turned into a ready-made summary for Sarah's visits, so she does not have to analyse anything herself. **Accessibility:** language options and adjustable light intensity and sensitivity, so prompts can better suit Cleber's preferences and sensory needs. |
| Limitations | Appliance activity is not confirmed consumption, and a table-only camera cannot tell eaten food from discarded food. Once the plate leaves the table, the camera sees nothing; the logged away-time is a proxy (he may be eating in another room, not skipping the meal). The design does not decide what a plate that never returns means; it is logged as it happened. Camera use raises privacy concerns even when limited to the table. Enough suitable prepared food must be available; sensing alone does not establish that requirement. The one-postponement limit is a design choice that has not been tested with Cleber. Language availability and the effects of accessibility settings depend on the selected hardware and software and would need to be checked with Cleber. |
| Maturity and feasibility | Medium to high for available smart-home components (speakers, appliance sensors, notifications). Integration, decision logic, the report generation and meal-consumption accuracy remain project work. |
| Failure and fallback behaviour | Dead batteries or disconnection can cause false alerts or silent failure. One speaker going offline leaves a room uncovered. If the camera does not activate, the meal is logged as unconfirmed rather than eaten, even if Cleber says he is done. Cleber is never required to say it. Sensor-health checks are needed, and the report should state when data is missing rather than showing a clean day; a fault missed between Sarah's visits can remain undetected for days. |
| Benefits | Intended support for the goal in [SA-01](../operational-demands/activities/SA-01.md) and security ([HV-01](../human-factors/human-values/HV-01.md)), with better visibility of unresolved meals between visits. These are proposed benefits, not evaluated outcomes. |
| Drawbacks | Autonomy/privacy versus safety; alert fatigue and extra on-call demands on Sarah. Limiting postponement trades Cleber's choice against the risk of a missed meal. [VT-01](../human-factors/value-tensions/VT-01.md) records the core trade-off. |
| Selected or rejected | Selected |
 
## Reminder and escalation sequence
 
Timings below are starting values taken from the storyboard scenario and are to be tuned in the evaluation.
 
| Step | What happens | Notes |
| --- | --- | --- |
| 1. First reminder | Soft cue, then a calm check-in using Cleber's name, played on all speakers. | Framed as a check-in, not an alarm. |
| 2. Second reminder | A little more direct, e.g. that the meal is ready in the fridge. | About ten minutes after the first in the storyboard. |
| 3. Third reminder | Final prompt; same voice, no rise in volume. | The three reminders are spread across roughly the first hour. |
| Postponement (once) | If Cleber says he does not want to eat at reminder 1 or 2, Echo tells him when it will return (starting value: 30 minutes), then the sequence restarts from step 1. | Logged and shown to Sarah. A second refusal does not reset the sequence. |
| 4. Escalation | The system does not send a fourth reminder. Sarah receives a short message: which meal, how long since the last confirmed meal, reminders sent, and whether Cleber declined or did not respond. | A refusal and silence mean different things, so the message separates them. |
| 5. Follow-up | Sarah calls Cleber instead of waiting for her next visit. If Cleber then eats, the system sends a short "resolved" update. | Closes the loop so the alert does not stay open. |
| Plate taken away | The camera sees the plate leave the table; the time until it returns is logged. | Logging only: no reminders while the plate is away. If it never returns, it is logged as not returned; no alert. |
| If Sarah does not respond | Repeat once to Sarah, then notify Gilbert ([ST-02](../operational-demands/stakeholders/ST-02.md)) as a backup.|
 
## Logs and the report for Sarah
 
Sarah will not analyse raw data. The system records timestamped events and produces the analysis for her.
 
**What is logged per meal:** when Sarah prepared it, trigger time, each reminder, Cleber's response or postponement, kitchen entry, plate leaving and returning, consumption outcome (eaten / uncertain / not eaten), and any escalation.
 
**What the report highlights, in this order:**
1. Items needing attention: escalations, meals not eaten, and unusually long plate-away times (starting value: more than one hour, a design decision to be tuned; the mealtime study below is only a rough reference for a normal duration).
2. Meals per day by outcome, compared with the previous visit period.
3. Reminder timing: how many reminders each meal needed, the time from first reminder to kitchen entry, and how often postponement was used.
4. Data gaps, such as an offline sensor, so missing data is not read as "all fine".
 
No study found tests the plate-away timing log or the exact one-postponement rule, so both are presented as design decisions.
 
[RP-01](../../2-specification/personas/robot/RP-01.md) describes Echo's intended profile; [AT-01](../../3-evaluation/artifacts/AT-01.md) states which parts the current build can address.

## References

[1] Hofstede, B. M., et al. (2025). [A field study to explore user experiences with socially assistive robots for older adults: emphasizing the need for more interactivity and personalisation](https://doi.org/10.3389/frobt.2025.1537272). *Frontiers in Robotics and AI*, 12.

[2] Pradhan, A., and Lazar, A. (2020). [Voice Technologies to Support Aging in Place: Opportunities and Challenges](https://doi.org/10.1093/geroni/igaa057.1016). *Innovation in Aging*, 4(Suppl 1), 317–318.

[3] Maidhof, C., Offermann, J., and Ziefle, M. (2023). [Eyes on privacy: acceptance of video-based AAL impacted by activities being filmed](https://doi.org/10.3389/fpubh.2023.1186944). *Frontiers in Public Health*, 11, 1186944.

[4] Narayan, A., Goncharova, M., Goncharov, M., Gostine, A., Shah, N., and Kaplan, R. (2024). [Continuous monitoring of eating and sleeping behaviors in the home environments of older adults: a case study demonstration](https://doi.org/10.3389/fpubh.2023.1277714). *Frontiers in Public Health*, 11.

[5] Jung, D., Lee, H., Choi, E., Park, J., and Yoo, L. (2024). [Description of the mealtime of older adults with dementia in a long-term care facility: A video analysis](https://doi.org/10.1016/j.gerinurse.2023.10.029). *Geriatric Nursing*, 55, 176–182.

[6] Mathur, N., Dhodapkar, K., Zubatiy, T., Li, J., Jones, B., and Mynatt, E. (2022). [A Collaborative Approach to Support Medication Management in Older Adults with Mild Cognitive Impairment Using Conversational Assistants (CAs)](https://doi.org/10.1145/3517428.3544830). In *Proceedings of the 24th International ACM SIGACCESS Conference on Computers and Accessibility (ASSETS '22)*, 1–14.
