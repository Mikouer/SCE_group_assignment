---
pageName: "IDP-01: Gentle non-intrusive meal reminders"
---
# IDP-01: Gentle, non-intrusive meal reminders

| Field | Description |
| --- | --- |
| ID | IDP-01 |
| Name | Gentle, non-intrusive meal reminders |
| Status | Under Review |
| Evidence basis |
 [HFC-01](../../1-foundation/human-factors/concepts/HFC-01.md) (improper or excessive persistence → annoyance and avoidance) and [HFC-02](../../1-foundation/human-factors/concepts/HFC-02.md) (people with dementia actively configure their own support). The literature supports the direction of the design: check-in framing, limited persistence, personalisation and preserved control. It does not tell us the effective number of reminders or the intervals. The three-reminder sequence is a team design decision, to be tuned in formative evaluation(see [TECH-02](../../1-foundation/technology/TECH-02.md)). |
| Problem | Cleber may forget meals or miss prompts, but frequent or forceful reminders can feel frustrating, controlling or intrusive. |
| Principle | A reminder is only useful if Cleber keeps accepting it. Prompts that repeat, get louder or ignore a refusal treat him as someone to be managed. They are likely to cause annoyance and avoidance (HFC-01), which would make every later reminder less effective. Prompts that are calm, spaced and easy to decline leave the decision with him, in line with how people with dementia keep control over their own support (HFC-02). So Echo does not push harder when Cleber doesn’t respond. After a small, agreed number of gentle prompts, the remaining concern goes to Sarah, a person who can talk to him. Responsibility moves to a human instead of the pressure on Cleber increasing. | 
| Personalisation and Sarah’s involvement | Sarah and Cleber agree on the mealtimes together, the interval between reminders, and when an unresolved meal should be shared with Sarah. Sarah can suggest settings based on Cleber’s routines, but Cleber’s preferences and choices guide them. They review and adjust the settings together as routines or preferences change. The proposed three-reminder sequence is a starting point for discussion, not a fixed threshold. |

## Solution

1. **Meal preperation by Sarah:** Meals are prepared by Sarah on her regular visits. Therefore, she ensures that Cleber has food to consume in his alone time. The logs the system saves according to Cleber's eating habits allow Sarah to review which foods he ate/didn't eat, and discuss dietary changes if necessary. 
2. **Agree on the settings:** Sarah discusses the reminder schedule and escalation preferences with Cleber. Together, they decide when reminders should begin, how long to wait between prompts, how many prompts to allow, and when Sarah should be notified. They can revisit these choices based on Cleber’s feedback, on Sarah's visits.
3. **First reminder:** Calm speech, soft LEDs and slow orientation invite Cleber
   to eat, without assuming he wants the meal Sarah prepared.
4. **Second reminder:** Respect refusal/non-response, wait the agreed interval,
   then offer another gentle reminder. An alternative meal may be offered only
   if one is available.
5. **Third reminder:** Give a final gentle prompt without louder speech or
   pressuring language.
6. **Conditional escalation:** Notify Sarah if refusal, non-response or
   uncertainty remains after the sequence, distinguishing these outcomes.
7. **Interaction closure:** Stop prompts after confirmed eating or escalation,
   and return to a resting posture.

## Research links

- Mathur et al. (2022), conversational assistants for medication management in MCI. Compared reminders that asked once, twice or continually. Check-in framing rather than alarm framing raised engagement. → HFC-01; the most direct support for spaced, limited persistence.

- McGee-Lennon, Wolters & Brewster (2011),[User-centred multimodal reminders for assistive living](https://doi.org/10.1145/1978942.1979248), user-centred multimodal reminders. Reminder preferences differed strongly between people and contexts, and badly matched reminders were seen as intrusive. → HFC-01; supports agreeing modality, timing and frequency with Cleber rather than fixing them.

- Dixon, Piper & Lazar (2021), ["Taking care of myself as long as I can": How People with Dementia Configure Self-Management Systems](https://doi.org/10.1145/3411764.3445225), self-management systems. People with mild to moderate dementia combined technology and other people to stay in control, and resisted support that took decisions away from them. → HFC-02; supports treating refusal as a valid choice and letting Cleber set the reminder settings with Sarah.

- Foley et al. (2019),[Printer Pals: Experience-centered design to support agency for people with dementia](https://doi.org/10.1145/3290605.3300634), Printer Pals. Designing around choice and enjoyment supported a sense of agency in people with dementia. → HFC-02; supports framing the prompt as an invitation, not an instruction.

- Moharana et al. (2019),[Robots for Joy, Robots for Sorrow: Community Based Robot Design for Dementia Caregivers](https://doi.org/10.1109/HRI.2019.8673206), community-based robot design with dementia caregivers. Caregivers wanted robots to support and encourage, not to replace them or be directive. → HFC-01/HFC-02; supports keeping the robot gentle and handing unresolved situations to Sarah.

- Jönsson et al. (2019),[A reminder system for independence in dementia care: A case study in an assisted living facility](https://doi.org/10.1145/3316782.3321530), reminder system in assisted living. A case study of reminders used to support residents’ independence. → HFC-02. (Check the exact finding against the paper before submitting.)

None of these studies tests a three-step meal reminder sequence. They support the principle, not the parameters.

## Connection to claims

- [UC01-F1-CL1](../use-cases/uc01/UC01-F1-CL1.md): a gentle initial prompt intended to support eating initiation.
- [UC01-F2-CL2](../use-cases/uc01/UC01-F2-CL2.md): bounded follow-ups after an unsuccessful first prompt.
- [UC01-F2-CL3](../use-cases/uc01/UC01-F2-CL3.md): calm, preference-respecting support for perceived control.
- [UC01-F3-CL4](../use-cases/uc01/UC01-F3-CL4.md): a final step that communicates an unresolved meal and closes
  the interaction.
