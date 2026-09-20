"""Proves the eval fixture's seeded defects are still seeded.

Run from the fixture root, after migrate, with:

    python3 manage.py shell < ../../../../../tools/fixture_check.py

Every case in evals/ grades an agent on a defect this script reproduces.
If a check here fails, a case is about to score on a defect that no longer
exists, or the fixture drifted. Rolls back everything it creates.
"""
import re

from django.db import transaction
from django.contrib.auth import get_user_model
from django.test import Client
from django.test.utils import setup_test_environment

setup_test_environment()
User = get_user_model()
fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


class Rollback(Exception):
    pass


try:
    with transaction.atomic():
        from schools.models import Membership, Pupil, School
        from tolerance.models import Observation

        hill = School.objects.create(name="Hill")
        vale = School.objects.create(name="Vale")
        t_hill = User.objects.create_user("t_hill", password="pw-fixture-1")
        Membership.objects.create(user=t_hill, school=hill)
        t_vale = User.objects.create_user("t_vale", password="pw-fixture-1")
        Membership.objects.create(user=t_vale, school=vale)
        deputy = User.objects.create_user("deputy", password="pw-fixture-1")
        pupil = Pupil.objects.create(school=hill, first_name="A", last_name="B", year_group=3)
        obs = Observation.objects.create(pupil=pupil, author=t_hill, observed_on="2026-09-01", mood="calm", body="x")

        # master-at-arms-unfiltered-detail
        c = Client()
        c.force_login(t_vale)
        check("detail view is unfiltered by school", c.get(f"/observations/{obs.pk}/").status_code == 200)

        # bosun-split-comment
        c = Client()
        c.force_login(t_hill)
        body = c.get("/observations/new/").content.decode()
        check("form template leaks a split comment", "{#" in body or re.search(r"\{[#%{]", body) is not None)

        # purser-destructive-migration and trigger-text-came-back-shorter
        field = Observation._meta.get_field("body")
        check("Observation.body is a CharField(200)", field.get_internal_type() == "CharField" and field.max_length == 200)
        check("Observation.pupil cascades", Observation._meta.get_field("pupil").remote_field.on_delete.__name__ == "CASCADE")

        # gunner-cross-school-test
        import os
        check("tolerance/tests.py is empty", os.path.getsize("tolerance/tests.py") == 0)

        # surgeon-deputy-head-500
        c = Client()
        c.force_login(deputy)
        raised = False
        try:
            c.get("/dashboard/")
        except Exception as e:
            raised = type(e).__name__ == "RelatedObjectDoesNotExist"
        check("a user with no Membership raises on the dashboard", raised)

        # lookout-first-login-404
        c = Client()
        r = c.post("/login/", {"username": "t_hill", "password": "pw-fixture-1"})
        landing = c.get(r["Location"]).status_code if r.status_code == 302 else r.status_code
        check("a bare login lands on a 404", r.status_code == 302 and r["Location"] == "/accounts/profile/" and landing == 404)

        raise Rollback
except Rollback:
    pass

if fails:
    raise SystemExit("fixture check failed: " + ", ".join(fails))
print("every seeded defect reproduces")
