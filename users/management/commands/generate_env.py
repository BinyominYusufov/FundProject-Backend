"""Generate a starter .env file at the project root."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = "Auto-generates a .env file with a secure SECRET_KEY"

    def handle(self, *args, **options) -> None:
        base_dir = Path(settings.BASE_DIR)
        env_path = base_dir / ".env"

        if env_path.is_file():
            answer = input("File .env already exists. Overwrite? [y/N]: ").strip().lower()
            if answer not in ("y", "yes"):
                self.stdout.write("Aborted.")
                return

        secret_key = get_random_secret_key()
        # Quote value so '=' inside the key does not break KEY=value parsing.
        lines = (
            f'SECRET_KEY="{secret_key}"',
            "DEBUG=True",
            "EMAIL_HOST_USER=",
            "EMAIL_HOST_PASSWORD=",
            "DATABASE_URL=",
        )
        content = "\n".join(lines) + "\n"

        try:
            with open(env_path, "w", encoding="utf-8", newline="\n") as env_file:
                env_file.write(content)
        except PermissionError:
            self.stderr.write(
                self.style.ERROR(
                    "Permission denied: cannot write the .env file. "
                    f"Check write access to: {env_path.resolve()}",
                ),
            )
            return

        resolved = env_path.resolve()
        self.stdout.write(self.style.SUCCESS(f"✅  .env created at: {resolved}"))
        self.stdout.write(self.style.SUCCESS("🔑  SECRET_KEY was generated automatically"))
        self.stdout.write(
            self.style.SUCCESS(
                "📧  Fill in EMAIL_HOST_USER and EMAIL_HOST_PASSWORD to enable email",
            ),
        )
        self.stdout.write(
            self.style.WARNING("⚠️   Set DEBUG=False before deploying to production"),
        )
