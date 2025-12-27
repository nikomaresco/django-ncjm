import re

from django import forms
from django.conf import settings

from .AddJokeFormBase import AddJokeFormBase
from ncjm.models import LongJoke, Tag


class AddLongJokeForm(AddJokeFormBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        supported_platforms = ", ".join(settings.NCJM_MEDIA_PROVIDERS)
        self.fields["media_url"].help_text = f"Supported platforms: {supported_platforms}"

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
                    "placeholder": "What's the name of this joke?",
                    "autocomplete": "off",
                }
            ),
            "transcript": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Tell the joke!",
                    "class": "markdown-editor",
                }
            ),
            "media_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "A URL to an audio or video recording of the joke.",
                    "autocomplete": "off",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Any notes about the joke, like tips on telling the joke.",
                    "class": "markdown-editor",
                }
            ),
            "hidden_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Any notes about the joke that should not be immediately visible, such as an explanation.",
                    "class": "markdown-editor",
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

