from django import forms

from .models import Observation


class ObservationForm(forms.ModelForm):
    class Meta:
        model = Observation
        fields = ["pupil", "observed_on", "mood", "body"]
        widgets = {
            "observed_on": forms.DateInput(attrs={"type": "date"}),
            "body": forms.Textarea(attrs={"rows": 8}),
        }

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school is not None:
            self.fields["pupil"].queryset = self.fields["pupil"].queryset.filter(school=school)
