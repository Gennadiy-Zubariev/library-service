from django.contrib.auth import get_user_model
from django.utils.translation import gettext
from rest_framework import serializers

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "password")
        extra_kwargs = {
            "password": {
                "write_only": True,
                "min_length": 5,
                "label": gettext("Password"),
                "style": {"input_type": "password"},
                "trim_whitespace": False,
            }
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "is_staff")
        read_only_fields = ("id", "email", "is_staff")
