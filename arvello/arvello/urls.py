"""
URL configuration for arvello project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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

from django.urls import path
from arvelloapp.views import *
from arvelloapp import views
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', login, name='login'),
    path('login/', login, name='login'),
    path('accounts/login/', login, name='login'),
    path('invoices/', views.invoices, name='invoices'),
    path('offers/', views.offers, name='offers'),
    path('invoice_pdf/<int:pk>/', invoice_pdf, name='invoice_pdf'),
    path('offer_pdf/<int:pk>/', offer_pdf, name='offer_pdf'),
    path('login/', login, name='login'),
    path('admin/', admin.site.urls),
    path('logout/', auth_views.logout_then_login, name='logout'),
    path('products/', views.products, name='products'),
    path('clients/', views.clients, name='clients'),
    path('companies/', views.companies, name='companies'),
    path('inventory/', views.inventory, name='inventory'),
    path('create_invoice/', views.create_invoice, name='create_invoice'),
    path('create_offer/', views.create_offer, name='create_offer'),
    path('inventory_label/<int:pk>/', inventory_label, name='inventory_label'),
    path('product_label/<int:pk>/', product_label, name='product_label'),
    path('outgoing_invoices_book_view/', views.OutgoingInvoicesBookView, name='outgoing_invoices_book_view'),
    path('expenses/', views.expenses, name='expenses'),
    path('expenses/delete/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('suppliers/', views.suppliers, name='suppliers'),
    path('incoming-invoice-book/', views.incoming_invoice_book, name='incoming_invoice_book'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Arvello backend administracija"
admin.site.site_title = "Arvello backend"
admin.site.index_title = "Dobrodošli u Arvello backend"