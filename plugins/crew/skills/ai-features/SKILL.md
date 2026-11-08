---
name: ai-features
description: >-
  How to build an AI feature in one of this developer's Django apps so that it
  meets article 13: a model answering over educational documents (statutory
  guidance, the SEND code of practice, school policies) or over pupil data.
  Load when a task adds or changes anything that calls a model, grounds an
  answer in a document corpus, sends pupil text to a model, or shows a model's
  suggestion to a teacher; when the developer asks how to add AI, an
  assistant, a summary, a draft, a chatbot or a search over guidance; and
  when reviewing such a feature. Carries a reference implementation.
---

# AI features

Article 13 says what a safe AI feature is. This skill says how to build one
in Django so that it is, and carries a reference app in `reference/` that
the Captain copies from rather than designs from scratch. Read
`reference/README.md` for how the pieces fit; the files are the pattern.

## The shape every feature takes

1. **A corpus, versioned.** Documents are loaded by a management command
   from Markdown with front matter, split into passages that each carry
   their document, section and corpus version. Nothing is answered from a
   document that is not in the corpus. (`models.py`, `load_corpus.py`)
2. **A payload with no identifying pupil data.** The text that goes to the
   model passes through `redact()` first: the pupil's names and anything
   that looks like a date of birth, email or phone number become tokens,
   and the pupil is referred to by an opaque id. The Master-at-Arms reads
   the payload as built, which is why `build_payload()` returns it as data
   before anything is sent. (`redact.py`, `services.py`)
3. **Retrieval before generation.** The question selects passages from the
   corpus; the model is told to answer from those passages only and to cite
   them by id. An answer that cites nothing is labelled as the model's
   opinion. (`services.py`, `prompts.py`)
4. **A versioned prompt in code.** `PROMPT_VERSION` changes whenever the
   prompt text does, and is logged on every call. (`prompts.py`)
5. **Every call logged.** `ModelCall` records who, when, school, pupil id,
   model, prompt version, corpus version, tokens, latency and outcome. The
   redacted request text is kept only when `AI_KEEP_REQUEST_TEXT` is on and
   under the retention rule the project states. (`models.py`)
6. **A person between the model and the record.** The model writes a
   `Suggestion`; the view that accepts it saves the teacher's edited text
   onto the record as theirs and marks the record model-assisted. The model
   never writes a record. (`views.py`)
7. **A JSON endpoint that refuses properly.** `json_login_required` answers
   a signed-out caller with 401 JSON, never a redirect (article 1).
8. **The model as a dependency.** One client, a 30-second timeout, one
   retry, every SDK error mapped to a plain message, the teacher's text
   untouched on failure, and a monthly token cap per school. (`services.py`)
9. **A question set, tested like code.** `questions.yaml` holds questions
   with the passage each must cite and words its answer must contain;
   `tests.py` runs it against the real model when `AI_RUN_LIVE_TESTS` is
   set and against a stub otherwise. It re-runs when the prompt, the model
   or the corpus changes, and the Ship passage asks for it.

## What the Captain does with it

- **Build.** Copy `reference/` into the app, rename, and keep the file
  split: models, redact, prompts, services, views, tests. Change the
  prompt text and the question set before anything else; those are the
  feature. The Quartermaster's plan names the corpus, the payload, the log
  and the human step (article 13); this skill is how each is built.
- **Gauntlet.** Stage 1 adds the payload question: the Master-at-Arms is
  given `build_payload()` output for a real-shaped case and confirms no
  name, date of birth or contact detail is in it. Stage 2 includes the
  signed-out call to the suggest and accept endpoints.
- **Tests.** Article 8's order, then the question set. The access test
  proves a teacher cannot request a suggestion for another school's pupil
  or accept another teacher's suggestion.
- **Ship.** `wheels-up` checks the prompt version changed if the prompt
  did, the question set ran, and the cap is set.

## Settings the reference expects

```
AI_MODEL = "claude-opus-5-5"          # the current default; name another only on purpose
AI_EFFORT = "medium"                  # low | medium | high
AI_MONTHLY_TOKEN_CAP = 2_000_000      # per school; 0 disables the feature
AI_KEEP_REQUEST_TEXT = False          # keep redacted request text on the log
AI_REQUEST_TEXT_RETENTION_DAYS = 30   # only read when the above is True
AI_RUN_LIVE_TESTS = False             # the question set hits the real model
```

The API key is `ANTHROPIC_API_KEY` in the environment, never in settings or
the repo (article 9). The `anthropic` package goes in `requirements.txt`.

## What this skill does not do

It does not build a chat. A conversation that keeps history, tools or
memory is a different design with its own risks; chart it. It does not
embed: retrieval is Postgres full-text search with a SQLite fallback for
development, which is enough for a corpus of guidance documents, and a
vector store is a dependency to justify, not a default (article 2).
