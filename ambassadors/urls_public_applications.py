from django.urls import path

from ambassadors.views_public import AmbassadorApplicationCreateView

urlpatterns = [
    path("", AmbassadorApplicationCreateView.as_view(), name="ambassador-application-create"),
]
