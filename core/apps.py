from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        import core.signals  # noqa: F401
        import core.models as models_package
        from core.models.homework import build_homework_upload_path

        if not hasattr(
            models_package,
            "build_homework_upload_path",
        ):
            models_package.build_homework_upload_path = (
                build_homework_upload_path
            )
