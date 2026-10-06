---
pageName: "IDP-01: Gentle non-intrusive meal reminders"
---
# IDP-01: Gentle, non-intrusive meal reminders

| Field | Description |
| --- | --- |
| ID | IDP-01 |
| Name | Gentle, non-intrusive meal reminders |
| Status | Under Review |
| Evidence basis | The project situation, [HFC-01](../../1-foundation/human-factors/concepts/HFC-01.md), [HFC-02](../../1-foundation/human-factors/concepts/HFC-02.md) and the literature below. The exact three-reminder rule is a proposed design decision, not an empirically established safe optimum. |
| Problem | Cleber may forget meals or miss prompts, but frequent or forceful reminders can feel frustrating, controlling or intrusive. |
| Principle | Respect food preferences and choices. Refusal does not trigger immediate escalation. Wait before another gentle prompt and notify Sarah if the bounded sequence remains unresolved. |

## Solution

1. **First reminder:** Calm speech, soft LEDs and slow orientation invite Cleber
   to eat, without assuming he wants the meal Sarah prepared.
2. **Second reminder:** Respect refusal/non-response, wait the agreed interval,
   then offer another gentle reminder. An alternative meal may be offered only
   if one is available.
3. **Third reminder:** Give a final gentle prompt without louder speech or
   pressuring language.
4. **Conditional escalation:** Notify Sarah if refusal, non-response or
   uncertainty remains after the sequence, distinguishing these outcomes.
5. **Interaction closure:** Stop prompts after confirmed eating or escalation,
   and return to a resting posture.

## Research links

- Dixon, E., Piper, A. M., and Lazar, A. (2021).
  ["Taking care of myself as long as I can": How People with Dementia Configure Self-Management Systems](https://doi.org/10.1145/3411764.3445225).
- Foley, S., Welsh, D., Pantidi, N., Morrissey, K., Nappey, T., and McCarthy, J.
  (2019). [Printer Pals: Experience-centered design to support agency for people with dementia](https://doi.org/10.1145/3290605.3300634).
- Jönsson, K.-E., Ornstein, K., Christensen, J., and Eriksson, J. (2019).
  [A reminder system for independence in dementia care: A case study in an assisted living facility](https://doi.org/10.1145/3316782.3321530).
- McGee-Lennon, M., Wolters, M., and Brewster, S. (2011).
  [User-centred multimodal reminders for assistive living](https://doi.org/10.1145/1978942.1979248).
- Moharana, S., Panduro, A. E., Lee, H. R., and Riek, L. D. (2019).
  [Robots for Joy, Robots for Sorrow: Community Based Robot Design for Dementia Caregivers](https://doi.org/10.1109/HRI.2019.8673206).

The citations support the design rationale around agency, reminders and
caregiving; they do not establish Echo's effectiveness or a validated escalation
interval.

## Connection to claims

- [UC01-F1-CL1](../use-cases/uc01/UC01-F1-CL1.md): a gentle initial prompt intended to support eating initiation.
- [UC01-F2-CL2](../use-cases/uc01/UC01-F2-CL2.md): bounded follow-ups after an unsuccessful first prompt.
- [UC01-F2-CL3](../use-cases/uc01/UC01-F2-CL3.md): calm, preference-respecting support for perceived control.
- [UC01-F3-CL4](../use-cases/uc01/UC01-F3-CL4.md): a final step that communicates an unresolved meal and closes
  the interaction.
