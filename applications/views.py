from __future__ import annotations

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions

from applications.models import FundApplication
from applications.serializers import FundApplicationSubmitSerializer


class FundApplicationCreateView(generics.CreateAPIView):
    queryset = FundApplication.objects.none()
    serializer_class = FundApplicationSubmitSerializer
    permission_classes = (permissions.AllowAny,)

    @swagger_auto_schema(tags=["Applications"])
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
