from rest_framework.routers import DefaultRouter

from .views import (
    HomeworkSubmissionViewSet,
    HomeworkTaskViewSet,
)

router = DefaultRouter()
router.register(
    "homework-tasks",
    HomeworkTaskViewSet,
    basename="homework-tasks",
)
router.register(
    "homework-submissions",
    HomeworkSubmissionViewSet,
    basename="homework-submissions",
)

urlpatterns = router.urls
