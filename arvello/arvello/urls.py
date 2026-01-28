"""
URL configuration for arvello project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

from arvelloapp import views
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

# Auth URL-ovi
auth_patterns = [
    path('', auth_views.LoginView.as_view(template_name='login.html', next_page='invoices'), name='login'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html', next_page='invoices'), name='login_alt'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]

# Ključni poslovni URL-ovi
core_patterns = [
    path('invoices/', views.invoices, name='invoices'),
    path('offers/', views.offers, name='offers'),
    path('products/', views.products, name='products'),
    path('clients/', views.clients, name='clients'),
    path('companies/', views.companies, name='companies'),
    path('inventory/', views.inventory, name='inventory'),
]

# URL-ovi za dokumente
document_patterns = [
    path('create_invoice/', views.create_invoice, name='create_invoice'),
    path('create_offer/', views.create_offer, name='create_offer'),
    path('invoice_pdf/<int:pk>/', views.invoice_pdf, name='invoice_pdf'),
    path('offer_pdf/<int:pk>/', views.offer_pdf, name='offer_pdf'),
    path('inventory_label/<int:pk>/', views.inventory_label, name='inventory_label'),
    path('product_label/<int:pk>/', views.product_label, name='product_label'),
    path('invoices/send_email/<int:invoice_id>/', views.send_invoice_email, name='send_invoice_email'),
    path('mark_offer_finished/<int:offer_id>/', views.mark_offer_finished, name='mark_offer_finished'),
]

table_exports = [
    path('export_inventory_excel/', views.export_inventory_to_excel, name='export_inventory_to_excel'),
    path('export_inventory_csv/', views.export_inventory_to_csv, name='export_inventory_to_csv'),
]

# Financijski URL-ovi
finance_patterns = [
    path('expenses/', views.expenses, name='expenses'),
    path('expenses/delete/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('suppliers/', views.suppliers, name='suppliers'),
    path('tax-parameters/', views.tax_parameters, name='tax_parameters'),
]

# HR/Plaće URL-ovi
hr_patterns = [
    path('employees/', views.employees, name='employees'),
    path('salaries/', views.salaries, name='salaries'),
    path('payslip/<int:salary_id>/', views.salary_payslip, name='salary_payslip'),
    path('employee-api/<int:employee_id>/', views.employee_api, name='employee_api'),
]

# Izvještajni URL-ovi
report_patterns = [
    path('outgoing_invoices_book_view/', views.OutgoingInvoicesBookView, name='outgoing_invoices_book_view'),
    path('incoming-invoice-book/', views.incoming_invoice_book, name='incoming_invoice_book'),
    path('joppd-report/', views.joppd_report, name='joppd_report'),
]

# URL-ovi za povijest - provjeriti jesu li ispravno postavljeni
history_patterns = [
    # Izmjene u konfiguraciji URL-ova za povijest
    path('history/user/<int:user_id>/', views.view_history, {'model_name': 'user'}, name='history_user'),
    path('history/<str:model_name>/<int:object_id>/', views.view_history, name='view_history_detail'),
    path('history/<str:model_name>/', views.view_history, name='history_model'),
    path('history/general/', views.view_history, {'model_name': 'general'}, name='view_history'),
    path('history/', views.view_history, name='history_general'),
]

# Informativni URL-ovi
info_patterns = [
    path('pension-info/', views.pension_info, name='pension_info'),
    path('tax-changes-2025/', views.tax_changes_2025, name='tax_changes_2025'),
]

# API URL-ovi
api_patterns = [
    path('local-tax-data/<int:tax_id>/', views.get_local_tax_data, name='get_local_tax_data'),
    path('invoices/<int:invoice_id>/mark-paid/', views.mark_invoice_paid, name='mark_invoice_paid'),
    path('api/ai-chat/', views.ai_chat, name='ai_chat'),
]

# Kombinirani URL-ovi
urlpatterns = [
    path('admin/', admin.site.urls),
    *auth_patterns,
    *core_patterns,
    *document_patterns,
    *finance_patterns,
    *hr_patterns,
    *report_patterns,
    *history_patterns,
    *info_patterns,
    *api_patterns,
    *table_exports,
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin site customization
admin.site.site_header = "Arvello backend administracija"
admin.site.site_title = "Arvello backend"
admin.site.index_title = "Dobrodošli u Arvello backend"