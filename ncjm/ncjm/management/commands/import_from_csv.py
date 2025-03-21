import csv

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.utils import timezone

from ncjm.models import CornyJoke, Tag, JokeTag

JOKES_CSV = r"c:/temp/jokes.csv"
TAGS_CSV = r"c:/temp/tags.csv"
TAG_RELATIONS_CSV = r"c:/temp/tag_relations.csv"

class Command(BaseCommand):
    help = "Import jokes, tags, and tag relations from CSV files"

    def handle(self, *args, **kwargs):
        self.import_jokes()
        self.import_tags()
        self.import_tag_relations()

    def import_jokes(self):
        with open(JOKES_CSV, newline="", encoding="UTF-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                is_queued = row["queued"] == "1"
                is_deleted = row["queued"] == "2"

                try:
                    created_at = timezone.make_aware(
                        timezone.datetime.strptime(row["submitted"],"%Y-%m-%d %H:%M:%S"),
                        timezone.get_current_timezone(),
                    )
                    CornyJoke.objects.update_or_create(
                        ext_id=row["id"],
                        defaults={
                            "setup": row["setup"],
                            "punchline": row["punchline"],
                            "submitter_name": row["submitter"],
                            "created_at": created_at,
                            "is_approved": not is_queued and not is_deleted,
                            "is_deleted": is_deleted,
                        }
                    )
                except IntegrityError as e:
                    self.stdout.write(self.style.ERROR(f"Problem adding joke:"))
                    self.stdout.write(self.style.ERROR(row))
                    self.stdout.write(self.style.ERROR(e))

    def import_tags(self):
        with open(TAGS_CSV, newline="", encoding="UTF-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    Tag.objects.update_or_create(
                        ext_id=row["id"],
                        defaults={
                            "tag_text": row["tag"],
                        }
                    )
                except IntegrityError as e:
                    self.stdout.write(self.style.ERROR(f"Problem adding tag:"))
                    self.stdout.write(self.style.ERROR(row))
                    self.stdout.write(self.style.ERROR(e))

    def import_tag_relations(self):
        with open(TAG_RELATIONS_CSV, newline="", encoding="UTF-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    joke = CornyJoke.objects.get(ext_id=row["joke_id"])
                    tag = Tag.objects.get(ext_id=row["tag_id"])
                    JokeTag.objects.update_or_create(
                        joke=joke,
                        tag=tag,
                        defaults={
                            "created_at": row["created"],
                        }
                    )
                except CornyJoke.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Joke with ext_id {row['joke_id']} does not exist"))
                except Tag.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Tag with ext_id {row['tag_id']} does not exist"))
