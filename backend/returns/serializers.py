from rest_framework import serializers
from .models import Return


class ReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Return
        fields = "__all__"

class ReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Return
        fields = [
            "id",
            "product",
            "sale",
            "quantity",
            "reason",
            "created_at"
        ]