"""
Signali za automatsku fiskalizaciju računa i kreiranje korisničkih profila.

Ovaj modul definira Django signale koji se aktiviraju pri kreiranju ili
ažuriranju računa, i automatski pokreću proces fiskalizacije.
Također automatski kreira UserProfile za nove korisnike.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Invoice, UserProfile
import logging

logger = logging.getLogger(__name__)


# ----- User Profile Signals -----

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatski kreira UserProfile za novog korisnika.
    """
    if created:
        try:
            UserProfile.objects.create(user=instance)
            logger.debug(f"UserProfile kreiran za korisnika {instance.username}")
        except Exception as e:
            logger.error(f"Greška pri kreiranju UserProfile za {instance.username}: {e}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Sprema UserProfile kada se korisnik spremi.
    Kreira profil ako ne postoji (za postojeće korisnike bez profila).
    """
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            # Kreira profil za postojeće korisnike koji ga nemaju
            UserProfile.objects.create(user=instance)
            logger.debug(f"UserProfile kreiran za postojećeg korisnika {instance.username}")
    except Exception as e:
        logger.error(f"Greška pri spremanju UserProfile za {instance.username}: {e}")


# ----- Invoice Signals -----


@receiver(pre_save, sender=Invoice)
def track_invoice_changes(sender, instance, **kwargs):
    """Prati originalne vrijednosti prije spremanja za detekciju promjena."""
    if instance.pk:
        try:
            original = Invoice.objects.get(pk=instance.pk)
            instance._original_is_paid = original.is_paid
            instance._original_sales_channel = original.sales_channel
        except Invoice.DoesNotExist:
            instance._original_is_paid = False
            instance._original_sales_channel = None
    else:
        instance._original_is_paid = False
        instance._original_sales_channel = None


@receiver(pre_save, sender=Invoice)
def auto_detect_sales_channel(sender, instance, **kwargs):
    """Automatski postavlja kanal prodaje i tip računa ako nisu eksplicitno postavljeni."""
    if instance.client:
        # Auto-detect sales channel if not set
        if not instance.sales_channel:
            instance.sales_channel = instance.auto_detect_sales_channel()
        # Auto-detect invoice type if not set
        if not instance.invoice_type:
            instance.invoice_type = instance.auto_detect_invoice_type()


@receiver(post_save, sender=Invoice)
def enqueue_invoice_for_fiscalization(sender, instance, created, **kwargs):
    """
    Stavlja račun u red za fiskalizaciju kada je kreiran ili označen kao plaćen.
    
    Fiskalizacija se pokreće:
    - Pri kreiranju novog računa s postavljenim kanalom prodaje
    - Kada se račun označi kao plaćen (is_paid promijeni na True)
    """
    # Preskoči ako je samo fiscal_status ažuriran (izbjegni rekurziju)
    if hasattr(instance, '_updating_fiscal_status'):
        return
    
    # Provjeri treba li pokrenuti fiskalizaciju
    should_enqueue = False
    
    if created and instance.sales_channel:
        # Novi račun s postavljenim kanalom prodaje
        should_enqueue = True
    elif hasattr(instance, '_original_is_paid') and not instance._original_is_paid and instance.is_paid:
        # Račun je označen kao plaćen
        should_enqueue = True
    
    if should_enqueue:
        # Provjeri je li kanal prodaje postavljen za fiskalizaciju
        fiscal_channels = ['retail', 'wholesale']
        if instance.sales_channel in fiscal_channels:
            try:
                from arvello_fiscal.services.fiscal_service import FiscalService
                
                fiscal_service = FiscalService()
                result = fiscal_service.fiscalize_invoice(instance)
                
                # Ažuriraj fiskalni status bez pokretanja signala
                instance._updating_fiscal_status = True
                instance.fiscal_status = 'enqueued'
                instance.save(update_fields=['fiscal_status'])
                delattr(instance, '_updating_fiscal_status')
                
                logger.info(f"Račun {instance.id} stavljen u red za fiskalizaciju")
                
            except ImportError as e:
                logger.warning(f"arvello_fiscal aplikacija nije dostupna: {e}")
            except Exception as e:
                logger.error(f"Greška pri stavljanju računa {instance.id} u red za fiskalizaciju: {e}")
                
                # Ažuriraj status na 'failed' bez pokretanja signala
                instance._updating_fiscal_status = True
                instance.fiscal_status = 'failed'
                instance.save(update_fields=['fiscal_status'])
                delattr(instance, '_updating_fiscal_status')
