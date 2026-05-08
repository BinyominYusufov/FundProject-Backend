from django.urls import path
from .views import DonationListView, DonationCreateView, DonationDetailView, CampaignDonationsView

urlpatterns = [
    path('', DonationListView.as_view(), name='donation-list'),
    path('create/', DonationCreateView.as_view(), name='donation-create'),
    path('<int:pk>/', DonationDetailView.as_view(), name='donation-detail'),
    path('campaign/<int:campaign_id>/', CampaignDonationsView.as_view(), name='campaign-donations'),
]
