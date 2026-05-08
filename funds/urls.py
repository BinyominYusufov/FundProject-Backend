from django.urls import include, path
from rest_framework.routers import DefaultRouter

from funds.views import FundViewSet

router = DefaultRouter()
router.register("", FundViewSet, basename="fund")

urlpatterns = [
    path("", include(router.urls)),
]
