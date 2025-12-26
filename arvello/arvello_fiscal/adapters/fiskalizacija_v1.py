import logging
from .base import ProviderAdapter
from lxml import etree
from datetime import datetime
import xmlsec
import requests
import os

logger = logging.getLogger(__name__)


class FiskalizacijaV1Adapter(ProviderAdapter):
    """Adapter for Fiskalizacija v1 (XML + PKI signing).

    Supports real XML signing with xmlsec and HTTP transport with requests.
    """

    def __init__(self, endpoint: str = None, cert_meta: dict = None, mode: str = "production"):
        super().__init__(mode)
        self.endpoint = endpoint
        self.cert_meta = cert_meta or {}

    def prepare_payload(self, document):
        """Priprema XML payload za fiskalizaciju v1."""
        if hasattr(document, 'get_fiscal_data'):
            fiscal_data = document.get_fiscal_data()
            return self._create_racun_zahtjev_xml(fiscal_data)
        else:
            # Legacy fallback
            return self._create_basic_xml(document)
    
    def _create_racun_zahtjev_xml(self, fiscal_data):
        """Stvara RacunZahtjev XML strukturu prema F1 fiskalnim specifikacijama."""
        from lxml import etree
        import uuid
        from datetime import datetime
        
        # Namespace
        ns = 'tns'
        ns_uri = 'http://www.apis-it.hr/fin/2012/types/f73'
        
        # Generate unique ID and UUID
        uri_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        
        # Root element
        root = etree.Element(f'{{{ns_uri}}}RacunZahtjev', nsmap={ns: ns_uri})
        root.set('Id', uri_id)
        
        # Zaglavlje (Header)
        zaglavlje = etree.SubElement(root, f'{{{ns_uri}}}Zaglavlje')
        etree.SubElement(zaglavlje, f'{{{ns_uri}}}IdPoruke').text = message_id
        etree.SubElement(zaglavlje, f'{{{ns_uri}}}DatumVrijeme').text = datetime.utcnow().strftime('%d.%m.%YT%H:%M:%S')
        
        # Racun (Invoice)
        racun = etree.SubElement(root, f'{{{ns_uri}}}Racun')
        
        # Issuer data
        issuer = fiscal_data['issuer_data']
        etree.SubElement(racun, f'{{{ns_uri}}}Oib').text = issuer['oib']
        etree.SubElement(racun, f'{{{ns_uri}}}USustPdv').text = '1'  # Always 1 for VAT payers
        
        # Invoice timestamp - must be exact to the second
        invoice = fiscal_data['invoice_data']
        invoice_datetime = f"{invoice['date']}T{datetime.now().strftime('%H:%M:%S')}"  # Use current time for demo
        etree.SubElement(racun, f'{{{ns_uri}}}DatVrijeme').text = invoice_datetime.replace('-', '.')
        
        # Sequence type: P (location level) or N (device level)
        etree.SubElement(racun, f'{{{ns_uri}}}OznSlijed').text = 'P'
        
        # Invoice number breakdown
        br_rac = etree.SubElement(racun, f'{{{ns_uri}}}BrRac')
        # Parse invoice number components (assuming format: sequential/location/device)
        number_parts = invoice['number'].split('/')
        if len(number_parts) >= 3:
            etree.SubElement(br_rac, f'{{{ns_uri}}}BrOznRac').text = number_parts[0]
            etree.SubElement(br_rac, f'{{{ns_uri}}}OznPosPr').text = number_parts[1]
            etree.SubElement(br_rac, f'{{{ns_uri}}}OznNapUr').text = number_parts[2]
        else:
            # Fallback if number format is different
            etree.SubElement(br_rac, f'{{{ns_uri}}}BrOznRac').text = invoice['number']
            etree.SubElement(br_rac, f'{{{ns_uri}}}OznPosPr').text = invoice.get('fiscal_location', 'POS1')
            etree.SubElement(br_rac, f'{{{ns_uri}}}OznNapUr').text = invoice.get('fiscal_device_id', 'DEV1')
        
        # PDV (VAT) information
        pdv = etree.SubElement(racun, f'{{{ns_uri}}}Pdv')
        for vat_rate, vat_data in fiscal_data['vat_summary'].items():
            porez = etree.SubElement(pdv, f'{{{ns_uri}}}Porez')
            etree.SubElement(porez, f'{{{ns_uri}}}Stopa').text = f"{vat_rate:.2f}"
            etree.SubElement(porez, f'{{{ns_uri}}}Osnovica').text = f"{vat_data['base_amount']:.2f}"
            etree.SubElement(porez, f'{{{ns_uri}}}Iznos').text = f"{vat_data['vat_amount']:.2f}"
        
        # Total amount
        totals = fiscal_data['totals']
        etree.SubElement(racun, f'{{{ns_uri}}}IznosUkupno').text = f"{totals['total_amount']:.2f}"
        
        # Payment method mapping
        payment_mapping = {
            'cash': 'G',
            'card': 'K',
            'bank_transfer': 'C',
            'other': 'C'
        }
        payment_method = payment_mapping.get(invoice.get('payment_method', 'cash'), 'G')
        etree.SubElement(racun, f'{{{ns_uri}}}NacinPlac').text = payment_method
        
        # Operator OIB
        etree.SubElement(racun, f'{{{ns_uri}}}OibOper').text = invoice.get('fiscal_operator_oib') or issuer['oib']
        
        # Security code (ZastKod) - calculate properly
        zast_kod = self._calculate_security_code(fiscal_data)
        etree.SubElement(racun, f'{{{ns_uri}}}ZastKod').text = zast_kod
        
        # Delivery note (NakDost) - 0 for retail pickup, 1 for delivery
        etree.SubElement(racun, f'{{{ns_uri}}}NakDost').text = '0'
        
        return etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True)
    
    def _calculate_security_code(self, fiscal_data):
        """Calculate ZastKod (security code) as MD5 of signed concatenated fields."""
        import hashlib
        
        issuer = fiscal_data['issuer_data']
        invoice = fiscal_data['invoice_data']
        totals = fiscal_data['totals']
        
        # Concatenate fields as per specification
        # OIB + DatVrijeme + BrOznRac + OznPosPr + OznNapUr + IznosUkupno
        oib = issuer['oib']
        dat_vrijeme = f"{invoice['date']}T{datetime.now().strftime('%H:%M:%S')}"
        
        # Parse invoice number components
        number_parts = invoice['number'].split('/')
        if len(number_parts) >= 3:
            br_ozn_rac = number_parts[0]
            ozn_pos_pr = number_parts[1]
            ozn_nap_ur = number_parts[2]
        else:
            br_ozn_rac = invoice['number']
            ozn_pos_pr = invoice.get('fiscal_location', 'POS1')
            ozn_nap_ur = invoice.get('fiscal_device_id', 'DEV1')
        
        iznos_ukupno = f"{totals['total_amount']:.2f}"
        
        # Concatenate
        unsigned_string = f"{oib}{dat_vrijeme}{br_ozn_rac}{ozn_pos_pr}{ozn_nap_ur}{iznos_ukupno}"
        
        # In production, this should be signed with private key first, then MD5
        # For now, we'll use MD5 of the concatenated string
        # TODO: Implement proper RSA signing for production
        return hashlib.md5(unsigned_string.encode('utf-8')).hexdigest()
    
    def _create_basic_xml(self, document):
        """Legacy XML creation for backward compatibility."""
        root = etree.Element('ObrazacJOPPD')
        meta = etree.SubElement(root, 'Meta')
        etree.SubElement(meta, 'GeneratedAt').text = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        # Example: include basic document fields
        doc_el = etree.SubElement(root, 'Document')
        if isinstance(document, dict):
            etree.SubElement(doc_el, 'Type').text = document.get('type', 'unknown')
            etree.SubElement(doc_el, 'Id').text = str(document.get('id', ''))
        else:
            etree.SubElement(doc_el, 'Type').text = getattr(document, 'document_type', 'unknown')
            etree.SubElement(doc_el, 'Id').text = str(getattr(document, 'document_id', ''))

        xml = etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True)
        return xml

    def sign_payload(self, payload):
        """Sign the RacunZahtjev XML with XML-DSig."""
        if self.mode == 'sandbox':
            # For sandbox, skip actual signing and just wrap in SOAP envelope
            return self._create_soap_envelope(payload)
        
        # Production signing logic
        cert_path = self.cert_meta.get('cert_path')
        key_path = self.cert_meta.get('key_path')
        if not cert_path or not key_path:
            raise ValueError("Certificate and key paths required for production signing")

        # Parse XML
        root = etree.fromstring(payload)
        
        # Create signature template
        signature_node = xmlsec.template.create(root, xmlsec.Transform.EXCL_C14N, xmlsec.Transform.RSA_SHA256)
        root.append(signature_node)
        
        # Add reference with URI to the RacunZahtjev element
        uri_id = root.get('Id')
        ref = xmlsec.template.add_reference(signature_node, xmlsec.Transform.SHA256, uri=f"#{uri_id}")
        xmlsec.template.add_transform(ref, xmlsec.Transform.EXCL_C14N)
        
        # Add key info
        key_info = xmlsec.template.ensure_key_info(signature_node)
        xmlsec.template.add_x509_data(key_info)
        
        # Load key
        key = xmlsec.Key.from_file(key_path, xmlsec.KeyFormat.PEM)
        key.load_cert_from_file(cert_path, xmlsec.KeyFormat.PEM)
        
        # Sign
        ctx = xmlsec.SignatureContext()
        ctx.key = key
        ctx.sign(signature_node)
        
        # Convert to string for SOAP envelope
        signed_xml_str = etree.tostring(root, encoding='utf-8', xml_declaration=False).decode('utf-8')
        soap_envelope = self._create_soap_envelope(signed_xml_str)
        
        return soap_envelope
    
    def _create_soap_envelope(self, signed_xml):
        """Wrap signed XML in SOAP envelope."""
        soap_ns = 'http://schemas.xmlsoap.org/soap/envelope/'
        
        # Handle both string and bytes input
        if isinstance(signed_xml, bytes):
            signed_xml = signed_xml.decode('utf-8')
        
        # Remove XML declaration if present
        if signed_xml.startswith('<?xml'):
            signed_xml = signed_xml.split('?>', 1)[1].strip()
        
        # Parse signed XML
        signed_root = etree.fromstring(signed_xml)
        
        # Create SOAP envelope
        envelope = etree.Element(f'{{{soap_ns}}}Envelope', nsmap={'soapenv': soap_ns})
        body = etree.SubElement(envelope, f'{{{soap_ns}}}Body')
        
        # Import and append the signed RacunZahtjev
        body.append(signed_root)
        
        return etree.tostring(envelope, encoding='utf-8', xml_declaration=True)

    def send(self, signed_payload):
        if self.mode == 'sandbox' or not self.endpoint:
            return {'status': 'OK', 'message': 'sandbox response', 'jir': 'V1-SANDBOX-JIR'}

        headers = {'Content-Type': 'text/xml; charset=utf-8'}
        try:
            response = requests.post(self.endpoint, data=signed_payload, headers=headers, timeout=30)
            response.raise_for_status()
            return self._parse_soap_response(response.text)
        except requests.RequestException as e:
            logger.error(f'HTTP request failed: {e}')
            raise
    
    def _parse_soap_response(self, soap_response):
        """Parse SOAP response and extract RacunOdgovor data."""
        try:
            root = etree.fromstring(soap_response)
            
            # Find RacunOdgovor in SOAP body
            ns = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                  'tns': 'http://www.apis-it.hr/fin/2012/types/f73'}
            
            racun_odgovor = root.find('.//tns:RacunOdgovor', ns)
            if racun_odgovor is not None:
                # Extract JIR (Fiscal Invoice Identifier)
                jir_elem = racun_odgovor.find('.//tns:Jir', ns)
                jir = jir_elem.text if jir_elem is not None else None
                
                return {
                    'status': 'OK',
                    'jir': jir,
                    'message': 'Fiscalization successful'
                }
            else:
                # Check for error
                error_elem = root.find('.//tns:SifraGreske', ns)
                error_msg_elem = root.find('.//tns:PorukaGreske', ns)
                
                return {
                    'status': 'ERROR',
                    'error_code': error_elem.text if error_elem is not None else 'UNKNOWN',
                    'message': error_msg_elem.text if error_msg_elem is not None else 'Unknown error'
                }
                
        except Exception as e:
            logger.error(f'Failed to parse SOAP response: {e}')
            return {
                'status': 'ERROR',
                'message': f'Failed to parse response: {str(e)}'
            }

    def parse_response(self, raw_response):
        """Parse provider response into standardized dict format."""
        if isinstance(raw_response, dict):
            return raw_response
        
        # If it's already parsed SOAP response, return as-is
        if isinstance(raw_response, str) and ('RacunOdgovor' in raw_response or 'SifraGreske' in raw_response):
            return self._parse_soap_response(raw_response)
        
        # Fallback for other response types
        try:
            root = etree.fromstring(raw_response)
            return {'status': root.findtext('.//Status') or 'unknown', 'raw': raw_response}
        except Exception:
            return {'status': 'error', 'raw': str(raw_response)}
