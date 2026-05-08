from django.urls import path

from applications.views import FundApplicationCreateView

urlpatterns = [
    path("submit/", FundApplicationCreateView.as_view(), name="application-submit"),
]
