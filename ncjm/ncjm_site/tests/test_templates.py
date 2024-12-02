from django.test import TestCase
from django.template import TemplateDoesNotExist, engines

class TemplateLoadingTest(TestCase):
    def test_template_loading(self):
        try:
            template = engines['django'].get_template('base.html')
            print(f"Template directory: {template.origin.name}")
        except TemplateDoesNotExist:
            self.fail("Template 'base.html' does not exist")
