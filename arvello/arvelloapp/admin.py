from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(Client)
admin.site.register(Invoice)
admin.site.register(Product)
admin.site.register(Offer)
admin.site.register(Company)
admin.site.register(Inventory)
admin.site.register(InvoiceProduct)
admin.site.register(OfferProduct)
admin.site.register(Expense)