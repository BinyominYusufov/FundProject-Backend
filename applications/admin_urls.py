from rest_framework.routers import SimpleRouter

from applications.viewsets import AdminFundApplicationViewSet

router = SimpleRouter()
router.register("", AdminFundApplicationViewSet, basename="admin-fund-application")

urlpatterns = router.urls
