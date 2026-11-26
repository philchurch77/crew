# Reference: an assistant people talk to

A Django app, `chat`, for a conversation with an assistant that answers
from tools: stored chats that belong to one person, a streamed reply, a
log of every call, and the page that draws it in the house style. Lifted
from a working project. Copy it, rename the assistant, replace the tool,
the prompt and the question set.

```
chat/
  models.py        ChatSession, ChatTurn, ToolCall, ModelCall
  prompts.py       PROMPT_VERSION, system_prompt()
  tools.py         TOOLS, definitions(), runner_for(user)
  streaming.py     stream_reply(): the model call and its tool loop
  services.py      build_agent(), api_history(), record_run(), rate_limited()
  views.py         the page, the stream, history, rename, delete, export
  urls.py          chat, chat_stream, chat_history, chat_rename, chat_delete, chat_export
  context_processors.py   assistant_name
  admin.py         the call log, read-only; chats are not in the admin
  templates/chat/  chat.html (fills the house style's chat.html), partials
  static/js/       chat_stream.js, vendor/marked.min.js (MIT)
  questions.yaml   the question set
  tests.py         ownership, signed out, nothing lost, the loop, limits
```

## Wiring it in

```python
# settings.py
INSTALLED_APPS += ["chat"]
TEMPLATES[0]["OPTIONS"]["context_processors"] += ["chat.context_processors.assistant"]
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Assistant")
AI_MODEL = os.getenv("AI_MODEL", "claude-opus-5-5")   # name another only on purpose
AI_EFFORT = "medium"                                   # low | medium | high
AI_RUN_LIVE_TESTS = False                              # the question set hits the real model

# urls.py
path("chat/", include("chat.urls")),
```

`anthropic` and `PyYAML` go in `requirements.txt`. The key is
`ANTHROPIC_API_KEY` in the environment, never in settings or the repo.
Then `makemigrations chat`, `migrate`, and add a "Chat" link to the nav in
`layout.html`. It needs the house style's `chat.html`, `chat.css` and
`chat.js`, and a shared cache in production (the rate limit counts there).

## How a message flows

1. The page posts `{message, session_key}` to `chat_stream`. The page
   names the chat, not the cookie, so two tabs cannot write into each
   other. Signed out is **401 JSON**; too fast is 429; empty is 400. On any
   of these nothing was saved and the text goes back in the box.
2. A key that is another person's chat is a **404**. A new key makes a new
   chat for this person.
3. `api_history()` builds what the model will see: the text of this
   chat's last 20 turns and the new message. Nothing from any other chat.
4. **The person's turn is saved before the stream opens**, so it survives
   a failed reply.
5. `stream_reply()` streams text and status frames (`\x1e label \x1e`,
   which the page shows as "Looking up…" and never stores). When the model
   asks for a tool, `runner_for(user)` runs it **for that user** and the
   result goes back; at most six calls to the model per message.
6. However it ends (answered, refused, cut short, failed, the browser
   gone), `record_run()` writes a `ModelCall`, and if there are words,
   saves the reply and its `ToolCall`s in one transaction.
7. The page asks `chat_history` for the sidebar, the title and the
   sources, and draws them.

## What to change, in this order

1. **`tools.py`.** Each tool is how something in the system reaches the
   model, so each handler filters by the user it is given and returns only
   what they may see. Return a `source` a person can read: it is what the
   Sources panel lists.
2. **`prompts.py`**, and bump `PROMPT_VERSION`.
3. **`questions.yaml`**, with the project's own questions. Keep one that
   offers a child's name.
4. The starter cards and the About text in `templates/chat/chat.html`,
   and `LINK_HOSTS` in `chat_stream.js`.

## What must not be tidied

- `streaming.py` catches exceptions **inside** the generator and wraps the
  save: it runs after the view has returned. Never make the response
  synchronous.
- The loop's history is append-only; assistant content goes back verbatim.
- The system prompt and tool definitions are byte-stable. A date, a name
  or a per-user line in either ends prompt caching silently.
- The request carries no `temperature`, `top_p`, `top_k`, `budget_tokens`,
  prefilled assistant turn or forced `tool_choice`: the model answers 400.
- `chat_stream.js` renders markdown from **escaped** text, never loads an
  image, and leaves a link clickable only for a host in `LINK_HOSTS`.
- Nothing is logged but exception types and tracebacks: never a message.
  Never set `ANTHROPIC_LOG=debug` on a deployment.

## What it leaves to the project

- **What people may type.** The composer's note asks them not to name a
  child, and the prompt tells the assistant not to use one, but the text
  is sent as typed. If the app holds pupils' names, pass the message
  through the grounded reference's `redact()` in `api_history()` before
  it is sent, and say so in the DPIA.
- **Retention.** Chats are kept until their owner deletes them. A project
  with a retention period adds a purge command.
- **A spend cap per school.** There is a rate limit per person and a call
  limit per message; a monthly cap is the grounded reference's
  `cap_reached()`, keyed on the project's own school link.
- **A fallback model.** A refusal is shown plainly and logged as one. The
  API can retry a refused request on another model; that sends the
  conversation to a second model and is a decision for the project.

## Not run

The tests use a stub in place of the model. The live question set
(`AI_RUN_LIVE_TESTS`) has not been run from this reference: run it once in
the first project that copies it, and fix the reference if it fails.
