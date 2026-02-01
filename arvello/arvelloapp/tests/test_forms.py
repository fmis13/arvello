from django.test import TestCase
from django.utils import timezone
from arvelloapp.forms import ClientForm, ProductForm, InvoiceForm, ExpenseForm, OfferForm, SalaryForm
from arvelloapp.models import Client, Company, Employee
from decimal import Decimal

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
