from django.core.management.base import BaseCommand
import pandas as pd
from arvelloapp.models import LocalIncomeTax
from decimal import Decimal
import datetime
import re

class Command(BaseCommand):
    help = 'Import city tax rates from Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file')
        parser.add_argument('--year', type=int, default=None, help='Year for tax rates (default: current year)')

    def handle(self, *args, **options):
        excel_file = options['excel_file']
        year = options['year'] or datetime.datetime.now().year
        
        try:
            # Pročitaj Excel datoteku
            self.stdout.write(f"Čitanje Excel datoteke: {excel_file}")
            df = pd.read_excel(excel_file)
            
            # Pronađi potrebne stupce
            city_code_col = None
            city_name_col = None
            city_type_col = None
            lower_rate_col = None
            higher_rate_col = None
            account_col = None
            nn_col = None
            
            # Iteriraj kroz stupce i pronađi potrebne
            for col in df.columns:
                col_lower = str(col).lower()
                if 'šifra' in col_lower and ('grad' in col_lower or 'općin' in col_lower):
                    city_code_col = col
                elif ('ime' in col_lower or 'naziv') and ('grad' in col_lower or 'općin' in col_lower):
                    city_name_col = col
                elif 'vrsta' in col_lower and ('jls' in col_lower or 'grad' in col_lower or 'općin' in col_lower):
                    city_type_col = col
                elif 'niža' in col_lower and 'stopa' in col_lower:
                    lower_rate_col = col
                elif 'viša' in col_lower and 'stopa' in col_lower:
                    higher_rate_col = col
                elif 'račun' in col_lower and 'uplat' in col_lower:
                    account_col = col
                elif 'nn' in col_lower or 'narodn' in col_lower:
                    nn_col = col
            
            # Idi kroz stupce i provjeri da li su pronađeni potrebni stupci
            if not city_name_col or not lower_rate_col or not higher_rate_col:
                self.stderr.write(self.style.ERROR(
                    f"Nisu pronađeni potrebni stupci. Pronađeno: "
                    f"Ime grada: {'DA' if city_name_col else 'NE'}, "
                    f"Niža stopa: {'DA' if lower_rate_col else 'NE'}, "
                    f"Viša stopa: {'DA' if higher_rate_col else 'NE'}"
                ))
                return
            
            created_count = 0
            updated_count = 0
            
            valid_from = datetime.date(year, 1, 1)
            
            # Iteriraj kroz redove i obrađuj podatke
            for _, row in df.iterrows():
                # Preskakanje praznih redova
                if pd.isna(row[city_name_col]) or str(row[city_name_col]).strip() == '':
                    continue
                
                # Pripremi podatke
                if city_code_col and not pd.isna(row[city_code_col]):
                    city_code = str(row[city_code_col]).strip()
                    # Ukloni sve znakove osim brojeva
                    digits_only = ''.join(c for c in city_code if c.isdigit())
                    # Dodaj vodeće nule ako je potrebno
                    city_code = digits_only.zfill(5)
                else:
                    city_code = ''
                
                city_name = str(row[city_name_col]).strip()
                
                # Konvertiraj postotke u decimalne vrijednosti
                try:
                    # Pretvori u string da bi se izbjegli problemi s decimalnim zarezima
                    tax_lower_str = str(row[lower_rate_col])
                    tax_higher_str = str(row[higher_rate_col])
                    
                    # Ukloni sve znakove osim brojeva i decimalnih točaka/zareza
                    lower_match = re.search(r'(\d+[.,]?\d*)', tax_lower_str)
                    higher_match = re.search(r'(\d+[.,]?\d*)', tax_higher_str)
                    
                    if lower_match and higher_match:
                        # Spremi kao pravi postotak (20.00 a ne 0.20)
                        tax_rate_lower = Decimal(lower_match.group(1).replace(',', '.'))
                        tax_rate_higher = Decimal(higher_match.group(1).replace(',', '.'))
                    else:
                        self.stderr.write(self.style.ERROR(f"Neispravna porezna stopa za {city_name} (šifra: {city_code})"))
                        continue
                except (ValueError, TypeError) as e:
                    self.stderr.write(self.style.ERROR(f"Neispravna porezna stopa za {city_name} (šifra: {city_code}): {str(e)}"))
                    continue
                
                # Opcionalni stupci
                account_number = str(row[account_col]) if account_col and not pd.isna(row[account_col]) else None
                official_gazette = str(row[nn_col]) if nn_col and not pd.isna(row[nn_col]) else None
                
                # Odredi tip grada
                # Ako nije pronađen stupac, postavi na GRAD
                city_type = 'GRAD'  # Default neka je  'GRAD'
                if city_type_col and not pd.isna(row[city_type_col]):
                    type_value = str(row[city_type_col]).strip().lower()
                    if 'općin' in type_value:
                        city_type = 'OPCINA'
                    elif 'veliki' in type_value or 'sjedište' in type_value or 'županij' in type_value:
                        city_type = 'VELIKI_GRAD'
                    elif 'zagreb' in type_value:
                        city_type = 'ZAGREB'
                    else:
                        city_type = 'GRAD'
                elif city_name and 'Zagreb' in city_name:
                    city_type = 'ZAGREB'
                
                try:
                    # Pretraži postojeći zapis
                    tax_obj = None
                    if city_code:
                        tax_obj = LocalIncomeTax.objects.filter(city_code=city_code).first()
                    
                    if not tax_obj and city_name:
                        tax_obj = LocalIncomeTax.objects.filter(city_name=city_name).first()
                    
                    if tax_obj:
                        # Update existing record
                        tax_obj.city_name = city_name
                        if city_code:
                            tax_obj.city_code = city_code
                        tax_obj.tax_rate_lower = tax_rate_lower
                        tax_obj.tax_rate_higher = tax_rate_higher
                        tax_obj.valid_from = valid_from
                        tax_obj.city_type = city_type
                        if account_number:
                            tax_obj.account_number = account_number
                        if official_gazette:
                            tax_obj.official_gazette = official_gazette
                        tax_obj.save()
                        updated_count += 1
                        self.stdout.write(f"Ažurirano: {city_name} ({city_code}) - {tax_rate_lower}%/{tax_rate_higher}%")
                    else:
                        # Stvaranje novog zapisa
                        LocalIncomeTax.objects.create(
                            city_name=city_name,
                            city_code=city_code,
                            tax_rate=Decimal('0.00'),  # Prirez je mrtav, ne znam zašto sam ga uopće implementirao
                            tax_rate_lower=tax_rate_lower,
                            tax_rate_higher=tax_rate_higher,
                            valid_from=valid_from,
                            account_number=account_number,
                            official_gazette=official_gazette,
                            city_type=city_type
                        )
                        created_count += 1
                        self.stdout.write(f"Kreirano: {city_name} ({city_code}) - {tax_rate_lower}%/{tax_rate_higher}%")
                        
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Greška pri obradi grada {city_name}: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS(
                f'Uspješno uvezeno {created_count} novih i ažurirano {updated_count} '
                f'postojećih poreznih stopa za {year}. godinu.'
            ))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Greška pri uvozu podataka: {str(e)}"))
