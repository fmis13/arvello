from django.core.management.base import BaseCommand
import csv
from arvelloapp.models import TaxParameter, LocalIncomeTax
from decimal import Decimal

class Command(BaseCommand):
    help = 'Import tax rates from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')
        parser.add_argument('--tax-type', choices=['local', 'parameters'], default='local', help='Type of tax data to import')
        parser.add_argument('--year', type=int, help='Year for tax parameters', default=2024)

    def handle(self, *args, **options):
        file_path = options['csv_file']
        tax_type = options['tax_type']
        year = options['year']
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                next(reader, None)  # Skip header row
                
                if tax_type == 'local':
                    self._import_local_tax_rates(reader)
                else:
                    self._import_tax_parameters(reader, year)
                    
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {tax_type} tax data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing data: {str(e)}'))
    
    def _import_local_tax_rates(self, reader):
        count = 0
        for row in reader:
            if len(row) < 2:
                continue
                
            city_name = row[0].strip()
            try:
                tax_rate = Decimal(row[1].replace(',', '.').strip())
                
                # Create or update local tax rate
                obj, created = LocalIncomeTax.objects.update_or_create(
                    city_name=city_name,
                    defaults={'tax_rate': tax_rate}
                )
                
                count += 1
                action = "Created" if created else "Updated"
                self.stdout.write(f"{action} tax rate for {city_name}: {tax_rate}%")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing row {row}: {str(e)}'))
        
        self.stdout.write(f"Processed {count} local tax rates")
    
    def _import_tax_parameters(self, reader, year):
        # Define parameter types to look for in the CSV
        param_types = {
            'base_deduction': 'Osnovica osobnog odbitka',
            'pension_rate_1': 'Stopa doprinosa za MIO I. stup',
            'pension_rate_2': 'Stopa doprinosa za MIO II. stup',
            'health_insurance': 'Stopa doprinosa za zdravstveno osiguranje',
            'tax_rate_1': 'Stopa poreza na dohodak 1. razred',
            'tax_rate_2': 'Stopa poreza na dohodak 2. razred',
            'tax_threshold': 'Porezni prag (između 1. i 2. razreda)',
        }
        
        count = 0
        for row in reader:
            if len(row) < 3:
                continue
                
            param_name = row[0].strip()
            param_type = None
            
            # Find matching parameter type
            for key, value in param_types.items():
                if value.lower() in param_name.lower():
                    param_type = key
                    break
            
            if param_type:
                try:
                    value = Decimal(row[1].replace(',', '.').strip())
                    description = row[2].strip() if len(row) > 2 else None
                    
                    # Create or update tax parameter
                    obj, created = TaxParameter.objects.update_or_create(
                        parameter_type=param_type,
                        year=year,
                        defaults={
                            'value': value,
                            'description': description
                        }
                    )
                    
                    count += 1
                    action = "Created" if created else "Updated"
                    self.stdout.write(f"{action} {param_name} for {year}: {value}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing parameter {param_name}: {str(e)}'))
        
        self.stdout.write(f"Processed {count} tax parameters for year {year}")
