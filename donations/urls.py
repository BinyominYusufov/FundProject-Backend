from rest_framework.routers import SimpleRouter

from donations.viewsets import DonationViewSet

router = SimpleRouter()
router.register("", DonationViewSet, basename="donation")

urlpatterns = router.urls
