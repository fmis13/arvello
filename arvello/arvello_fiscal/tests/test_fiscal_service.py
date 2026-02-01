from django.test import TestCase
from django.test import override_settings
from unittest.mock import patch, MagicMock
from arvello_fiscal.services.fiscal_service import FiscalService
from arvello_fiscal.models import FiscalConfig
from arvelloapp.models import Invoice, Company, Client, Product, InvoiceProduct
from datetime import date


class FiscalServiceTests(TestCase):
    """Tests for FiscalService, focusing on F1/F2 fiscalization routing and auto-detection."""

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
            clientUniqueId="1234",
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
            clientUniqueId="5432",
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
            clientUniqueId="9999",
            clientType="Pravna osoba",
            OIB="99999999999",
            VATID="HR99999999999"
        )

        self.product = Product.objects.create(
            title="Test Product",
            price=100.0,
            taxPercent=25,
            barid="TEST001"
        )

    def _create_invoice_with_product(self, client, sales_channel=None, invoice_type=None, **extra_fields):
        """Helper to create a complete invoice with product item."""
        invoice = Invoice.objects.create(
            title="Test Invoice",
            number="001/1/1",
            dueDate=date(2025, 1, 31),
            date=date(2025, 1, 15),
            client=client,
            subject=self.company,
            sales_channel=sales_channel,
            invoice_type=invoice_type,
            **extra_fields
        )
        InvoiceProduct.objects.create(
            invoice=invoice,
            product=self.product,
            quantity=1
        )
        return invoice

    def test_invoice_sales_channel_auto_detection_individual(self):
        """Test that invoices for individual clients default to retail channel (F1)."""
        invoice = self._create_invoice_with_product(self.individual_client)
        self.assertEqual(invoice.sales_channel, 'retail')
        self.assertEqual(invoice.invoice_type, 'maloprodajni')
        self.assertEqual(invoice.get_fiscalization_type(), 'F1')

    def test_invoice_sales_channel_auto_detection_business(self):
        """Test that invoices for business clients default to wholesale channel (F2)."""
        invoice = self._create_invoice_with_product(self.business_client)
        self.assertEqual(invoice.sales_channel, 'wholesale')
        self.assertEqual(invoice.invoice_type, 'veleprodajni')
        self.assertEqual(invoice.get_fiscalization_type(), 'F2')

    def test_invoice_sales_channel_explicit_setting(self):
        """Test that explicitly set sales_channel is preserved."""
        invoice = self._create_invoice_with_product(
            self.individual_client,
            sales_channel='wholesale',
            invoice_type='veleprodajni'
        )
        self.assertEqual(invoice.sales_channel, 'wholesale')
        self.assertEqual(invoice.invoice_type, 'veleprodajni')
        self.assertEqual(invoice.get_fiscalization_type(), 'F2')

    def test_fiscalize_invoice_not_ready_no_date(self):
        """Test that fiscalize_invoice raises ValueError for invoice without date."""
        invoice = Invoice.objects.create(
            title="Test Invoice",
            number="002/1/1",
            dueDate=date(2025, 1, 31),
            client=self.individual_client,
            subject=self.company
        )

        with self.assertRaises(ValueError) as cm:
            FiscalService.fiscalize_invoice(invoice)
        self.assertIn("Račun nema datum", str(cm.exception))

    def test_fiscalize_invoice_not_ready_no_items(self):
        """Test that fiscalize_invoice raises ValueError for invoice without items."""
        invoice = Invoice.objects.create(
            title="Test Invoice",
            number="003/1/1",
            dueDate=date(2025, 1, 31),
            date=date(2025, 1, 15),
            client=self.individual_client,
            subject=self.company
        )

        with self.assertRaises(ValueError) as cm:
            FiscalService.fiscalize_invoice(invoice)
        self.assertIn("Račun nema stavki", str(cm.exception))

    def test_get_fiscal_adapter_type_retail(self):
        """Test that retail invoice routes to fiskalizacija_v1 adapter."""
        invoice = self._create_invoice_with_product(self.individual_client)
        adapter_type = invoice.get_fiscal_adapter_type()
        self.assertEqual(adapter_type, 'fiskalizacija_v1')

    def test_get_fiscal_adapter_type_wholesale(self):
        """Test that wholesale invoice routes to fiskalizacija_v2 adapter."""
        invoice = self._create_invoice_with_product(self.business_client)
        adapter_type = invoice.get_fiscal_adapter_type()
        self.assertEqual(adapter_type, 'fiskalizacija_v2')

    def test_requires_fiscalization_property(self):
        """Test requires_fiscalization property."""
        invoice = self._create_invoice_with_product(self.individual_client)
        self.assertTrue(invoice.requires_fiscalization)
        
        # Already processed should not require fiscalization
        invoice.fiscal_status = 'processed'
        invoice.save()
        self.assertFalse(invoice.requires_fiscalization)

    def test_get_adapter_for_invoice_f1(self):
        """Test get_adapter_for_invoice returns V1 adapter for F1."""
        invoice = self._create_invoice_with_product(self.individual_client)
        adapter = FiscalService.get_adapter_for_invoice(invoice)
        
        # Without config, should return V1 adapter with sandbox mode
        from arvello_fiscal.adapters.fiskalizacija_v1 import FiskalizacijaV1Adapter
        self.assertIsInstance(adapter, FiskalizacijaV1Adapter)
        self.assertEqual(adapter.mode, 'sandbox')

    def test_get_adapter_for_invoice_f2(self):
        """Test get_adapter_for_invoice returns V2 adapter for F2."""
        invoice = self._create_invoice_with_product(self.business_client)
        adapter = FiscalService.get_adapter_for_invoice(invoice)
        
        # Without config, should return V2 adapter with sandbox mode
        from arvello_fiscal.adapters.fiskalizacija_v2 import FiskalizacijaV2Adapter
        self.assertIsInstance(adapter, FiskalizacijaV2Adapter)
        self.assertEqual(adapter.mode, 'sandbox')

    def test_get_adapter_for_invoice_with_config_f1(self):
        """Test get_adapter_for_invoice with config returns V1 adapter for F1."""
        FiscalConfig.objects.create(
            company_id=str(self.company.id),
            adapter='fiskalizacija_v1',
            mode='sandbox'
        )
        
        invoice = self._create_invoice_with_product(self.individual_client)
        adapter = FiscalService.get_adapter_for_invoice(invoice)
        
        from arvello_fiscal.adapters.fiskalizacija_v1 import FiskalizacijaV1Adapter
        self.assertIsInstance(adapter, FiskalizacijaV1Adapter)

    def test_get_adapter_for_invoice_with_config_f2(self):
        """Test get_adapter_for_invoice with config returns V2 adapter for F2."""
        FiscalConfig.objects.create(
            company_id=str(self.company.id),
            adapter='fiskalizacija_v2',
            mode='sandbox'
        )
        
        invoice = self._create_invoice_with_product(self.business_client)
        adapter = FiscalService.get_adapter_for_invoice(invoice)
        
        from arvello_fiscal.adapters.fiskalizacija_v2 import FiskalizacijaV2Adapter
        self.assertIsInstance(adapter, FiskalizacijaV2Adapter)

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

    def test_fiscalization_type_display(self):
        """Test get_fiscalization_type_display returns correct labels."""
        invoice_retail = self._create_invoice_with_product(self.individual_client)
        self.assertEqual(invoice_retail.get_fiscalization_type_display(), 'F1 - Maloprodaja')
        
        invoice_wholesale = self._create_invoice_with_product(self.business_client)
        self.assertEqual(invoice_wholesale.get_fiscalization_type_display(), 'F2 - Veleprodaja')

    def test_fiscalization_type_badge(self):
        """Test get_fiscalization_type_badge returns correct badges."""
        invoice_retail = self._create_invoice_with_product(self.individual_client)
        badge_retail = invoice_retail.get_fiscalization_type_badge()
        self.assertIn('bg-primary', badge_retail)
        self.assertIn('F1', badge_retail)
        
        invoice_wholesale = self._create_invoice_with_product(self.business_client)
        badge_wholesale = invoice_wholesale.get_fiscalization_type_badge()
        self.assertIn('bg-success', badge_wholesale)
        self.assertIn('F2', badge_wholesale)