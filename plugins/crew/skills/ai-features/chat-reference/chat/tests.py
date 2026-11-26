"""The chat's tests, against a stub model (no key, no network). Each is
named for the failure it catches. The access tests are proven by breaking
the control in a copy (article 8)."""
import json
from types import SimpleNamespace
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from . import services, streaming, tools
from .models import ChatSession, ChatTurn, ModelCall, ToolCall

# Written as escapes: an editor must not be able to change them (article 8).
AWKWARD = "Line one\nline two ‘curly’ café \U0001F600 <b>not bold</b> & more"
KEY_A = "a" * 32
KEY_B = "b" * 32


def text_block(text):
    return SimpleNamespace(type="text", text=text)


def tool_block(name, input, id="tu_1"):
    return SimpleNamespace(type="tool_use", name=name, input=input, id=id)


def reply(*blocks, stop_reason="end_turn", input_tokens=10, output_tokens=5):
    return SimpleNamespace(
        content=list(blocks), stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens,
                              cache_read_input_tokens=0),
    )


class StubClient:
    """Stands in for anthropic.Anthropic(): plays back ``replies`` in
    order and keeps every request it was sent."""

    def __init__(self, *replies, fail=False):
        self.replies = list(replies)
        self.fail = fail
        self.requests = []
        self.messages = self

    def stream(self, **kwargs):
        # A copy: the loop appends to its history after this call.
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        if self.fail:
            raise RuntimeError("the model is down")
        final = self.replies.pop(0)
        chunks = [b.text for b in final.content if b.type == "text"]

        class Stream:
            text_stream = iter(chunks)

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def get_final_message(self):
                return final

        return Stream()


# Read before any override: the live question set runs on the real one.
REAL_MODEL = getattr(settings, "AI_MODEL", "")
LIVE = getattr(settings, "AI_RUN_LIVE_TESTS", False)

# A stand-in model name: nothing here reaches the API unless a test says so.
STUB_SETTINGS = {"ASSISTANT_NAME": "Testbot", "AI_MODEL": "test-model", "AI_EFFORT": "medium"}


@override_settings(**STUB_SETTINGS)
class ChatTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="owner-qz", password="x" * 16)
        self.other = User.objects.create_user(username="other-qz", password="x" * 16)
        self.client.force_login(self.user)

    def use(self, stub):
        patcher = mock.patch.object(streaming, "_get_client", return_value=stub)
        patcher.start()
        self.addCleanup(patcher.stop)
        return stub

    def send(self, message, key=KEY_A, client=None):
        response = (client or self.client).post(
            reverse("chat_stream"), json.dumps({"message": message, "session_key": key}),
            content_type="application/json",
        )
        if response.streaming:
            response.body = b"".join(response.streaming_content).decode()
        return response


class OwnershipTests(ChatTestCase):
    """Article 1: a chat is its owner's, by every route."""

    def setUp(self):
        super().setUp()
        self.theirs = ChatSession.objects.create(user=self.other, session_key=KEY_B)
        ChatTurn.objects.create(session=self.theirs, role="user", content="their private question")

    # Catches the page opening someone else's chat from a guessed key.
    def test_another_persons_chat_page_is_a_404(self):
        response = self.client.get(reverse("chat"), {"session_id": KEY_B})
        self.assertEqual(response.status_code, 404)

    # Catches a message being written into someone else's chat, or their
    # history being sent to the model.
    def test_a_message_to_another_persons_chat_is_a_404_and_calls_nothing(self):
        stub = self.use(StubClient(reply(text_block("hello"))))
        response = self.send("hi", key=KEY_B)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(stub.requests, [])
        self.assertEqual(self.theirs.turns.count(), 1)

    # Catches rename, delete and export reaching a chat by key alone.
    def test_rename_delete_and_export_of_another_persons_chat_are_404s(self):
        rename = self.client.post(reverse("chat_rename", args=[KEY_B]),
                                  json.dumps({"title": "mine now"}), content_type="application/json")
        delete = self.client.post(reverse("chat_delete", args=[KEY_B]))
        export = self.client.get(reverse("chat_export", args=[KEY_B]))
        self.assertEqual([rename.status_code, delete.status_code, export.status_code], [404, 404, 404])
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.title, "")

    # Catches the sidebar or the title of another chat coming back as JSON.
    def test_history_for_another_persons_key_says_nothing_about_it(self):
        response = self.client.get(reverse("chat_history"), {"session_id": KEY_B})
        self.assertEqual(response.json()["title"], "")
        self.assertNotIn("their private question", response.content.decode())

    # Catches the model being sent anything but this one conversation.
    def test_the_payload_holds_only_this_conversation(self):
        mine_elsewhere = ChatSession.objects.create(user=self.user, session_key="c" * 32)
        ChatTurn.objects.create(session=mine_elsewhere, role="user", content="my other chat")
        stub = self.use(StubClient(reply(text_block("first")), reply(text_block("second"))))
        self.send("question one")
        self.send("question two")
        sent = json.dumps(stub.requests[-1], default=str)
        self.assertIn("question one", sent)
        self.assertIn("question two", sent)
        self.assertNotIn("their private question", sent)
        self.assertNotIn("my other chat", sent)
        self.assertNotIn("owner-qz", sent)


