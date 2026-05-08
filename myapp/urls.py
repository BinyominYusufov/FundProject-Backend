from django.urls import path

from myapp.views import FundOwnerApplicationCollectionView, FundOwnerApplicationReviewView

urlpatterns = [
    path(
        "",
        FundOwnerApplicationCollectionView.as_view(),
        name="fund-application-list-create",
    ),
    path(
        "<int:pk>/review/",
        FundOwnerApplicationReviewView.as_view(),
        name="fund-application-review",
    ),
]
