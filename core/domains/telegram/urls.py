from django.urls import path

from .views import (
    BroadcastView,
    GenerateTelegramBindCodeView,
    GetTelegramBindCodeView,
)

urlpatterns = [
    path(
        "broadcast/send/",
        BroadcastView.as_view(),
        name="broadcast-send",
    ),
    path(
        "bot/generate-bind-code/",
        GenerateTelegramBindCodeView.as_view(),
        name="bot-generate-bind-code",
    ),
    path(
        "bot/bind-code/",
        GetTelegramBindCodeView.as_view(),
        name="bot-bind-code",
    ),
]
