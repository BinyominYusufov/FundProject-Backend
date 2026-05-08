from __future__ import annotations

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
# from rest_framework_simplejwt.authentication import JWTAuthentication

from myapp.exceptions import EmailDeliveryError
from myapp.models import FundOwnerApplication
# from myapp.permissions import IsAdminRole
from myapp.serializers import (
    FundOwnerApplicationReviewSerializer,
    FundOwnerApplicationSerializer,
)
from myapp.services import (
    create_fund_owner_user,
    generate_password,
    send_approval_email,
    send_rejection_email,
)
from users.models import Organization


class FundOwnerApplicationCollectionView(generics.GenericAPIView):
    queryset = FundOwnerApplication.objects.all()
    serializer_class = FundOwnerApplicationSerializer
    pagination_class = None
    # authentication_classes = (JWTAuthentication,)
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    def get_permissions(self):
        # DEV: список заявок без админа
        # if self.request.method == "GET":
        #     return [IsAdminRole()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        qs = FundOwnerApplication.objects.all().order_by("-created_at")
        st = self.request.query_params.get("status")
        if st is not None and str(st).strip() != "":
            allowed = {choice for choice, _ in FundOwnerApplication.Status.choices}
            st_norm = str(st).strip().lower()
            if st_norm not in allowed:
                allowed_str = ", ".join(sorted(allowed))
                raise ValidationError(
                    {"status": f"Invalid status. Allowed: {allowed_str}"},
                )
            qs = qs.filter(status=st_norm)
        return qs

    @swagger_auto_schema(tags=["Fund owner applications"])
    def get(self, request: Request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(tags=["Fund owner applications"])
    def post(self, request: Request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Your application has been submitted successfully."},
            status=status.HTTP_201_CREATED,
        )


class FundOwnerApplicationReviewView(generics.GenericAPIView):
    queryset = FundOwnerApplication.objects.all()
    serializer_class = FundOwnerApplicationReviewSerializer
    # authentication_classes = (JWTAuthentication,)
    # permission_classes = (IsAdminRole,)
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    lookup_field = "pk"

    @swagger_auto_schema(tags=["Fund owner applications"])
    def patch(self, request, *args, **kwargs):
        application = self.get_object()
        if application.status != FundOwnerApplication.Status.PENDING:
            return Response(
                {"detail": "Only pending applications can be reviewed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ser = FundOwnerApplicationReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        action = ser.validated_data["action"]

        User = get_user_model()

        if action == "approve":
            if application.email and User.objects.filter(
                email__iexact=User.objects.normalize_email(application.email),
            ).exists():
                return Response(
                    {
                        "detail": (
                            "A user account with this email already exists. "
                            "Resolve the conflict before approving."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            org = Organization.objects.create(
                name=application.full_name,
                verified=True,
            )
            pwd = generate_password()
            new_user = create_fund_owner_user(
                email=application.email,
                full_name=application.full_name,
                password=pwd,
                organization=org,
            )

            application.status = FundOwnerApplication.Status.APPROVED
            application.reviewed_at = timezone.now()
            application.save(update_fields=("status", "reviewed_at"))

            try:
                send_approval_email(
                    application.full_name,
                    application.email,
                    pwd,
                    new_user.username,
                )
            except EmailDeliveryError:
                return Response(
                    {
                        "status": "approved",
                        "email_sent": False,
                        "organization_id": org.pk,
                        "warning": (
                            "User created but email delivery failed. "
                            "Share credentials manually."
                        ),
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                {
                    "status": "approved",
                    "email_sent": True,
                    "organization_id": org.pk,
                },
                status=status.HTTP_200_OK,
            )

        application.status = FundOwnerApplication.Status.REJECTED
        application.reviewed_at = timezone.now()
        application.save(update_fields=("status", "reviewed_at"))

        try:
            send_rejection_email(application.full_name, application.email)
        except EmailDeliveryError:
            return Response(
                {
                    "status": "rejected",
                    "email_sent": False,
                    "warning": (
                        "Application rejected but email delivery failed. "
                        "Notify the applicant manually."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"status": "rejected", "email_sent": True},
            status=status.HTTP_200_OK,
        )
