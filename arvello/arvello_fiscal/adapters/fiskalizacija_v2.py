"""FINA eRačun Adapter for Croatian B2B/B2G electronic invoicing.

FINA (Financijska agencija) is the Croatian government agency that operates
the eRačun (e-Invoice) system for B2B and B2G electronic invoicing.

This adapter implements FINA's eRačun API specification:
- UBL 2.1 XML format for invoice documents
- XML-DSIG signing with RSA-SHA256
- SOAP web service transport (or REST for newer API versions)
- Envelope numbering and routing via FINA's information intermediary system

References:
- FINA eRačun Technical Documentation
- Croatian e-Invoice normative framework (Direktiva 2014/55/EU)
- UBL 2.1 Invoice specification (ISO/IEC 19845)
"""
import logging
import uuid
import hashlib
from datetime import datetime
from decimal import Decimal
from .base import ProviderAdapter
from lxml import etree
import requests

logger = logging.getLogger(__name__)

# FINA eRačun endpoints
FINA_PRODUCTION_ENDPOINT = 'https://b2g.apis-it.hr:8446/eracun-ws/services/SendInvoice'
FINA_TEST_ENDPOINT = 'https://b2g-test.apis-it.hr:8446/eracun-ws/services/SendInvoice'

# UBL 2.1 Namespaces
UBL_NS = 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
CBC_NS = 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
CAC_NS = 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
DS_NS = 'http://www.w3.org/2000/09/xmldsig#'
SOAP_NS = 'http://schemas.xmlsoap.org/soap/envelope/'

NSMAP = {
    None: UBL_NS,
    'cbc': CBC_NS,
    'cac': CAC_NS,
}


