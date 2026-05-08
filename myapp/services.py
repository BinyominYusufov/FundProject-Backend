from __future__ import annotations

import logging
import secrets
import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.mail import send_mail

from myapp.exceptions import EmailDeliveryError
from myapp.permissions import FUNOWNERS_GROUP
from users.models import Organization, User as UsersUser

logger = logging.getLogger(__name__)

SPECIAL_CHARS = "!@#$%^&*"
PASSWORD_ALPHABET = string.ascii_letters + string.digits + SPECIAL_CHARS
MIN_PASSWORD_LENGTH = 12

# Optional branding/URLs: set on `settings` to override defaults.
_APP_NAME = getattr(settings, "EMAIL_APP_BRAND_NAME", "Payvast")
_ADMIN_URL = getattr(settings, "FUND_OWNER_ADMIN_PANEL_URL", "http://yoursite.com/admin/")
_SUPPORT_EMAIL = getattr(settings, "SUPPORT_EMAIL", "support@yoursite.com")


def generate_password() -> str:
    while True:
        raw = "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(MIN_PASSWORD_LENGTH))
        if not any(c.isupper() for c in raw):
            continue
        if not any(c.isdigit() for c in raw):
            continue
        if not any(c in SPECIAL_CHARS for c in raw):
            continue
        return raw


def _get_fund_owners_group() -> Group:
    group, _ = Group.objects.get_or_create(name=FUNOWNERS_GROUP)
    return group


def create_fund_owner_user(
    *,
    email: str | None,
    full_name: str,
    password: str,
    organization: Organization | None = None,
) -> UsersUser:
    from users.models import unique_username_from_email_hint

    User = get_user_model()
    uname = unique_username_from_email_hint(email or "applicant@local", UserModel=User)
    user = User.objects.create_user(
        username=uname,
        email=User.objects.normalize_email(email) if email else None,
        password=password,
        name=full_name,
        role=UsersUser.Role.FUND_OWNER,
        is_verified=True,
        is_active=True,
    )
    if organization is not None:
        user.organization = organization
        user.save(update_fields=["organization"])
    group = _get_fund_owners_group()
    user.groups.add(group)
    return user


def send_approval_email(full_name: str, email: str, password: str, login_username: str) -> None:
    subject = "Поздравляем! Ваша заявка одобрена — данные для входа"
    sep = "─────────────────────────────"
    body = (
        f"Уважаемый(ая) {full_name},\n\n"
        "Поздравляем: Ваша заявка на роль Владельца Фонда одобрена. "
        "Теперь у Вас есть соответствующий доступ в системе.\n\n"
        "Теперь Вы можете создавать фонды и принимать пожертвования.\n\n"
        f"{sep}\n"
        " Ваши данные для входа:\n"
        f"{sep}\n"
        f" Логин (имя пользователя): {login_username}\n"
    )
    if email:
        body += f" Email (для связи):        {email}\n"
    body += (
        f" Пароль:                 {password}\n"
        f"{sep}\n\n"
        "Рекомендуем сменить пароль после первого входа.\n\n"
        f"Панель администратора: {_ADMIN_URL}\n\n"
        f"С уважением,\nКоманда {_APP_NAME}\n"
    )
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception("Не удалось отправить письмо об одобрении заявки на адрес %s", email)
        raise EmailDeliveryError("Failed to send approval email.") from exc


def send_rejection_email(full_name: str, email: str) -> None:
    subject = "Ваша заявка на роль Владельца Фонда"
    body = (
        f"Уважаемый(ая) {full_name},\n\n"
        "Благодарим Вас за интерес к нашей платформе. После рассмотрения Ваша заявка "
        "на роль Владельца Фонда, к сожалению, не была одобрена.\n\n"
        "Это не окончательное решение — Вы можете подать заявку повторно позже.\n\n"
        f"Если у Вас есть вопросы — свяжитесь с нами по адресу {_SUPPORT_EMAIL}.\n\n"
        f"С уважением,\nКоманда {_APP_NAME}\n"
    )
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception("Не удалось отправить письмо об отклонении заявки на адрес %s", email)
        raise EmailDeliveryError("Failed to send rejection email.") from exc
