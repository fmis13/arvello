"""
Django settings for arvello project.
"""

from datetime import date
from pathlib import Path
import os
from decouple import config
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-3w)9_3=d$k#05)a((27lpiu=ezzm-uydvx443x3)$x5qx6d9q=')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'crispy_forms',
    'crispy_bootstrap5',
    'localflavor',
    'django_bootstrap5',
    'simple_history',
]

LOCAL_APPS = [
    'arvelloapp',
]

INSTALLED_APPS = THIRD_PARTY_APPS + DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'arvelloapp.middleware.RequestMiddleware',
]

ROOT_URLCONF = 'arvello.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'arvello.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Authentication settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'invoices'
LOGOUT_REDIRECT_URL = 'login'

# Internationalization
LANGUAGE_CODE = 'hr-hr'
TIME_ZONE = 'Europe/Zagreb'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Create media directory if it doesn't exist
if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT)

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms settings
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Security settings for production
if not DEBUG:
    # HTTPS settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    
    # Other security settings
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_BROWSER_XSS_FILTER = True
    

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='user@example.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='password')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool) 


# Logging configuration
"""
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'arvelloapp': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
"""

# AI Chat System Prompt
AI_CHAT_SYSTEM_PROMPT = '''
    Vi ste korisni asistent za računovodstveni softver Arvello. Uvijek govorite na hrvatskom jeziku.
    Arvello je napredni računovodstveni softver koji pomaže malim i srednjim hrvatskim poduzećima u upravljanju njihovim financijama, uključujući fiskalizaciju, podnošenje JOPPD izvještaja te ostale računovodstvene zadatke.

    Strogo se drži idućih pravila:
    1. Odgovaraj isključivo na standardnom hrvatskom jeziku.
    2. Odgovaraj kratko i jasno.
    3. Odgovaraj samo na pitanja vezana uz funkcionalnosti Arvello softvera i računovodstvo te druga pitanja o financijama, porezima itd. Možeš ostati prijateljski nastrojen, ali ne smiješ pretjerano izlaziti izvan okvira računovodstvenog softvera.
    4. Nemoj koristiti stilizirane izraze ili emotikone.
    5. Funkcije su jako korisne za dobivanje podataka iz baze podataka Arvello softvera. Uvijek koristi funkcije za čitanje podataka iz baze podataka kako bi korisniku pružio relevantne informacije.
    6. Nikad nemoj koristiti ID-eve iz baze podataka u odgovorima korisniku. Umjesto toga, koristi razumljive nazive poput "broj računa", "ime klijenta", "naziv proizvoda" itd.
    7. Ako imaš sumnje o značenju korisnikovog upita, postavi dodatna pitanja kako bi razjasnio što korisnik želi.

    Tvoje mogućnosti su trostuke:
    a) Pružanje informacija o funkcionalnostima Arvello softvera te pomoć u računovodstvu.
    b) Čitanje podataka iz baze podataka Arvello softvera kako bi korisniku pružio relevantne informacije.
    c) Mijenjanje podataljaka u bazi podataka Arvello softvera na zahtjev korisnika, uz prethodnu potvrdu korisnika.
    d) Čitanje datoteka koje korisnik priloži u razgovoru kako bi izvukao relevantne informacije.

    KRITIČNO - EFIKASNOST I PARALELNO IZVRŠAVANJE:
    - UVIJEK pozivaj više funkcija PARALELNO kada su nezavisne jedna od druge. Nikad nemoj jednu funkciju čekati da se završi prije nego što pozoveš drugu, osim ako je to apsolutno neophodno zbog ovisnosti podataka.
    - Prije kreiranja računa/ponude, PRVO dohvati sve potrebne podatke (klijente, proizvode, postojeće račune) U JEDNOM PARALELNOM POZIVU.
    - Primjer: Ako korisnik traži 3 računa za 3 klijenta, PRVO pozovi filter_clients_to_string i filter_products_to_string PARALELNO, 
      pa tek onda kreiraj račune.
    - NIKADA ne pokušavaj kreirati račun prije nego što potvrdiš da klijent i proizvod postoje u bazi.
    - Kada radiš više sličnih operacija (npr. 3 računa), pozovi sve propose_ funkcije PARALELNO u istoj iteraciji.
    - Koristi filtere kako bi smanjio broj rezultata prilikom čitanja podataka iz baze. Čak i ako korisnik ne specificira filtere, pokušaj ih zaključiti iz konteksta razgovora. Barem po godini ili imenu klijenta/proizvoda.
    - Osim u konačnom odgovoru, UVIJEK koristi što manji broj riječi u odgovorima za vrijeme pozivanja funkcija.

    Kada koristiš funkcije za čitanje podataka, pokušaj biti efikasan i koristiti filtere kako bi ograničio broj rezultata. Na primjer, prilikom traženja računa, koristi filtere poput datuma, statusa plaćanja, klijenta ili proizvoda.
    Uvijek koristi funkcije za čitanje i pisanje podataka iz baze podataka Arvello softvera. Nikada nemoj izmišljati ili pretpostavljati podatke.
    Nakon što se funkcija izvrši, vidjet ćeš njene rezultate u povijesti chata. Na temelju tih rezultata možeš nastaviti razgovor s korisnikom.
    Najgora stvar koju možeš učiniti pri izražavanju je korištenje ID-eva iz baze podataka. Uvijek koristi razumljive nazive umjesto id brojeva koji nisu vidljivi korisniku.
    
    Pojmovnik:
    - Račun: službeni dokument koji zahtijeva plaćanje do datuma dospijeća.
    - Ponuda: cjenovni prijedlog koji se šalje klijentu - sličan računu ali ne zahtijeva plaćanje.
    - Klijent: osoba ili tvrtka koja prima račun ili ponudu.
    - Subjekt: osoba ili tvrtka koja izdaje račun ili ponudu. Obično po jedna tvrtka po Arvello računu.
    - Proizvod: roba ili usluga navedena na računu ili ponudi.
    - Inventar: popis stavki koje subjekt posjeduje za prodaju ili upotrebu. Služi za evidentiranje stvari u vlasništvu subjekta. 
    - Dobavljač: osoba ili tvrtka od koje subjekt kupuje robu ili usluge.
    - Trošak: izdatak koji subjekt ima, često povezan s dobavljačima.

    TRENUTNI DATUM JE: {current_date}
    '''

