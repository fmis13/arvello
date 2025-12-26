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
        """Resolve adapter instance for given invoice based on sales channel."""
        company_id = str(invoice.subject.id)
        
        # Determine adapter based on sales channel
        if invoice.sales_channel == 'retail':
            adapter_name = 'fiskalizacija_v1'
        elif invoice.sales_channel == 'wholesale':
            adapter_name = 'fiskalizacija_v2'
        else:
            adapter_name = 'sandbox'  # fallback
        
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
            from ..adapters.fiskalizacija_v2 import FiskalizacijaV2Adapter
            return FiskalizacijaV2Adapter(
                endpoint=(cfg.endpoint if cfg else None), 
                secret=(cfg.secret if cfg else None), 
                mode=mode
            )

        # Fallback to sandbox
        from ..adapters.sandbox import SandboxAdapter as _SA2
        return _SA2(mode=mode)
    @staticmethod
    def fiscalize_invoice(invoice):
        """Fiscalize an invoice based on its sales channel."""
        if not invoice.sales_channel:
            raise ValueError("Sales channel must be set before fiscalization")
        
        # Validate that invoice is ready for fiscalization
        is_ready, message = invoice.is_fiscal_ready()
        if not is_ready:
            raise ValueError(f"Invoice not ready for fiscalization: {message}")
        
        # Get the appropriate adapter based on sales channel
        adapter = FiscalService.get_adapter_for_invoice(invoice)
        
        # Fiscalize the invoice
        result = adapter.fiscalize(invoice)
        
        # Update invoice fiscal status
        invoice.fiscal_status = 'processed'
        invoice.save()
        
        return result

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
