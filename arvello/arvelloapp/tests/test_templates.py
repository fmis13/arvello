from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, timedelta
from arvelloapp.models import Invoice, Client, Company

class InvoiceTemplateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        # Ensure user has a subject (helpers.ensure_user_has_subject will create one on view load),
        # but create a explicit client to attach to invoices
        self.company = Company.objects.create(
            clientName='Test Subject',
            addressLine1='Test Address',
            town='TestTown',
            province='GRAD ZAGREB',
            postalCode='10000',
            phoneNumber='',
            emailAddress='',
            clientUniqueId='9999',
            clientType='Pravna osoba'
        )
        self.client_obj = Client.objects.create(
            clientName='Test Client',
            addressLine1='Client Address',
            province='GRAD ZAGREB',
            postalCode='10000',
            phoneNumber='',
            emailAddress='client@example.com',
            clientUniqueId='0001',
            clientType='Pravna osoba',
            VATID='HR1234567890123'
        )

    def test_empty_title_renders_empty_value(self):
        # Create invoice with no title
        inv = Invoice.objects.create(
            title=None,
            number='INV-0001',
            dueDate=date.today(),
            date=date.today(),
            client=self.client_obj,
            subject=self.company,
        )
        resp = self.client.get(reverse('invoices'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'class="empty-value"')
        self.assertContains(resp, '(prazno)')

    def test_overdue_row_has_overdue_class(self):
        # Create an overdue invoice (2 days late -> warning)
        past = date.today() - timedelta(days=2)
        inv = Invoice.objects.create(
            title='Overdue Invoice',
            number='INV-0002',
            dueDate=past,
            date=past,
            client=self.client_obj,
            subject=self.company,
            is_paid=False,
        )
        resp = self.client.get(reverse('invoices'))
        self.assertEqual(resp.status_code, 200)
        # The row should include the class for warning
        self.assertContains(resp, 'row-overdue-warning')

    def test_due_date_formatted(self):
        d = date(2025, 12, 31)
        inv = Invoice.objects.create(
            title='DateTest',
            number='INV-0003',
            dueDate=d,
            date=d,
            client=self.client_obj,
            subject=self.company,
        )
        resp = self.client.get(reverse('invoices'))
        self.assertContains(resp, '31.12.2025.')

    def test_notes_have_title_attribute(self):
        long_notes = 'x' * 100
        inv = Invoice.objects.create(
            title='NotesTest',
            number='INV-0004',
            dueDate=date.today(),
            date=date.today(),
            client=self.client_obj,
            subject=self.company,
            notes=long_notes,
        )
        resp = self.client.get(reverse('invoices'))
        self.assertContains(resp, 'title="')
        self.assertContains(resp, long_notes)
