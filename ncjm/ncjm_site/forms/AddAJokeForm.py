import re

from django import forms
from django.core.exceptions import ValidationError
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Invisible
from ncjm.models import Joke, Tag


class AddAJokeForm(forms.ModelForm):
    tags = forms.CharField(
        help_text="Enter tags separated by commas.",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "placeholder": "e.g., 'funny animal classic'",
            }
        )
    )

    captcha = ReCaptchaField(widget=ReCaptchaV2Invisible(
        attrs={
            "data-size": "compact",
        }
    ))

    class Meta:
        model = Joke
        fields = ["setup", "punchline", "submitter_name", "tags", "captcha", ]
        widgets = {
            "submitter_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., 'Funny McJokerson'",
                }
            ),
            "setup": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., 'Why did the chicken cross the road?'",
                }
            ),
            "punchline": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., 'To get to the other side!'",
                }
            ),
            "tags": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g., 'funny animal classic'",
                }
            )
        }

    def clean_submitter_name(self):
        """
        Validate the submitter name by ensuring it is not empty, is not in the
        banned names list, and does not contain an email address.
        """
        BANNED_NAMES = [
            "admin",
            "administrator",
            "funny mcjokerson"
        ]

        submitter_name = self._validate_text_field_not_empty("submitter_name")

        if not submitter_name:
            raise forms.ValidationError("Submitter name is required.")

        if submitter_name.lower() in BANNED_NAMES:
            raise forms.ValidationError("Invalid submitter name.")

        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', submitter_name):
            raise ValidationError("Submitter name cannot contain an email address.")

        return submitter_name

    def _validate_text_field_not_empty(self, field_name):
        """
        Validate a text field by ensuring it is not empty.

        Args:
            field_name (str): The name of the field to validate.

        Returns:
            str: The cleaned field value.
        """
        field_value = self.cleaned_data.get(field_name, "").strip()
        if not field_value:
            raise forms.ValidationError(f"{field_name.capitalize()} is required.")
        return field_value

    def clean_setup(self):
        return self._validate_text_field_not_empty("setup")

    def clean_punchline(self):
        return self._validate_text_field_not_empty("punchline")

    def save(self, commit=True):
        joke = super().save(commit=False)
        # turn tags to a list, or an empty list if none are provided (an empty
        #  string would normally result in [""])
        tags_list = [
            tag.strip().lower() for tag in self.cleaned_data["tags"].split(" ")
                if tag.strip()
        ]

        if commit:
            joke.save()

            joke.tags.clear()
#TODO: this logic also exists in the Joke serializer. refactor to a helper function.
            for tag in tags_list:
                tag_record, _ = Tag.objects.get_or_create(tag_text=tag)
                joke.tags.add(tag_record)

        return joke



