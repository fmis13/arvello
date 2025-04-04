from decimal import Decimal
from django.utils import timezone
from ..models import TaxParameter, LocalIncomeTax
from .text_utils import standardize_city_name

def calculate_income_tax(tax_base: Decimal, city: str, payment_date=None) -> Decimal:
    """Izračunaj porez na dohodak koristeći mjesečni prag i lokalne stope"""
    # Import modela unutar funkcije da se izbjegne circular dependency
    from ..models import TaxParameter, LocalIncomeTax
    if payment_date is None:
        # Ako datum isplate nije zadan, koristi današnji datum
        payment_date = timezone.now().date()
    
    # Dohvati mjesečni prag poreza iz parametara za danu godinu
    try:
        threshold_param = TaxParameter.objects.get(
            parameter_type='monthly_tax_threshold',
            year=payment_date.year
        )
        monthly_threshold = Decimal(str(threshold_param.value))
    except TaxParameter.DoesNotExist:
        # Ako parametar nije pronađen, koristi zadanu vrijednost
        monthly_threshold = Decimal('5000.00')  # Default threshold

    # Dohvati porezne stope za grad (standardiziraj ime grada za pretragu)
    try:
        local_tax = LocalIncomeTax.objects.filter(
            city_name__iexact=standardize_city_name(city),
            valid_from__lte=payment_date # Dohvati stope koje vrijede na datum isplate
        ).latest('valid_from') # Uzmi najnovije važeće stope
        
        # Izračunaj porez koristeći pragove i stope
        if tax_base <= monthly_threshold:
            # Ako je osnovica manja ili jednaka pragu, koristi samo nižu stopu
            return round(tax_base * Decimal(str(local_tax.tax_rate_lower)) / 100, 2)
        
        # Ako je osnovica veća od praga, izračunaj porez za oba razreda
        lower_tax = monthly_threshold * Decimal(str(local_tax.tax_rate_lower)) / 100
        higher_tax = (tax_base - monthly_threshold) * Decimal(str(local_tax.tax_rate_higher)) / 100
        return round(lower_tax + higher_tax, 2)
        
    except LocalIncomeTax.DoesNotExist:
        # Ako stope za grad nisu pronađene, vrati 0
        return Decimal('0')
