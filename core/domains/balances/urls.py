from django.urls import path

from .views import UserBalanceHistoryView, UserBalanceMeView

urlpatterns = [
    path(
        "user/balance/me/",
        UserBalanceMeView.as_view(),
        name="user-balance-me",
    ),
    path(
        "user/balance/history/",
        UserBalanceHistoryView.as_view(),
        name="user-balance-history",
    ),
]
