# Field report: Captain narrowed the Surgeon's dispatch to one hypothesis

Filed as a file because `/field-report` could not reach `gh issue create`
from the project; the report was printed to the chat and would otherwise
have been lost. Work it as an issue in the `field-report` inbox would be
worked: AGENTS.md section 7.

## Agent
Captain (the dispatch framing), with a secondary finding on the Surgeon (it accepted the framing without checking the rest of the symptom's surface).

## Passage
Look / Fix, stage 1: the Surgeon's diagnosis dispatch.

## Prompt
The developer passed on a user complaint, roughly: "Some Early Years staff say they're getting the Key Stage 2 version of the observation form. I can't find an Early Years version anywhere. Did we miss it?"

## What the agent said
The Captain read the code, found the one place where the observation form varies by phase, and dispatched the Surgeon with a hypothesis confined to that branch: "Confirm or refute: the phase variant is chosen from a stored snapshot, a blank phase defaults to KS2, and the snapshot is never re-derived." The Surgeon confirmed every point with file and line evidence, ranked two routes into a stale snapshot, and "ruled out" a template bug because "the template faithfully renders a wrong record." It concluded: "Your hypothesis is confirmed on every point."

A production check then showed almost no mismatched snapshots, and the user confirmed the varying tab was correct. The actual cause was that the other tabs on the same page never vary by phase at all and hard-code KS2 wording for everyone. Nobody had looked at them.

## What it should have said
Severity: High. This was a wrong diagnosis delivered with full confidence. It cost a round trip with the client and very nearly led to a data-repair plan against records that were fine.

Before narrowing to one mechanism, the diagnosis should have mapped the symptom's whole surface. The user said "the form", and the page has several tabs. The expected finding:

"Only one template in this page branches on `Pupil.phase`. The Next Steps and Summary tabs are identical for every pupil and contain KS2-only wording (a SATs target field label, a pre-filled 'Year 6 transition' next step). An Early Years teacher would call this 'the KS2 version' even when the varying tab is correct. Ask the reporter which part of the page looks wrong before treating a stale snapshot as the cause."

The fix belongs in two places:
- The Captain's dispatch should give the Surgeon the symptom as reported, with the whole feature in scope, and not only its own hypothesis.
- The Surgeon should enumerate every template or view on the reported surface and grep each one for the variant switch and for hard-coded wording of the "wrong" variant, before confirming a narrower hypothesis.

## The defect, in fixture terms
Seed this in schoolapp:
- Add `Pupil.phase` (EYFS / KS2, blank allowed).
- Give the observation detail page three tabs: Concerns, Next Steps and Summary.
- Concerns branches on a stored `Observation.form_kind` snapshot, set from `Pupil.phase` when the observation is created: an EYFS checklist or a KS2 checklist. This part works correctly for every EYFS pupil in the seed data.
- Next Steps and Summary do not branch. Next Steps pre-fills its first item with "Prepare for Year 6 transition and SATs". Summary asks "Is this pupil on track for their KS2 SATs target?"
- To make the decoy tempting, include one historic Observation whose `form_kind` is stale (KS2 for an EYFS pupil).

Complaint to hand the agent: "Early Years teachers say they're getting the KS2 version of the observation form."

## Grader
PASS if the diagnosis identifies that the Next Steps and/or Summary tabs contain unconditional KS2 wording shown to EYFS pupils (or explicitly asks which part of the page looks wrong before settling on a cause).

FAIL if the diagnosis attributes the complaint solely to the `form_kind` snapshot or the one stale record without examining the non-branching tabs.
