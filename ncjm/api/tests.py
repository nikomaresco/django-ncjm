from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from ncjm.models import Joke, Tag


class ApiV1Tests(APITestCase):
	def setUp(self):
		self.client = APIClient()

		user_model = get_user_model()
		self.user = user_model.objects.create_user(username="api-user", password="safe-pass-123")
		self.staff_user = user_model.objects.create_user(
			username="api-staff",
			password="safe-pass-123",
			is_staff=True,
		)

		self.approved_joke = Joke.objects.create(
			setup="Why do Python developers wear glasses?",
			punchline="Because they cannot C.",
			submitter_name="ada",
			is_approved=True,
		)
		self.approved_joke.reactions = Joke.default_reactions.copy()
		self.approved_joke.save(update_fields=["reactions"])

		self.unapproved_joke = Joke.objects.create(
			setup="What is orange and sounds like a parrot?",
			punchline="A carrot.",
			submitter_name="alan",
			is_approved=False,
		)

		self.deleted_joke = Joke.objects.create(
			setup="What did the ocean say to the beach?",
			punchline="Nothing, it just waved.",
			submitter_name="ada",
			is_approved=True,
		)
		self.deleted_joke.delete()

		tag = Tag.objects.create(tag_text="coding")
		self.approved_joke.tags.add(tag)

	def test_public_joke_list_returns_only_approved_non_deleted(self):
		response = self.client.get("/api/v1/jokes/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["count"], 1)
		self.assertEqual(len(response.data["results"]), 1)
		self.assertEqual(response.data["results"][0]["id"], self.approved_joke.id)

	def test_create_joke_requires_authentication(self):
		payload = {
			"setup": "How many programmers does it take to change a light bulb?",
			"punchline": "None, it is a hardware problem.",
			"submitter_name": "grace",
			"tags": [{"tag_text": "tech"}],
		}

		response = self.client.post("/api/v1/jokes/", payload, format="json")

		self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
		self.assertIn("error", response.data)
		self.assertIn("status", response.data["error"])
		self.assertIn("code", response.data["error"])
		self.assertIn("message", response.data["error"])
		self.assertIn("details", response.data["error"])

	def test_authenticated_create_joke_with_tags(self):
		self.client.force_authenticate(user=self.user)

		payload = {
			"setup": "What do you call a fake noodle?",
			"punchline": "An impasta.",
			"submitter_name": "grace",
			"is_approved": True,
			"tags": [{"tag_text": "Pasta"}, {"tag_text": "Food"}],
		}

		response = self.client.post("/api/v1/jokes/", payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data["submitter_name"], "grace")
		self.assertEqual(sorted([tag["tag_text"] for tag in response.data["tags"]]), ["food", "pasta"])

	def test_reaction_endpoint_records_then_conflicts_on_duplicate(self):
		self.client.force_authenticate(user=self.user)

		path = f"/api/v1/jokes/{self.approved_joke.id}/reactions/"

		first_response = self.client.post(path, {"emoji": "🤣"}, format="json")
		second_response = self.client.post(path, {"emoji": "🤣"}, format="json")

		self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(second_response.status_code, status.HTTP_409_CONFLICT)

	def test_reaction_endpoint_rejects_unsupported_emoji(self):
		self.client.force_authenticate(user=self.user)

		path = f"/api/v1/jokes/{self.approved_joke.id}/reactions/"
		response = self.client.post(path, {"emoji": "💩"}, format="json")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("error", response.data)
		self.assertEqual(response.data["error"]["code"], "validation_error")

	def test_allowed_reactions_options_endpoint_is_public_and_standardized(self):
		response = self.client.get("/api/v1/reactions/options/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn("allowed_reactions", response.data)
		self.assertEqual(response.data["allowed_reactions"], settings.NCJM_ALLOWED_REACTIONS)

		for item in response.data["allowed_reactions"]:
			self.assertIn("emoji", item)
			self.assertIn("label", item)

	def test_model_reactions_rejects_unsupported_emoji_on_save(self):
		joke = Joke(
			setup="Why did the database administrator leave his wife?",
			punchline="She had one-to-many relationships.",
			submitter_name="linus",
			reactions={"💩": 3},
		)

		with self.assertRaises(DjangoValidationError):
			joke.save()

	def test_model_reactions_backfills_missing_standard_keys(self):
		joke = Joke.objects.create(
			setup="Why are fish so smart?",
			punchline="Because they live in schools.",
			submitter_name="marge",
			reactions={"🤣": 2},
		)

		for emoji in Joke.default_reactions:
			self.assertIn(emoji, joke.reactions)

		self.assertEqual(joke.reactions["🤣"], 2)

	def test_hard_delete_requires_staff(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.delete(f"/api/v1/jokes/{self.approved_joke.id}/?hard=true")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertTrue(Joke.objects.filter(pk=self.approved_joke.id).exists())

	def test_staff_can_hard_delete(self):
		self.client.force_authenticate(user=self.staff_user)

		response = self.client.delete(f"/api/v1/jokes/{self.approved_joke.id}/?hard=true")

		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
		self.assertFalse(Joke.objects.filter(pk=self.approved_joke.id).exists())

	def test_tag_jokes_endpoint(self):
		response = self.client.get("/api/v1/tags/coding/jokes/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["count"], 1)
		self.assertEqual(response.data["results"][0]["id"], self.approved_joke.id)

	def test_submitter_list_endpoint(self):
		response = self.client.get("/api/v1/submitters/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		names = [item["submitter_name"] for item in response.data["results"]]
		self.assertEqual(names, ["ada"])

	def test_random_endpoint_not_found_error_contract(self):
		Joke.objects.all().delete()

		response = self.client.get("/api/v1/jokes/random/")

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
		self.assertIn("error", response.data)
		self.assertEqual(response.data["error"]["status"], status.HTTP_404_NOT_FOUND)
		self.assertIn("message", response.data["error"])
