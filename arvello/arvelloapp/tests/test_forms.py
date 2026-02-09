"""
Tests for form validation in arvelloapp.

FISCALIZATION NOTE:
-------------------
These tests only validate forms (form.is_valid()) - they do NOT save objects to
the database. Since fiscalization is triggered by Django's post_save signal on
the Invoice model, no fiscalization occurs during these tests.

If you extend these tests to save Invoice objects, either:
1. Use the FiscalSafeMixin from this module to disconnect the signal
2. Set fiscal_status='exempt' on the invoice before saving
3. Let it run with SandboxAdapter (default when no FiscalConfig exists)

See: arvelloapp/signals.py -> enqueue_invoice_for_fiscalization
"""
from django.test import TestCase
from django.utils import timezone
from django.db.models.signals import post_save
from arvelloapp.forms import ClientForm, ProductForm, InvoiceForm, ExpenseForm, OfferForm, SalaryForm
from arvelloapp.models import Client, Company, Employee, Invoice
from decimal import Decimal


class FiscalSafeMixin:
    """
    Mixin that disconnects the fiscalization signal during tests.
    
    Use this for tests that create/save Invoice objects but should not trigger
    fiscalization. For tests that intentionally test fiscalization behavior,
    do NOT use this mixin.
    
    Usage:
        class MyInvoiceTest(FiscalSafeMixin, TestCase):
            ...
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Import here to avoid circular imports at module level
        from arvelloapp.signals import enqueue_invoice_for_fiscalization
        post_save.disconnect(enqueue_invoice_for_fiscalization, sender=Invoice)
        cls._fiscal_signal_disconnected = True
    
    @classmethod
    def tearDownClass(cls):
        if getattr(cls, '_fiscal_signal_disconnected', False):
            from arvelloapp.signals import enqueue_invoice_for_fiscalization
            post_save.connect(enqueue_invoice_for_fiscalization, sender=Invoice)
        super().tearDownClass()


class ClientFormTest(TestCase):
    def test_valid_client_form(self):
        """Provjera da je forma ispravna s točnim podacima"""
        form_data = {
            'clientName': 'Test Client',
            'addressLine1': 'Test Address',
            'province': 'GRAD ZAGREB',
            'postalCode': '10000',
            'phoneNumber': '+385123456789',
            'emailAddress': 'test@example.com',
            'clientUniqueId': '0001',
            'clientType': 'Fizička osoba',
            'OIB': '12345678901',
            'VATID': 'HR12345678901'
        }
        form = ClientForm(data=form_data)
        if not form.is_valid():
            print(f"Client form errors: {form.errors}")
        self.assertTrue(form.is_valid())
    
    def test_invalid_client_form(self):
        """Provjera da je forma neispravna s pogrešnim podacima"""
        form_data = {
            'clientName': '',
            'addressLine1': 'Test Address',
        }
        form = ClientForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('clientName', form.errors)

class ProductFormTest(TestCase):
    def test_valid_product_form(self):
        """Provjera da je forma ispravna s točnim podacima"""
        form_data = {
            'title': 'Test Product',
            'description': 'Test Description',
            'price': 100.00,
            'taxPercent': 25.0,
            'currency': '€',
            'barid': '1'
        }
        form = ProductForm(data=form_data)
        if not form.is_valid():
            print(f"Product form errors: {form.errors}")
        self.assertTrue(form.is_valid())
    
    def test_invalid_product_form(self):
        """Provjera da je forma neispravna s pogrešnim podacima"""
        form_data = {
            'title': '',
            'price': 'not-a-number',
        }
        form = ProductForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('price', form.errors)

class InvoiceFormTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            clientName='Test Client',
            addressLine1='Test Address',
            province='GRAD ZAGREB',
            postalCode='10000',
            phoneNumber='+385123456789',
            emailAddress='test@example.com',
            clientUniqueId='0001',
            clientType='Fizička osoba',
            OIB='12345678901'
        )
        
        self.company = Company.objects.create(
            clientName='Test Company',
            addressLine1='Company Address',
            town='Zagreb',
            province='GRAD ZAGREB',
            postalCode='10000',
            phoneNumber='+385123456789',
            emailAddress='company@example.com',
            clientUniqueId='0002',
            clientType='Pravna osoba',
            OIB='98765432109',
            SustavPDVa=True,
            IBAN='HR1723600001101234565'
        )
    
    def test_valid_invoice_form(self):
        """Provjera da je forma ispravna s točnim podacima"""
        form_data = {
            'title': 'Test Invoice',
            'number': '1-1-25',
            'date': timezone.now().date(),
            'dueDate': timezone.now().date(),
            'client': self.client.id,
            'subject': self.company.id,
            'notes': 'Test Notes',
            'invoice_type': 'maloprodajni',
            'payment_method': 'bank_transfer'
        }
        form = InvoiceForm(data=form_data)
        if not form.is_valid():
            print(f"Invoice form errors: {form.errors}")
        self.assertTrue(form.is_valid())
    
    def test_invalid_invoice_form(self):
        """Provjera da je forma neispravna s pogrešnim podacima"""
        form_data = {
            'title': 'Test Invoice',
        }
        form = InvoiceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)
        self.assertIn('dueDate', form.errors)
