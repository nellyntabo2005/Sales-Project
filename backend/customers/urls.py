from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet

from django.urls import path, include
router = DefaultRouter()
router.register(r'', CustomerViewSet, basename='customer')

urlpatterns = [ 
     path('api/', include(router.urls)),
]