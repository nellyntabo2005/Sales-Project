from rest_framework import viewsets
from .models import Product
from .serializers import ProductSerializer
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin
from notifications.utils import send_notification
from urllib3 import request

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def perform_create(self, serializer):
        product = serializer.save()
        send_notification(request.user, f"📦 New product added: {product.name}")

    def perform_update(self, serializer):
        product = serializer.save()

        send_notification(request.user, f"✏️ Product updated: {product.name}")

        if product.stock < 20:
            send_notification(request.user, f"⚠️ Low stock alert: {product.name}: Only {product.stock} left!")