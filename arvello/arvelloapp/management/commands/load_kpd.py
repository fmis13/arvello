"""
Management command za uvoz KPD šifara iz CSV datoteke.
Korištenje: python manage.py load_kpd /putanja/do/KPD_2025_struktura.csv
"""
import csv
from django.core.management.base import BaseCommand, CommandError
from arvelloapp.models import KPDCode


class Command(BaseCommand):
    help = 'Uvozi KPD 2025 šifre iz CSV datoteke'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Putanja do CSV datoteke s KPD šiframa')
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Obriši sve postojeće KPD šifre prije uvoza',
        )

    def get_level(self, code):
        """Odredi razinu hijerarhije na temelju formata šifre."""
        if not code or len(code) == 0:
            return 0
        
        # Primjeri: A=1, 01=2, 01.1=3, 01.11=4, 01.11.1=5, 01.11.11=6
        if code.isalpha():  # Sekcija (A, B, C...)
            return 1
        
        parts = code.split('.')
        if len(parts) == 1:
            return 2  # Odjeljak (01, 02...)
        elif len(parts) == 2:
            # 01.1 ili 01.11
            if len(parts[1]) == 1:
                return 3  # Skupina
            else:
                return 4  # Razred
        elif len(parts) == 3:
            if len(parts[2]) == 1:
                return 5  # Kategorija
            else:
                return 6  # Potkategorija
        
        return len(parts) + 1

    def get_parent_code(self, code):
        """Odredi šifru nadređene kategorije."""
        if not code or code.isalpha():
            return None
        
        parts = code.split('.')
        
        if len(parts) == 1:
            # Odjeljak (01) -> sekcija se određuje prema rasponu
            return None  # Može se dodati mapiranje ako je potrebno
        
        if len(parts) == 2:
            # 01.1 -> 01
            # 01.11 -> 01.1
            if len(parts[1]) == 1:
                return parts[0]
            else:
                return f"{parts[0]}.{parts[1][0]}"
        
        if len(parts) == 3:
            # 01.11.1 -> 01.11
            # 01.11.11 -> 01.11.1
            if len(parts[2]) == 1:
                return f"{parts[0]}.{parts[1]}"
            else:
                return f"{parts[0]}.{parts[1]}.{parts[2][0]}"
        
        return None

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                # Čitanje CSV-a
                reader = csv.reader(f)
                rows = list(reader)
        except FileNotFoundError:
            raise CommandError(f'CSV datoteka nije pronađena: {csv_file_path}')
        except Exception as e:
            raise CommandError(f'Greška pri čitanju CSV datoteke: {e}')

        if options['clear']:
            deleted_count, _ = KPDCode.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Obrisano {deleted_count} postojećih KPD šifara.'))

        # Preskoči zaglavlje (prvi red je naslov "KPD 2025", drugi red ima stupce)
        data_rows = []
        header_skipped = False
        
        for row in rows:
            if not row or not row[0].strip():
                continue
            
            code = row[0].strip()
            
            # Preskoči naslovne redove
            if 'KPD' in code.upper():
                continue
            if code.lower() == 'šifra':
                continue
            
            # Dobij naziv iz drugog stupca
            name = row[1].strip() if len(row) > 1 else ''
            
            if code and name:
                data_rows.append((code, name))

        self.stdout.write(f'Pronađeno {len(data_rows)} KPD šifara za uvoz...')

        created_count = 0
        updated_count = 0
        errors = []

        for code, name in data_rows:
            level = self.get_level(code)
            parent_code = self.get_parent_code(code)
            
            try:
                kpd, created = KPDCode.objects.update_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'level': level,
                        'parent_code': parent_code,
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                    
            except Exception as e:
                errors.append(f'{code}: {e}')

        self.stdout.write(self.style.SUCCESS(
            f'Uvoz završen: {created_count} novih, {updated_count} ažuriranih šifara.'
        ))
        
        if errors:
            self.stdout.write(self.style.ERROR(f'Greške ({len(errors)}):'))
            for error in errors[:10]:  # Prikaži prvih 10 grešaka
                self.stdout.write(self.style.ERROR(f'  - {error}'))
            if len(errors) > 10:
                self.stdout.write(self.style.ERROR(f'  ... i još {len(errors) - 10} grešaka'))
