from rest_framework.routers import SimpleRouter

from campaigns.viewsets import AdminCampaignViewSet

router = SimpleRouter()
router.register("", AdminCampaignViewSet, basename="admin-campaign")

urlpatterns = router.urls