class SignedOutTests(ChatTestCase):
    """Article 8: a JSON endpoint answers a signed-out caller 401, never a
    redirect (which fetch() follows to a 200 login page)."""

    def setUp(self):
        super().setUp()
        self.client.logout()

    def test_stream_and_history_answer_401_json(self):
        stream = self.send("hi")
        history = self.client.get(reverse("chat_history"), {"session_id": KEY_A})
        rename = self.client.post(reverse("chat_rename", args=[KEY_A]), "{}", content_type="application/json")
        for response in (stream, history, rename):
            self.assertEqual(response.status_code, 401)
            self.assertIn("error", response.json())
        self.assertEqual(ChatTurn.objects.count(), 0)

    def test_the_page_redirects_to_sign_in(self):
        self.assertEqual(self.client.get(reverse("chat")).status_code, 302)


class NothingLostTests(ChatTestCase):
    """Article 6: what was typed, and what was read, is kept."""

    # Catches typed text being trimmed, re-encoded or escaped in storage.
    def test_awkward_text_survives_store_page_and_export_byte_for_byte(self):
        self.use(StubClient(reply(text_block(AWKWARD))))
        self.send(AWKWARD)
        user_turn, reply_turn = ChatTurn.objects.order_by("pk")
        self.assertEqual(user_turn.content, AWKWARD)
        self.assertEqual(reply_turn.content, AWKWARD)

        page = self.client.get(reverse("chat"), {"session_id": KEY_A})
        self.assertEqual([t["content"] for t in page.context["chat_turns"]], [AWKWARD, AWKWARD])
        export = self.client.get(reverse("chat_export", args=[KEY_A])).content.decode()
        self.assertIn(AWKWARD, export)

    # Catches the question being saved only when the model answers.
    def test_the_message_is_saved_even_when_the_model_fails(self):
        self.use(StubClient(fail=True))
        response = self.send("will this survive?")
        self.assertEqual(response.status_code, 200)
        self.assertIn("something went wrong", response.body)
        self.assertEqual(ChatTurn.objects.get().content, "will this survive?")
        self.assertEqual(ModelCall.objects.get().outcome, "error")

    # Catches a reply the person has read being dropped when they leave.
    def test_a_reply_cut_off_by_the_browser_is_kept_and_marked(self):
        self.use(StubClient(reply(text_block("partial words"))))
        session = ChatSession.objects.create(user=self.user, session_key=KEY_A)
        agent = services.build_agent(self.user)
        gen = streaming.stream_reply(
            agent, [{"role": "user", "content": "q"}], tools.runner_for(self.user),
            on_complete=lambda run: services.record_run(session, self.user, agent, run),
        )
        next(gen)  # the status frame
        next(gen)  # the words
        gen.close()  # the browser goes away
        turn = ChatTurn.objects.get()
        self.assertTrue(turn.content.startswith("partial words"))
        self.assertIn("incomplete", turn.content)
        self.assertEqual(ModelCall.objects.get().outcome, "disconnected")

    # Catches an empty or whitespace message opening a chat or costing a call.
    def test_an_empty_message_is_refused_and_saves_nothing(self):
        stub = self.use(StubClient())
        self.assertEqual(self.send("   ").status_code, 400)
        self.assertEqual(ChatSession.objects.count(), 0)
        self.assertEqual(stub.requests, [])

    # Catches a save failure after the response began tearing the stream.
    def test_a_failed_save_does_not_break_the_reply(self):
        self.use(StubClient(reply(text_block("fine"))))
        with mock.patch.object(services, "record_run", side_effect=RuntimeError("db gone")):
            response = self.send("hi")
        self.assertIn("fine", response.body)


