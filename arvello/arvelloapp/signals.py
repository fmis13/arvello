from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Invoice
from arvello_fiscal.services.fiscal_service import FiscalService

@receiver(pre_save, sender=Invoice)
def track_invoice_changes(sender, instance, **kwargs):
    """Track original values before save."""
    if instance.pk:
        try:
            original = Invoice.objects.get(pk=instance.pk)
            instance._original_is_paid = original.is_paid
        except Invoice.DoesNotExist:
            instance._original_is_paid = False
    else:
        instance._original_is_paid = False

@receiver(post_save, sender=Invoice)
def enqueue_invoice_for_fiscalization(sender, instance, created, **kwargs):
    """Enqueue invoice for fiscalization when created or marked as paid."""
    # Skip if only fiscal_status was updated to avoid recursion
    if hasattr(instance, '_updating_fiscal_status'):
        return
    
    # Check if created or is_paid changed to True
    should_enqueue = False
    if created:
        should_enqueue = True
    elif hasattr(instance, '_original_is_paid') and not instance._original_is_paid and instance.is_paid:
        should_enqueue = True
    
    if should_enqueue:
        # Check sales_channel - fiscal channels need fiscalization
        fiscal_channels = ['retail', 'wholesale']  # Both channels need fiscalization
        if instance.sales_channel in fiscal_channels:
            try:
                fiscal_service = FiscalService()
                # Use fiscalize_invoice method
                result = fiscal_service.fiscalize_invoice(instance)
                # Update fiscal_status without triggering signal
                instance._updating_fiscal_status = True
                instance.fiscal_status = 'enqueued'
                instance.save(update_fields=['fiscal_status'])
                delattr(instance, '_updating_fiscal_status')
            except Exception as e:
                # Log error and set status to failed
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to enqueue fiscal request for invoice {instance.id}: {e}")
                # Update fiscal_status without triggering signal
                instance._updating_fiscal_status = True
                instance.fiscal_status = 'failed'
                instance.save(update_fields=['fiscal_status'])
                delattr(instance, '_updating_fiscal_status')