from .base import ProviderAdapter


class SandboxAdapter(ProviderAdapter):
    """Simple sandbox adapter that echoes payload and returns success."""

    def prepare_payload(self, document):
        # Handle Invoice objects with full fiscal data
        if hasattr(document, 'get_fiscal_data'):  # It's an Invoice with fiscal methods
            fiscal_data = document.get_fiscal_data()
            return {
                'document_type': 'invoice',
                'document_id': str(document.id),
                'invoice_number': document.number,
                'created_at': document.date_created.isoformat() if document.date_created else None,
                'sales_channel': document.sales_channel,
                'fiscal_data': fiscal_data,
                'items_count': len(fiscal_data.get('items', [])),
                'total_amount': fiscal_data.get('totals', {}).get('total_amount'),
                'vat_summary': fiscal_data.get('vat_summary', {}),
            }
        # Handle Invoice objects (legacy)
        elif hasattr(document, 'number'):  # It's an Invoice
            return {
                'document_type': 'invoice',
                'document_id': str(document.id),
                'invoice_number': document.number,
                'created_at': document.date_created.isoformat() if document.date_created else None,
                'sales_channel': getattr(document, 'sales_channel', 'retail'),
            }
        # Handle dict
        elif isinstance(document, dict):
            return {
                'document_type': document.get('type', 'unknown'),
                'document_id': document.get('id'),
            }
        # Handle other objects
        else:
            return {
                'document_type': getattr(document, 'document_type', 'unknown'),
                'document_id': getattr(document, 'document_id', None),
            }

    def sign_payload(self, payload):
        # No-op for sandbox
        return payload

    def send(self, signed_payload):
        # Emulate provider response
        return {'status': 'ok', 'fiscal_id': 'SANDBOX-' + str(signed_payload.get('document_id'))}

    def parse_response(self, raw_response):
        return {'ok': raw_response.get('status') == 'ok', 'fiscal_id': raw_response.get('fiscal_id')}
