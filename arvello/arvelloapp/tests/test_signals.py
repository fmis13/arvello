from django.test import TestCase
from django.db.models.signals import post_save
from ..models import Invoice, Client, Company
from arvello_fiscal.services.fiscal_service import FiscalService
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User


class InvoiceSignalsTestCase(TestCase):
    def setUp(self):
        # Create test data
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.company = Company.objects.create(
            clientName='Test Company',
            addressLine1='Test Address',
            town='Test City',
            province='GRAD ZAGREB',
            postalCode='10000',
            phoneNumber='0123456789',
            emailAddress='test@company.com',
            clientUniqueId='1234',
            clientType='Pravna osoba',
            OIB='12345678901',
            IBAN='HR12345678901234567890'
        )
        self.client = Client.objects.create(
            clientName='Test Client',
            addressLine1='Test Address',
            province='GRAD ZAGREB',
            postalCode='10000',
            emailAddress='test@client.com',
            clientUniqueId='5678',
            clientType='Pravna osoba',
            OIB='12345678902',
            VATID='HR12345678902'
        )
        self.invoice_data = {
            'title': 'Test Invoice',
            'number': '001',
            'dueDate': '2025-12-31',
            'client': self.client,
            'subject': self.company,
            'date': '2025-12-26',
            'is_paid': False,
            'sales_channel': 'retail',
        }

    @patch('arvello_fiscal.services.fiscal_service.FiscalService.fiscalize_invoice')
    def test_enqueue_on_create_fiscal_channel(self, mock_fiscalize):
        """Test enqueuing on invoice creation for fiscal channels."""
        invoice = Invoice.objects.create(**self.invoice_data)
        mock_fiscalize.assert_called_once_with(invoice)
        invoice.refresh_from_db()
        self.assertEqual(invoice.fiscal_status, 'enqueued')

    @patch('arvello_fiscal.services.fiscal_service.FiscalService.fiscalize_invoice')
    def test_enqueue_on_status_change_to_paid(self, mock_fiscalize):
        """Test enqueuing when is_paid changes to True."""
        invoice = Invoice.objects.create(**self.invoice_data)
        mock_fiscalize.reset_mock()
        
        invoice.is_paid = True
        invoice.save()
        
        mock_fiscalize.assert_called_once_with(invoice)
        invoice.refresh_from_db()
        self.assertEqual(invoice.fiscal_status, 'enqueued')

    @patch('arvello_fiscal.services.fiscal_service.FiscalService.fiscalize_invoice')
    def test_no_enqueue_non_fiscal_channel(self, mock_fiscalize):
        """Test no enqueuing for non-fiscal channels."""
        self.invoice_data['sales_channel'] = 'online'  # Non-fiscal channel
        invoice = Invoice.objects.create(**self.invoice_data)
        mock_fiscalize.assert_not_called()
        invoice.refresh_from_db()
        self.assertEqual(invoice.fiscal_status, 'pending')

    @patch('arvello_fiscal.services.fiscal_service.FiscalService.fiscalize_invoice')
    def test_no_enqueue_on_other_changes(self, mock_fiscalize):
        """Test no enqueuing when other fields change but is_paid stays False."""
        invoice = Invoice.objects.create(**self.invoice_data)
        mock_fiscalize.reset_mock()
        
        invoice.title = 'Updated Title'
        invoice.save()
        
        mock_fiscalize.assert_not_called()
        invoice.refresh_from_db()
        self.assertEqual(invoice.fiscal_status, 'enqueued')  # Should remain enqueued from creation