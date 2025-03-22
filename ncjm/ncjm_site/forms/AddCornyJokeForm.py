import re

from django import forms

from . import AddJokeFormBase
from ncjm.models import CornyJoke, Tag


class AddCornyJokeForm(AddJokeFormBase):
    class Meta:
        model = CornyJoke
        fields = AddJokeFormBase.Meta.fields + ["setup", "punchline",]
        widgets = {
            **AddJokeFormBase.Meta.widgets,
            "setup": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., 'Why did the chicken cross the road?'",
                    "autocomplete": "off",
                }
            ),
            "punchline": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., 'To get to the other side!'",
                }
            ),
        }

    def clean_setup(self):
        return self._validate_text_field_not_empty("setup")

    def clean_punchline(self):
        return self._validate_text_field_not_empty("punchline")
