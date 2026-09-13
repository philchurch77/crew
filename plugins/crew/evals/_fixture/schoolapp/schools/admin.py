from django.contrib import admin

from .models import Membership, Pupil, School

admin.site.register(School)
admin.site.register(Membership)
admin.site.register(Pupil)
