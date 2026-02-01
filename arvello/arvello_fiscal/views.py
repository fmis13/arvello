from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import FiscalDocument, FiscalRequest
from .services.fiscal_service import FiscalService
from django.contrib import messages


@login_required
def fiscal_documents(request):
    docs = FiscalDocument.objects.all().order_by('-created_at')
    return render(request, 'fiscal_documents.html', {'docs': docs})


@login_required
def submit_fiscal_document(request, doc_id):
    doc = get_object_or_404(FiscalDocument, pk=doc_id)
    # Build a minimal payload from document for sandbox testing
    payload = {
        'document_type': doc.document_type,
        'document_id': doc.document_id,
        'company_id': doc.company_id,
        'created_at': str(doc.created_at),
    }
    fr = FiscalService.submit_and_enqueue(doc.document_type, doc.document_id, doc.company_id, payload, enqueue=True)
    messages.success(request, f'Fiscal request {fr.id} submitted (sandbox-first).')
    return redirect('fiscal_documents')
