from rest_framework.routers import SimpleRouter

from users.viewsets import AdminUserViewSet

router = SimpleRouter()
router.register("", AdminUserViewSet, basename="admin-user")

urlpatterns = router.urls
