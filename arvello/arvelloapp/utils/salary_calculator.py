from decimal import Decimal
from django.utils import timezone
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

def update_salary_with_calculations(salary_instance):
    """Ažuriraj instancu plaće s izračunanim vrijednostima (bruto, doprinosi, porezi, neto)."""

    # Izračunaj iznose za redovni rad, godišnji odmor i bolovanje
    regular_amount = salary_instance.regular_hours * salary_instance.employee.hourly_rate
    vacation_amount = salary_instance.vacation_hours * salary_instance.employee.hourly_rate
    sick_leave_amount = salary_instance.sick_leave_hours * salary_instance.employee.hourly_rate * salary_instance.sick_leave_rate

    # Izračunaj iznos za prekovremeni rad
    overtime_rate_increase = Decimal(salary_instance.overtime_rate_increase) / Decimal('100')
    overtime_rate = salary_instance.employee.hourly_rate * (Decimal('1') + overtime_rate_increase)
    overtime_amount = salary_instance.overtime_hours * overtime_rate

    # Dohvati iznos bonusa (ili 0 ako nije zadan)
    bonus_amount = salary_instance.bonus or Decimal('0')

    # Izračunaj dodatak za staž
    base_for_seniority = regular_amount + vacation_amount + sick_leave_amount + overtime_amount + bonus_amount
    experience_bonus_amount = salary_instance.employee.calculate_experience_bonus(base_for_seniority)

    # Izračunaj i postavi bruto iznos plaće
    gross_salary = regular_amount + vacation_amount + sick_leave_amount + overtime_amount + bonus_amount + experience_bonus_amount

    # Izračunaj doprinose
    pension_pillar_1 = gross_salary * Decimal('0.15')
    pension_pillar_2 = gross_salary * Decimal('0.05')
    health_insurance = gross_salary * Decimal('0.165')

    # Izračunaj ukupne doprinose
    total_contributions = pension_pillar_1 + pension_pillar_2

    # Izračunaj dohodak
    income = gross_salary - total_contributions

    # Izračunaj osobni odbitak
    personal_deduction = salary_instance.employee.calculate_personal_deduction()
    if personal_deduction > income:
        personal_deduction = income

    # Izračunaj poreznu osnovicu
    income_tax_base = max(income - personal_deduction, Decimal('0'))

    # Izračunaj porez na dohodak koristeći lokalne stope
    from .salary_calculator import calculate_income_tax # Importaj funkciju za izračun poreza
    income_tax = calculate_income_tax(income_tax_base, salary_instance.employee.city, salary_instance.payment_date)

    # Izračunaj neto plaću
    net_salary = income - income_tax

    # Postavi izračunate vrijednosti na instancu
    salary_instance.regular_amount = round(regular_amount, 2)
    salary_instance.vacation_amount = round(vacation_amount, 2)
    salary_instance.sick_leave_amount = round(sick_leave_amount, 2)
    salary_instance.overtime_amount = round(overtime_amount, 2)
    salary_instance.experience_bonus_amount = round(experience_bonus_amount, 2)
    salary_instance.gross_salary = round(gross_salary, 2)
    salary_instance.pension_pillar_1 = round(pension_pillar_1, 2)
    salary_instance.pension_pillar_2 = round(pension_pillar_2, 2)
    salary_instance.health_insurance = round(health_insurance, 2)
    salary_instance.tax_deduction = round(personal_deduction, 2)
    salary_instance.income_tax_base = round(income_tax_base, 2)
    salary_instance.income_tax = round(income_tax, 2)
    salary_instance.net_salary = round(net_salary, 2)

    # Spremi izračunate vrijednosti (ako se metoda poziva izvan save metode Salary modela)
    salary_instance.save()
