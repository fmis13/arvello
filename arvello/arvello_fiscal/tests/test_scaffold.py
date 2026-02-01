from django.test import TestCase
from arvello_fiscal.services.fiscal_service import FiscalService


class FiscalScaffoldTests(TestCase):
    def test_idempotency_key_stable(self):
        k1 = FiscalService.idempotency_key('C1', 'invoice', '123', 1)
        k2 = FiscalService.idempotency_key('C1', 'invoice', '123', 1)
        self.assertEqual(k1, k2)
