from rest_framework import generics, permissions

from users.serializers import UserDetailSerializer, UserRegisterSerializer


class UserRegisterView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = (permissions.AllowAny,)


class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ("get", "patch")

    def get_object(self):
        return self.request.user
