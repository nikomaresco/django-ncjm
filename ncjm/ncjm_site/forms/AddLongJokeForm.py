import re

from django import forms
from django.conf import settings

from . import AddJokeFormBase
from ncjm.models import LongJoke, Tag


class AddLongJokeForm(AddJokeFormBase):
    class Meta:
        model = LongJoke
        fields = AddJokeFormBase.Meta.fields + [
            "title",
            "transcript",
            "media_url",
            "notes",
            "hidden_notes",
        ]
        widgets = {
            **AddJokeFormBase.Meta.widgets,
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "The title of the joke.",
                }
            ),
            "transcript": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "The text of the joke.",
                }
            ),
            "media_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "A URL to an audio or video recording of the joke.",
                }
            ),
            "notes": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Any notes about the joke.",
                }
            ),
            "hidden_notes": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Any notes about the joke that should not be immediately visible.",
                }
            ),
        }

    def clean_transcript(self):
        return self._validate_text_field_not_empty("setup")

    def clean_media_url(self):
        media_url = self.cleaned_data.get("media_url")
        # check if the URL is valid and points to a supported platform (e.g., YouTube, Vimeo)
        if media_url:
            supported_platforms = settings.NCJM_MEDIA_PROVIDERS
            if not any(platform in media_url for platform in supported_platforms):
                raise forms.ValidationError("The URL must point to a supported platform (e.g., YouTube, Vimeo).")
        return media_url

