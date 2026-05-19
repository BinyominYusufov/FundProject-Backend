from rest_framework.routers import SimpleRouter

from donations.viewsets import AdminDonationViewSet

router = SimpleRouter()
router.register("", AdminDonationViewSet, basename="admin-donation")

urlpatterns = router.urls
