from django.core.management.base import BaseCommand
from arvelloapp.models import TaxParameter
from decimal import Decimal
from django.utils import timezone

class Command(BaseCommand):
    help = 'Potvrdi i kreiraj porezne parametre za tekuću godinu'

    def handle(self, *args, **options):
        current_year = timezone.now().year
        
        parameters_exist = TaxParameter.objects.filter(year=current_year).exists()
        
        if not parameters_exist:
            latest_year = TaxParameter.objects.all().order_by('-year').values_list('year', flat=True).first()
            
            if latest_year:
                
                for param in TaxParameter.objects.filter(year=latest_year):
                    TaxParameter.objects.create(
                        parameter_type=param.parameter_type,
                        year=current_year,
                        value=param.value,
                        description=f"{param.description.split('(')[0]} ({current_year})"
                    )
            else:
                default_parameters = self.get_default_parameters(current_year)
                
                for parameter_type, value, description in default_parameters:
                    TaxParameter.objects.create(
                        parameter_type=parameter_type,
                        year=current_year,
                        value=Decimal(value),
                        description=f"{description} ({current_year})"
                    )


    def get_default_parameters(self, year):
        """Dohvati default parametre ovisno o godini"""
        return [
            ('base_deduction', '7200.00', 'Osnovni godišnji odbitak'),
            ('monthly_tax_threshold', '5000.00', 'Mjesečni porezni prag'),
            ('health_insurance', '16.50', 'Zdravstveno osiguranje'),
            ('pension_rate_1', '15.00', 'MIO I. stup'),
            ('pension_rate_2', '5.00', 'MIO II. stup'),
        ]
