from __future__ import annotations

from django.db.models import (
    BigIntegerField,
    Count,
    IntegerField,
    OuterRef,
    QuerySet,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from users.models import User


def with_admin_list_annotations(qs: QuerySet[User]) -> QuerySet[User]:
    qs = qs.select_related("organization")
    campaigns_count_sq = (
        User.objects.filter(pk=OuterRef("pk"))
        .values("pk")
        .annotate(
            c=Count("organization__campaigns", distinct=True),
        )
        .values("c")[:1]
    )
    return qs.annotate(
        campaigns_count=Coalesce(
            Subquery(campaigns_count_sq, output_field=IntegerField()),
            Value(0),
            output_field=IntegerField(),
        ),
        donations_count=Coalesce(
            Count("donations", distinct=True),
            Value(0),
            output_field=IntegerField(),
        ),
        total_donated=Coalesce(
            Sum("donations__amount"),
            Value(0),
            output_field=BigIntegerField(),
        ),
    )
