from django.contrib import admin
from .models import *
from simple_history.admin import SimpleHistoryAdmin

# Register your models here.
# Školsko 24.
admin.site.register(Client)
admin.site.register(Invoice)
admin.site.register(Product)
# Županijsko 24.
admin.site.register(Offer)
    #admin.site.register(Company)
# Državno 24.
admin.site.register(Inventory)
admin.site.register(InvoiceProduct)
admin.site.register(OfferProduct)
# Županijsko 25.
admin.site.register(Expense)
admin.site.register(Supplier)
# Državno 25.
    #admin.site.register(Employee)
    #admin.site.register(Salary)
    #admin.site.register(TaxParameter)
    #admin.site.register(LocalIncomeTax)
admin.site.register(NonTaxablePaymentType)

@admin.register(Company)
class CompanyAdmin(SimpleHistoryAdmin):
    list_display = ('clientName', 'OIB', 'town')
    search_fields = ('clientName', 'OIB')

@admin.register(Employee)
class EmployeeAdmin(SimpleHistoryAdmin):
    list_display = ('first_name', 'last_name', 'oib', 'city')
    search_fields = ('first_name', 'last_name', 'oib')

@admin.register(Salary)
class SalaryAdmin(SimpleHistoryAdmin):
    list_display = ('employee', 'period_month', 'period_year', 'gross_salary', 'net_salary')
    list_filter = ('period_year', 'period_month')
    search_fields = ('employee__first_name', 'employee__last_name')

@admin.register(LocalIncomeTax)
class LocalIncomeTaxAdmin(SimpleHistoryAdmin):
    list_display = ('city_name', 'tax_rate_lower', 'tax_rate_higher', 'valid_from')
    search_fields = ('city_name',)

@admin.register(TaxParameter)
class TaxParameterAdmin(SimpleHistoryAdmin):
    list_display = ('parameter_type', 'value', 'year')
    list_filter = ('year', 'parameter_type')


@admin.register(KPDCode)
class KPDCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'level', 'parent_code')
    search_fields = ('code', 'name')
    list_filter = ('level',)
    ordering = ('code',)


@admin.register(CourtRegistryConfig)
class CourtRegistryConfigAdmin(SimpleHistoryAdmin):
    list_display = ('api_url', 'is_active', 'use_sandbox', 'updated_at')
    list_filter = ('is_active', 'use_sandbox')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('API konfiguracija', {
            'fields': ('api_url', 'client_id', 'client_secret', 'use_sandbox', 'is_active')
        }),
        ('Metapodaci', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )