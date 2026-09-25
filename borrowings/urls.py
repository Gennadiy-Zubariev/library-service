from django.urls import include, path
from rest_framework.routers import DefaultRouter

from borrowings.views import BorrowingView

app_name = "borrowings"

router = DefaultRouter()
router.register("", BorrowingView, basename="borrowing")

urlpatterns = [
    path("", include(router.urls)),
]