class FINAeRacunAdapter(ProviderAdapter):
    """Adapter for FINA eRačun (Croatian B2B/B2G electronic invoicing).

    Implements FINA's eRačun API using UBL 2.1 XML format with XML-DSIG signing.
    This is specifically designed for FINA as the Croatian information intermediary.
    """

    def __init__(self, endpoint: str = None, cert_meta: dict = None, mode: str = 'production'):
        super().__init__(mode)
        self.endpoint = endpoint or (FINA_TEST_ENDPOINT if mode == 'sandbox' else FINA_PRODUCTION_ENDPOINT)
        self.cert_meta = cert_meta or {}

    def prepare_payload(self, document):
        """Prepare UBL 2.1 Invoice XML for FINA eRačun."""
        if hasattr(document, 'get_fiscal_data'):
            fiscal_data = document.get_fiscal_data()
            return self._create_ubl_invoice(fiscal_data)
        else:
            # Legacy fallback - create minimal UBL from dict
            return self._create_basic_ubl(document)

    def _create_ubl_invoice(self, fiscal_data):
        """Create UBL 2.1 Invoice XML per FINA eRačun specification.
        
        Structure follows EN 16931 (European e-invoicing semantic data model)
        and Croatian national rules for B2B/B2G invoicing.
        """
        # Generate unique invoice UUID
        invoice_uuid = str(uuid.uuid4())
        
        issuer = fiscal_data['issuer_data']
        invoice = fiscal_data['invoice_data']
        totals = fiscal_data['totals']
        buyer = fiscal_data.get('buyer_data') or {}
        
        # Create root Invoice element
        root = etree.Element('{%s}Invoice' % UBL_NS, nsmap=NSMAP)
        
        # UBL Version ID
        etree.SubElement(root, '{%s}UBLVersionID' % CBC_NS).text = '2.1'
        
        # Customization ID - FINA Croatia profile
        etree.SubElement(root, '{%s}CustomizationID' % CBC_NS).text = \
            'urn:cen.eu:en16931:2017#compliant#urn:fina.hr:eracun'
        
        # Profile ID - FINA eRačun
        etree.SubElement(root, '{%s}ProfileID' % CBC_NS).text = 'HR:ERACUN'
        
        # Invoice ID (unique identifier)
        etree.SubElement(root, '{%s}ID' % CBC_NS).text = invoice['number']
        
        # Invoice UUID
        etree.SubElement(root, '{%s}UUID' % CBC_NS).text = invoice_uuid
        
        # Issue Date
        etree.SubElement(root, '{%s}IssueDate' % CBC_NS).text = invoice['date']
        
        # Due Date
        if invoice.get('due_date'):
            etree.SubElement(root, '{%s}DueDate' % CBC_NS).text = invoice['due_date']
        
        # Invoice Type Code (380 = Commercial invoice)
        etree.SubElement(root, '{%s}InvoiceTypeCode' % CBC_NS).text = '380'
        
        # Note (optional)
        if invoice.get('notes'):
            etree.SubElement(root, '{%s}Note' % CBC_NS).text = invoice['notes']
        
        # Document Currency Code
        etree.SubElement(root, '{%s}DocumentCurrencyCode' % CBC_NS).text = 'EUR'
        
        # Accounting Supplier Party (Seller/Issuer)
        supplier_party = etree.SubElement(root, '{%s}AccountingSupplierParty' % CAC_NS)
        party = etree.SubElement(supplier_party, '{%s}Party' % CAC_NS)
        
        # Seller endpoint ID (OIB)
        endpoint = etree.SubElement(party, '{%s}EndpointID' % CBC_NS, schemeID='HR:OIB')
        endpoint.text = issuer['oib']
        
        # Seller identification
        party_id = etree.SubElement(party, '{%s}PartyIdentification' % CAC_NS)
        etree.SubElement(party_id, '{%s}ID' % CBC_NS, schemeID='HR:OIB').text = issuer['oib']
        
        # Seller name
        party_name = etree.SubElement(party, '{%s}PartyName' % CAC_NS)
        etree.SubElement(party_name, '{%s}Name' % CBC_NS).text = issuer['name']
        
        # Seller postal address
        postal_addr = etree.SubElement(party, '{%s}PostalAddress' % CAC_NS)
        etree.SubElement(postal_addr, '{%s}StreetName' % CBC_NS).text = issuer.get('address', '')
        etree.SubElement(postal_addr, '{%s}CityName' % CBC_NS).text = issuer.get('city', '')
        etree.SubElement(postal_addr, '{%s}PostalZone' % CBC_NS).text = issuer.get('postal_code', '')
        country = etree.SubElement(postal_addr, '{%s}Country' % CAC_NS)
        etree.SubElement(country, '{%s}IdentificationCode' % CBC_NS).text = 'HR'
        
        # Seller VAT ID
        if issuer.get('vat_id'):
            tax_scheme = etree.SubElement(party, '{%s}PartyTaxScheme' % CAC_NS)
            etree.SubElement(tax_scheme, '{%s}CompanyID' % CBC_NS).text = issuer['vat_id']
            scheme = etree.SubElement(tax_scheme, '{%s}TaxScheme' % CAC_NS)
            etree.SubElement(scheme, '{%s}ID' % CBC_NS).text = 'VAT'
        
        # Seller legal entity
        legal_entity = etree.SubElement(party, '{%s}PartyLegalEntity' % CAC_NS)
        etree.SubElement(legal_entity, '{%s}RegistrationName' % CBC_NS).text = issuer['name']
        etree.SubElement(legal_entity, '{%s}CompanyID' % CBC_NS, schemeID='HR:OIB').text = issuer['oib']
        
        # Accounting Customer Party (Buyer)
        customer_party = etree.SubElement(root, '{%s}AccountingCustomerParty' % CAC_NS)
        buyer_party = etree.SubElement(customer_party, '{%s}Party' % CAC_NS)
        
        if buyer:
            # Buyer endpoint ID (OIB)
            buyer_endpoint = etree.SubElement(buyer_party, '{%s}EndpointID' % CBC_NS, schemeID='HR:OIB')
            buyer_endpoint.text = buyer.get('oib', '')
            
            # Buyer identification
            buyer_party_id = etree.SubElement(buyer_party, '{%s}PartyIdentification' % CAC_NS)
            etree.SubElement(buyer_party_id, '{%s}ID' % CBC_NS, schemeID='HR:OIB').text = buyer.get('oib', '')
            
            # Buyer name
            buyer_name = etree.SubElement(buyer_party, '{%s}PartyName' % CAC_NS)
            etree.SubElement(buyer_name, '{%s}Name' % CBC_NS).text = buyer.get('name', '')
            
            # Buyer postal address
            buyer_postal = etree.SubElement(buyer_party, '{%s}PostalAddress' % CAC_NS)
            etree.SubElement(buyer_postal, '{%s}StreetName' % CBC_NS).text = buyer.get('address', '')
            etree.SubElement(buyer_postal, '{%s}CityName' % CBC_NS).text = buyer.get('city', '')
            etree.SubElement(buyer_postal, '{%s}PostalZone' % CBC_NS).text = buyer.get('postal_code', '')
            buyer_country = etree.SubElement(buyer_postal, '{%s}Country' % CAC_NS)
            etree.SubElement(buyer_country, '{%s}IdentificationCode' % CBC_NS).text = 'HR'
            
            # Buyer legal entity
            buyer_legal = etree.SubElement(buyer_party, '{%s}PartyLegalEntity' % CAC_NS)
            etree.SubElement(buyer_legal, '{%s}RegistrationName' % CBC_NS).text = buyer.get('name', '')
        
        # Payment Means
        payment_means = etree.SubElement(root, '{%s}PaymentMeans' % CAC_NS)
        # Payment means code mapping
        payment_code_map = {
            'cash': '10',           # In cash
            'card': '48',           # Bank card
            'bank_transfer': '30',  # Credit transfer
            'other': '1',           # Instrument not defined
        }
        code = payment_code_map.get(invoice.get('payment_method', 'bank_transfer'), '30')
        etree.SubElement(payment_means, '{%s}PaymentMeansCode' % CBC_NS).text = code
        
        # Tax Total
        tax_total = etree.SubElement(root, '{%s}TaxTotal' % CAC_NS)
        total_vat = Decimal('0.00')
        for vat_data in fiscal_data.get('vat_summary', {}).values():
            total_vat += Decimal(str(vat_data.get('vat_amount', 0)))
        
        etree.SubElement(tax_total, '{%s}TaxAmount' % CBC_NS, currencyID='EUR').text = f'{total_vat:.2f}'
        
        # Tax subtotals by rate
        for vat_rate, vat_data in fiscal_data.get('vat_summary', {}).items():
            tax_subtotal = etree.SubElement(tax_total, '{%s}TaxSubtotal' % CAC_NS)
            etree.SubElement(tax_subtotal, '{%s}TaxableAmount' % CBC_NS, currencyID='EUR').text = \
                f"{vat_data['base_amount']:.2f}"
            etree.SubElement(tax_subtotal, '{%s}TaxAmount' % CBC_NS, currencyID='EUR').text = \
                f"{vat_data['vat_amount']:.2f}"
            
            tax_category = etree.SubElement(tax_subtotal, '{%s}TaxCategory' % CAC_NS)
            etree.SubElement(tax_category, '{%s}ID' % CBC_NS).text = 'S'  # Standard rate
            etree.SubElement(tax_category, '{%s}Percent' % CBC_NS).text = f'{vat_rate:.2f}'
            tax_scheme = etree.SubElement(tax_category, '{%s}TaxScheme' % CAC_NS)
            etree.SubElement(tax_scheme, '{%s}ID' % CBC_NS).text = 'VAT'
        
        # Legal Monetary Total
        legal_total = etree.SubElement(root, '{%s}LegalMonetaryTotal' % CAC_NS)
        line_ext = Decimal(str(totals.get('subtotal', totals['total_amount']) - float(total_vat)))
        etree.SubElement(legal_total, '{%s}LineExtensionAmount' % CBC_NS, currencyID='EUR').text = f'{line_ext:.2f}'
        etree.SubElement(legal_total, '{%s}TaxExclusiveAmount' % CBC_NS, currencyID='EUR').text = f'{line_ext:.2f}'
        etree.SubElement(legal_total, '{%s}TaxInclusiveAmount' % CBC_NS, currencyID='EUR').text = \
            f"{totals['total_amount']:.2f}"
        etree.SubElement(legal_total, '{%s}PayableAmount' % CBC_NS, currencyID='EUR').text = \
            f"{totals['total_amount']:.2f}"
        
        # Invoice Lines
        line_num = 1
        for vat_rate, vat_data in fiscal_data.get('vat_summary', {}).items():
            for item in vat_data.get('items', []):
                inv_line = etree.SubElement(root, '{%s}InvoiceLine' % CAC_NS)
                etree.SubElement(inv_line, '{%s}ID' % CBC_NS).text = str(line_num)
                
                etree.SubElement(inv_line, '{%s}InvoicedQuantity' % CBC_NS, unitCode='C62').text = \
                    str(item.get('quantity', 1))
                etree.SubElement(inv_line, '{%s}LineExtensionAmount' % CBC_NS, currencyID='EUR').text = \
                    f"{item.get('base_amount', 0):.2f}"
                
                # Item
                item_elem = etree.SubElement(inv_line, '{%s}Item' % CAC_NS)
                etree.SubElement(item_elem, '{%s}Name' % CBC_NS).text = item.get('name', '')
                
                # Item tax category
                item_tax_cat = etree.SubElement(item_elem, '{%s}ClassifiedTaxCategory' % CAC_NS)
                etree.SubElement(item_tax_cat, '{%s}ID' % CBC_NS).text = 'S'
                etree.SubElement(item_tax_cat, '{%s}Percent' % CBC_NS).text = f'{vat_rate:.2f}'
                item_tax_scheme = etree.SubElement(item_tax_cat, '{%s}TaxScheme' % CAC_NS)
                etree.SubElement(item_tax_scheme, '{%s}ID' % CBC_NS).text = 'VAT'
                
                # Price
                price = etree.SubElement(inv_line, '{%s}Price' % CAC_NS)
                etree.SubElement(price, '{%s}PriceAmount' % CBC_NS, currencyID='EUR').text = \
                    f"{item.get('unit_price', 0):.2f}"
                
                line_num += 1
        
        return {
            'xml': etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True),
            'uuid': invoice_uuid,
            'invoice_id': invoice['number'],
        }

    def _create_basic_ubl(self, document):
        """Create minimal UBL from legacy document dict."""
        root = etree.Element('{%s}Invoice' % UBL_NS, nsmap=NSMAP)
        etree.SubElement(root, '{%s}UBLVersionID' % CBC_NS).text = '2.1'
        etree.SubElement(root, '{%s}ID' % CBC_NS).text = str(document.get('id', 'UNKNOWN'))
        etree.SubElement(root, '{%s}IssueDate' % CBC_NS).text = datetime.utcnow().strftime('%Y-%m-%d')
        etree.SubElement(root, '{%s}InvoiceTypeCode' % CBC_NS).text = '380'
        
        return {
            'xml': etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True),
            'uuid': str(uuid.uuid4()),
            'invoice_id': str(document.get('id', '')),
        }

    def sign_payload(self, payload):
        """Sign UBL Invoice XML with XML-DSIG for FINA eRačun.
        
        FINA requires XML Digital Signature (XML-DSIG) using enveloped signature.
        The signature uses RSA-SHA256 for the signature algorithm.
        """
        xml_bytes = payload['xml']
        
        if self.mode == 'sandbox':
            # Skip signing for sandbox mode
            return self._wrap_in_soap_envelope(xml_bytes, payload['uuid'])
        
        cert_path = self.cert_meta.get('cert_path')
        key_path = self.cert_meta.get('key_path')
        
        if not cert_path or not key_path:
            logger.warning('Certificate and key not provided, skipping signature')
            return self._wrap_in_soap_envelope(xml_bytes, payload['uuid'])
        
        try:
            import xmlsec
            
            # Parse XML
            root = etree.fromstring(xml_bytes)
            
            # Add Id attribute to root for reference
            root.set('Id', 'invoice-data')
            
            # Create signature template (enveloped signature with RSA-SHA256)
            signature_node = xmlsec.template.create(
                root, 
                xmlsec.Transform.EXCL_C14N, 
                xmlsec.Transform.RSA_SHA256
            )
            root.append(signature_node)
            
            # Add reference to the signed content
            ref = xmlsec.template.add_reference(
                signature_node, 
                xmlsec.Transform.SHA256, 
                uri='#invoice-data'
            )
            xmlsec.template.add_transform(ref, xmlsec.Transform.ENVELOPED)
            xmlsec.template.add_transform(ref, xmlsec.Transform.EXCL_C14N)
            
            # Add key info with X509 certificate data
            key_info = xmlsec.template.ensure_key_info(signature_node)
            xmlsec.template.add_x509_data(key_info)
            
            # Load private key and certificate
            key = xmlsec.Key.from_file(key_path, xmlsec.KeyFormat.PEM)
            key.load_cert_from_file(cert_path, xmlsec.KeyFormat.PEM)
            
            # Sign
            ctx = xmlsec.SignatureContext()
            ctx.key = key
            ctx.sign(signature_node)
            
            signed_xml = etree.tostring(root, encoding='utf-8', xml_declaration=True)
            return self._wrap_in_soap_envelope(signed_xml, payload['uuid'])
            
        except ImportError:
            logger.error('xmlsec library not available for signing')
            return self._wrap_in_soap_envelope(xml_bytes, payload['uuid'])
        except Exception as e:
            logger.error(f'Failed to sign UBL invoice: {e}')
            raise

    def _wrap_in_soap_envelope(self, xml_content, invoice_uuid):
        """Wrap signed UBL XML in SOAP envelope for FINA web service."""
        if isinstance(xml_content, bytes):
            xml_content = xml_content.decode('utf-8')
        
        # Remove XML declaration if present (will be in SOAP envelope)
        if xml_content.startswith('<?xml'):
            xml_content = xml_content.split('?>', 1)[1].strip()
        
        # Parse the invoice XML
        invoice_root = etree.fromstring(xml_content)
        
        # Create SOAP envelope
        envelope = etree.Element('{%s}Envelope' % SOAP_NS, nsmap={'soapenv': SOAP_NS})
        header = etree.SubElement(envelope, '{%s}Header' % SOAP_NS)
        body = etree.SubElement(envelope, '{%s}Body' % SOAP_NS)
        
        # FINA SendInvoice request wrapper
        send_req_ns = 'http://fina.hr/eracun/sendInvoice'
        send_invoice = etree.SubElement(body, '{%s}SendInvoiceRequest' % send_req_ns, 
                                        nsmap={'send': send_req_ns})
        
        # Document UUID
        etree.SubElement(send_invoice, '{%s}DocumentUUID' % send_req_ns).text = invoice_uuid
        
        # Attach the invoice
        invoice_data = etree.SubElement(send_invoice, '{%s}InvoiceData' % send_req_ns)
        invoice_data.append(invoice_root)
        
        return {
            'soap_envelope': etree.tostring(envelope, encoding='utf-8', xml_declaration=True),
            'uuid': invoice_uuid,
        }

    def send(self, signed_payload):
        """Send signed SOAP envelope to FINA eRačun web service."""
        if self.mode == 'sandbox' or not self.endpoint:
            # Return sandbox response
            return {
                'status': 'OK',
                'eracun_uuid': signed_payload.get('uuid', 'SANDBOX-UUID'),
                'message': 'Sandbox: Invoice accepted',
                'fina_reference': f'FINA-SANDBOX-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
            }
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'http://fina.hr/eracun/sendInvoice',
        }
        
        try:
            response = requests.post(
                self.endpoint,
                data=signed_payload['soap_envelope'],
                headers=headers,
                timeout=60,
                verify=True,  # Verify SSL certificates
            )
            response.raise_for_status()
            return self._parse_soap_response(response.text, signed_payload.get('uuid'))
            
        except requests.Timeout:
            logger.error('FINA eRačun request timed out')
            raise
        except requests.RequestException as e:
            logger.error(f'FINA eRačun HTTP request failed: {e}')
            raise

    def _parse_soap_response(self, soap_response, invoice_uuid):
        """Parse FINA eRačun SOAP response."""
        try:
            root = etree.fromstring(soap_response.encode('utf-8') if isinstance(soap_response, str) else soap_response)
            
            # Define namespaces for response parsing
            ns = {
                'soap': SOAP_NS,
                'send': 'http://fina.hr/eracun/sendInvoice',
            }
            
            # Look for successful response
            send_response = root.find('.//send:SendInvoiceResponse', ns)
            if send_response is not None:
                status_elem = send_response.find('.//send:Status', ns)
                ref_elem = send_response.find('.//send:DocumentReference', ns)
                
                status = status_elem.text if status_elem is not None else 'UNKNOWN'
                fina_ref = ref_elem.text if ref_elem is not None else None
                
                if status.upper() in ('OK', 'ACCEPTED', 'RECEIVED'):
                    return {
                        'status': 'OK',
                        'eracun_uuid': invoice_uuid,
                        'fina_reference': fina_ref,
                        'message': 'Invoice successfully submitted to FINA',
                    }
                else:
                    return {
                        'status': 'ERROR',
                        'eracun_uuid': invoice_uuid,
                        'error_code': status,
                        'message': f'FINA rejected invoice: {status}',
                    }
            
            # Look for fault/error
            fault = root.find('.//soap:Fault', ns)
            if fault is not None:
                fault_string = fault.findtext('.//faultstring', default='Unknown error')
                fault_code = fault.findtext('.//faultcode', default='UNKNOWN')
                return {
                    'status': 'ERROR',
                    'eracun_uuid': invoice_uuid,
                    'error_code': fault_code,
                    'message': fault_string,
                }
            
            # Unknown response format
            return {
                'status': 'UNKNOWN',
                'eracun_uuid': invoice_uuid,
                'raw': soap_response,
                'message': 'Could not parse FINA response',
            }
            
        except Exception as e:
            logger.error(f'Failed to parse FINA response: {e}')
            return {
                'status': 'ERROR',
                'eracun_uuid': invoice_uuid,
                'message': f'Failed to parse response: {str(e)}',
                'raw': soap_response,
            }

    def parse_response(self, raw_response):
        """Parse FINA eRačun response into standardized dict."""
        if isinstance(raw_response, dict):
            return raw_response
        
        if isinstance(raw_response, str) and '<' in raw_response:
            return self._parse_soap_response(raw_response, None)
        
        return {'status': 'error', 'raw': str(raw_response)}

    def health_check(self) -> bool:
        """Check connectivity to FINA eRačun service."""
        if self.mode == 'sandbox':
            return True
        
        try:
            # Send a simple ping/test request if FINA provides one
            # For now, just check if endpoint is reachable
            response = requests.get(self.endpoint.replace('/SendInvoice', ''), timeout=10)
            return response.status_code < 500
        except Exception:
            return False


# Backwards compatibility alias
FiskalizacijaV2Adapter = FINAeRacunAdapter
