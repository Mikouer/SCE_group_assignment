---
pageName: UC01-F4-PR4
---
# UC01-F4-PR4: Meal event log and report for Sarah

| Field | Description |
| --- | --- |
| ID | UC01-F4-PR4 |
| Function | [F4](F4.md). |
| Evaluation Method(s) / Measure(s) | [EM-03](../../../1-foundation/human-factors/evaluation-methods/EM-03.md) and [M-04](../../../1-foundation/human-factors/measures/M-04.md). |
| Verification Criteria | In every scripted scenario ([M-04](../../../1-foundation/human-factors/measures/M-04.md)): the log contains the specified events (trigger, each reminder, response, postponement, kitchen entry, plate leaving and returning, eating outcome, escalation); the plate leaving and returning are recorded from the table camera and the away time is logged, with no reminder sent while the plate is away and a plate that does not return logged as not returned; the summary lists escalations, uneaten meals and plate-away times over one hour first; and when a sensor is reported offline the summary states a data gap instead of a clean day. The properties concerned are correctness, availability of the record and robustness to missing data. |
| Action Sequence step(s) | [UC01](UC01.md), steps 8-9. |
| Assessment | Not assessed; verification is planned in [ER-01](../../../3-evaluation/reports/ER-01.md). |
