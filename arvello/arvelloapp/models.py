from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
from uuid import uuid4
from django.core.validators import RegexValidator
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

def validate_phone_number(value):
    if not all(char.isdigit() or char == '+' for char in value):
        raise ValidationError(
            ('Telefonski broj može sadržavati samo brojeve i znak +.'),
            params={'value': value},
        )

class Company(models.Model):

    PROVINCES = [
    ("ZAGREBAČKA ŽUPANIJA", "ZAGREBAČKA ŽUPANIJA"),
    ("KRAPINSKO-ZAGORSKA ŽUPANIJA", "KRAPINSKO-ZAGORSKA ŽUPANIJA"),
    ("SISAČKO-MOSLAVAČKA ŽUPANIJA", "SISAČKO-MOSLAVAČKA ŽUPANIJA"),
    ("KARLOVAČKA ŽUPANIJA", "KARLOVAČKA ŽUPANIJA"),
    ("VARAŽDINSKA ŽUPANIJA", "VARAŽDINSKA ŽUPANIJA"),
    ("KOPRIVNIČKO-KRIŽEVAČKA ŽUPANIJA", "KOPRIVNIČKO-KRIŽEVAČKA ŽUPANIJA"),
    ("BJELOVARSKO-BILOGORSKA ŽUPANIJA", "BJELOVARSKO-BILOGORSKA ŽUPANIJA"),
    ("PRIMORSKO-GORANSKA ŽUPANIJA", "PRIMORSKO-GORANSKA ŽUPANIJA"),
    ("LIČKO-SENJSKA ŽUPANIJA", "LIČKO-SENJSKA ŽUPANIJA"),
    ("VIROVITIČKO-PODRAVSKA ŽUPANIJA", "VIROVITIČKO-PODRAVSKA ŽUPANIJA"),
    ("POŽEŠKO-SLAVONSKA ŽUPANIJA", "POŽEŠKO-SLAVONSKA ŽUPANIJA"),
    ("BRODSKO-POSAVSKA ŽUPANIJA", "BRODSKO-POSAVSKA ŽUPANIJA"),
    ("ZADARSKA ŽUPANIJA", "ZADARSKA ŽUPANIJA"),
    ("OSJEČKO-BARANJSKA ŽUPANIJA", "OSJEČKO-BARANJSKA ŽUPANIJA"),
    ("ŠIBENSKO-KNINSKA ŽUPANIJA", "ŠIBENSKO-KNINSKA ŽUPANIJA"),
    ("VUKOVARSKO-SRIJEMSKA ŽUPANIJA", "VUKOVARSKO-SRIJEMSKA ŽUPANIJA"),
    ("SPLITSKO-DALMATINSKA ŽUPANIJA", "SPLITSKO-DALMATINSKA ŽUPANIJA"),
    ("ISTARSKA ŽUPANIJA", "ISTARSKA ŽUPANIJA"),
    ("DUBROVAČKO-NERETVANSKA ŽUPANIJA", "DUBROVAČKO-NERETVANSKA ŽUPANIJA"),
    ("MEĐIMURSKA ŽUPANIJA", "MEĐIMURSKA ŽUPANIJA"),
    ("GRAD ZAGREB", "GRAD ZAGREB"),
    ("INOZEMSTVO / NIJE PRIMJENJIVO", "INOZEMSTVO / NIJE PRIMJENJIVO")
    ]

    clientTypes = [
    ("Fizička osoba", "Fizička osoba"),
    ("Pravna osoba", "Pravna osoba"),
    ]

    vatcountry = ["AF", "AX", "AL", "DZ", "AS", "AD", "AO", "AI", "AQ", "AG", "AR",
    "AM", "AW", "AU", "AT", "AZ", "BS", "BH", "BD", "BB", "BY", "BE",
    "BZ", "BJ", "BM", "BT", "BO", "BQ", "BA", "BW", "BV", "BR", "IO",
    "BN", "BG", "BF", "BI", "CV", "KH", "CM", "CA", "KY", "CF", "TD",
    "CL", "CN", "CX", "CC", "CO", "KM", "CG", "CD", "CK", "CR", "CI",
    "HR", "CU", "CW", "CY", "CZ", "DK", "DJ", "DM", "DO", "EC", "EG",
    "SV", "GQ", "ER", "EE", "ET", "FK", "FO", "FJ", "FI", "FR", "GF",
    "PF", "TF", "GA", "GM", "GE", "DE", "GH", "GI", "GR", "GL", "GD",
    "GP", "GU", "GT", "GG", "GN", "GW", "GY", "HT", "HM", "VA", "HN",
    "HK", "HU", "IS", "IN", "ID", "IR", "IQ", "IE", "IM", "IL", "IT",
    "JM", "JP", "JE", "JO", "KZ", "KE", "KI", "KP", "KR", "KW", "KG",
    "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT", "LU", "MO", "MK",
    "MG", "MW", "MY", "MV", "ML", "MT", "MH", "MQ", "MR", "MU", "YT",
    "MX", "FM", "MD", "MC", "MN", "ME", "MS", "MA", "MZ", "MM", "NA",
    "NR", "NP", "NL", "NC", "NZ", "NI", "NE", "NG", "NU", "NF", "MP",
    "NO", "OM", "PK", "PW", "PS", "PA", "PG", "PY", "PE", "PH", "PN",
    "PL", "PT", "PR", "QA", "RE", "RO", "RU", "RW", "BL", "SH", "KN",
    "LC", "MF", "PM", "VC", "WS", "SM", "ST", "SA", "SN", "RS", "SC",
    "SL", "SG", "SX", "SK", "SI", "SB", "SO", "ZA", "GS", "SS", "ES",
    "LK", "SD", "SR", "SJ", "SZ", "SE", "CH", "SY", "TW", "TJ", "TZ",
    "TH", "TL", "TG", "TK", "TO", "TT", "TN", "TR", "TM", "TC", "TV",
    "UG", "UA", "AE", "GB", "US", "UM", "UY", "UZ", "VU", "VE", "VN",
    "VG", "VI", "WF", "EH", "YE", "ZM", "ZW"]

    clientName = models.CharField(null=True, blank=True, max_length=200)
    addressLine1 = models.CharField(null=True, blank=True, max_length=200)
    town = models.CharField(null=True, blank=True, max_length=200)
    province = models.CharField(choices=PROVINCES, blank=True, max_length=100)
    postalCode = models.CharField(null=True, blank=True, max_length=5)
    phoneNumber = models.CharField(null=True, blank=True, max_length=40, validators=[validate_phone_number])
    emailAddress = models.CharField(null=True, blank=True, max_length=100)
    clientUniqueId = models.CharField(null=True, blank=True, max_length=4, unique=True, validators=[RegexValidator(r'^\d{4}$', 'Idetifikacijski broj klijenta mora sadržavati točno 4 broja.')])
    clientType = models.CharField(choices=clientTypes, blank=True, max_length=40)
    OIB = models.CharField(null=True, blank=True, max_length=11, unique=True, validators=[RegexValidator(r'^\d{11}$', 'OIB mora sadržavati točno 11 broja.')])
    SustavPDVa = models.BooleanField(default=False)
    IBAN = models.CharField(null=True, blank=True, max_length=36)
    uniqueId = models.CharField(null=True, blank=True, max_length=100)
    slug = models.SlugField(max_length=500, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)


    def __str__(self):
        return '{} {} {}'.format(self.clientName, self.province, self.uniqueId)


    def get_absolute_url(self):
        return reverse('settings-detail', kwargs={'slug': self.slug})


    def save(self, *args, **kwargs):
        if self.date_created is None:
            self.date_created = timezone.localtime(timezone.now())
        if self.uniqueId is None:
            self.uniqueId = str(uuid4()).split('-')[4]
            self.slug = slugify('{} {} {}'.format(self.clientName, self.province, self.uniqueId))

        self.slug = slugify('{} {} {}'.format(self.clientName, self.province, self.uniqueId))
        self.last_updated = timezone.localtime(timezone.now())

        super(Company, self).save(*args, **kwargs)

