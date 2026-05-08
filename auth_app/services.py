from __future__ import annotations

from django.db import transaction

from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from users.models import User


def revoke_all_refresh_tokens_for_user(user: User) -> None:
    qs = OutstandingToken.objects.filter(user=user).select_for_update()
    for outstanding in qs:
        BlacklistedToken.objects.get_or_create(token=outstanding)


def change_user_password(user: User, new_password: str) -> None:
    with transaction.atomic():
        user.set_password(new_password)
        user.save(update_fields=["password"])
        revoke_all_refresh_tokens_for_user(user)
