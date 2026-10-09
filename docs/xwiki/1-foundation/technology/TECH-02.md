---
pageName: "Technology Option 2"
---
# TECH-02: Speaker assistance and caregiver alerts
 
| Field | Description |
| --- | --- |
| ID | TECH-02 |
| Name | Speaker assistance and caregiver alerts |
| Status | In Progress |
| Evidence basis | The breakdown pattern in [SA-01](../operational-demands/activities/SA-01.md), general technology literature (see Research links), and the existing wiki's selected-technology record; provisional. The design decisions below are team decisions supported by adjacent literature, not results of a trial with Cleber. |
| Category | Sensing, automation and socially assistive interaction. |
| Capabilities | **Reach:** speakers in every room play the spoken reminders, so a prompt does not depend on Cleber being in the kitchen. **Trigger:** appliance sensors detect when prepared meals are taken out of their location/that a prepared meal appears untouched; this starts the reminders and does not depend on the camera. **Confirmation:** a camera that only sees the table becomes active only after kitchen activity is detected, and records the meal event. If Cleber never comes to the kitchen there is no kitchen activity, so the camera stays off, eating stays unconfirmed and the reminder sequence continues as normal. A suitable consumption check stops reminders after eating (therefore it stays on until meal completion is either verbally said by Cleber/the camera detects end of meal consumption/stays on if the escalation sequence is happening). **Plate taken away:** the table camera sees when the plate leaves the table, and the system logs the time between the plate leaving and returning, for Sarah to review later. This is only logged: no reminders are sent while the plate is away. If the plate does not return, the log records that the food was taken and the plate has not returned, and nothing further is sent. **Postponing:** if Cleber does not want to eat, he can postpone once; the reminder sequence then restarts from the first notification, and a second postponement is not accepted. **Escalation:** after three unanswered reminders, Sarah ([ST-03](../operational-demands/stakeholders/ST-03.md)) is alerted (see the sequence below). **Reporting:** logs are turned into a ready-made summary for Sarah's visits, so she does not have to analyse anything herself. **Accessibility:** language options and adjustable light intensity and sensitivity, so prompts can better suit Cleber's preferences and sensory needs. |
| Limitations | Appliance activity is not confirmed consumption, and a table-only camera cannot tell eaten food from discarded food. Once the plate leaves the table, the camera sees nothing; the logged away-time is a proxy (he may be eating in another room, not skipping the meal). The design does not decide what a plate that never returns means; it is logged as it happened. Camera use raises privacy concerns even when limited to the table. Enough suitable prepared food must be available; sensing alone does not establish that requirement. The one-postponement limit is a design choice that has not been tested with Cleber. Language availability and the effects of accessibility settings depend on the selected hardware and software and would need to be checked with Cleber. |
| Maturity and feasibility | Medium to high for available smart-home components (speakers, appliance sensors, notifications). Integration, decision logic, the report generation and meal-consumption accuracy remain project work. |
| Failure and fallback behaviour | Dead batteries or disconnection can cause false alerts or silent failure. One speaker going offline leaves a room uncovered. If the camera does not activate, the meal is logged as unconfirmed rather than eaten, unless Cleber says he is done, in which case it is marked as done. Cleber is never required to say it. Sensor-health checks are needed, and the report should state when data is missing rather than showing a clean day; a fault missed between Sarah's visits can remain undetected for days. |
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
| Postponement (once) | If Cleber says he does not want to eat, the sequence pauses and restarts from step 1. | Logged and shown to Sarah. A second refusal does not reset the sequence. |
| 4. Escalation | The system does not send a fourth reminder. Sarah receives a short message: which meal, how long since the last confirmed meal, reminders sent, and whether Cleber declined or did not respond. | A refusal and silence mean different things, so the message separates them. |
| 5. Follow-up | Sarah calls Cleber instead of waiting for her next visit. If Cleber then eats, the system sends a short "resolved" update. | Closes the loop so the alert does not stay open. |
| Plate taken away | The camera sees the plate leave the table; the time until it returns is logged. | Logging only: no reminders while the plate is away. If it never returns, it is logged as not returned; no alert. |
| If Sarah does not respond | Repeat once to Sarah, then notify Gilbert ([ST-02](../operational-demands/stakeholders/ST-02.md)) as a backup.|
 
## Logs and the report for Sarah
 
Sarah will not analyse raw data. The system records timestamped events and produces the analysis for her.
 
**What is logged per meal:** when Sarah prepared it, trigger time, each reminder, Cleber's response or postponement, kitchen entry, plate leaving and returning, consumption outcome (eaten / uncertain / not eaten), and any escalation.
 
**What the report highlights, in this order:**
1. Items needing attention: escalations, meals not eaten, and unusually long plate-away times (starting value: more than one hour, a team decision to be tuned; the mealtime study below is only a rough reference for a normal duration).
2. Meals per day by outcome, compared with the previous visit period.
3. Reminder timing: how many reminders each meal needed, the time from first reminder to kitchen entry, and how often postponement was used.
4. Data gaps, such as an offline sensor, so missing data is not read as "all fine".
**Using simulation logs to understand timing:** the same logs from the Wizard-of-Oz sessions let the team check whether meals usually resolve at the first, second or third reminder, and whether the gaps between reminders feel right. They also show whether Sarah can read the report and act on it. Because the sessions are staged with a proxy participant, they test the timing design and the report format, not Cleber's real behaviour; real timing would only come from a deployment.
 
## Research links
 
- Hofstede, B. M., et al. (2025). [A field study to explore user experiences with socially assistive robots for older adults: emphasizing the need for more interactivity and personalisation](https://doi.org/10.3389/frobt.2025.1537272). Supports discussion of interactivity and personalisation in older-adult robot use, not a claim that the proposed meal sensor is accurate.
- Pradhan, A., & Lazar, A. (2020). [Voice Technologies to Support Aging in Place: Opportunities and Challenges](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7741808/). Older adults valued voice agents partly because they were not seen as aging-specific, but used reminders less than expected because they doubted their reliability. Supports speakers over wearables and covering every room.
- [Eyes on privacy: acceptance of video-based AAL impacted by activities being filmed](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10352951/). Acceptance of video monitoring falls as a room becomes more private; the kitchen was among the more accepted rooms and the bedroom and bathroom the least. Supports limiting the camera to the kitchen table.
- [Continuous monitoring of eating and sleeping behaviors in the home environments of older adults: a case study demonstration](https://pmc.ncbi.nlm.nih.gov/articles/PMC10811267/). Uses a dashboard of periodic summaries with eating times outside regular hours highlighted. Cited for the summary design only; that study relied on continuous cameras.
- [Description of the mealtime of older adults with dementia in a long-term care facility: A video analysis](https://www.sciencedirect.com/science/article/pii/S0197457223002720). Average meal duration of about 12 minutes (range roughly 5 to 34). A rough reference for what counts as a normal plate-away time; the residents were highly dependent, so it does not transfer directly to Cleber.
- Mathur, et al. (2022). [A Collaborative Approach to Support Medication Management in Older Adults with MCI Using Conversational Assistants](https://dl.acm.org/doi/fullHtml/10.1145/3517428.3544830). ASSETS '22. Tested reminders that ask once, twice or continually; check-in framing rather than alarms raised engagement. The closest support for limiting persistence.
No study found tests the plate-away timing log or the exact one-postponement rule, so both are presented as design decisions.
 
[RP-01](../../2-specification/personas/robot/RP-01.md) describes Echo's intended profile; [AT-01](../../3-evaluation/artifacts/AT-01.md) states which parts the current build can address.
 
