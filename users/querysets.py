from __future__ import annotations

from django.db.models import QuerySet

from users.models import User


def with_admin_list_annotations(qs: QuerySet[User]) -> QuerySet[User]:
    return qs.select_related("organization")
