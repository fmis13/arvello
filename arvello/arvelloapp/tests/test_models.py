from django.test import TestCase
from django.utils import timezone
from arvelloapp.models import Client, Product, Invoice, Company, InvoiceProduct, Offer, OfferProduct, Expense, LocalIncomeTax

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
        """Provjera da možemo stvoriti klijenta"""
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
        """Provjera da možemo stvoriti proizvod"""
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
        """Provjera da možemo stvoriti račun"""
        invoice = Invoice.objects.create(**self.invoice_data)
        self.assertEqual(invoice.title, 'Test Invoice')
        self.assertEqual(invoice.client, self.client)
        self.assertEqual(Invoice.objects.count(), 1)
        
    def test_invoice_subject(self):
        """Provjera da možemo promijeniti subjekt računa"""
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
        """Provjera da možemo stvoriti firmu"""
        company = Company.objects.create(**self.company_data)
        self.assertEqual(company.clientName, 'Test Company')
        self.assertEqual(company.town, 'Zagreb')
        self.assertEqual(company.province, 'GRAD ZAGREB')
        self.assertEqual(company.clientType, 'Pravna osoba')
        self.assertTrue(company.SustavPDVa)
        self.assertEqual(company.IBAN, 'HR1723600001101234565')
        self.assertEqual(Company.objects.count(), 1)
        
    def test_company_auto_fields(self):
        """Provjera automatski generiranih polja za firmu"""
        company = Company.objects.create(**self.company_data)
        
        self.assertIsNotNone(company.uniqueId)
        self.assertIsNotNone(company.slug)
        self.assertIsNotNone(company.date_created)
        self.assertIsNotNone(company.last_updated)

        expected_slug_prefix = f"{company.clientName}-{company.uniqueId}".lower().replace(" ", "-")
        self.assertTrue(company.slug.startswith(expected_slug_prefix))
        
    def test_company_str_method(self):
        """Provjera __str__ metode za firmu"""
        company = Company.objects.create(**self.company_data)
        self.assertEqual(str(company), company.clientName)

class OfferModelTest(TestCase):
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
        self.offer_data = {
            'title': 'Test Offer',
            'number': 'O-1',
            'dueDate': timezone.now().date(),
            'client': self.client,
            'subject': self.company,
            'notes': 'Test Notes'
        }

    def test_create_offer(self):
        """Provjera da možemo stvoriti ponudu"""
        offer = Offer.objects.create(**self.offer_data)
        self.assertEqual(offer.title, 'Test Offer')
        self.assertEqual(offer.client, self.client)
        self.assertEqual(Offer.objects.count(), 1)

class OfferProductModelTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            title='Test Product',
            description='Test Description',
            price=100.00,
            taxPercent=25.0,
            currency='EUR',
            barid='1'
        )
        self.offer = Offer.objects.create(
            title='Test Offer',
            number='O-1',
            dueDate=timezone.now().date(),
            client=Client.objects.create(
                clientName='Test Client',
                addressLine1='Test Address',
                province='GRAD ZAGREB',
                postalCode='10000',
                phoneNumber='+385123456789',
                emailAddress='test@example.com',
                clientUniqueId='0001',
                clientType='Fizička osoba',
                OIB='12345678901'
            ),
            subject=Company.objects.create(
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
        )
        self.offer_product_data = {
            'product': self.product,
            'offer': self.offer,
            'quantity': 2,
            'discount': 10.0,
            'rabat': 5.0
        }

    def test_create_offer_product(self):
        """Provjera da možemo stvoriti proizvod u ponudi"""
        offer_product = OfferProduct.objects.create(**self.offer_product_data)
        self.assertEqual(offer_product.quantity, 2)
        self.assertEqual(offer_product.offer, self.offer)
        self.assertEqual(OfferProduct.objects.count(), 1)

class ExpenseModelTest(TestCase):
    def setUp(self):
        self.subject = Company.objects.create(
            clientName='Test Subject',
            addressLine1='Subject Address',
            town='Zagreb',
            province='GRAD ZAGREB',
            postalCode='10000',
            phoneNumber='+385123456789',
            emailAddress='subject@example.com',
            clientUniqueId='0003',
            clientType='Pravna osoba',
            OIB='12345678901',
            SustavPDVa=True,
            IBAN='HR1723600001101234565'
        )
        self.expense_data = {
            'title': 'Test Expense',
            'amount': 100.00,
            'currency': 'EUR',
            'date': timezone.now().date(),
            'description': 'Test Description',
            'subject': self.subject
        }

    def test_create_expense(self):
        """Provjera da možemo stvoriti trošak"""
        expense = Expense.objects.create(**self.expense_data)
        self.assertEqual(expense.title, 'Test Expense')
        self.assertEqual(expense.amount, 100.00)
        self.assertEqual(Expense.objects.count(), 1)

class LocalIncomeTaxModelTest(TestCase):
    def setUp(self):
        self.local_income_tax_data = {
            'city_name': 'Test City',
            'city_code': 'TC',
            'tax_rate': 10.0,
            'valid_from': timezone.now().date(),
            'valid_until': timezone.now().date()
        }

    def test_create_local_income_tax(self):
        """Provjera da možemo stvoriti lokalni porez na dohodak"""
        local_income_tax = LocalIncomeTax.objects.create(**self.local_income_tax_data)
        self.assertEqual(local_income_tax.city_name, 'Test City')
        self.assertEqual(local_income_tax.tax_rate, 10.0)
        self.assertEqual(LocalIncomeTax.objects.count(), 1)
