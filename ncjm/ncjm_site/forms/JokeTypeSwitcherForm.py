from django import forms

class JokeTypeSwitcherForm(forms.Form):
#TODO: make this dynamic based on form_type or something like that
    joke_types = forms.MultipleChoiceField(
        choices=[
            ("CornyJoke", "Corny Joke"),
            ("LongJoke", "Long Joke"),
        ],
        widget=forms.CheckboxSelectMultiple,
        initial=["CornyJoke", "LongJoke"],
        required=False,
    )