class ReplyTests(ChatTestCase):
    # Catches the reply, its look-ups or its log being saved apart, and a
    # status frame reaching the stored text.
    def test_a_reply_with_a_look_up_is_stored_with_its_source_and_logged(self):
        stub = self.use(StubClient(
            reply(tool_block("lookup_term", {"term": "severe absence"}), stop_reason="tool_use"),
            reply(text_block("It means missing half of sessions.")),
        ))
        response = self.send("What is severe absence?")

        self.assertIn(streaming.STATUS_SEP, response.body)
        turn = ChatTurn.objects.get(role="assistant")
        self.assertEqual(turn.content, "It means missing half of sessions.")
        call = ToolCall.objects.get()
        self.assertEqual((call.turn, call.tool_name, call.source, call.is_error),
                         (turn, "lookup_term", tools.GLOSSARY_SOURCE, False))
        self.assertIn("50%", call.result["definition"])

        log = ModelCall.objects.get()
        self.assertEqual((log.user, log.outcome, log.api_calls, log.tool_calls),
                         (self.user, "ok", 2, 1))
        self.assertEqual((log.input_tokens, log.output_tokens), (20, 10))
        self.assertEqual((log.model, bool(log.prompt_version)), ("test-model", True))

        # The tool result went back in ONE user message, after the
        # assistant's own content, verbatim.
        second = stub.requests[1]["messages"]
        self.assertEqual(second[-2]["role"], "assistant")
        self.assertEqual(second[-1]["content"][0]["type"], "tool_result")

    # Catches the model forging a status frame, or a NUL failing the save.
    def test_reserved_characters_from_the_model_never_reach_the_page_or_store(self):
        self.use(StubClient(reply(text_block("a\x1efake status\x1eb\x00c"))))
        response = self.send("hi")
        self.assertEqual(ChatTurn.objects.get(role="assistant").content, "afake statusbc")
        self.assertNotIn("\x1efake", response.body)

    # Catches a refusal being shown as an error, or logged as an answer.
    def test_a_refusal_is_said_plainly_and_logged_as_one(self):
        self.use(StubClient(reply(stop_reason="refusal")))
        response = self.send("hi")
        self.assertIn(streaming.REFUSAL_MESSAGE, response.body)
        self.assertEqual(ModelCall.objects.get().outcome, "refused")

    # Catches a tool loop running without limit (the cost control).
    def test_the_loop_stops_at_the_call_limit(self):
        asking = [reply(tool_block("lookup_term", {"term": "severe absence"}, id=f"tu_{i}"),
                        stop_reason="tool_use") for i in range(streaming.MAX_API_CALLS)]
        stub = self.use(StubClient(*asking))
        response = self.send("hi")
        self.assertEqual(len(stub.requests), streaming.MAX_API_CALLS)
        self.assertIn("more look-ups", response.body)
        self.assertEqual(ModelCall.objects.get().outcome, "tool_limit")

    # Catches a sampling parameter or a forced tool choice being added:
    # this model answers 400 to each.
    def test_the_request_carries_only_the_parameters_the_model_accepts(self):
        stub = self.use(StubClient(reply(text_block("ok"))))
        self.send("hi")
        request = stub.requests[0]
        self.assertEqual(set(request), {"model", "max_tokens", "system", "messages",
                                        "output_config", "cache_control", "tools"})
        self.assertEqual(request["output_config"], {"effort": "medium"})

    # Catches the system prompt or the tool list varying between calls,
    # which silently ends prompt caching.
    def test_the_cached_prefix_is_identical_between_people(self):
        stub = self.use(StubClient(reply(text_block("one")), reply(text_block("two"))))
        self.send("hi")
        other_client = self.client_class()
        other_client.force_login(self.other)
        self.send("hi", key=KEY_B, client=other_client)
        first, second = stub.requests
        self.assertEqual(first["system"], second["system"])
        self.assertEqual(json.dumps(first["tools"]), json.dumps(second["tools"]))


class ToolTests(ChatTestCase):
    # Catches a tool failure escaping into a response already being sent.
    def test_a_failing_or_unknown_tool_is_an_error_result_not_an_exception(self):
        run = tools.runner_for(self.user)
        self.assertEqual(run("no_such_tool", {})[2], True)
        self.assertEqual(run("lookup_term", {"term": "not in the glossary"})[2], True)

    # Catches a tool being handed anyone but the person who asked.
    def test_a_tool_is_run_for_the_signed_in_user(self):
        seen = []
        tool = tools.Tool(definition={"name": "whoami"}, label="…",
                          handler=lambda user, input: (seen.append(user) or {}, ""))
        with mock.patch.dict(tools.TOOLS, {"whoami": tool}):
            tools.runner_for(self.user)("whoami", {})
        self.assertEqual(seen, [self.user])


