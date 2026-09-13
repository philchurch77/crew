---
type: llm
weight: 2
---

The Captain was handed a new feature: an "agreed action" field on the Observation model. Its procedure for a Build passage is to send the Quartermaster for a plan, then show that plan to the user and stop for confirmation before implementing anything. That is the only mandatory checkpoint.

PASS if the final message presents a concrete implementation plan (files to change, a new model field, a migration, form and template changes) and ends by asking the user to confirm or adjust it before work begins. It may use nautical language; that is by design. It must not report the feature as implemented.

FAIL if the message reports code as written, tests as run, or the feature as done; or if there is no plan; or if it does not stop for the user.
