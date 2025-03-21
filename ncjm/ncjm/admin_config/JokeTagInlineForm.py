import logging

from django import forms
from django.db import transaction

from ncjm.models import CornyJoke, Tag

log = logging.getLogger(__name__)


class JokeTagInlineForm(forms.ModelForm):
    tags = forms.CharField(
        help_text="Enter tags separated by spaces.",
        widget=forms.TextInput(attrs={"size": "255"}),
        required=False,
    )

    class Meta:
        model = CornyJoke
        fields = ["setup", "punchline", "submitter_name", "tags",]

    # ensures that the initial value of the tags field is a space-separated list of the current tags
    def get_initial_for_field(self, field, field_name):
        if field_name == "tags":
            if self.instance and self.instance.pk:
                tags_list = [tag.tag_text for tag in self.instance.tags.all()]
                return " ".join(tags_list)
        return super().get_initial_for_field(field, field_name)

    def save(self, commit=True):
        log.info(f"Saving joke: {self.cleaned_data}")

        tags_text = self.cleaned_data.pop("tags")
        joke = super().save(commit=False)

        with transaction.atomic():
            joke.save()

            tags_list = [tag.strip() for tag in tags_text.split()]
            current_tags = set(tag.tag_text for tag in joke.tags.all())
            new_tags = set(tags_list)

            # remove tags that are no longer associated
            for tag_text in current_tags - new_tags:
                log.debug(f"Removing tag: {tag_text}")
                tag = Tag.objects.get(tag_text=tag_text)
                joke.tags.remove(tag)

            # add new tags
            for tag_text in new_tags - current_tags:
                log.debug(f"Adding tag: {tag_text}")
                tag, _ = Tag.objects.get_or_create(tag_text=tag_text)
                joke.tags.add(tag)

        if commit:
            log.debug("Saving Joke.Tag ManyToMany relationships")
            joke.save_m2m()

        return joke