class Client(models.Model):

    PROVINCES = [
    ("ZAGREBAČKA ŽUPANIJA", "ZAGREBAČKA ŽUPANIJA"),
    ("KRAPINSKO-ZAGORSKA ŽUPANIJA", "KRAPINSKO-ZAGORSKA ŽUPANIJA"),
    ("SISAČKO-MOSLAVAČKA ŽUPANIJA", "SISAČKO-MOSLAVAČKA ŽUPANIJA"),
    ("KARLOVAČKA ŽUPANIJA", "KARLOVAČKA ŽUPANIJA"),
    ("VARAŽDINSKA ŽUPANIJA", "VARAŽDINSKA ŽUPANIJA"),
    ("KOPRIVNIČKO-KRIŽEVAČKA ŽUPANIJA", "KOPRIVNIČKO-KRIŽEVAČKA ŽUPANIJA"),
    ("BJELOVARSKO-BILOGORSKA ŽUPANIJA", "BJELOVARSKO-BILOGORSKA ŽUPANIJA"),
    ("PRIMORSKO-GORANSKA ŽUPANIJA", "PRIMORSKO-GORANSKA ŽUPANIJA"),
    ("LIČKO-SENJSKA ŽUPANIJA", "LIČKO-SENJSKA ŽUPANIJA"),
    ("VIROVITIČKO-PODRAVSKA ŽUPANIJA", "VIROVITIČKO-PODRAVSKA ŽUPANIJA"),
    ("POŽEŠKO-SLAVONSKA ŽUPANIJA", "POŽEŠKO-SLAVONSKA ŽUPANIJA"),
    ("BRODSKO-POSAVSKA ŽUPANIJA", "BRODSKO-POSAVSKA ŽUPANIJA"),
    ("ZADARSKA ŽUPANIJA", "ZADARSKA ŽUPANIJA"),
    ("OSJEČKO-BARANJSKA ŽUPANIJA", "OSJEČKO-BARANJSKA ŽUPANIJA"),
    ("ŠIBENSKO-KNINSKA ŽUPANIJA", "ŠIBENSKO-KNINSKA ŽUPANIJA"),
    ("VUKOVARSKO-SRIJEMSKA ŽUPANIJA", "VUKOVARSKO-SRIJEMSKA ŽUPANIJA"),
    ("SPLITSKO-DALMATINSKA ŽUPANIJA", "SPLITSKO-DALMATINSKA ŽUPANIJA"),
    ("ISTARSKA ŽUPANIJA", "ISTARSKA ŽUPANIJA"),
    ("DUBROVAČKO-NERETVANSKA ŽUPANIJA", "DUBROVAČKO-NERETVANSKA ŽUPANIJA"),
    ("MEĐIMURSKA ŽUPANIJA", "MEĐIMURSKA ŽUPANIJA"),
    ("GRAD ZAGREB", "GRAD ZAGREB"),
    ("INOZEMSTVO / NIJE PRIMJENJIVO", "INOZEMSTVO / NIJE PRIMJENJIVO")
    ]

    clientTypes = [
    ("Fizička osoba", "Fizička osoba"),
    ("Pravna osoba", "Pravna osoba"),
    ]

    vatcountry = ["AF", "AX", "AL", "DZ", "AS", "AD", "AO", "AI", "AQ", "AG", "AR",
    "AM", "AW", "AU", "AT", "AZ", "BS", "BH", "BD", "BB", "BY", "BE",
    "BZ", "BJ", "BM", "BT", "BO", "BQ", "BA", "BW", "BV", "BR", "IO",
    "BN", "BG", "BF", "BI", "CV", "KH", "CM", "CA", "KY", "CF", "TD",
    "CL", "CN", "CX", "CC", "CO", "KM", "CG", "CD", "CK", "CR", "CI",
    "HR", "CU", "CW", "CY", "CZ", "DK", "DJ", "DM", "DO", "EC", "EG",
    "SV", "GQ", "ER", "EE", "ET", "FK", "FO", "FJ", "FI", "FR", "GF",
    "PF", "TF", "GA", "GM", "GE", "DE", "GH", "GI", "GR", "GL", "GD",
    "GP", "GU", "GT", "GG", "GN", "GW", "GY", "HT", "HM", "VA", "HN",
    "HK", "HU", "IS", "IN", "ID", "IR", "IQ", "IE", "IM", "IL", "IT",
    "JM", "JP", "JE", "JO", "KZ", "KE", "KI", "KP", "KR", "KW", "KG",
    "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT", "LU", "MO", "MK",
    "MG", "MW", "MY", "MV", "ML", "MT", "MH", "MQ", "MR", "MU", "YT",
    "MX", "FM", "MD", "MC", "MN", "ME", "MS", "MA", "MZ", "MM", "NA",
    "NR", "NP", "NL", "NC", "NZ", "NI", "NE", "NG", "NU", "NF", "MP",
    "NO", "OM", "PK", "PW", "PS", "PA", "PG", "PY", "PE", "PH", "PN",
    "PL", "PT", "PR", "QA", "RE", "RO", "RU", "RW", "BL", "SH", "KN",
    "LC", "MF", "PM", "VC", "WS", "SM", "ST", "SA", "SN", "RS", "SC",
    "SL", "SG", "SX", "SK", "SI", "SB", "SO", "ZA", "GS", "SS", "ES",
    "LK", "SD", "SR", "SJ", "SZ", "SE", "CH", "SY", "TW", "TJ", "TZ",
    "TH", "TL", "TG", "TK", "TO", "TT", "TN", "TR", "TM", "TC", "TV",
    "UG", "UA", "AE", "GB", "US", "UM", "UY", "UZ", "VU", "VE", "VN",
    "VG", "VI", "WF", "EH", "YE", "ZM", "ZW"]

    clientName = models.CharField(null=True, blank=True, max_length=200)
    addressLine1 = models.CharField(null=True, blank=True, max_length=200)
    province = models.CharField(choices=PROVINCES, blank=True, max_length=100)
    postalCode = models.CharField(null=True, blank=True, max_length=5)
    phoneNumber = models.CharField(null=True, blank=True, max_length=40, validators=[validate_phone_number])
    emailAddress = models.CharField(null=True, blank=True, max_length=100)
    clientUniqueId = models.CharField(null=True, blank=True, max_length=4, unique=True, validators=[RegexValidator(r'^\d{4}$', 'Idetifikacijski broj klijenta mora sadržavati točno 4 broja.')])
    clientType = models.CharField(choices=clientTypes, blank=True, max_length=40)
    OIB = models.CharField(null=True, blank=True, max_length=11, unique=True, validators=[RegexValidator(r'^\d{11}$', 'OIB mora sadržavati točno 11 broja.')])
    SustavPDVa = models.BooleanField(default=False)
    VATID = models.CharField(null=True, blank=True, max_length=13, unique=True, validators=[RegexValidator(r'^[A-Za-z0-9]{13}$', 'Porezni identifikacijski broj mora sadržavati točno 13 karaktera, prva dva karaktera moraju biti identifikatori države, a ostalih 11 karaktera moraju biti brojevi koji označavaju entitet.')])
    uniqueId = models.CharField(null=True, blank=True, max_length=100)
    slug = models.SlugField(max_length=500, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)


    def __str__(self):
        return '{} {} {}'.format(self.clientName, self.province, self.uniqueId)


    def get_absolute_url(self):
        return reverse('client-detail', kwargs={'slug': self.slug})


    def save(self, *args, **kwargs):
        if self.date_created is None:
            self.date_created = timezone.localtime(timezone.now())
        if self.uniqueId is None:
            self.uniqueId = str(uuid4()).split('-')[4]
            self.slug = slugify('{} {} {}'.format(self.clientName, self.province, self.VATID))

        self.slug = slugify('{} {} {}'.format(self.clientName, self.province, self.VATID))
        self.last_updated = timezone.localtime(timezone.now())
        

        super(Client, self).save(*args, **kwargs)



