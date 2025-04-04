from django.core.management.base import BaseCommand
from arvelloapp.models import NonTaxableAdditionLimit

class Command(BaseCommand):
    help = 'Učitava neoporezive dodatke plaći iz podataka Porezne uprave'

    def handle(self, *args, **options):
        # Brisanje postojećih podataka
        NonTaxableAdditionLimit.objects.all().delete()
        
        # Definiranje neoporezivih dodataka
        additions = [
            # DNEVNICE I NAKNADE
            {
                'code': 'D1', 
                'description': 'Dnevnice za službeno putovanje u tuzemstvu (>12h)',
                'monthly_limit': None,
                'yearly_limit': None,
                'category': 'DNEVNICE'
            },
            {
                'code': 'D2', 
                'description': 'Dnevnice za službeno putovanje u tuzemstvu (8-12h)',
                'monthly_limit': None,
                'yearly_limit': None,
                'category': 'DNEVNICE'
            },
            # NAKNADE TROŠKOVA
            {
                'code': 'NT1', 
                'description': 'Naknade prijevoznih troškova na službenom putovanju',
                'monthly_limit': None,
                'yearly_limit': None,
                'category': 'NAKNADE TROŠKOVA'
            },
            {
                'code': 'NT2', 
                'description': 'Naknade troškova noćenja na službenom putovanju',
                'monthly_limit': None,
                'yearly_limit': None,
                'category': 'NAKNADE TROŠKOVA'
            },
            {
                'code': 'NT3', 
                'description': 'Naknade troškova prijevoza na posao i s posla',
                'monthly_limit': None,
                'yearly_limit': None,
                'category': 'NAKNADE TROŠKOVA'
            },
            {
                'code': 'NT6', 
                'description': 'Novčane paušalne naknade za podmirivanje troškova prehrane',
                'monthly_limit': 100,
                'yearly_limit': 1200,
                'category': 'NAKNADE TROŠKOVA'
            },
            # OTPREMNINE, DAROVI, NAGRADE
            {
                'code': 'OD1', 
                'description': 'Otpremnine prilikom odlaska u mirovinu',
                'monthly_limit': None,
                'yearly_limit': 1500,
                'category': 'OTPREMNINE I NAGRADE'
            },
            {
                'code': 'OD4', 
                'description': 'Prigodne nagrade (božićnica, regres i sl.)',
                'monthly_limit': None,
                'yearly_limit': 700,
                'category': 'OTPREMNINE I NAGRADE'
            },
            {
                'code': 'OD5', 
                'description': 'Dar u naravi',
                'monthly_limit': None,
                'yearly_limit': 133,
                'category': 'OTPREMNINE I NAGRADE'
            },
            {
                'code': 'OD7', 
                'description': 'Nagrade za radne rezultate',
                'monthly_limit': None,
                'yearly_limit': 1200,
                'category': 'OTPREMNINE I NAGRADE'
            },
            # POTPORE
            {
                'code': 'P1', 
                'description': 'Potpora za novorođenče',
                'monthly_limit': None,
                'yearly_limit': 1500,
                'category': 'POTPORE'
            },
            {
                'code': 'P5', 
                'description': 'Potpora zbog bolovanja dužeg od 90 dana',
                'monthly_limit': None,
                'yearly_limit': 600,
                'category': 'POTPORE'
            },
            # JUBILARNE NAGRADE
            {
                'code': 'JN10', 
                'description': 'Jubilarna nagrada - 10 godina staža',
                'monthly_limit': None,
                'yearly_limit': 300,
                'category': 'JUBILARNE NAGRADE'
            },
            {
                'code': 'JN15', 
                'description': 'Jubilarna nagrada - 15 godina staža',
                'monthly_limit': None,
                'yearly_limit': 360,
                'category': 'JUBILARNE NAGRADE'
            },
            {
                'code': 'JN20', 
                'description': 'Jubilarna nagrada - 20 godina staža',
                'monthly_limit': None,
                'yearly_limit': 420,
                'category': 'JUBILARNE NAGRADE'
            },
            # Dodajte i ostale dodatke prema tablici
        ]
        
        # Stvaranje zapisa u bazi
        for addition in additions:
            NonTaxableAdditionLimit.objects.create(**addition)
            
        self.stdout.write(self.style.SUCCESS(f'Uspješno učitano {len(additions)} neoporezivih dodataka'))
