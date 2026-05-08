from django.urls import include, path
from rest_framework.routers import SimpleRouter

from campaigns.viewsets import FundOwnerCampaignViewSet
from donations.viewsets import FundOwnerDonationViewSet

from .views import OrganizationDetailView, OrganizationListView, OrganizationProfileView

fo_campaign_router = SimpleRouter()
fo_campaign_router.register("", FundOwnerCampaignViewSet, basename="fund-owner-campaign")

fo_donation_router = SimpleRouter()
fo_donation_router.register("", FundOwnerDonationViewSet, basename="fund-owner-donation")

urlpatterns = [
    path("donations/", include(fo_donation_router.urls)),
    path("my-funds/", include(fo_campaign_router.urls)),
    path("", OrganizationListView.as_view(), name="fund-owner-list"),
    path("profile/", OrganizationProfileView.as_view(), name="fund-owner-profile"),
    path("<int:pk>/", OrganizationDetailView.as_view(), name="fund-owner-detail"),
]
