from django.contrib import admin

from .models import Sale, SaleItem
from .models import Receipt

admin.site.register(Receipt)
admin.site.register(Sale)
admin.site.register(SaleItem)
