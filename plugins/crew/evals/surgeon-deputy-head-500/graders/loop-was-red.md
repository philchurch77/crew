---
type: llm
---

The Surgeon's method is to get one command that goes red on the reported symptom and run it before naming a cause. Reading `tolerance/views.py` and spotting `user.membership` is a guess until it has been seen to fail.

PASS if the response shows or describes an actual run (a test, a `manage.py shell` script, or a request to a dev server) that reproduced the failure for a user without a Membership, for example by quoting `RelatedObjectDoesNotExist` or "User has no membership" from its output, or by stating that the reproduction raised.

FAIL if the diagnosis is presented from reading the code alone, with no evidence that the failure was reproduced by running something.
