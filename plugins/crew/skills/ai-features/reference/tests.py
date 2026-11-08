"""Article 8's order first: access, signed-out behaviour, nothing lost. Then
article 13: the payload, the log, the human step, the question set.

The model is stubbed unless AI_RUN_LIVE_TESTS is set. The stub cites the
first passage it was given, which is enough to prove the pipeline."""
import types
from pathlib import Path
from unittest import mock

import anthropic
import httpx2 as httpx
import yaml
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from . import services
from .models import ModelCall, Suggestion
from .redact import redact

HERE = Path(__file__).parent


def fake_response(text, stop_reason="end_turn"):
    block = types.SimpleNamespace(type="text", text=text)
    usage = types.SimpleNamespace(input_tokens=120, output_tokens=40)
    return types.SimpleNamespace(content=[block], usage=usage, stop_reason=stop_reason, _request_id="req_test")


class StubClient:
    """Answers with a citation of the first passage sent, or raises."""

    def __init__(self, raise_=None, text=None, stop_reason="end_turn"):
        self.raise_, self.text, self.stop_reason = raise_, text, stop_reason
        self.last_payload = None
        self.messages = types.SimpleNamespace(create=self._create)
        self.beta = types.SimpleNamespace(messages=types.SimpleNamespace(create=self._create))

    def _create(self, **payload):
        self.last_payload = payload
        if self.raise_:
            raise self.raise_
        if self.text is not None:
            return fake_response(self.text, self.stop_reason)
        ids = services.CITATION.findall(payload["messages"][0]["content"])
        cite = f"[P{ids[0]}]" if ids else ""
        return fake_response(f"The guidance says what to do. {cite}", self.stop_reason)


def timeout_error():
    return anthropic.APITimeoutError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))


