from django.core.management.base import BaseCommand
from arvelloapp.models import TaxParameter
from decimal import Decimal

class Command(BaseCommand):
    help = 'Initialize tax parameters for 2025'

    def handle(self, *args, **options):
        tax_parameters_2025 = [
            {
                'parameter_type': 'tax_rate_1',
                'year': 2025,
                'value': Decimal('20.00'),
                'description': 'Niža stopa poreza na dohodak (2025)'
            },
            {
                'parameter_type': 'tax_rate_2',
                'year': 2025,
                'value': Decimal('30.00'),
                'description': 'Viša stopa poreza na dohodak (2025)'
            },
            {
                'parameter_type': 'tax_threshold',
                'year': 2025,
                'value': Decimal('60000.00'),
                'description': 'Prag za primjenu više stope poreza (2025)'
            },
            {
                'parameter_type': 'base_deduction',
                'year': 2025,
                'value': Decimal('7200.00'),
                'description': 'Osnovni osobni odbitak godišnje (2025)'
            },
            {
                'parameter_type': 'health_insurance',
                'year': 2025,
                'value': Decimal('16.50'),
                'description': 'Stopa doprinosa za zdravstveno osiguranje (2025)'
            },
            {
                'parameter_type': 'pension_rate_1',
                'year': 2025,
                'value': Decimal('15.00'),
                'description': 'Stopa doprinosa za mirovinsko osiguranje - I. stup (2025)'
            },
            {
                'parameter_type': 'pension_rate_2',
                'year': 2025,
                'value': Decimal('5.00'),
                'description': 'Stopa doprinosa za mirovinsko osiguranje - II. stup (2025)'
            },
        ]
        
        count = 0
        for param in tax_parameters_2025:
            obj, created = TaxParameter.objects.update_or_create(
                parameter_type=param['parameter_type'],
                year=param['year'],
                defaults={
                    'value': param['value'],
                    'description': param['description']
                }
            )
            if created:
                count += 1
                self.stdout.write(f"Created: {param['parameter_type']} for {param['year']} with value {param['value']}")
            else:
                self.stdout.write(f"Updated: {param['parameter_type']} for {param['year']} with value {param['value']}")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} tax parameters for 2025'))
