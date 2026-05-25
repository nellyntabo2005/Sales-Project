# Create your views here.
from rest_framework import viewsets
from .models import Return
from .serializers import ReturnSerializer
from notifications.utils import send_notification
from urllib3 import request


class ReturnViewSet(viewsets.ModelViewSet):
    queryset = Return.objects.all()
    serializer_class = ReturnSerializer

    def perform_create(self, serializer):
        returned_product = serializer.save()

        send_notification(
          request.user,  f"🔄 Product returned: {returned_product.product.name}"
        )

        send_notification(
          request.user,  f"💰 Refund processed for return #{returned_product.id}"
        )