from __future__ import annotations

from django.db.models import Q, QuerySet
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from applications.models import FundApplication
from applications.serializers import AdminFundApplicationSerializer
from myapp.permissions import IsAdminRole
from users.permissions import IsAuthenticatedActiveUser, is_active_admin_request


@method_decorator(name="list", decorator=swagger_auto_schema(tags=["Admin"]))
@method_decorator(name="retrieve", decorator=swagger_auto_schema(tags=["Admin"]))
@method_decorator(name="approve", decorator=swagger_auto_schema(tags=["Admin"]))
@method_decorator(name="reject", decorator=swagger_auto_schema(tags=["Admin"]))
class AdminFundApplicationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticatedActiveUser, IsAdminRole)
    serializer_class = AdminFundApplicationSerializer

    def get_queryset(self) -> QuerySet[FundApplication]:
        if not is_active_admin_request(self.request):
            return FundApplication.objects.none()
        qs = FundApplication.objects.all().order_by("-created_at")
        search = (self.request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(email__icontains=search) | Q(fund_name__icontains=search),
            )
        return qs

    @action(detail=True, methods=["patch"], url_path="approve")
    def approve(self, request: Request, pk: str | None = None) -> Response:
        application = self.get_object()
        if application.status != FundApplication.Status.PENDING:
            return Response(
                {"detail": "Only pending applications can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        application.status = FundApplication.Status.APPROVED
        application.save(update_fields=["status"])
        return Response(AdminFundApplicationSerializer(application, context={"request": request}).data)

    @action(detail=True, methods=["patch"], url_path="reject")
    def reject(self, request: Request, pk: str | None = None) -> Response:
        application = self.get_object()
        if application.status != FundApplication.Status.PENDING:
            return Response(
                {"detail": "Only pending applications can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        application.status = FundApplication.Status.REJECTED
        application.save(update_fields=["status"])
        return Response(AdminFundApplicationSerializer(application, context={"request": request}).data)
