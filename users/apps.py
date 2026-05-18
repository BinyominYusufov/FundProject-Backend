import logging
import os

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Пользователи'

    def ready(self):
        from django.db.models.signals import post_migrate
        from users import signals  # noqa: F401  registers post_save handler
        post_migrate.connect(_post_migrate_bootstrap, sender=self)
        post_migrate.connect(_post_migrate_groups, sender=self)

        if os.environ.get("RUN_MAIN") != "true" and not _is_management_command():
            return
        _try_bootstrap("ready")


def _is_management_command() -> bool:
    import sys
    if len(sys.argv) < 2:
        return False
    cmd = sys.argv[1]
    return cmd in {"runserver", "shell", "shell_plus", "test"}


def _post_migrate_bootstrap(sender, **kwargs):
    _try_bootstrap("post_migrate")


def _post_migrate_groups(sender, **kwargs):
    try:
        from users.signals import ensure_role_groups
        ensure_role_groups()
    except Exception as exc:
        logger.warning("[GROUPS/post_migrate] Skipped: %s", exc)


def _try_bootstrap(origin: str) -> None:
    try:
        from config.dev_auth import AUTO_BOOTSTRAP, _bootstrap_dev_entities
        if not AUTO_BOOTSTRAP:
            return
        _bootstrap_dev_entities()
    except Exception as exc:
        logger.warning("[BOOTSTRAP/%s] Skipped: %s", origin, exc)
