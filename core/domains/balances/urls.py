from django.urls import path

from .views import UserBalanceMeView

urlpatterns = [
    path(
        "user/balance/me/",
        UserBalanceMeView.as_view(),
        name="user-balance-me",
    ),
]
