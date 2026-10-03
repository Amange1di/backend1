from rest_framework.routers import DefaultRouter

from .views import LibraryFolderViewSet, LibraryItemViewSet

router = DefaultRouter()
router.register("library", LibraryItemViewSet, basename="library")
router.register("library-folders", LibraryFolderViewSet, basename="library-folders")

urlpatterns = router.urls
