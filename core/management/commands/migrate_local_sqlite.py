"""One-time, transaction-safe SQLite-to-PostgreSQL migration for EduOsh."""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import DEFAULT_DB_ALIAS, connections, transaction

SOURCE = "sqlite_migration_source"
APPS = {"auth", "authtoken", "core", "finance"}
EXCLUDED = {"auth.Permission", "contenttypes.ContentType"}


class Command(BaseCommand):
    help = "Inspect or one-time copy a SQLite EduOsh source into an empty PostgreSQL target."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True, help="Absolute source db.sqlite3 path")
        parser.add_argument("--apply", action="store_true", help="Actually write; dry-run is default")
        parser.add_argument(
            "--allow-nonempty", action="store_true",
            help="Permit inventory-only dry-run of a populated target; never permits writes.",
        )
        parser.add_argument("--batch-size", type=int, default=500)

    def handle(self, *args, **options):
        path = Path(options["source"]).expanduser().resolve()
        if not path.is_file():
            raise CommandError(f"Source SQLite does not exist: {path}")
        if connections[DEFAULT_DB_ALIAS].vendor != "postgresql":
            raise CommandError("Target must be PostgreSQL; refusing any other target.")
        # Start with Django's fully normalized default settings so the dynamic
        # connection includes required keys such as TIME_ZONE and TEST.
        connections.databases[SOURCE] = {
            **connections.databases[DEFAULT_DB_ALIAS],
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(path),
        }
        models = self.models()
        source_counts, target_counts = self.counts(models, SOURCE), self.counts(models, DEFAULT_DB_ALIAS)
        self.print_counts("SOURCE", source_counts)
        self.print_counts("TARGET", target_counts)
        existing = {name: count for name, count in target_counts.items() if count}
        if existing and not options["allow_nonempty"]:
            raise CommandError("Target is not empty; refusing merge/overwrite: " + ", ".join(f"{k}={v}" for k, v in existing.items()))
        if options["allow_nonempty"] and options["apply"]:
            raise CommandError("--allow-nonempty is inventory-only and cannot be used with --apply.")
        self.check_source_relations(models)
        self.check_content_types(models)
        if not options["apply"]:
            message = "Dry-run passed; no target data changed."
            if existing:
                message = "Inventory completed for populated target; no target data changed."
            self.stdout.write(self.style.SUCCESS(message))
            return
        with transaction.atomic(using=DEFAULT_DB_ALIAS):
            type_ids = self.content_type_ids()
            for model in self.order(models):
                self.copy_model(model, type_ids, options["batch_size"])
            self.copy_m2m(models)
            self.reset_sequences(models)
            after = self.counts(models, DEFAULT_DB_ALIAS)
            if after != source_counts:
                raise CommandError("Post-import count mismatch; transaction will roll back.")
            self.check_target_relations(models)
        self.print_counts("POSTGRES", self.counts(models, DEFAULT_DB_ALIAS))
        self.stdout.write(self.style.SUCCESS("Import committed; PostgreSQL sequences reset."))

    def models(self):
        return [m for m in apps.get_models() if m._meta.app_label in APPS and not m._meta.auto_created and not m._meta.proxy and m._meta.label not in EXCLUDED]

    def counts(self, models, using):
        return {m._meta.label: m._default_manager.using(using).count() for m in models}

    def print_counts(self, heading, counts):
        self.stdout.write(f"{heading} inventory:")
        for label, count in counts.items(): self.stdout.write(f"  {label}: {count}")

    def check_source_relations(self, models):
        model_set = set(models)
        for model in models:
            for field in model._meta.fields:
                related = getattr(field.remote_field, "model", None)
                if related not in model_set or field.null:
                    continue
                if model._default_manager.using(SOURCE).exclude(**{f"{field.name}__isnull": True}).exclude(**{f"{field.name}__in": related._default_manager.using(SOURCE).values("pk")}).exists():
                    raise CommandError(f"Source orphan relation: {model._meta.label}.{field.name}")

    def check_target_relations(self, models):
        model_set = set(models)
        for model in models:
            for field in model._meta.fields:
                related = getattr(field.remote_field, "model", None)
                if related not in model_set or field.null:
                    continue
                if model._default_manager.exclude(**{f"{field.name}__isnull": True}).exclude(**{f"{field.name}__in": related._default_manager.values("pk")}).exists():
                    raise CommandError(f"Target orphan relation: {model._meta.label}.{field.name}")

    def check_content_types(self, models):
        ids = set()
        for model in models:
            for field in model._meta.fields:
                if getattr(field.remote_field, "model", None) is ContentType:
                    ids.update(model._default_manager.using(SOURCE).values_list(field.attname, flat=True))
        known = ContentType.objects.using(SOURCE).in_bulk(pk for pk in ids if pk is not None)
        if any(pk is not None and pk not in known for pk in ids):
            raise CommandError("Source has an invalid ContentType reference.")

    def content_type_ids(self):
        return {source.pk: ContentType.objects.get_by_natural_key(source.app_label, source.model).pk for source in ContentType.objects.using(SOURCE).all()}

    def order(self, models):
        all_models, needed, children = set(models), defaultdict(set), defaultdict(set)
        for model in models:
            for field in model._meta.fields:
                parent = getattr(field.remote_field, "model", None)
                if parent in all_models and parent is not model:
                    needed[model].add(parent); children[parent].add(model)
        ready, result = deque(m for m in models if not needed[m]), []
        while ready:
            model = ready.popleft(); result.append(model)
            for child in children[model]:
                needed[child].discard(model)
                if not needed[child]: ready.append(child)
        if len(result) != len(models):
            raise CommandError("Cyclic model dependencies need manual review: " + ", ".join(m._meta.label for m in models if m not in result))
        return result

    def copy_model(self, model, type_ids, batch_size):
        type_fields = {f.attname for f in model._meta.fields if getattr(f.remote_field, "model", None) is ContentType}
        batch = []
        for source in model._default_manager.using(SOURCE).iterator(chunk_size=batch_size):
            target = model()
            for field in model._meta.local_fields:
                value = getattr(source, field.attname)
                setattr(target, field.attname, type_ids[value] if field.attname in type_fields and value is not None else value)
            batch.append(target)
            if len(batch) >= batch_size:
                model._default_manager.using(DEFAULT_DB_ALIAS).bulk_create(batch, batch_size=batch_size); batch.clear()
        if batch: model._default_manager.using(DEFAULT_DB_ALIAS).bulk_create(batch, batch_size=batch_size)
        self.stdout.write(f"Copied {model._meta.label}")

    def copy_m2m(self, models):
        for model in models:
            for field in model._meta.many_to_many:
                if not field.remote_field.through._meta.auto_created: continue
                for pk in model._default_manager.using(SOURCE).values_list("pk", flat=True).iterator():
                    related = getattr(model._default_manager.using(SOURCE).get(pk=pk), field.name).values_list("pk", flat=True)
                    getattr(model._default_manager.get(pk=pk), field.name).add(*related)

    def reset_sequences(self, models):
        with connections[DEFAULT_DB_ALIAS].cursor() as cursor:
            for statement in connections[DEFAULT_DB_ALIAS].ops.sequence_reset_sql(no_style(), models): cursor.execute(statement)
