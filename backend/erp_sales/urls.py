"""
URL configuration for erp_sales project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from sales import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
<<<<<<< HEAD
=======
    path('',views.Home,name='my index'),


>>>>>>> 8c05e676f9e5f713ad213e0a46b3f92e73af6c4d
    path('api/customers/', include('customers.urls')),
    path('api/users/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/sales/', include('sales.urls')),
    #path('api/returns/', include('returns.urls')),
    path('api/payments/', include('payments.urls')),
    #path('api/reports/', include('reports.urls')),
    #path('api/notifications/', include('notifications.urls')),
    #path('api/inventory/', include('inventory.urls')),
    
    path(
        'api/token/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),

    path(
        'api/token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),
    path('api/reports/', include('reports.urls')),
]


