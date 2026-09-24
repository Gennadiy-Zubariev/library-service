from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users.views import UserMeView, UserRegisterView

app_name = "users"

urlpatterns = [
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("register/", UserRegisterView.as_view(), name="register"),
    path("me/", UserMeView.as_view(), name="me"),
]
