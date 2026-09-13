import hashlib
import json
from datetime import datetime

from django.apps import apps
from django.core import serializers
from django.core.management.base import BaseCommand, CommandError
from django.db import models


EXCLUDED_MODELS = {
    "auth.permission",
    "contenttypes.contenttype",
    "sessions.session",
}


def migration_models():
    return sorted(
        (
            model
            for model in apps.get_models()
            if model._meta.label_lower not in EXCLUDED_MODELS
        ),
        key=lambda model: model._meta.label_lower,
    )


def normalize_datetimes(model, serialized_object):
    datetime_fields = {
        field.name
        for field in model._meta.concrete_fields
        if isinstance(field, models.DateTimeField)
    }
    for field_name in datetime_fields:
        value = serialized_object["fields"].get(field_name)
        if value is not None:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            serialized_object["fields"][field_name] = parsed.isoformat(
                timespec="milliseconds"
            )
    return serialized_object


class Command(BaseCommand):
    help = "Print deterministic row counts and hashes for database migration verification."

    def add_arguments(self, parser):
        parser.add_argument("--database", default="default")
        parser.add_argument(
            "--assert-import-target-empty",
            action="store_true",
            help="Fail if any application data that dumpdata would import already exists.",
        )

    def handle(self, *args, **options):
        database = options["database"]
        report = {}

        for model in migration_models():
            label = model._meta.label_lower
            queryset = model._default_manager.using(database).order_by(model._meta.pk.name)
            count = queryset.count()

            if options["assert_import_target_empty"] and count:
                raise CommandError(
                    f"Import target is not empty: {label} contains {count} row(s)."
                )

            serialized_objects = json.loads(
                serializers.serialize(
                    "json",
                    queryset.iterator(),
                    use_natural_foreign_keys=True,
                    use_natural_primary_keys=True,
                )
            )
            serialized_objects = [
                normalize_datetimes(model, item) for item in serialized_objects
            ]
            serialized_records = sorted(
                json.dumps(item, sort_keys=True, separators=(",", ":"))
                for item in serialized_objects
            )
            serialized = json.dumps(serialized_records, separators=(",", ":"))
            report[label] = {
                "count": count,
                "sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            }

        canonical = json.dumps(report, sort_keys=True, separators=(",", ":"))
        output = {
            "database": database,
            "models": report,
            "total_rows": sum(item["count"] for item in report.values()),
            "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        }
        self.stdout.write(json.dumps(output, sort_keys=True, indent=2))
