"""Core fiscal service: prepare payloads and create fiscal requests."""
from decimal import Decimal
import hashlib
from ..models import FiscalDocument, FiscalRequest, FiscalConfig
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
try:
    from ..adapters.sandbox import SandboxAdapter
except Exception:
    SandboxAdapter = None



class FiscalService:
    @staticmethod
    def idempotency_key(company_id: str, document_type: str, document_id: str, version: int = 1) -> str:
        s = f"{company_id}:{document_type}:{document_id}:{version}"
        return hashlib.sha256(s.encode('utf-8')).hexdigest()

    @staticmethod
    def create_fiscal_document(document_type: str, document_id: str, company_id: str) -> FiscalDocument:
        doc = FiscalDocument.objects.create(
            document_type=document_type,
            document_id=str(document_id),
            company_id=str(company_id),
            status='pending'
        )
        return doc

    @staticmethod
    def create_request(fiscal_document: FiscalDocument, payload: dict, idempotency_key: str = None) -> FiscalRequest:
        if idempotency_key is None:
            idempotency_key = FiscalService.idempotency_key(fiscal_document.company_id, fiscal_document.document_type, fiscal_document.document_id)

        fr = FiscalRequest.objects.create(
            fiscal_document=fiscal_document,
            idempotency_key=idempotency_key,
            payload=payload,
            status='queued',
        )
        return fr

    @staticmethod
    def get_adapter_for_invoice(invoice):
        """Resolve adapter instance for given invoice based on fiscalization type (F1/F2)."""
        company_id = str(invoice.subject.id)
        
        # Determine adapter based on invoice's get_fiscal_adapter_type method
        adapter_name = invoice.get_fiscal_adapter_type()
        
        # Get config for the company
        try:
            cfg = FiscalConfig.objects.get(company_id=company_id)
            mode = cfg.mode
        except FiscalConfig.DoesNotExist:
            cfg = None
            mode = 'sandbox'
        
        # Map adapter names to classes
        if adapter_name == 'sandbox' or adapter_name is None:
            from ..adapters.sandbox import SandboxAdapter as _SA
            return _SA(mode=mode)
        if adapter_name == 'fiskalizacija_v1':
            from ..adapters.fiskalizacija_v1 import FiskalizacijaV1Adapter
            return FiskalizacijaV1Adapter(
                endpoint=(cfg.endpoint if cfg else None), 
                cert_meta={
                    'cert_path': cfg.certificate_file.path if cfg and cfg.certificate_file else None,
                    'key_path': cfg.private_key_file.path if cfg and cfg.private_key_file else None,
                } if cfg else None, 
                mode=mode
            )
        if adapter_name == 'fiskalizacija_v2':
            from ..adapters.fiskalizacija_v2 import FINAeRacunAdapter
            return FINAeRacunAdapter(
                endpoint=(cfg.endpoint if cfg else None), 
                cert_meta={
                    'cert_path': cfg.certificate_file.path if cfg and cfg.certificate_file else None,
                    'key_path': cfg.private_key_file.path if cfg and cfg.private_key_file else None,
                    'password': cfg.certificate_password if cfg else None,
                } if cfg else None,
                mode=mode
            )

        # Fallback to sandbox
        from ..adapters.sandbox import SandboxAdapter as _SA2
        return _SA2(mode=mode)

    @staticmethod
    def fiscalize_invoice(invoice):
        """Fiscalize an invoice based on its fiscalization type (F1/F2)."""
        # Validate that invoice is ready for fiscalization
        is_ready, message = invoice.is_fiscal_ready()
        if not is_ready:
            raise ValueError(f"Invoice not ready for fiscalization: {message}")
        
        # Get the appropriate adapter based on fiscalization type
        adapter = FiscalService.get_adapter_for_invoice(invoice)
        ftype = invoice.get_fiscalization_type()
        
        # Fiscalize the invoice
        result = adapter.fiscalize(invoice)
        
        # Update invoice fiscal status and type-specific fields
        invoice.fiscal_status = 'processed'
        invoice.fiscalized_at = timezone.now()
        
        # For F1 (retail) - save JIR and ZKI
        if ftype == 'F1':
            if result.get('jir'):
                invoice.fiscal_jir = result.get('jir')
            if result.get('zki'):
                invoice.fiscal_zki = result.get('zki')
        
        # For F2 (wholesale) - save eRačun UUID and UBL reference
        elif ftype == 'F2':
            if result.get('eracun_uuid'):
                invoice.eracun_uuid = result.get('eracun_uuid')
            if result.get('ubl_reference'):
                invoice.ubl_xml_reference = result.get('ubl_reference')
            if result.get('fiscal_id'):
                invoice.eracun_uuid = result.get('fiscal_id')
        
        invoice.save()
        
        return result

    @staticmethod
    def get_adapter_for_company(company_id: str):
        """Resolve adapter instance for a company based on its FiscalConfig."""
        try:
            cfg = FiscalConfig.objects.get(company_id=company_id)
            mode = cfg.mode
            adapter_name = cfg.adapter
        except FiscalConfig.DoesNotExist:
            # Fallback to sandbox if no config exists
            from ..adapters.sandbox import SandboxAdapter as _SA
            return _SA(mode='sandbox')
        
        if adapter_name == 'sandbox' or adapter_name is None:
            from ..adapters.sandbox import SandboxAdapter as _SA
            return _SA(mode=mode)
        if adapter_name == 'fiskalizacija_v1':
            from ..adapters.fiskalizacija_v1 import FiskalizacijaV1Adapter
            return FiskalizacijaV1Adapter(
                endpoint=(cfg.endpoint if cfg else None), 
                cert_meta={
                    'cert_path': cfg.certificate_file.path if cfg and cfg.certificate_file else None,
                    'key_path': cfg.private_key_file.path if cfg and cfg.private_key_file else None,
                    'password': cfg.certificate_password if cfg else None,
                } if cfg else None, 
                mode=mode
            )
        if adapter_name == 'fiskalizacija_v2':
            from ..adapters.fiskalizacija_v2 import FINAeRacunAdapter
            return FINAeRacunAdapter(
                endpoint=(cfg.endpoint if cfg else None), 
                cert_meta={
                    'cert_path': cfg.certificate_file.path if cfg and cfg.certificate_file else None,
                    'key_path': cfg.private_key_file.path if cfg and cfg.private_key_file else None,
                    'password': cfg.certificate_password if cfg else None,
                } if cfg else None,
                mode=mode
            )
        
        # Fallback to sandbox
        from ..adapters.sandbox import SandboxAdapter as _SA2
        return _SA2(mode=mode)

    @staticmethod
    def submit_and_enqueue(document_type: str, document_id: str, company_id: str, payload: dict, enqueue=True):
        """Create fiscal document/request and enqueue sending task.

        If enqueue=False, run send synchronously (useful for testing).
        """
        fiscal_doc = FiscalService.create_fiscal_document(document_type, document_id, company_id)
        idemp = FiscalService.idempotency_key(company_id, document_type, document_id)
        fr = FiscalService.create_request(fiscal_doc, payload, idempotency_key=idemp)

        adapter = FiscalService.get_adapter_for_company(company_id)
        # attach resolved adapter name/meta to payload for debugging
        fr.payload = payload
        fr.save()

        if enqueue:
            try:
                # defer to Celery task
                from ..tasks import send_fiscal_request
                send_fiscal_request.delay(fr.id)
            except Exception as e:
                logger.warning(f'Celery not available or task dispatch failed: {e}. Falling back to sync send.')
                # fallback to synchronous send
                signed = adapter.sign_payload(payload)
                raw = adapter.send(signed)
                parsed = adapter.parse_response(raw)
                from ..models import FiscalResponse
                FiscalResponse.objects.create(fiscal_request=fr, raw_response=str(raw), parsed=parsed)
                fr.status = 'sent' if parsed.get('ok') else 'failed'
                fr.save()
                fiscal_doc.status = fr.status
                fiscal_doc.save()
        else:
            signed = adapter.sign_payload(payload)
            raw = adapter.send(signed)
            parsed = adapter.parse_response(raw)
            from ..models import FiscalResponse
            FiscalResponse.objects.create(fiscal_request=fr, raw_response=str(raw), parsed=parsed)
            fr.status = 'sent' if parsed.get('ok') else 'failed'
            fr.save()
            fiscal_doc.status = fr.status
            fiscal_doc.save()
        return fr
