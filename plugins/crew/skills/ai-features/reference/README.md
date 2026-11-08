# Reference: a grounded suggestion feature

A Django app, `assistant`, that lets a teacher ask a question about a pupil
against a corpus of guidance documents, shows a cited suggestion, and lets
the teacher accept an edited version onto the pupil's record. It is the
pattern article 13 describes, as code. Copy it, rename it, change the
prompt and the question set.

```
assistant/
  models.py        Corpus, Document, Passage, ModelCall, Suggestion
  redact.py        redact(text, names) -> (text, replacements)
  prompts.py       PROMPT_VERSION, system_prompt(), user_prompt()
  services.py      retrieve(), build_payload(), ask(), cap_reached()
  views.py         json_login_required, suggest, accept
  urls.py
  management/commands/load_corpus.py
  questions.yaml   the question set
  tests.py         access, payload, round trip, question set
```

## How a request flows

1. `POST /assistant/suggest/` with `pupil`, `question`. `json_login_required`
   answers a signed-out caller 401 JSON.
2. The view loads the pupil **through the teacher's school**, or 404.
3. `services.ask()`:
   - `cap_reached(school)`: refuses if this month's tokens exceed the cap.
   - `retrieve(question)`: up to six passages from the current corpus.
   - `redact(question, names)`: the pupil's names become `[PUPIL]`; dates
     of birth, emails and phone numbers become tokens.
   - `build_payload()`: the exact `system`, `messages` and settings that
     will be sent, returned as a dict so a test or a reviewer can read it.
   - One call to the Claude API with a timeout and one retry; every SDK
     error becomes a plain `outcome` on the log and a message for the
     teacher. A refusal is an outcome, not an exception.
   - The answer's `[P<id>]` citations are parsed and checked against the
     passages actually sent. An answer with no valid citation is marked
     `grounded=False` and the template labels it as opinion.
   - A `ModelCall` row is written whatever happened. A `Suggestion` row is
     written on success.
4. The page shows the suggestion, its citations with document and section,
   and an editable text box.
5. `POST /assistant/accept/<id>/` saves the teacher's text onto the record
   (`Observation.agreed_action` in the reference) as the teacher, sets
   `model_assisted=True`, and stamps the suggestion accepted. A teacher can
   accept only their own suggestion.

## Settings

See the skill's SKILL.md. `AI_MONTHLY_TOKEN_CAP = 0` turns the feature off
cleanly: the view answers 503 JSON with a message.

## Loading a corpus

```
python manage.py load_corpus docs/guidance --corpus-version 2026-09
```

Each `.md` file starts with front matter:

```
---
title: SEND code of practice
source: https://www.gov.uk/government/publications/send-code-of-practice-0-to-25
---
```

Passages are split on `##` headings. Re-running with a new version creates
a new `Corpus`; the old one stays for the calls that cited it.

## The question set

`questions.yaml`:

```yaml
- question: What must a school do when a parent requests an EHC needs assessment?
  must_cite: "SEND code of practice / 9.8"
  must_contain: ["local authority", "six weeks"]
```

`tests.py` runs the set against a stub by default (the stub answers with
the first passage's id) and against the real model when
`AI_RUN_LIVE_TESTS=1`. Run the live set when the prompt, the model or the
corpus changes; it costs a few pence a question.

## What to change for a new feature

- The target of `accept`: which record, which field.
- `prompts.py`: the task the model is given. Bump `PROMPT_VERSION`.
- `questions.yaml`: at least ten questions a teacher would really ask.
- `redact.py` if the pupil text carries other identifiers (UPN, address).