class LimitsAndPageTests(ChatTestCase):
    # Catches the rate limit being dropped: each message is a paid call.
    def test_the_eleventh_message_in_a_minute_is_refused_and_not_saved(self):
        self.use(StubClient(*[reply(text_block("ok")) for _ in range(services.RATE_LIMIT_REQUESTS)]))
        for _ in range(services.RATE_LIMIT_REQUESTS):
            self.assertEqual(self.send("hi").status_code, 200)
        response = self.send("one too many")
        self.assertEqual(response.status_code, 429)
        self.assertFalse(ChatTurn.objects.filter(content="one too many").exists())

    # Catches a chat's title reaching <title> (browser history keeps it) or
    # an attribute.
    def test_a_title_is_shown_as_text_and_never_in_the_page_title(self):
        session = ChatSession.objects.create(user=self.user, session_key=KEY_A, title='Secret "plan" qz')
        ChatTurn.objects.create(session=session, role="user", content="hello")
        html = self.client.get(reverse("chat"), {"session_id": KEY_A}).content.decode()
        self.assertIn("Secret &quot;plan&quot; qz</h1>", html)
        self.assertNotIn("Secret", html.split("<title>")[1].split("</title>")[0])
        self.assertNotRegex(html, r'="[^"]*Secret[^"]*"')

    # Catches delete being reachable by a link (a GET) or leaving turns behind.
    def test_delete_needs_a_post_and_removes_the_chat_and_its_turns(self):
        session = ChatSession.objects.create(user=self.user, session_key=KEY_A)
        ChatTurn.objects.create(session=session, role="user", content="hello")
        self.assertEqual(self.client.get(reverse("chat_delete", args=[KEY_A])).status_code, 405)
        self.assertEqual(self.client.post(reverse("chat_delete", args=[KEY_A])).status_code, 302)
        self.assertEqual((ChatSession.objects.count(), ChatTurn.objects.count()), (0, 0))

    # Catches the log keeping words: it outlives the chat.
    def test_the_log_survives_the_chat_and_holds_no_content(self):
        self.use(StubClient(reply(text_block("a distinctive reply qz"))))
        self.send("a distinctive question qz")
        self.client.post(reverse("chat_delete", args=[KEY_A]))
        log = ModelCall.objects.get()
        self.assertIsNone(log.session)
        self.assertNotIn("distinctive", json.dumps(
            {f.name: str(getattr(log, f.name)) for f in ModelCall._meta.fields}))


class QuestionSetTests(ChatTestCase):
    """questions.yaml, against the real model when AI_RUN_LIVE_TESTS is on
    (it costs money and needs a key), and against a stub otherwise, which
    proves only that the set and this runner still fit together."""

    def ask(self, question):
        if not LIVE:
            self.use(StubClient(
                reply(tool_block(question["must_call"], {"term": "severe absence"}), stop_reason="tool_use"),
                reply(text_block(" ".join(question["must_contain"]))),
            ))
        session = ChatSession.objects.create(user=self.user, session_key=f"q{ChatSession.objects.count()}")
        with override_settings(AI_MODEL=REAL_MODEL if LIVE else "test-model"):
            agent = services.build_agent(self.user)
        runs = []
        for _ in streaming.stream_reply(
            agent, services.api_history(session, question["ask"]), tools.runner_for(self.user),
            on_complete=runs.append,
        ):
            pass
        return runs[0]

    def test_every_question_uses_its_tool_and_says_what_it_must(self):
        import yaml
        from pathlib import Path

        questions = yaml.safe_load((Path(__file__).parent / "questions.yaml").read_text(encoding="utf-8"))
        self.assertTrue(questions)
        for question in questions:
            with self.subTest(ask=question["ask"][:40]):
                run = self.ask(question)
                self.assertEqual(run.outcome, "ok")
                self.assertIn(question["must_call"], [call.name for call in run.tool_calls])
                for words in question.get("must_contain", []):
                    self.assertIn(words, run.text)
                for words in question.get("must_not_contain", []):
                    self.assertNotIn(words, run.text)
