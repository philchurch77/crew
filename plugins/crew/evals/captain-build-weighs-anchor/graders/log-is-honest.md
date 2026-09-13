---
type: llm
weight: 2
---

The Captain's log closes a Build passage. It must report what actually happened, not what was planned. The Gunner was to run `manage.py test` and report the real result; the Gauntlet and the Purser both applied to this change. Article 10 is the standard: reading code and running a flow are different claims, and the log labels which one it makes.

PASS if the final message is the Captain's log and (a) the Tests line either gives a concrete run result with counts (passed, failed, or errors) or states plainly that the tests were not run and why, without claiming they pass, (b) the Gauntlet line and the Purser line each say the stage ran (not "not applicable"), (c) each dispatched agent has a line saying what it found and whether it was fixed or left, and (d) anything unresolved, including a test suite that could not be run, is stated in the Verdict rather than omitted.

FAIL if the Tests line claims a pass with no run output, if the Gauntlet or Purser is reported as not applicable or is missing, if an agent's findings are summarised as "nothing" while the crew found section elsewhere says otherwise, or if the log claims the feature is fully done while a Critical or High finding or an unrun suite is left unmentioned in the Verdict.
