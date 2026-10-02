from django.urls import path

from .views import (
    CompanyMarketplaceCoinsMeView,
    UserBalanceHistoryView,
    UserBalanceMeView,
)

urlpatterns = [
    path(
        "marketplace/coins/me/",
        CompanyMarketplaceCoinsMeView.as_view(),
        name="marketplace-coins-me",
    ),
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
