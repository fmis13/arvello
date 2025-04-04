from django.core.management.base import BaseCommand
from arvelloapp.models import LocalIncomeTax
from arvelloapp.utils.text_utils import standardize_city_name

class Command(BaseCommand):
    help = 'Standardizira imena gradova u tablici poreznih stopa'

    def handle(self, *args, **options):
        updated = 0
        for tax in LocalIncomeTax.objects.all():
            std_name = standardize_city_name(tax.city_name)
            if std_name != tax.city_name:
                tax.city_name = std_name
                tax.save()
                updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Uspješno standardizirano {updated} imena gradova')
        )
