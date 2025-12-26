import logging
from .base import ProviderAdapter
import json
import jwt
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class FiskalizacijaV2Adapter(ProviderAdapter):
    """Adapter for Fiskalizacija v2 (JSON/REST + token/JWT auth).

    Supports HTTP transport with requests and JWT signing.
    """

    def __init__(self, endpoint: str = None, secret: str = None, mode: str = 'production'):
        super().__init__(mode)
        self.endpoint = endpoint
        self.secret = secret

    def prepare_payload(self, document):
        """Priprema JSON payload za fiskalizaciju v2."""
        if hasattr(document, 'get_fiscal_data'):
            fiscal_data = document.get_fiscal_data()
            return self._create_fiscal_json(fiscal_data)
        else:
            # Legacy fallback
            return self._create_basic_json(document)
    
    def _create_fiscal_json(self, fiscal_data):
        """Stvara JSON strukturu prema fiskalnim specifikacijama v2."""
        payload = {
            'version': '2.0',
            'documentType': 'invoice',
            'documentId': fiscal_data['invoice_data']['id'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'issuer': {
                'oib': fiscal_data['issuer_data']['oib'],
                'name': fiscal_data['issuer_data']['name'],
                'address': fiscal_data['issuer_data']['address'],
                'city': fiscal_data['issuer_data']['city'],
                'postalCode': fiscal_data['issuer_data']['postal_code'],
                'vatId': fiscal_data['issuer_data'].get('vat_id'),
            },
            'invoice': {
                'number': fiscal_data['invoice_data']['number'],
                'date': fiscal_data['invoice_data']['date'],
                'dueDate': fiscal_data['invoice_data']['due_date'],
                'salesChannel': fiscal_data['invoice_data']['sales_channel'],
                'paymentMethod': fiscal_data['invoice_data']['payment_method'],
                'operatorOib': fiscal_data['invoice_data']['fiscal_operator_oib'],
                'location': fiscal_data['invoice_data']['fiscal_location'],
                'deviceId': fiscal_data['invoice_data']['fiscal_device_id'],
                'notes': fiscal_data['invoice_data']['notes'],
                'isPaid': fiscal_data['invoice_data']['is_paid'],
                'paymentDate': fiscal_data['invoice_data']['payment_date'],
            },
            'items': [],
            'vatSummary': [],
            'totals': fiscal_data['totals']
        }
        
        # Dodaj stavke
        for vat_rate, vat_data in fiscal_data['vat_summary'].items():
            for item in vat_data['items']:
                payload['items'].append({
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'unitPrice': item['unit_price'],
                    'discount': item['discount'],
                    'rebate': item['rebate'],
                    'vatRate': item['vat_rate'],
                    'baseAmount': item['base_amount'],
                    'vatAmount': item['vat_amount'],
                    'totalAmount': item['total_amount']
                })
        
        # Dodaj PDV sažetak
        for vat_rate, vat_data in fiscal_data['vat_summary'].items():
            payload['vatSummary'].append({
                'rate': vat_rate,
                'baseAmount': float(vat_data['base_amount']),
                'vatAmount': float(vat_data['vat_amount'])
            })
        
        # Dodaj podatke o kupcu za veleprodaju
        if fiscal_data['buyer_data'] and fiscal_data['invoice_data']['sales_channel'] == 'wholesale':
            payload['buyer'] = {
                'oib': fiscal_data['buyer_data']['oib'],
                'name': fiscal_data['buyer_data']['name'],
                'address': fiscal_data['buyer_data']['address'],
                'city': fiscal_data['buyer_data']['city'],
                'postalCode': fiscal_data['buyer_data']['postal_code'],
                'vatId': fiscal_data['buyer_data'].get('vat_id'),
                'clientType': fiscal_data['buyer_data']['client_type']
            }
        
        return payload
    
    def _create_basic_json(self, document):
        """Legacy JSON creation for backward compatibility."""
        if isinstance(document, dict):
            payload = document
        else:
            payload = {
                'type': getattr(document, 'document_type', 'unknown'),
                'id': getattr(document, 'document_id', None),
                'created_at': datetime.utcnow().isoformat()
            }
        return payload

    def sign_payload(self, payload):
        # If secret provided, produce a JWT token that can be used as Authorization
        if self.secret:
            token = jwt.encode({'payload': payload, 'iat': int(datetime.utcnow().timestamp())}, self.secret, algorithm='HS256')
            return {'token': token, 'payload': payload}
        return {'token': None, 'payload': payload}

    def send(self, signed_payload):
        if self.mode == 'sandbox' or not self.endpoint:
            return {'status': 'OK', 'fiscal_id': 'V2-SANDBOX'}
        
        headers = {'Content-Type': 'application/json'}
        data = signed_payload['payload']
        if signed_payload['token']:
            headers['Authorization'] = f'Bearer {signed_payload["token"]}'
        
        try:
            response = requests.post(self.endpoint, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'HTTP request failed: {e}')
            raise

    def parse_response(self, raw_response):
        if isinstance(raw_response, dict):
            return raw_response
        try:
            return json.loads(raw_response)
        except Exception:
            return {'status': 'error', 'raw': str(raw_response)}
