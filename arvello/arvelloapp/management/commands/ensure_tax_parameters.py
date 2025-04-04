from django.core.management.base import BaseCommand
from arvelloapp.models import TaxParameter
from decimal import Decimal
from django.utils import timezone

class Command(BaseCommand):
    help = 'Ensures tax parameters exist for the current year'

    def handle(self, *args, **options):
        current_year = timezone.now().year
        self.stdout.write(f"Checking tax parameters for {current_year}")
        
        # Check if tax parameters for the current year exist
        parameters_exist = TaxParameter.objects.filter(year=current_year).exists()
        
        if not parameters_exist:
            # Find the most recent year with parameters
            latest_year = TaxParameter.objects.all().order_by('-year').values_list('year', flat=True).first()
            
            if latest_year:
                self.stdout.write(f"Copying tax parameters from {latest_year} to {current_year}")
                
                # Copy parameters from the most recent year
                for param in TaxParameter.objects.filter(year=latest_year):
                    TaxParameter.objects.create(
                        parameter_type=param.parameter_type,
                        year=current_year,
                        value=param.value,
                        description=f"{param.description.split('(')[0]} ({current_year})"
                    )
                    self.stdout.write(f"Created {param.parameter_type} for {current_year}")
            else:
                self.stdout.write("No existing tax parameters found. Creating default values.")
                
                # Create default parameters
                default_parameters = self.get_default_parameters(current_year)
                
                for parameter_type, value, description in default_parameters:
                    TaxParameter.objects.create(
                        parameter_type=parameter_type,
                        year=current_year,
                        value=Decimal(value),
                        description=f"{description} ({current_year})"
                    )
                    self.stdout.write(f"Created {parameter_type} for {current_year}")
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created tax parameters for {current_year}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Tax parameters for {current_year} already exist'))

    def get_default_parameters(self, year):
        """Dohvati default parametre ovisno o godini"""
        return [
            ('base_deduction', '7200.00', 'Osnovni godišnji odbitak'),
            ('monthly_tax_threshold', '5000.00', 'Mjesečni porezni prag'),
            ('health_insurance', '16.50', 'Zdravstveno osiguranje'),
            ('pension_rate_1', '15.00', 'MIO I. stup'),
            ('pension_rate_2', '5.00', 'MIO II. stup'),
        ]
