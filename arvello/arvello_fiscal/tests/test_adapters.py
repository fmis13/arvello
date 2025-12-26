from django.test import TestCase
from arvello_fiscal.adapters.sandbox import SandboxAdapter
from arvello_fiscal.adapters.fiskalizacija_v1 import FiskalizacijaV1Adapter
from arvello_fiscal.adapters.fiskalizacija_v2 import FiskalizacijaV2Adapter
from unittest.mock import patch, MagicMock
import xmlsec
from lxml import etree
from decimal import Decimal


class AdapterTests(TestCase):
    def test_sandbox_adapter(self):
        a = SandboxAdapter()
        payload = a.prepare_payload({'type': 'invoice', 'id': '123'})
        self.assertIn('document_id', payload)
        resp = a.send(payload)
        self.assertEqual(resp.get('status'), 'ok')

    def test_v1_prepare_payload(self):
        a = FiskalizacijaV1Adapter(mode='sandbox')
        xml = a.prepare_payload({'type': 'salary', 'id': 's1'})
        self.assertTrue(b'ObrazacJOPPD' in xml)

    def test_v1_sign_payload_sandbox(self):
        a = FiskalizacijaV1Adapter(mode='sandbox')
        # Use proper F1 fiscal data structure
        fiscal_data = {
            'issuer_data': {
                'oib': '12345678901',
                'name': 'Test Company'
            },
            'invoice_data': {
                'number': '1/POS1/DEV1',
                'date': '26.12.2025',
                'fiscal_location': 'POS1',
                'fiscal_device_id': 'DEV1',
                'payment_method': 'cash',
                'fiscal_operator_oib': '12345678901'
            },
            'vat_summary': {
                Decimal('25.00'): {
                    'base_amount': Decimal('100.00'),
                    'vat_amount': Decimal('25.00')
                }
            },
            'totals': {
                'total_amount': Decimal('125.00')
            }
        }
        payload = a._create_racun_zahtjev_xml(fiscal_data)
        signed = a.sign_payload(payload)
        # Check that SOAP envelope is created (sandbox mode doesn't sign)
        root = etree.fromstring(signed)
        # Root should be the SOAP envelope
        self.assertEqual(root.tag, '{http://schemas.xmlsoap.org/soap/envelope/}Envelope')
        # Check that RacunZahtjev is inside the envelope
        body = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Body')
        self.assertIsNotNone(body)
        racun_zahtjev = body.find('.//{http://www.apis-it.hr/fin/2012/types/f73}RacunZahtjev')
        self.assertIsNotNone(racun_zahtjev)

    @patch('arvello_fiscal.adapters.fiskalizacija_v1.requests.post')
    def test_v1_send_production(self, mock_post):
        mock_response = MagicMock()
        mock_response.text = '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><tns:RacunOdgovor xmlns:tns="http://www.apis-it.hr/fin/2012/types/f73"><tns:Jir>12345678901234567890123456789012345678901234</tns:Jir></tns:RacunOdgovor></soap:Body></soap:Envelope>'
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        a = FiskalizacijaV1Adapter(endpoint='http://test.com', mode='production')
        signed = b'<test></test>'
        result = a.send(signed)
        expected = {
            'status': 'OK',
            'jir': '12345678901234567890123456789012345678901234',
            'message': 'Fiscalization successful'
        }
        self.assertEqual(result, expected)
        mock_post.assert_called_once()

    def test_v2_prepare_and_sign(self):
        a = FiskalizacijaV2Adapter(mode='sandbox', secret=None)
        p = a.prepare_payload({'type': 'invoice', 'id': 'inv-1'})
        signed = a.sign_payload(p)
        self.assertIn('payload', signed)

    def test_v2_sign_with_secret(self):
        a = FiskalizacijaV2Adapter(mode='sandbox', secret='test_secret')
        p = a.prepare_payload({'type': 'invoice', 'id': 'inv-1'})
        signed = a.sign_payload(p)
        self.assertIn('token', signed)
        self.assertIsNotNone(signed['token'])

    @patch('arvello_fiscal.adapters.fiskalizacija_v2.requests.post')
    def test_v2_send_production(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {'status': 'OK', 'fiscal_id': '123'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        a = FiskalizacijaV2Adapter(endpoint='http://test.com', secret='secret', mode='production')
        signed = {'token': 'jwt_token', 'payload': {'type': 'invoice'}}
        result = a.send(signed)
        self.assertEqual(result, {'status': 'OK', 'fiscal_id': '123'})
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['headers']['Authorization'], 'Bearer jwt_token')
