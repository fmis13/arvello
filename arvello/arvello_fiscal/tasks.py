from celery import shared_task
from .models import FiscalRequest, FiscalResponse
from .services.fiscal_service import FiscalService
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_fiscal_request(self, fiscal_request_id):
    try:
        fr = FiscalRequest.objects.get(pk=fiscal_request_id)
    except FiscalRequest.DoesNotExist:
        logger.error(f'FiscalRequest {fiscal_request_id} not found')
        return False

    adapter = FiscalService.get_adapter_for_company(fr.fiscal_document.company_id)
    fr.attempt_count += 1
    fr.last_attempt_at = timezone.now()
    fr.save()

    try:
        signed = adapter.sign_payload(fr.payload or {})
        raw = adapter.send(signed)
        parsed = adapter.parse_response(raw)

        FiscalResponse.objects.create(fiscal_request=fr, raw_response=str(raw), parsed=parsed)
        fr.status = 'sent' if parsed.get('ok') else 'failed'
        fr.save()
        fr.fiscal_document.status = fr.status
        fr.fiscal_document.save()
        return parsed.get('ok', False)
    except Exception as e:
        logger.exception(f'Error sending fiscal request {fr.id}: {e}')
        fr.status = 'error'
        fr.save()
        fr.fiscal_document.status = fr.status
        fr.fiscal_document.save()
        raise
