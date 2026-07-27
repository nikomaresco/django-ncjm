from django.test import TestCase
from django.template import TemplateDoesNotExist, engines

from ncjm.models import Joke

class TemplateLoadingTest(TestCase):
    def test_template_loading(self):
        try:
            template = engines['django'].get_template('base.html')
            print(f"Template directory: {template.origin.name}")
        except TemplateDoesNotExist:
            self.fail("Template 'base.html' does not exist")


class ReactionsTemplateAccessibilityTest(TestCase):
    def setUp(self):
        Joke.objects.create(
            setup="Why did the scarecrow win an award?",
            punchline="Because he was outstanding in his field.",
            submitter_name="dana",
            is_approved=True,
        )

    def test_reaction_buttons_include_label_aria_attributes(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="reaction-button"')
        self.assertContains(response, 'aria-label="angry"')
        self.assertContains(response, 'aria-label="hilarious"')
