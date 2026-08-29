from django.test import TestCase, override_settings
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


class AnalyticsTemplateTest(TestCase):
    def setUp(self):
        Joke.objects.create(
            setup="Why was six afraid of seven?",
            punchline="Because seven eight nine.",
            submitter_name="dana",
            is_approved=True,
        )

    @override_settings(GA_ENABLED=False, GA_MEASUREMENT_ID="")
    def test_google_analytics_is_disabled_by_default(self):
        response = self.client.get("/")

        self.assertNotContains(response, "googletagmanager.com")
        self.assertNotContains(response, "random_joke_view")

    @override_settings(GA_ENABLED=True, GA_MEASUREMENT_ID="G-TEST123")
    def test_google_analytics_uses_configured_measurement_id(self):
        response = self.client.get("/")

        self.assertContains(response, "googletagmanager.com/gtag/js?id=G-TEST123")
        self.assertContains(response, 'gtag("config", "G-TEST123"')
        self.assertContains(response, "random_joke_view")


class PrivacyPageTest(TestCase):
    def test_privacy_page_and_footer_link(self):
        response = self.client.get("/privacy/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The short version")
        self.assertContains(response, "Google Analytics")
        self.assertContains(response, 'href="/privacy/"')
