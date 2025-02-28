from django.test import TestCase
from django.utils import timezone
from arvelloapp.models import Client, Product, Invoice, Company, InvoiceProduct

class ClientModelTest(TestCase):
    def setUp(self):
        self.client_data = {
            'clientName': 'Test Client',
            'addressLine1': 'Test Address',
            'province': 'GRAD ZAGREB',
            'postalCode': '10000',
            'phoneNumber': '+385123456789',
            'emailAddress': 'test@example.com',
            'clientUniqueId': '0001',
            'clientType': 'Fizička osoba',
            'OIB': '12345678901'
        }
        
    def test_create_client(self):
        """Test that we can create a client"""
        client = Client.objects.create(**self.client_data)
        self.assertEqual(client.clientName, 'Test Client')
        self.assertEqual(client.emailAddress, 'test@example.com')
        self.assertEqual(Client.objects.count(), 1)

class ProductModelTest(TestCase):
    def setUp(self):
        self.product_data = {
            'title': 'Test Product',
            'description': 'Test Description',
            'price': 100.00,
            'taxPercent': 25.0,
            'currency': 'EUR',
            'barid': '1'
        }
        
    def test_create_product(self):
        """Test that we can create a product"""
        product = Product.objects.create(**self.product_data)
        self.assertEqual(product.title, 'Test Product')
        self.assertEqual(product.price, 100.00)
        self.assertEqual(Product.objects.count(), 1)

class InvoiceModelTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            clientName='Test Client',
            addressLine1= 'Test Address',
            province= 'GRAD ZAGREB',
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
        
        self.invoice_data = {
            'title': 'Test Invoice',
            'number': '1-1-25',
            'date': timezone.now().date(),
            'dueDate': timezone.now().date(),
            'client': self.client,
            'subject': self.company,
            'notes': 'Test Notes'
        }
        
    def test_create_invoice(self):
        """Test that we can create an invoice"""
        invoice = Invoice.objects.create(**self.invoice_data)
        self.assertEqual(invoice.title, 'Test Invoice')
        self.assertEqual(invoice.client, self.client)
        self.assertEqual(Invoice.objects.count(), 1)
        
    def test_invoice_subject(self):
        """Test that invoice subject (Company) is correctly set and retrieved"""
        invoice = Invoice.objects.create(**self.invoice_data)
        self.assertEqual(invoice.subject, self.company)
        
        new_company = Company.objects.create(
            clientName='New Company',
            addressLine1='New Address',
            town='Split',
            province='SPLITSKO-DALMATINSKA ŽUPANIJA',
            postalCode='21000',
            phoneNumber='+385987654321',
            emailAddress='new@example.com',
            clientUniqueId='0003',
            clientType='Pravna osoba',
            OIB='11223344556',
            SustavPDVa=False,
            IBAN='HR1723600001101234566'
        )
        
        invoice.subject = new_company
        invoice.save()
        
        refreshed_invoice = Invoice.objects.get(id=invoice.id)
        self.assertEqual(refreshed_invoice.subject, new_company)
        self.assertEqual(refreshed_invoice.subject.clientName, 'New Company')

class CompanyModelTest(TestCase):
    def setUp(self):
        self.company_data = {
            'clientName': 'Test Company',
            'addressLine1': 'Company Address',
            'town': 'Zagreb',
            'province': 'GRAD ZAGREB',
            'postalCode': '10000',
            'phoneNumber': '+385123456789',
            'emailAddress': 'company@example.com',
            'clientUniqueId': '0002',
            'clientType': 'Pravna osoba',
            'OIB': '98765432109',
            'SustavPDVa': True,
            'IBAN': 'HR1723600001101234565'
        }
        
    def test_create_company(self):
        """Test that we can create a company"""
        company = Company.objects.create(**self.company_data)
        self.assertEqual(company.clientName, 'Test Company')
        self.assertEqual(company.town, 'Zagreb')
        self.assertEqual(company.province, 'GRAD ZAGREB')
        self.assertEqual(company.clientType, 'Pravna osoba')
        self.assertTrue(company.SustavPDVa)
        self.assertEqual(company.IBAN, 'HR1723600001101234565')
        self.assertEqual(Company.objects.count(), 1)
        
    def test_company_auto_fields(self):
        """Test that auto-generated fields are created properly"""
        company = Company.objects.create(**self.company_data)
        
        self.assertIsNotNone(company.uniqueId)
        self.assertIsNotNone(company.slug)
        self.assertIsNotNone(company.date_created)
        self.assertIsNotNone(company.last_updated)

        expected_slug_prefix = f"{company.clientName}-{company.uniqueId}".lower().replace(" ", "-")
        self.assertTrue(company.slug.startswith(expected_slug_prefix))
        
    def test_company_str_method(self):
        """Test the __str__ method of Company model"""
        company = Company.objects.create(**self.company_data)
        self.assertEqual(str(company), company.clientName)
