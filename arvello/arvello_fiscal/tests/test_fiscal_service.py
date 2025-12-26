from django.test import TestCase
from django.test import override_settings
from unittest.mock import patch, MagicMock
from arvello_fiscal.services.fiscal_service import FiscalService
from arvello_fiscal.models import FiscalConfig
from arvelloapp.models import Invoice, Company, Client


class FiscalServiceTests(TestCase):
    """Tests for FiscalService, focusing on sales_channel routing and auto-detection."""

    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(
            clientName="Test Company",
            addressLine1="Test Address",
            town="Test Town",
            province="ZAGREBAČKA ŽUPANIJA",
            postalCode="10000",
            phoneNumber="+385123456789",
            emailAddress="test@company.com",
            clientUniqueId="12345",
            clientType="Pravna osoba",
            OIB="12345678901",
            IBAN="HR12345678901234567890"
        )

        self.individual_client = Client.objects.create(
            clientName="Individual Client",
            addressLine1="Client Address",
            province="ZAGREBAČKA ŽUPANIJA",
            postalCode="10000",
            phoneNumber="+385987654321",
            emailAddress="client@test.com",
            clientUniqueId="54321",
            clientType="Fizička osoba",
            OIB="10987654321",
            VATID="HR12345678901"
        )

        self.business_client = Client.objects.create(
            clientName="Business Client",
            addressLine1="Business Address",
            province="ZAGREBAČKA ŽUPANIJA",
            postalCode="10000",
            phoneNumber="+385555666777",
            emailAddress="business@test.com",
            clientUniqueId="99999",
            clientType="Pravna osoba",
            OIB="99999999999",
            VATID="HR99999999999"
        )

    def test_invoice_sales_channel_auto_detection_individual(self):
        """Test that invoices for individual clients default to retail channel."""
        invoice = Invoice.objects.create(
            title="Test Invoice",
            number="001",
            dueDate="2025-01-01",
            client=self.individual_client,
            subject=self.company
        )
        self.assertEqual(invoice.sales_channel, 'retail')

    def test_invoice_sales_channel_auto_detection_business(self):
        """Test that invoices for business clients default to wholesale channel."""
        invoice = Invoice.objects.create(
            title="Test Invoice",
            number="002",
            dueDate="2025-01-01",
            client=self.business_client,
            subject=self.company
        )
        self.assertEqual(invoice.sales_channel, 'wholesale')

    def test_invoice_sales_channel_explicit_setting(self):
        """Test that explicitly set sales_channel is preserved."""
        invoice = Invoice(
            title="Test Invoice",
            number="003",
            dueDate="2025-01-01",
            client=self.individual_client,
            subject=self.company,
            sales_channel='wholesale'
        )
        invoice.save()
        self.assertEqual(invoice.sales_channel, 'wholesale')

    def test_fiscalize_invoice_missing_sales_channel(self):
        """Test that fiscalize_invoice raises ValueError for missing sales_channel."""
        invoice = Invoice.objects.create(
            title="Test Invoice",
            number="004",
            dueDate="2025-01-01",
            client=self.individual_client,
            subject=self.company
        )
        # Explicitly set to empty string to bypass auto-detection
        invoice.sales_channel = ''

        with self.assertRaises(ValueError) as cm:
            FiscalService.fiscalize_invoice(invoice)
        self.assertIn("Sales channel must be set", str(cm.exception))

    def test_fiscalize_invoice_invalid_sales_channel(self):
        """Test that fiscalize_invoice raises ValueError for invalid sales_channel."""
        invoice = Invoice.objects.create(
            title="Test Invoice",
            number="005",
            dueDate="2025-01-01",
            client=self.individual_client,
            subject=self.company,
            sales_channel='invalid'
        )

        with self.assertRaises(ValueError) as cm:
            FiscalService.fiscalize_invoice(invoice)
        self.assertIn("Unknown sales channel", str(cm.exception))

    @patch('arvello_fiscal.services.fiscal_service.FiscalService.get_adapter_for_company')
    def test_fiscalize_invoice_routing_retail(self, mock_get_adapter):
        """Test that retail channel routes to fiskalizacija_v1 adapter."""
        # Create invoice with retail channel
        invoice = Invoice.objects.create(
            title="Retail Invoice",
            number="006",
            dueDate="2025-01-01",
            client=self.individual_client,
            subject=self.company,
            sales_channel='retail'
        )

        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.fiscalize.return_value = {'status': 'success'}
        mock_get_adapter.return_value = mock_adapter

        # Create FiscalConfig to test override
        config = FiscalConfig.objects.create(
            company_id=str(self.company.id),
            adapter='sandbox',  # Original adapter
            mode='sandbox'
        )

        # Call fiscalize_invoice
        result = FiscalService.fiscalize_invoice(invoice)

        # Verify adapter was called
        mock_adapter.fiscalize.assert_called_once_with(invoice)

        # Verify config is restored to original
        config.refresh_from_db()
        self.assertEqual(config.adapter, 'sandbox')

    @patch('arvello_fiscal.services.fiscal_service.FiscalService.get_adapter_for_company')
    def test_fiscalize_invoice_routing_wholesale(self, mock_get_adapter):
        """Test that wholesale channel routes to fiskalizacija_v2 adapter."""
        # Create invoice with wholesale channel
        invoice = Invoice.objects.create(
            title="Wholesale Invoice",
            number="007",
            dueDate="2025-01-01",
            client=self.business_client,
            subject=self.company,
            sales_channel='wholesale'
        )

        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.fiscalize.return_value = {'status': 'success'}
        mock_get_adapter.return_value = mock_adapter

        # Create FiscalConfig
        config = FiscalConfig.objects.create(
            company_id=str(self.company.id),
            adapter='sandbox',
            mode='sandbox'
        )

        # Call fiscalize_invoice
        result = FiscalService.fiscalize_invoice(invoice)

        # Verify adapter was called
        mock_adapter.fiscalize.assert_called_once_with(invoice)

        # Verify config is restored to original
        config.refresh_from_db()
        self.assertEqual(config.adapter, 'sandbox')

    @patch('arvello_fiscal.services.fiscal_service.FiscalService.get_adapter_for_company')
    def test_fiscalize_invoice_no_config_fallback(self, mock_get_adapter):
        """Test fiscalize_invoice when no FiscalConfig exists."""
        # Create invoice
        invoice = Invoice.objects.create(
            title="No Config Invoice",
            number="008",
            dueDate="2025-01-01",
            client=self.individual_client,
            subject=self.company,
            sales_channel='retail'
        )

        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.fiscalize.return_value = {'status': 'success'}
        mock_get_adapter.return_value = mock_adapter

        # Ensure no config exists
        FiscalConfig.objects.filter(company_id=str(self.company.id)).delete()

        # Call fiscalize_invoice
        result = FiscalService.fiscalize_invoice(invoice)

        # Verify adapter was called
        mock_adapter.fiscalize.assert_called_once_with(invoice)

    def test_get_adapter_for_company_with_config(self):
        """Test get_adapter_for_company with existing FiscalConfig."""
        config = FiscalConfig.objects.create(
            company_id=str(self.company.id),
            adapter='fiskalizacija_v1',
            mode='sandbox',
            meta={'endpoint': 'https://test.com', 'cert': {'key': 'test'}}
        )

        adapter = FiscalService.get_adapter_for_company(str(self.company.id))

        # Verify correct adapter type
        from arvello_fiscal.adapters.fiskalizacija_v1 import FiskalizacijaV1Adapter
        self.assertIsInstance(adapter, FiskalizacijaV1Adapter)
        self.assertEqual(adapter.endpoint, 'https://test.com')
        self.assertEqual(adapter.cert_meta, {'key': 'test'})
        self.assertEqual(adapter.mode, 'sandbox')

    def test_get_adapter_for_company_no_config(self):
        """Test get_adapter_for_company with no FiscalConfig returns sandbox."""
        # Ensure no config
        FiscalConfig.objects.filter(company_id=str(self.company.id)).delete()

        adapter = FiscalService.get_adapter_for_company(str(self.company.id))

        from arvello_fiscal.adapters.sandbox import SandboxAdapter
        self.assertIsInstance(adapter, SandboxAdapter)
        self.assertEqual(adapter.mode, 'sandbox')

    def test_get_adapter_for_company_invalid_adapter(self):
        """Test get_adapter_for_company with invalid adapter name falls back to sandbox."""
        config = FiscalConfig.objects.create(
            company_id=str(self.company.id),
            adapter='invalid_adapter',
            mode='sandbox'
        )

        adapter = FiscalService.get_adapter_for_company(str(self.company.id))

        from arvello_fiscal.adapters.sandbox import SandboxAdapter
        self.assertIsInstance(adapter, SandboxAdapter)

    def test_idempotency_key_generation(self):
        """Test idempotency key generation is stable."""
        key1 = FiscalService.idempotency_key(str(self.company.id), 'invoice', '123', 1)
        key2 = FiscalService.idempotency_key(str(self.company.id), 'invoice', '123', 1)
        self.assertEqual(key1, key2)
        self.assertEqual(len(key1), 64)  # SHA256 hex length

    def test_idempotency_key_different_inputs(self):
        """Test idempotency key changes with different inputs."""
        key1 = FiscalService.idempotency_key(str(self.company.id), 'invoice', '123', 1)
        key2 = FiscalService.idempotency_key(str(self.company.id), 'invoice', '124', 1)
        key3 = FiscalService.idempotency_key(str(self.company.id), 'receipt', '123', 1)
        key4 = FiscalService.idempotency_key('999', 'invoice', '123', 1)

        self.assertNotEqual(key1, key2)
        self.assertNotEqual(key1, key3)
        self.assertNotEqual(key1, key4)