class Product(models.Model):
    CURRENCY = [
    ('$', 'USD'),
    ('€', 'EUR'),
    ('£', 'GBP'),
    #Slobodno nadodajte valute
    #Add other currencies freely
    ]

    title = models.CharField(null=True, blank=True, max_length=100)
    description = models.TextField(null=True, blank=True)
    quantity = models.FloatField(null=True, blank=True) #FloatField jer se može dogoditi da klijent želi naručiti 1.5 proizvoda (kruh), ili se može prodavati npr. jabuke po kilogramu
    price = models.FloatField(null=True, blank=True)
    currency = models.CharField(choices=CURRENCY, default='€', max_length=100)
    taxPercent = models.FloatField(null=True, blank=True, default=25)

    uniqueId = models.CharField(null=True, blank=True, max_length=100)
    slug = models.SlugField(max_length=500, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    def price_with_vat(self):
        return round(self.price * (1+(self.taxPercent/100)), 2)
    
    def __str__(self):
        return '{} {}'.format(self.title, self.uniqueId)


    def get_absolute_url(self):
        return reverse('product-detail', kwargs={'slug': self.slug})


    def save(self, *args, **kwargs):
        if self.date_created is None:
            self.date_created = timezone.localtime(timezone.now())
        if self.uniqueId is None:
            self.uniqueId = str(uuid4()).split('-')[4]
            self.slug = slugify('{} {}'.format(self.title, self.uniqueId))

        self.slug = slugify('{} {}'.format(self.title, self.uniqueId))
        self.last_updated = timezone.localtime(timezone.now())

        super(Product, self).save(*args, **kwargs)


class Offer(models.Model):
    title = models.CharField(null=True, blank=True, max_length=100)
    number = models.CharField(null=True, blank=True, max_length=100)
    dueDate = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    client = models.ForeignKey(Client, blank=True, null=True, on_delete=models.SET_NULL)
    product = models.ManyToManyField(Product, blank=True)
    subject = models.ForeignKey(Company, blank=True, null=True, on_delete=models.SET_NULL)
    uniqueId = models.CharField(null=True, blank=True, max_length=100, unique=True)
    slug = models.SlugField(max_length=500, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    def poziv_na_broj(self):
        return "HR 00 " + self.number.replace('/', '-')

    def __str__(self):
        return '{} {}'.format(self.title, self.uniqueId)

    def save(self, *args, **kwargs):
        if self.date_created is None:
            self.date_created = timezone.localtime(timezone.now())
        if self.uniqueId is None:
            self.uniqueId = str(uuid4()).split('-')[4]
            self.slug = slugify('{} {}'.format(self.title, self.uniqueId))

        self.slug = slugify('{} {}'.format(self.title, self.uniqueId))
        self.last_updated = timezone.localtime(timezone.now())

        super(Offer, self).save(*args, **kwargs)

    def price_with_vat(self):
        return round(sum((product.price * (1 + (product.taxPercent / 100))) for product in self.product.all()), 2)

    def sum(self):
        return sum(product.price for product in self.product.all())
    
    def curr(self):
        first_product = self.product.first()
        return first_product.currency


class Invoice(models.Model):
    title = models.CharField(null=True, blank=True, max_length=100)
    number = models.CharField(null=True, blank=True, max_length=100)
    dueDate = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    client = models.ForeignKey(Client, blank=True, null=True, on_delete=models.SET_NULL)
    product = models.ManyToManyField(Product, blank=True)
    subject = models.ForeignKey(Company, blank=True, null=True, on_delete=models.SET_NULL)
    uniqueId = models.CharField(null=True, blank=True, max_length=100, unique=True)
    slug = models.SlugField(max_length=500, unique=True, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    def poziv_na_broj(self):
        return "HR 00 " + self.number.replace('/', '-')

    def __str__(self):
        return '{} {}'.format(self.title, self.uniqueId)

    def save(self, *args, **kwargs):
        if self.date_created is None:
            self.date_created = timezone.localtime(timezone.now())
        if self.uniqueId is None:
            self.uniqueId = str(uuid4()).split('-')[4]
            self.slug = slugify('{} {}'.format(self.title, self.uniqueId))

        self.slug = slugify('{} {}'.format(self.title, self.uniqueId))
        self.last_updated = timezone.localtime(timezone.now())

        super(Invoice, self).save(*args, **kwargs)

    def price_with_vat(self):
        return round(sum((product.price * (1 + (product.taxPercent / 100))) for product in self.product.all()), 2)

    def sum(self):
        return sum(product.price for product in self.product.all())
    
    def curr(self):
        first_product = self.product.first()
        return first_product.currency


