from __future__ import annotations

from django.db import transaction
from django.db.models import F, QuerySet
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from donations.models import Donation
from donations.serializers import (
    AdminDonationStatusSerializer,
    DonationCreateSerializer,
    DonationSerializer,
)
from funds.models import Fund
from myapp.permissions import IsAdminRole
from users.permissions import IsAuthenticatedActiveUser


@method_decorator(name="list", decorator=swagger_auto_schema(tags=["Donations"]))
@method_decorator(name="retrieve", decorator=swagger_auto_schema(tags=["Donations"]))
@method_decorator(name="create", decorator=swagger_auto_schema(tags=["Donations"]))
class DonationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Authenticated donor: create a donation, list/retrieve only their own."""

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticatedActiveUser,)

    def get_serializer_class(self):
        if self.action == "create":
            return DonationCreateSerializer
        return DonationSerializer

    def get_queryset(self) -> QuerySet[Donation]:
        user = self.request.user
        if not getattr(user, "is_authenticated", False):
            return Donation.objects.none()
        return (
            Donation.objects.select_related("fund", "user")
            .filter(user_id=user.pk)
            .order_by("-created_at")
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = DonationCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)  # amount <= 0 -> 400

        fund_id = serializer.validated_data["fund_id"]
        fund = Fund.objects.filter(pk=fund_id).first()
        if fund is None:
            raise NotFound("Fund not found.")  # invalid fund_id -> 404
        if fund.status != Fund.Status.ACTIVE:
            raise ValidationError({"fund_id": "Fund is not active."})  # -> 400

        amount = serializer.validated_data["amount"]
        with transaction.atomic():
            donation = Donation.objects.create(
                user=request.user,  # never from request body
                fund=fund,
                amount=amount,
                status=Donation.Status.COMPLETED,
            )
            # Atomic F() update — safe against races when two donations to the
            # same fund are created concurrently.
            Fund.objects.filter(pk=fund.pk).update(
                raised_amount=F("raised_amount") + amount,
            )
        return Response(
            DonationSerializer(donation).data,
            status=status.HTTP_201_CREATED,
        )


@method_decorator(name="list", decorator=swagger_auto_schema(tags=["Admin"]))
@method_decorator(name="partial_update", decorator=swagger_auto_schema(tags=["Admin"]))
class AdminDonationViewSet(
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Admin: list every donation (filterable), and transition status via PATCH."""

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticatedActiveUser, IsAdminRole)

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return AdminDonationStatusSerializer
        return DonationSerializer

    def get_queryset(self) -> QuerySet[Donation]:
        qs = Donation.objects.select_related("fund", "user").order_by("-created_at")
        status_param = (self.request.query_params.get("status") or "").strip().lower()
        if status_param:
            valid = {c for c, _ in Donation.Status.choices}
            if status_param not in valid:
                raise ValidationError(
                    {"status": f"Invalid status. Allowed: {', '.join(sorted(valid))}."}
                )
            qs = qs.filter(status=status_param)
        fund_id = self.request.query_params.get("fund_id")
        if fund_id:
            try:
                qs = qs.filter(fund_id=int(fund_id))
            except (TypeError, ValueError):
                raise ValidationError({"fund_id": "fund_id must be an integer."})
        return qs

    def update(self, request: Request, *args, **kwargs) -> Response:
        # PUT intentionally disabled — clients must use PATCH.
        return Response(
            {"detail": 'Method "PUT" not allowed. Use PATCH to update status.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = AdminDonationStatusSerializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(DonationSerializer(instance).data)
