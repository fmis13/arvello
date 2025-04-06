from django.utils import timezone
from decimal import Decimal
from ..models import TaxParameter, LocalIncomeTax, Salary, Employee, Company, NonTaxablePaymentType 
from .salary_calculator import update_salary_with_calculations, standardize_city_name # Adjust import if needed
import logging

logger = logging.getLogger(__name__)

def get_payslip_context(salary):
    """Generira kontekst za platnu listu."""
    # Osiguraj da su osnovni izračuni na salary objektu ažurni

    # Izračunaj dodatne vrijednosti za kontekst
    non_taxable_total = sum(Decimal(str(v)) for v in salary.non_taxable_payments.values()) if salary.non_taxable_payments else Decimal('0.00')
    
    # Izračunaj osnovni osobni odbitak (bez koeficijenta)
    # Koristimo spremljeni tax_deduction koji je već pomnožen s koeficijentom
    base_deduction_display = salary.tax_deduction 
    if salary.employee.tax_deduction_coefficient and salary.employee.tax_deduction_coefficient > 0:
         # Izračunaj osnovni odbitak (prije koeficijenta) samo za prikaz
         base_deduction_no_coeff = salary.tax_deduction / salary.employee.tax_deduction_coefficient
    else:
         base_deduction_no_coeff = salary.tax_deduction # Ako nema koeficijenta, isti je

    # Dohvati mjesečni prag za porez koji je korišten pri izračunu
    monthly_threshold = Decimal('4200.00') # Default
    payment_year = salary.payment_date.year if salary.payment_date else timezone.now().year
    try:
        threshold_param = TaxParameter.objects.get(
            parameter_type='monthly_tax_threshold', 
            year=payment_year
        )
        monthly_threshold = Decimal(str(threshold_param.value))
    except TaxParameter.DoesNotExist:
        logger.warning(f"Nije pronađen mjesečni prag za godinu {payment_year}. Koristi se default vrijednost.")
        pass 
        
    # Izračunaj porezne osnovice na temelju spremljene income_tax_base i praga
    # Koristimo salary.income_tax_base jer je to vrijednost NAKON odbitka
    lower_tax_base = min(salary.income_tax_base, monthly_threshold)
    higher_tax_base = max(salary.income_tax_base - monthly_threshold, Decimal('0.00'))
    
    # Ponovno dohvati porezne stope za prikaz
    display_lower_tax_rate = Decimal('20.00') # Default stopa za prikaz
    display_higher_tax_rate = Decimal('30.00') # Default stopa za prikaz
    try:
        # Dohvati stope koje su trebale vrijediti na datum isplate
        payment_date_obj = salary.payment_date or timezone.now().date()
        local_tax = LocalIncomeTax.objects.filter(
            city_name__iexact=standardize_city_name(salary.employee.city),
            valid_from__lte=payment_date_obj
        ).latest('valid_from')
        display_lower_tax_rate = local_tax.tax_rate_lower
        display_higher_tax_rate = local_tax.tax_rate_higher
    except LocalIncomeTax.DoesNotExist:
        logger.warning(f"Nisu pronađene lokalne porezne stope za {salary.employee.city} na datum {payment_date_obj}. Prikazuju se default stope.")
    except Exception as e:
        logger.error(f"Greška pri dohvaćanju lokalnih poreznih stopa za prikaz: {e}")
    # Kraj dohvaćanja stopa za prikaz

    # Pripremi listu neoporezivih primitaka s opisima
    non_taxable_items = []
    if salary.non_taxable_payments:
        # Dohvati sve relevantne podatke (code, description, name) za aktivne tipove
        payment_type_data = {pt.code: {'description': pt.description, 'name': pt.name} 
                             for pt in NonTaxablePaymentType.objects.filter(active=True)}
        
        for code, amount in salary.non_taxable_payments.items():
            data = payment_type_data.get(code)
            display_text = code # Default fallback je sam kod

            if data:
                # Ako smo pronašli podatke za taj kod
                # Prvo pokušaj koristiti opis, ako postoji i nije prazan
                if data.get('description'):
                    display_text = data['description']
                # Ako je opis prazan, pokušaj koristiti naziv
                elif data.get('name'):
                    display_text = data['name']
                # Ako su i opis i naziv prazni, fallback ostaje kod (što se ne bi smjelo dogoditi)

            non_taxable_items.append({
                'description': display_text, # Koristi display_text koji sadrži opis, naziv ili kod
                'amount': Decimal(str(amount)) # Osiguraj da je Decimal
            })
    # Kraj pripreme neoporezivih primitaka

    # Izračunaj iznose poreza direktno ovdje za prikaz
    # Koristi dohvaćene stope i izračunate osnovice
    calculated_lower_tax_amount = (lower_tax_base * display_lower_tax_rate / Decimal('100.00')).quantize(Decimal('0.01'))
    calculated_higher_tax_amount = (higher_tax_base * display_higher_tax_rate / Decimal('100.00')).quantize(Decimal('0.01'))
    # Kraj izračuna iznosa poreza
    
    # Ukupni doprinosi iz bruto plaće (već izračunati i spremljeni)
    total_contributions = salary.pension_pillar_1 + salary.pension_pillar_2
    # Dohodak (osnovica za porez prije odbitka) (već izračunat i spremljen kao gross_salary - total_contributions)
    income = salary.gross_salary - total_contributions

    context = {
        'salary': salary, # Proslijedi cijeli objekt za ostale podatke
        'employee': salary.employee,
        'company': salary.employee.company,
        'generated_at': timezone.now(),
        'non_taxable_total': non_taxable_total,
        'base_deduction': base_deduction_no_coeff, # Osnovni odbitak (bez koeficijenta) za prikaz
        'total_deduction': salary.tax_deduction, # Ukupni odbitak (s koeficijentom) za prikaz
        'lower_tax_base': lower_tax_base, 
        'higher_tax_base': higher_tax_base, 
        'lower_tax_rate': display_lower_tax_rate, # Koristi svježe dohvaćenu stopu za prikaz
        'higher_tax_rate': display_higher_tax_rate, # Koristi svježe dohvaćenu stopu za prikaz
        'lower_tax_amount': calculated_lower_tax_amount, # Koristi upravo izračunati iznos
        'higher_tax_amount': calculated_higher_tax_amount, # Koristi upravo izračunati iznos
        'total_contributions': total_contributions, 
        'income': income, 
        # Dodaj i ukupan porez za lakši prikaz u predlošku
        'total_income_tax': calculated_lower_tax_amount + calculated_higher_tax_amount, 
        'non_taxable_items': non_taxable_items, # Dodaj pripremljenu listu u kontekst
    }
    
    # Vrati rječnik konteksta
    return context
