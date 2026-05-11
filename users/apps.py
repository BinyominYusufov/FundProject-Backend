from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Пользователи'

    def ready(self):
        from decouple import config
        # AUTO-BOOTSTRAP FALLBACK: register post_migrate handler so dev entities
        # are created automatically after `manage.py migrate` on a fresh database.
        if config("AUTO_BOOTSTRAP", default=False, cast=bool):
            from django.db.models.signals import post_migrate
            post_migrate.connect(_post_migrate_bootstrap, sender=self)


def _post_migrate_bootstrap(sender, **kwargs):
    """AUTO-BOOTSTRAP FALLBACK: Ensure minimum required dev entities exist after migrations."""
    try:
        from config.dev_auth import _bootstrap_dev_entities
        _bootstrap_dev_entities()
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            "[AUTO-BOOTSTRAP] Bootstrap skipped (safe during initial migration): %s", exc,
        )