@override_settings(AI_MONTHLY_TOKEN_CAP=1_000_000, AI_KEEP_REQUEST_TEXT=False)
class AssistantTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("load_corpus", str(HERE / "sample_corpus"), corpus_version="test", verbosity=0)
        School = apps.get_model("schools.School")
        Membership = apps.get_model("schools.Membership")
        Pupil = apps.get_model(settings.AI_PUPIL_MODEL)
        Target = apps.get_model(settings.AI_TARGET_MODEL)
        User = get_user_model()
        cls.school = School.objects.create(name="Oak")
        other = School.objects.create(name="Elm")
        cls.teacher = User.objects.create_user("teacher", password="x")
        cls.colleague = User.objects.create_user("colleague", password="x")
        cls.outsider = User.objects.create_user("outsider", password="x")
        Membership.objects.create(user=cls.teacher, school=cls.school)
        Membership.objects.create(user=cls.colleague, school=cls.school)
        Membership.objects.create(user=cls.outsider, school=other)
        cls.pupil = Pupil.objects.create(school=cls.school, first_name="Amara", last_name="Okafor")
        cls.target = Target.objects.create(pupil=cls.pupil, body="observed")

    def suggest(self, user, pupil=None, question="Can I edit a concern I recorded yesterday?"):
        if user:
            self.client.force_login(user)
        return self.client.post(reverse("assistant:suggest"), {"pupil": (pupil or self.pupil).pk, "question": question})

    # access and signed-out behaviour (articles 1 and 8)

    def test_signed_out_suggest_is_401_json_not_a_redirect(self):
        r = self.suggest(None)
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["error"], "signed_out")

    def test_teacher_cannot_ask_about_another_schools_pupil(self):
        with mock.patch.object(services, "client", return_value=StubClient()):
            r = self.suggest(self.outsider)
        self.assertEqual(r.status_code, 404)
        self.assertEqual(ModelCall.objects.count(), 0)

    def test_teacher_cannot_accept_another_teachers_suggestion(self):
        with mock.patch.object(services, "client", return_value=StubClient()):
            sid = self.suggest(self.teacher).json()["suggestion"]
        self.client.force_login(self.colleague)
        r = self.client.post(reverse("assistant:accept", args=[sid]), {"text": "x", "target": self.target.pk})
        self.assertEqual(r.status_code, 404)

    # the payload (article 13)

    def test_payload_carries_no_pupil_name_date_of_birth_or_contact(self):
        question = "Amara Okafor (dob 03/04/2017, mum@example.com, 07700 900123) was upset. What should I record?"
        passages = services.retrieve(question, services.current_corpus())
        payload, redacted = services.build_payload(question, passages, ["Amara", "Okafor"])
        sent = payload["system"] + payload["messages"][0]["content"]
        for secret in ("Amara", "Okafor", "03/04/2017", "mum@example.com", "07700 900123"):
            self.assertNotIn(secret, sent)
        self.assertIn("[PUPIL]", redacted)
        self.assertEqual(payload["model"], settings.AI_MODEL)

    def test_redact_handles_surname_inside_full_name(self):
        text, n = redact("Okafor and Amara Okafor", ["Amara Okafor", "Okafor"])
        self.assertEqual(text, "[PUPIL] and [PUPIL]")
        self.assertEqual(n, 2)

    # the log and the suggestion

    def test_suggest_logs_the_call_and_returns_a_grounded_cited_answer(self):
        with mock.patch.object(services, "client", return_value=StubClient()):
            r = self.suggest(self.teacher)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["grounded"])
        self.assertEqual(body["citations"][0]["ref"], "Sample guidance (replace with real documents) / Recording a concern")
        call = ModelCall.objects.get()
        self.assertEqual((call.outcome, call.prompt_version, call.corpus_version), ("ok", "1", "test"))
        self.assertEqual(call.input_tokens + call.output_tokens, 160)
        self.assertEqual(call.request_text, "", "request text is not kept unless the setting says so")
        self.assertEqual(Suggestion.objects.get().question, "Can I edit a concern I recorded yesterday?")

    def test_an_answer_that_cites_nothing_is_opinion_not_guidance(self):
        with mock.patch.object(services, "client", return_value=StubClient(text="Probably fine. [P999999]")):
            r = self.suggest(self.teacher)
        self.assertFalse(r.json()["grounded"])
        self.assertEqual(r.json()["citations"], [])

    def test_a_refusal_is_an_outcome_with_a_message_not_a_crash(self):
        with mock.patch.object(services, "client", return_value=StubClient(text="", stop_reason="refusal")):
            r = self.suggest(self.teacher)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["error"], "refused")
        self.assertEqual(ModelCall.objects.get().outcome, "refused")

    def test_a_timeout_is_logged_and_nothing_is_written(self):
        with mock.patch.object(services, "client", return_value=StubClient(raise_=timeout_error())):
            r = self.suggest(self.teacher)
        self.assertEqual(r.status_code, 503)
        self.assertEqual(ModelCall.objects.get().outcome, "timeout")
        self.assertEqual(Suggestion.objects.count(), 0)
        self.target.refresh_from_db()
        self.assertEqual(self.target.agreed_action, "")

    @override_settings(AI_MONTHLY_TOKEN_CAP=0)
    def test_the_cap_refuses_cleanly_before_any_call(self):
        stub = StubClient()
        with mock.patch.object(services, "client", return_value=stub):
            r = self.suggest(self.teacher)
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.json()["error"], "cap")
        self.assertIsNone(stub.last_payload)

    # the human step (article 13) and nothing lost (article 6)

    def test_accept_saves_the_teachers_text_as_theirs_and_marks_the_record(self):
        with mock.patch.object(services, "client", return_value=StubClient()):
            sid = self.suggest(self.teacher).json()["suggestion"]
        text = "Agreed with the lead: record it today, don't edit – add a new entry 😊\r\nSecond line"
        r = self.client.post(reverse("assistant:accept", args=[sid]), {"text": text, "target": self.target.pk})
        self.assertEqual(r.status_code, 200)
        self.target.refresh_from_db()
        self.assertEqual(self.target.agreed_action, text, "byte for byte, line endings included (article 6)")
        self.assertTrue(self.target.model_assisted)
        s = Suggestion.objects.get(pk=sid)
        self.assertIsNotNone(s.accepted_at)
        self.assertEqual(s.accepted_text, text)

    # the question set (article 13), stubbed by default, live on request

    def test_question_set(self):
        questions = yaml.safe_load((HERE / "questions.yaml").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(questions), 2)
        live = getattr(settings, "AI_RUN_LIVE_TESTS", False)
        corpus = services.current_corpus()
        for q in questions:
            with self.subTest(q=q["question"]):
                refs = [p.ref() for p in services.retrieve(q["question"], corpus)]
                self.assertIn(q["must_cite"], refs, "retrieval did not surface the passage the answer needs")
                if not live:
                    continue
                result = services.ask(user=self.teacher, school_id=self.school.pk, pupil_ref="pupil:test", names=[], question=q["question"])
                self.assertTrue(result.ok, result.message)
                self.assertTrue(result.suggestion.grounded)
                self.assertIn(q["must_cite"], [c["ref"] for c in result.suggestion.citations])
                for word in q["must_contain"]:
                    self.assertIn(word.lower(), result.suggestion.answer.lower())