# AI Chat Tools Configuration
AI_CHAT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "filter_invoices_to_string",
            "description": "Filtrira račune prema zadanim kriterijima i vraća podatke o njima. Koristi za pretraživanje računa po klijentu, datumu, statusu plaćanja, proizvodu itd. Zbog velikog broja računa, koristiti filtere gdje je to moguće. Umjesto invoice Id, referiraj se na 'broj' računa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Kratki opis (3-5 riječi) što tražiš, npr. 'neplaćeni računi za siječanj' ili 'računi klijenta Horvat'"
                    },
                    "client_id": {
                        "type": ["integer", "null"],
                        "description": "ID klijenta"
                    },
                    "client_name": {
                        "type": ["string", "null"],
                        "description": "Ime klijenta (djelomično podudaranje)"
                    },
                    "subject_id": {
                        "type": ["integer", "null"],
                        "description": "ID subjekta (tvrtke)"
                    },
                    "is_paid": {
                        "type": ["boolean", "null"],
                        "description": "Status plaćanja (true=plaćen, false=neplaćen)"
                    },
                    "due_date_from": {
                        "type": ["string", "null"],
                        "description": "Datum dospijeća od (YYYY-MM-DD)"
                    },
                    "due_date_to": {
                        "type": ["string", "null"],
                        "description": "Datum dospijeća do (YYYY-MM-DD)"
                    },
                    "date_from": {
                        "type": ["string", "null"],
                        "description": "Datum računa od (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": ["string", "null"],
                        "description": "Datum računa do (YYYY-MM-DD)"
                    },
                    "number": {
                        "type": ["string", "null"],
                        "description": "Broj računa (djelomično podudaranje)"
                    },
                    "product_id": {
                        "type": ["integer", "null"],
                        "description": "ID proizvoda (računi koji sadrže taj proizvod)"
                    },
                    "product_title": {
                        "type": ["string", "null"],
                        "description": "Naziv proizvoda (djelomično podudaranje)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "filter_offers_to_string",
            "description": "Filtrira ponude prema zadanim kriterijima i vraća podatke o njima. Ponude su slične računima, ali predstavljaju cjenovne prijedloge koji se šalju klijentima. Za razliku od računa, ponude ne zahtijevaju plaćanje - to su prijedlozi koji mogu, ali ne moraju biti prihvaćeni. Datum isteka (dueDate) na ponudama nema pravne posljedice ako prođe bez plaćanja, za razliku od računa. Koristi za pretraživanje ponuda po klijentu, datumu, proizvodu itd.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Kratki opis (3-5 riječi) što tražiš, npr. 'ponude za klijenta Horvat' ili 'ponude iz siječnja'"
                    },
                    "client_id": {
                        "type": ["integer", "null"],
                        "description": "ID klijenta"
                    },
                    "client_name": {
                        "type": ["string", "null"],
                        "description": "Ime klijenta (djelomično podudaranje)"
                    },
                    "subject_id": {
                        "type": ["integer", "null"],
                        "description": "ID subjekta (tvrtke)"
                    },
                    "due_date_from": {
                        "type": ["string", "null"],
                        "description": "Datum isteka ponude od (YYYY-MM-DD)"
                    },
                    "due_date_to": {
                        "type": ["string", "null"],
                        "description": "Datum isteka ponude do (YYYY-MM-DD)"
                    },
                    "date_from": {
                        "type": ["string", "null"],
                        "description": "Datum ponude od (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": ["string", "null"],
                        "description": "Datum ponude do (YYYY-MM-DD)"
                    },
                    "number": {
                        "type": ["string", "null"],
                        "description": "Broj ponude (djelomično podudaranje)"
                    },
                    "product_id": {
                        "type": ["integer", "null"],
                        "description": "ID proizvoda (ponude koje sadrže taj proizvod)"
                    },
                    "product_title": {
                        "type": ["string", "null"],
                        "description": "Naziv proizvoda (djelomično podudaranje)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_suppliers_to_string",
            "description": "Dohvaća sve dobavljače iz baze podataka. Vraća popis svih dobavljača s njihovim podacima.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Kratki opis (3-5 riječi) što tražiš, npr. 'popis svih dobavljača'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expenses_to_string",
            "description": "Dohvaća sve troškove iz baze podataka. Vraća popis svih troškova s njihovim podacima uključujući iznose, kategorije, dobavljače i porezne podatke.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Kratki opis (3-5 riječi) što tražiš, npr. 'svi troškovi' ili 'pregled troškova'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_subjects_to_string",
            "description": "Dohvaća sve subjekte (tvrtke) iz baze podataka. Vraća popis svih tvrtki/subjekata s njihovim podacima.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Kratki opis (3-5 riječi) što tražiš, npr. 'popis subjekata'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_inventory_to_string",
            "description": "Dohvaća sve stavke inventara iz baze podataka. Vraća popis svih stavki inventara s količinama.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Kratki opis (3-5 riječi) što tražiš, npr. 'stanje inventara'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "filter_clients_to_string",
            "description": "Filtrira klijente prema zadanim kriterijima i vraća podatke o njima. Koristi za pretraživanje klijenata po imenu ili županiji.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Kratki opis (3-5 riječi) što tražiš, npr. 'klijenti iz Zagreba' ili 'svi klijenti'"
                    },
                    "name": {
                        "type": ["string", "null"],
                        "description": "Ime klijenta (djelomično podudaranje)"
                    },
                    "province": {
                        "type": ["string", "null"],
                        "description": "Županija klijenta (djelomično podudaranje)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "filter_products_to_string",
            "description": "Filtrira proizvode prema zadanim kriterijima i vraća podatke o njima. Koristi za pretraživanje proizvoda po nazivu ili rasponu cijena.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Kratki opis (3-5 riječi) što tražiš, npr. 'proizvodi do 100€' ili 'svi proizvodi'"
                    },
                    "title": {
                        "type": ["string", "null"],
                        "description": "Naziv proizvoda (djelomično podudaranje)"
                    },
                    "price_min": {
                        "type": ["number", "null"],
                        "description": "Minimalna cijena proizvoda"
                    },
                    "price_max": {
                        "type": ["number", "null"],
                        "description": "Maksimalna cijena proizvoda"
                    },
                    "currency": {
                        "type": ["string", "null"],
                        "description": "Valuta (€, $, £)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "filter_change_history_to_string",
            "description": "Dohvaća povijest promjena za određeni model. Koristi za praćenje tko je i kada mijenjao podatke.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Kratki opis (3-5 riječi) što tražiš, npr. 'promjene na računima' ili 'sve promjene danas'"
                    },
                    "model_name": {
                        "type": ["string", "null"],
                        "description": "Naziv modela za koji se traži povijest (Invoice, Client, Product, Expense, Supplier, Company, Inventory, Employee, Salary)"
                    },
                    "date_from": {
                        "type": ["string", "null"],
                        "description": "Datum od kojeg se traži povijest (YYYY-MM-DD)"
                    },
                    "date_to": {
                        "type": ["string", "null"],
                        "description": "Datum do kojeg se traži povijest (YYYY-MM-DD)"
                    },
                    "object_id": {
                        "type": ["integer", "null"],
                        "description": "ID objekta za koji se traži povijest"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_employees_to_string",
            "description": "Dohvaća sve zaposlenike iz baze podataka. Vraća popis svih zaposlenika s njihovim osobnim podacima, podacima o zaposlenju, satnici, poreznim koeficijentima i mirovinskim stupovima.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Kratki opis (3-5 riječi) što tražiš, npr. 'popis zaposlenika' ili 'svi zaposlenici'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_salaries_to_string",
            "description": "Dohvaća sve plaće iz baze podataka. Vraća popis svih plaća s detaljima o bruto i neto iznosima, doprinosima, porezima, satima rada, godišnjem odmoru, bolovanju, prekovremenom radu i neoporezivim primicima.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Kratki opis (3-5 riječi) što tražiš, npr. 'popis plaća' ili 'sve plaće'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_inventory_add",
            "description": "PREDLAŽE dodavanje nove stavke u inventar. NE izvršava promjenu odmah - korisnik mora potvrditi akciju. Koristi ovu funkciju kada korisnik želi dodati novu stavku u inventar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Naziv stavke inventara koju treba dodati"
                    },
                    "quantity": {
                        "type": "number",
                        "description": "Količina stavke"
                    },
                    "subject_name": {
                        "type": ["string", "null"],
                        "description": "Naziv subjekta/tvrtke kojoj se dodaje stavka (djelomično podudaranje)"
                    },
                    "subject_id": {
                        "type": ["integer", "null"],
                        "description": "ID subjekta/tvrtke (alternativa nazivu)"
                    }
                },
                "required": ["title", "quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_inventory_remove",
            "description": "PREDLAŽE uklanjanje stavke iz inventara. NE izvršava promjenu odmah - korisnik mora potvrditi akciju. Koristi ovu funkciju kada korisnik želi ukloniti stavku iz inventara.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_title": {
                        "type": ["string", "null"],
                        "description": "Naziv stavke inventara koju treba ukloniti (djelomično podudaranje)"
                    },
                    "item_id": {
                        "type": ["integer", "null"],
                        "description": "ID stavke inventara (alternativa nazivu)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_inventory_update",
            "description": "PREDLAŽE promjenu postojeće stavke inventara (naziv ili količinu). NE izvršava promjenu odmah - korisnik mora potvrditi akciju. Koristi ovu funkciju kada korisnik želi promijeniti podatke o stavci inventara.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_title": {
                        "type": ["string", "null"],
                        "description": "Trenutni naziv stavke inventara koju treba promijeniti (djelomično podudaranje)"
                    },
                    "item_id": {
                        "type": ["integer", "null"],
                        "description": "ID stavke inventara (alternativa nazivu)"
                    },
                    "new_title": {
                        "type": ["string", "null"],
                        "description": "Novi naziv stavke (ako se mijenja)"
                    },
                    "new_quantity": {
                        "type": ["number", "null"],
                        "description": "Nova količina stavke (ako se mijenja)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_invoice_add",
            "description": "PREDLAŽE kreiranje novog računa. NE izvršava promjenu odmah - korisnik mora potvrditi akciju. Račun je službeni dokument koji zahtijeva plaćanje do datuma dospijeća. Prije pozivanja ove funkcije, provjeri postojeće račune s filter_invoices_to_string da vidiš konvenciju numeriranja koja se koristi, te provjeri dostupne proizvode s filter_products_to_string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {
                        "type": "string",
                        "description": "Broj računa - jedinstveni identifikator. Uobičajena hrvatska praksa je format poput '1/1/1' (broj/poslovni prostor/naplatni uređaj) ili datumski format poput '2026-001' (godina-sekvencijalni broj). UVIJEK provjeri postojeće račune s filter_invoices_to_string kako bi pratio ustaljenu konvenciju numeriranja koju koristi ovo poduzeće."
                    },
                    "client_name": {
                        "type": ["string", "null"],
                        "description": "Ime klijenta kojem se izdaje račun (djelomično podudaranje). Klijent je kupac/primatelj računa."
                    },
                    "client_id": {
                        "type": ["integer", "null"],
                        "description": "ID klijenta ako je poznat (alternativa imenu)"
                    },
                    "subject_name": {
                        "type": ["string", "null"],
                        "description": "Naziv subjekta/tvrtke koja izdaje račun (djelomično podudaranje). Subjekt je prodavatelj/izdavatelj računa."
                    },
                    "subject_id": {
                        "type": ["integer", "null"],
                        "description": "ID subjekta/tvrtke ako je poznat (alternativa nazivu)"
                    },
                    "date": {
                        "type": ["string", "null"],
                        "description": "Datum računa u formatu YYYY-MM-DD (npr. '2026-01-29'). Ako nije naveden, koristi se današnji datum."
                    },
                    "due_date": {
                        "type": ["string", "null"],
                        "description": "Datum dospijeća plaćanja u formatu YYYY-MM-DD (npr. '2026-02-13'). Uobičajeno je 15-30 dana nakon datuma računa. Ako nije naveden, postavlja se na 15 dana od datuma računa."
                    },
                    "title": {
                        "type": ["string", "null"],
                        "description": "Naslov/opis računa (opcionalno, maksimalno 30 znakova)"
                    },
                    "notes": {
                        "type": ["string", "null"],
                        "description": "Dodatne napomene koje će se prikazati na računu (opcionalno)"
                    },
                    "products": {
                        "type": "array",
                        "description": "Lista proizvoda/usluga na računu. OBAVEZNO - račun mora imati barem jedan proizvod. Format: [{\"product_name\": \"Naziv proizvoda\", \"quantity\": 1, \"discount\": 0, \"rabat\": 0}]. Koristi filter_products_to_string da pronađeš točne nazive dostupnih proizvoda.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_name": {
                                    "type": "string",
                                    "description": "Naziv proizvoda (djelomično podudaranje)"
                                },
                                "quantity": {
                                    "type": "number",
                                    "description": "Količina proizvoda (zadano: 1)"
                                },
                                "discount": {
                                    "type": "number",
                                    "description": "Postotak popusta (0-100, zadano: 0)"
                                },
                                "rabat": {
                                    "type": "number",
                                    "description": "Postotak rabata (0-100, zadano: 0)"
                                }
                            }
                        }
                    }
                },
                "required": ["number", "products"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_offer_add",
            "description": "PREDLAŽE kreiranje nove ponude. NE izvršava promjenu odmah - korisnik mora potvrditi akciju. Ponuda je cjenovni prijedlog koji se šalje klijentu - NIJE račun i ne zahtijeva plaćanje. Datum isteka na ponudi nema pravne posljedice ako prođe bez prihvaćanja. Ponude se mogu pretvoriti u račune kada ih klijent prihvati. Prije pozivanja ove funkcije, provjeri postojeće ponude s filter_offers_to_string da vidiš konvenciju numeriranja koja se koristi, te provjeri dostupne proizvode s filter_products_to_string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {
                        "type": "string",
                        "description": "Broj ponude - jedinstveni identifikator. Uobičajena hrvatska praksa je slična računima: 'P-2026-001' (P za ponuda + godina + sekvencijalni broj) ili isti format kao računi. UVIJEK provjeri postojeće ponude s filter_offers_to_string kako bi pratio ustaljenu konvenciju numeriranja koju koristi ovo poduzeće."
                    },
                    "client_name": {
                        "type": ["string", "null"],
                        "description": "Ime klijenta kojem se šalje ponuda (djelomično podudaranje). Klijent je potencijalni kupac. Provjeri kupce s filter_clients_to_string ako nisi siguran u točan naziv."
                    },
                    "client_id": {
                        "type": ["integer", "null"],
                        "description": "ID klijenta ako je poznat (alternativa imenu)"
                    },
                    "subject_name": {
                        "type": ["string", "null"],
                        "description": "Naziv subjekta/tvrtke koja izdaje ponudu (djelomično podudaranje). Subjekt je prodavatelj/ponuditelj. Provjeri subjekte s filter_subjects_to_string ako nisi siguran u točan naziv."
                    },
                    "subject_id": {
                        "type": ["integer", "null"],
                        "description": "ID subjekta/tvrtke ako je poznat (alternativa nazivu)"
                    },
                    "date": {
                        "type": ["string", "null"],
                        "description": "Datum ponude u formatu YYYY-MM-DD (npr. '2026-01-29'). Ako nije naveden, koristi se današnji datum."
                    },
                    "due_date": {
                        "type": ["string", "null"],
                        "description": "Datum isteka ponude u formatu YYYY-MM-DD (npr. '2026-02-28'). Ovo je datum do kojeg ponuda vrijedi. Uobičajeno je 30 dana nakon datuma ponude. Ako nije naveden, postavlja se na 30 dana od datuma ponude."
                    },
                    "title": {
                        "type": ["string", "null"],
                        "description": "Naslov/opis ponude (opcionalno, maksimalno 30 znakova)"
                    },
                    "notes": {
                        "type": ["string", "null"],
                        "description": "Dodatne napomene koje će se prikazati na ponudi (opcionalno)"
                    },
                    "products": {
                        "type": "array",
                        "description": "Lista proizvoda/usluga na ponudi. OBAVEZNO - ponuda mora imati barem jedan proizvod. Format: [{\"product_name\": \"Naziv proizvoda\", \"quantity\": 1, \"discount\": 0, \"rabat\": 0}]. Koristi filter_products_to_string da pronađeš točne nazive dostupnih proizvoda.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_name": {
                                    "type": "string",
                                    "description": "Naziv proizvoda (djelomično podudaranje)"
                                },
                                "quantity": {
                                    "type": "number",
                                    "description": "Količina proizvoda (zadano: 1)"
                                },
                                "discount": {
                                    "type": "number",
                                    "description": "Postotak popusta (0-100, zadano: 0)"
                                },
                                "rabat": {
                                    "type": "number",
                                    "description": "Postotak rabata (0-100, zadano: 0)"
                                }
                            }
                        }
                    }
                },
                "required": ["number", "products"]
            }
        }
    }
]