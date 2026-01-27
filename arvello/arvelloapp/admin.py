from django.contrib import admin
from .models import *
from simple_history.admin import SimpleHistoryAdmin
from django.contrib import admin


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

from .models import UserProfile, SubjectMembership
from .models import Payslip


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'active_company', 'created_at')


@admin.register(SubjectMembership)
class SubjectMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'role', 'created_at')


@admin.register(Payslip)
class PayslipAdmin(SimpleHistoryAdmin):
    list_display = ('employee', 'subject', 'period_month', 'period_year', 'gross', 'net', 'status')
    list_filter = ('period_year', 'period_month', 'status')
    search_fields = ('employee__first_name', 'employee__last_name', 'subject__clientName')

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