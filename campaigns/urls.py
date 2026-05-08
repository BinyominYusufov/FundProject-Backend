from django.urls import path

from campaigns.views import CampaignDetailView, CampaignListView

urlpatterns = [
    path("", CampaignListView.as_view(), name="campaign-list"),
    path("<int:pk>/", CampaignDetailView.as_view(), name="campaign-detail"),
]
