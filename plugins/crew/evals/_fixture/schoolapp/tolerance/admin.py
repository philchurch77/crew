from django.contrib import admin

from .models import Observation


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ["pupil", "observed_on", "mood", "author"]
    list_filter = ["mood"]
