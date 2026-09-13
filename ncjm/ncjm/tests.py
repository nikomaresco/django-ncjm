from django.test import SimpleTestCase


class HealthCheckTest(SimpleTestCase):
    def test_health_check(self):
        response = self.client.get("/health/", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_health_check_rejects_post(self):
        response = self.client.post("/health/", secure=True)

        self.assertEqual(response.status_code, 405)
