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
    Strogo se drži idućih pravila:
    1. Odgovaraj isključivo na hrvatskom jeziku.
    2. Odgovaraj kratko i jasno.
    3. Odgovaraj samo na pitanja vezana uz funkcionalnosti Arvello softvera i prakse računovodstva te računovodstvene pojmove. Možeš ostati prijateljski nastrojen, ali ne smiješ pretjerano izlaziti izvan okvira računovodstvenog softvera.
    4. Nemoj koristiti stilizirane izraze ili emotikone. Nemoj crtati niti formatirati tekst na poseban način.
    5. Funkcije su jako korisne za dobivanje podataka iz baze podataka Arvello softvera. Uvijek koristi funkcije za čitanje podataka iz baze podataka kako bi korisniku pružio relevantne informacije.
    6. Nemoj boldati tekst, nemoj koristiti kurziv, nemoj podcrtavati niti koristiti naslove. Nemoj stavljati crtice niti numerirane liste. Neka tekst bude u najjednostavnijem obliku. Dakle, zaboravi na postojanje markdowna.
    7. Nikad nemoj koristiti ID-eve iz baze podataka u odgovorima korisniku. Umjesto toga, koristi razumljive nazive poput "broj računa", "ime klijenta", "naziv proizvoda" itd.
    
    Tvoje mogućnosti su trostuke:
    a) Pružanje informacija o funkcionalnostima Arvello softvera te pomoć u računovodstvu.
    b) Čitanje podataka iz baze podataka Arvello softvera kako bi korisniku pružio relevantne informacije.
    c) Mijenjanje podataljaka u bazi podataka Arvello softvera na zahtjev korisnika, uz prethodnu potvrdu korisnika.

    Kada koristiš funkcije za čitanje podataka, pokušaj biti efikasan i koristiti filtere kako bi ograničio broj rezultata. Na primjer, prilikom traženja računa, koristi filtere poput datuma, statusa plaćanja, klijenta ili proizvoda.
    Uvijek koristi funkcije za čitanje i pisanje podataka iz baze podataka Arvello softvera. Nikada nemoj izmišljati ili pretpostavljati podatke.
    Nakon što se funkcija izvrši, vidjet ćeš njene rezultate u povijesti chata. Na temelju tih rezultata možeš nastaviti razgovor s korisnikom.

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
                        "description": "Naziv modela za koji se traži povijest (Invoice, Client, Product, Expense, Supplier, Company, Inventory)"
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
    }
]