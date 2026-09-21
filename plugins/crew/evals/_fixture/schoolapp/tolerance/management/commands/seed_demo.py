"""Fills an empty development database with one school's worth of demo data.

Dates are relative to today so the dashboard always has something to show.
Users get no usable password unless --password is given; log in through
the admin or the test client's force_login.
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from schools.models import Membership, Pupil, School
from tolerance.models import Observation

PUPILS = [
    ("Priya", "Nair", 4),
    ("Tom", "Reilly", 4),
    ("Aisha", "Khan", 5),
    ("Ben", "Okoro", 3),
]

# (pupil index, days ago, mood, body)
OBSERVATIONS = [
    (0, 2, "dysregulated", "Threw her chair at the start of numeracy, calmed after ten minutes outside."),
    (0, 6, "calm", "Settled all day, led the reading group."),
    (0, 9, "dysregulated", "Refused to come in from break, shouting at staff."),
    (0, 15, "anxious", "Tearful before the assembly, sat with TA."),
    (0, 28, "dysregulated", "Kicked the door when asked to line up."),
    (0, 35, "calm", "Good morning, worked with partner."),
    (1, 1, "anxious", "Worried about the spelling test, reassured."),
    (1, 12, "withdrawn", "Quiet at lunch, sat alone."),
    (1, 20, "calm", "Fine."),
    (2, 3, "calm", "Helped a younger pupil find her coat."),
    (2, 30, "dysregulated", "Argument at the gate with parent, upset for an hour."),
    (3, 5, "withdrawn", "Did not join PE, said he felt sick."),
    (3, 8, "withdrawn", "Head on desk most of the afternoon."),
    (3, 11, "anxious", "Asked to phone home twice."),
]


class Command(BaseCommand):
    help = "Seed a development database with one demo school, its teachers, pupils and observations."

    def add_arguments(self, parser):
        parser.add_argument("--password", help="Give the demo teachers this password instead of none.")

    @transaction.atomic
    def handle(self, *args, password=None, **options):
        User = get_user_model()
        if School.objects.exists():
            self.stdout.write("Database already has a school; nothing seeded.")
            return
        hill = School.objects.create(name="Hill Lane Primary")
        vale = School.objects.create(name="Vale Road Primary")
        teachers = {}
        for username, first, last, school in [
            ("m.okafor", "Mary", "Okafor", hill),
            ("j.brennan", "James", "Brennan", hill),
            ("s.lindqvist", "Sara", "Lindqvist", vale),
        ]:
            user = User.objects.create_user(username, first_name=first, last_name=last)
            if password:
                user.set_password(password)
                user.save()
            Membership.objects.create(user=user, school=school)
            teachers[username] = user
        pupils = [
            Pupil.objects.create(school=hill, first_name=f, last_name=l, year_group=y) for f, l, y in PUPILS
        ]
        Pupil.objects.create(school=vale, first_name="Ella", last_name="Doyle", year_group=2)
        today = date.today()
        for index, days_ago, mood, body in OBSERVATIONS:
            Observation.objects.create(
                pupil=pupils[index],
                author=teachers["m.okafor" if index != 3 else "j.brennan"],
                observed_on=today - timedelta(days=days_ago),
                mood=mood,
                body=body,
            )
        self.stdout.write(f"Seeded {School.objects.count()} schools, {Pupil.objects.count()} pupils, {Observation.objects.count()} observations.")
