from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, FileResponse, JsonResponse, Http404
from django.core.cache import cache
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.db.models import Sum, Q, Count
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.views.generic import FormView
from django.utils import timezone
from django.apps import apps
from io import BytesIO
from .forms import *
import requests
import json
import base64
from barcode import Code128
from barcode.writer import SVGWriter
from datetime import datetime, date
from calendar import monthrange
import calendar
from django.utils import timezone
from decimal import Decimal
from simple_history.utils import get_history_model_for_model
from .utils.salary_calculator import update_salary_with_calculations
import logging
from .utils.payslip_context import get_payslip_context 
import tempfile
import os
import re
import pandas as pd
from decimal import Decimal, InvalidOperation
from .utils.joppd_generator import generate_joppd_xml, validate_joppd_xml, mark_salaries_as_reported
from django.template.loader import render_to_string, get_template
from weasyprint import HTML, CSS
from .utils.email_utils import send_email_with_attachment
from django.conf import settings
import os
from django.utils.timezone import now

logger = logging.getLogger(__name__)

def anonymous_required(function=None):
    # Dekorator koji zahtijeva da korisnik bude anoniman (neprijavljen)
    def _dec(view_function):
        def _view(request, *args, **kwargs):
            if request.user.is_authenticated:
                # Ako je korisnik prijavljen, preusmjeri ga na stranicu s računima
                return redirect('invoices')
            # Inače, izvrši originalnu view funkciju
            return view_function(request, *args, **kwargs)
        return _view

    if function:
        return _dec(function)
        return _dec(function)
    return _dec

def loginredir(request):
    # Preusmjerava na stranicu za prijavu
    return redirect('/account/login')

@login_required
def select_subject(request):
    # Prikazuje stranicu za odabir subjekta (tvrtke)
    companies = Company.objects.all()
    return render(request, 'selectSubject.html', {'companies': companies})

@login_required
def products(request):
    # Prikazuje stranicu s proizvodima/uslugama i omogućuje dodavanje novih
    context = {}
    products = Product.objects.all()
    context['product'] = products

    if request.method == 'GET':
        # Ako je GET zahtjev, prikaži praznu formu
        form = ProductForm()
        context['form'] = form
        return render(request, 'products.html', context)

    if request.method == 'POST':
        # Ako je POST zahtjev, obradi podatke iz forme
        form = ProductForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Ako je forma ispravna, spremi proizvod
            form.save()
            messages.success(request, 'Nadoan je novi proizvod/usluga')
            return redirect('products')
        else:
            # Ako forma nije ispravna, prikaži greške
            messages.error(request, 'Problem pri obradi zahtjeva')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('products')
    else:
        # Ako nije ni GET ni POST (što je rijetko), prikaži praznu formu
        form = ProductForm()

    return render(request, 'products.html', {'form': form}, context)

@login_required
def invoices(request):
    # Prikazuje stranicu s računima i omogućuje dodavanje novih (jednostavna forma)
    context = {}
    invoices = Invoice.objects.all()
    
    context['invoices'] = invoices

    if request.method == 'GET':
        # Ako je GET zahtjev, prikaži praznu formu
        form = InvoiceForm()
        context['form'] = form
        return render(request, 'invoices.html', context)

    if request.method == 'POST':
        # Ako je POST zahtjev, obradi podatke iz forme
        form = InvoiceForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Ako je forma ispravna, spremi račun
            form.save()
            messages.success(request, 'Nadodan je novi račun')
            return redirect('invoices')
        else:
            # Ako forma nije ispravna, prikaži greške
            messages.error(request, 'Problem pri obradi zahtjeva')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('invoices')
    else:
        # Ako nije ni GET ni POST, prikaži praznu formu
        form = InvoiceForm()

    return render(request, 'invoices.html', {'form': form}, context)

@login_required
def create_invoice(request):
    """Kreira novi račun s više stavki (proizvoda/usluga)."""
    if request.method == 'POST':
        # Obradi podatke iz glavne forme i formseta za stavke
        invoice_form = InvoiceForm(request.POST)
        invoice_formset = InvoiceProductFormSet(request.POST)

        if invoice_form.is_valid() and invoice_formset.is_valid():
            # Ako su obje forme ispravne, spremi račun i stavke
            invoice = invoice_form.save()
            invoice_products = []
            total = Decimal('0.00')

            for invoice_form in invoice_formset:
                # Spremi svaku stavku računa
                invoice_product = invoice_form.save(commit=False)
                invoice_product.invoice = invoice

                # Provjeri i konvertiraj podatke
                try:
                    product_price = Decimal(str(invoice_product.product.price))
                    product_quantity = Decimal(str(invoice_product.quantity))
                except (ValueError, TypeError) as e:
                    messages.error(request, f"Greška u podacima stavke: {e}")
                    return redirect('create_invoice')

                # Izračunaj ukupni iznos
                total += product_price * product_quantity
                invoice_products.append(invoice_product)

            # Spremi ukupan iznos na račun
            invoice.total = total
            invoice.save()

            # Spremi sve stavke računa
            for invoice_product in invoice_products:
                invoice_product.save()

            messages.success(request, 'Nadodan je novi račun')
            return redirect('invoices')

        # Ako formset nije ispravan, prikaži greške
        if not invoice_formset.is_valid():
            print(invoice_formset.errors)
            messages.error(request, 'Problem pri obradi zahtjeva')
            for field, errors in invoice_formset.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    else:
        # Ako je GET zahtjev, prikaži prazne forme
        invoice_form = InvoiceForm()
        invoice_formset = InvoiceProductFormSet(queryset=InvoiceProduct.objects.none())

    # Prazan formset za dinamičko dodavanje stavki na frontendu
    empty_form = InvoiceProductFormSet(queryset=InvoiceProduct.objects.none())
    context = {
        'invoice_form': invoice_form,
        'invoice_formset': invoice_formset,
        'empty_form': empty_form,
    }

    return render(request, 'makeinvoice.html', context)


@login_required
def export_inventory_to_excel(request):
    # Izvozi inventar u Excel datoteku
    inventory_items = Inventory.objects.all()

    # Pripremi podatke za DataFrame
    data = []
    for item in inventory_items:
        data.append({
            'Naziv': item.title,
            'Količina': item.quantity,
            'Datum dodavanja': item.date_created.strftime('%Y-%m-%d %H:%M:%S'),
            'Zadnje ažuriranje': item.last_updated.strftime('%Y-%m-%d %H:%M:%S'),
            'Subjekt': item.subject.clientName if item.subject else '',
        })

    # Kreiraj DataFrame
    df = pd.DataFrame(data)

    # Kreiraj privremenu Excel datoteku
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        excel_path = tmp.name
        df.to_excel(excel_path, index=False)

    # Otvori datoteku za čitanje i pripremi odgovor
    with open(excel_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="inventory.xlsx"'

    # Obriši privremenu datoteku
    os.remove(excel_path)

    return response

@login_required
def create_offer(request):
    # Kreira novu ponudu s više stavki (proizvoda/usluga)
    if request.method == 'POST':
        # Ako je POST zahtjev, obradi podatke iz glavne forme i formseta za stavke
        offer_form = OfferForm(request.POST)
        offer_formset = OfferProductFormSet(request.POST)

        if offer_form.is_valid() and offer_formset.is_valid():
            # Ako su obje forme ispravne, spremi ponudu i stavke
            offer = offer_form.save()
            offer_products = []
            total = 0
            for offer_form in offer_formset:
                # Spremi svaku stavku ponude
                offer_product = offer_form.save(commit=False)
                offer_product.offer = offer
                offer_product.product = offer_form.cleaned_data["product"]
                total += Decimal(offer_product.product.price) * offer_product.quantity # Izračunaj ukupni iznos (vjerojatno treba doraditi)
                offer_products.append(offer_product)

            # Spremi ukupan iznos na ponudu (vjerojatno treba doraditi)
            offer.total = total
            offer.save()

            # Spremi sve stavke ponude
            for offer_product in offer_products:
                offer_product.save()
            messages.success(request, 'Nadodana je nova ponuda')
            return redirect('offers')
        if not offer_formset.is_valid():
            # Ako formset nije ispravan, prikaži greške
            logger.error(f"Offer formset errors: {offer_formset.errors}")
            messages.error(request, 'Problem pri obradi zahtjeva')
            for field, errors in offer_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Ako je GET zahtjev, prikaži prazne forme
        offer_form = OfferForm()
        offer_formset = OfferProductFormSet(queryset=OfferProduct.objects.none())

    # Prazan formset za dinamičko dodavanje stavki na frontendu
    empty_form = OfferProductFormSet(queryset=OfferProduct.objects.none())
    context = {
        'offer_form': offer_form,
        'offer_formset': offer_formset,
        'empty_form': empty_form,
    }

    return render(request, 'makeoffer.html', context)

@login_required
def companies(request):
    # Prikazuje stranicu s tvrtkama/subjektima i omogućuje dodavanje novih
    context = {}
    companies = Company.objects.all()
    
    context['companies'] = companies

    if request.method == 'GET':
        # Ako je GET zahtjev, prikaži praznu formu
        form = CompanyForm()
        context['form'] = form
        return render(request, 'companies.html', context)

    if request.method == 'POST':
        # Ako je POST zahtjev, obradi podatke iz forme
        form = CompanyForm(request.POST, request.FILES)
        if form.errors:
                # Ispiši greške forme u konzolu za debugiranje
                logger.error(f"Greška s validacijom forme: {form.errors}")
        
        if form.is_valid():
            # Ako je forma ispravna, spremi tvrtku
            form.save()
            messages.success(request, 'Nadodan je novi subjekt')
            return redirect('companies')
        else:
            # Ako forma nije ispravna, prikaži greške
            messages.error(request, 'Problem pri obradi zahtjeva')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('companies')
    else:
        # Ako nije ni GET ni POST, prikaži praznu formu
        form = CompanyForm()

    return render(request, 'companies.html', {'form': form}, context)

@login_required
def offers(request):
    # Prikazuje stranicu s ponudama i omogućuje dodavanje novih (jednostavna forma)
    context = {}
    offers = Offer.objects.all()
    
    context['offers'] = offers

    if request.method == 'GET':
        # Ako je GET zahtjev, prikaži praznu formu
        form = OfferForm()
        context['form'] = form
        return render(request, 'offers.html', context)

    if request.method == 'POST':
        # Ako je POST zahtjev, obradi podatke iz forme
        form = OfferForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Ako je forma ispravna, spremi ponudu
            form.save()
            messages.success(request, 'Nadodana je nova ponuda')
            return redirect('offers')
        else:
            # Ako forma nije ispravna, prikaži greške
            messages.error(request, 'Problem pri obradi zahtjeva')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('offers')
    else:
        # Ako nije ni GET ni POST, prikaži praznu formu
        form = OfferForm()

    return render(request, 'offers.html', {'form': form}, context)


@login_required
def clients(request):
    # Prikazuje stranicu s klijentima i omogućuje dodavanje novih
    context = {}
    clients = Client.objects.all()
    
    context['clients'] = clients

    if request.method == 'GET':
        # Ako je GET zahtjev, prikaži praznu formu
        form = ClientForm()
        context['form'] = form
        return render(request, 'clients.html', context)

    if request.method == 'POST':
        # Ako je POST zahtjev, obradi podatke iz forme
        form = ClientForm(request.POST, request.FILES)

        if form.is_valid():
            # Ako je forma ispravna, spremi klijenta
            form.save()

            messages.success(request, 'Nadodan je novi klijent')
            return redirect('clients')
        else:
            # Ako forma nije ispravna, prikaži greške
            messages.error(request, 'Problem pri obradi zahtjeva')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('clients')


    return render(request, 'clients.html', context)

@anonymous_required
def login(request):
    # Prikazuje stranicu za prijavu korisnika
    if request.user.is_authenticated:
        # Ako je korisnik već prijavljen, preusmjeri ga
        return redirect('invoices')  # preusmjeri na račune ako je već prijavljen
    context = {}
    if request.method == 'GET':
        # Ako je GET zahtjev, prikaži formu za prijavu
        form = UserLoginForm()
        context['form'] = form
        return render(request, 'login.html', context)

    if request.method == 'POST':
        # Ako je POST zahtjev, obradi podatke za prijavu
        form = UserLoginForm(request.POST)

        username = request.POST['username']
        password = request.POST['password']

        # Autentificiraj korisnika
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            # Ako je autentifikacija uspješna, prijavi korisnika
            auth.login(request, user)
            return redirect('/invoices')
        else:
            # Ako autentifikacija nije uspješna, prikaži grešku
            context['form'] = form
            messages.error(request, 'Netočne vjerodajnice')
            return redirect('login')


    return render(request, 'login.html', context)

@login_required
def invoice_pdf(request, pk):
    # Generira PDF prikaz računa s HUB3 barkodom
    invoice = get_object_or_404(Invoice, pk=pk)
    subject = invoice.subject
    product = InvoiceProduct.objects.filter(invoice=invoice)
    client = invoice.client
    
    # URL za generiranje HUB3 barkoda
    url = "https://hub3.bigfish.software/api/v2/barcode"
    headers = {'Content-Type': 'application/json'}
    
    # Podaci za HUB3 barkod
    data = {
        "renderer": "image",
        "options": {
            "format": "png",
            "color": "#000000",
            "bgColor": "#ffffff",
            "scale": 3,
            "ratio": 3
        },
        "data": {
            "amount": int(invoice.total100()), # Iznos u centima
            "currency": invoice.currtext(), # Valuta (npr. EUR)
            "sender": {
                "name": client.clientName,
                "street": client.addressLine1,
                "place": client.postalCode + " " + client.province,
            },
            "receiver": {
                "name": subject.clientName[:25], # Ograničenje duljine imena primatelja
                "street": subject.addressLine1,
                "place": subject.postalCode + " " + subject.province,
                "iban": subject.IBAN,
                "model": "00",
                "reference": invoice.client.clientUniqueId + "-" + invoice.number.replace('/', '-'), # Poziv na broj
            },
            "purpose": "", # Svrha plaćanja (opcionalno)
            "description": "Uplata po računu " + invoice.number, # Opis plaćanja
        }
    }
    
    # Pošalji zahtjev za generiranje barkoda
    response = requests.post(url, headers=headers, data=json.dumps(data))
    # Kodiraj sliku barkoda u base64 za prikaz u HTML-u
    barcode_image = base64.b64encode(response.content).decode()
    print(response.status_code) # Ispis statusa odgovora za debugiranje
    #print(response.content) # Ispis sadržaja odgovora za debugiranje
    
    # Renderiraj HTML predložak s podacima računa i barkodom
    return render(request, 'invoice_export_view.html', {'invoice': invoice, 'products': product, 'client': client, 'subject': subject, 'barcode_image': barcode_image})

@login_required
def offer_pdf(request, pk):
    # Generira PDF prikaz ponude s HUB3 barkodom
    offer = get_object_or_404(Offer, pk=pk)
    subject = offer.subject
    product = OfferProduct.objects.filter(offer=offer)
    client = offer.client
    
    # URL za generiranje HUB3 barkoda
    url = "https://hub3.bigfish.software/api/v2/barcode"
    headers = {'Content-Type': 'application/json'}
    
    # Podaci za HUB3 barkod
    data = {
        "renderer": "image",
        "options": {
            "format": "png",
            "color": "#000000",
            "bgColor": "#ffffff",
            "scale": 3,
            "ratio": 3
        },
        "data": {
            "amount": int(offer.total100()), # Iznos u centima
            "currency": offer.currtext(), # Valuta (npr. EUR)
            "sender": {
                "name": client.clientName,
                "street": client.addressLine1,
                "place": client.postalCode + " " + client.province,
            },
            "receiver": {
                "name": subject.clientName[:25], # Ograničenje duljine imena primatelja
                "street": subject.addressLine1,
                "place": subject.postalCode + " " + subject.province,
                "iban": subject.IBAN,
                "model": "00",
                "reference": offer.client.clientUniqueId + "-" + offer.number.replace('/', '-'), # Poziv na broj
            },
            "purpose": "", # Svrha plaćanja (opcionalno)
            "description": "Uplata po ponudi " + offer.number, # Opis plaćanja
        }
    }
    
    # Pošalji zahtjev za generiranje barkoda
    response = requests.post(url, headers=headers, data=json.dumps(data))
    # Kodiraj sliku barkoda u base64 za prikaz u HTML-u
    barcode_image = base64.b64encode(response.content).decode()
    #print(response.status_code) # Ispis statusa odgovora za debugiranje
    #print(response.content) # Ispis sadržaja odgovora za debugiranje
    
    # Renderiraj HTML predložak s podacima ponude i barkodom
    return render(request, 'offer_export_view.html', {'offer': offer, 'products': product, 'client': client, 'subject': subject, 'barcode_image': barcode_image})

@login_required
def inventory_label(request, pk):
    # Generira naljepnicu za stavku inventara s Code128 barkodom
    item = get_object_or_404(Inventory, pk=pk)
    # Generiraj Code128 barkod koristeći primarni ključ (pk) kao podatak
    barcode = Code128(str(pk), writer=SVGWriter())
    barcode_output = BytesIO() # Spremnik za SVG podatke
    barcode.write(barcode_output)
    barcode_svg = barcode_output.getvalue().decode() # Dekodiraj SVG podatke za prikaz u HTML-u
    
    # Renderiraj HTML predložak s podacima stavke i SVG barkodom
    return render(request, 'label.html', {'item': item, 'barcode_svg': barcode_svg})

@login_required
def product_label(request, pk):
    # Generira naljepnicu za proizvod s Code128 barkodom
    item = get_object_or_404(Product, pk=pk)
    # Generiraj Code128 barkod koristeći `barid` proizvoda kao podatak
    barcode = Code128(str(item.barid), writer=SVGWriter())
    barcode_output = BytesIO() # Spremnik za SVG podatke
    barcode.write(barcode_output)
    barcode_svg = barcode_output.getvalue().decode() # Dekodiraj SVG podatke za prikaz u HTML-u
    
    # Renderiraj HTML predložak s podacima proizvoda i SVG barkodom
    return render(request, 'label.html', {'item': item, 'barcode_svg': barcode_svg})

@login_required
def logout(request):
    # Odjavljuje trenutno prijavljenog korisnika
    auth.logout(request)
    # Preusmjerava na stranicu za prijavu
    return redirect('/accounts/login')

@login_required
def inventory(request):
    # Prikazuje stranicu s inventarom i omogućuje dodavanje novih stavki
    context = {}
    inventory = Inventory.objects.all()
    
    context['inventory'] = inventory

    if request.method == 'GET':
        # Ako je GET zahtjev, prikaži praznu formu
        form = InventoryForm()
        context['form'] = form
        return render(request, 'inventory.html', context)

    if request.method == 'POST':
        # Ako je POST zahtjev, obradi podatke iz forme
        form = InventoryForm(request.POST, request.FILES)

        if form.is_valid():
            # Ako je forma ispravna, spremi stavku inventara
            form.save()

            messages.success(request, 'Nadodan je novi predmet u inventar')
            return redirect('inventory')
        else:
            # Ako forma nije ispravna, prikaži greške
            messages.error(request, 'Problem pri obradi zahtjeva')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('inventory')


    return render(request, 'inventory.html', {'form': form}, context)

@login_required
def OutgoingInvoicesBookView(request):
    # Prikazuje i generira Knjigu izlaznih računa (KIRA)
    context = {}
    
    if request.method == 'GET':
        # Ako je GET zahtjev, prikaži formu za filtriranje
        form = InvoiceFilterForm()
        context['form'] = form
        return render(request, 'outgoing_invoice_book_print.html', context)

    if request.method == 'POST':
        # Ako je POST zahtjev, obradi filtere i prikaži rezultate
        form = InvoiceFilterForm(request.POST)
        context['form'] = form

        if form.is_valid():
            try:
                # Dohvati podatke iz forme
                company = form.cleaned_data['company']
                filter_type = form.cleaned_data['filter_type']
                
                # Odredi početni i završni datum na temelju vrste filtera
                if filter_type == 'month_year':
                    year = int(form.cleaned_data['year'])
                    month = int(form.cleaned_data['month'])
                    start_date = datetime(year, month, 1).date()
                    _, last_day = monthrange(year, month)
                    end_date = datetime(year, month, last_day).date()
                else: # date_range
                    start_date = form.cleaned_data['date_from']
                    end_date = form.cleaned_data['date_to']

                # Filtriraj račune prema odabranoj tvrtki i datumu
                invoices = Invoice.objects.filter(
                    subject=company,
                    date__gte=start_date,
                    date__lte=end_date
                ).order_by('date')

                # Ako nema računa, prikaži upozorenje
                if not invoices.exists():
                    if filter_type == 'month_year':
                        period_desc = f"mjesec {calendar.month_name[month]} {year}"
                    else:
                        period_desc = f"razdoblje od {start_date.strftime('%d.%m.%Y.')} do {end_date.strftime('%d.%m.%Y.')}"
                    
                    messages.warning(
                        request,
                        f"Nema pronađenih računa za {company.clientName} za {period_desc}"
                    )

                # Pripremi kontekst za prikaz rezultata
                context.update({
                    'invoices': invoices,
                    'company': company,
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_pretax': sum(invoice.pretax() for invoice in invoices), # Ukupno bez PDV-a
                    'total_tax': sum(invoice.tax() for invoice in invoices), # Ukupno PDV
                    'total_with_tax': sum(invoice.price_with_vat() for invoice in invoices), # Ukupno s PDV-om
                    'generated_at': timezone.now(), # Datum generiranja izvještaja
                    'show_results': True # Zastavica za prikaz tablice s rezultatima
                })
                
            except Exception as e:
                # U slučaju greške, prikaži poruku
                messages.error(
                    request,
                    'Došlo je do greške prilikom obrade podataka. Molimo pokušajte ponovno.'
                )
        else:
            # Ako forma nije ispravna, prikaži greške
            messages.error(request, 'Problem pri obradi zahtjeva')
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    # Renderiraj predložak s formom i/ili rezultatima
    return render(request, 'outgoing_invoice_book_print.html', context)

@login_required
def expenses(request):
    # Prikazuje stranicu s troškovima, omogućuje dodavanje i uređivanje
    context = {}
    try:
        # Dohvati sve troškove sortirane po datumu silazno
        expenses_list = Expense.objects.all().order_by('-date')
        context['expenses'] = expenses_list
    except Exception as e:
        # U slučaju greške pri dohvaćanju, prikaži poruku
        messages.error(request, f"Nije moguće prikazati troškove. Greška: {str(e)}")
        context['expenses'] = []
    
    if request.method == 'POST':
        # Ako je POST zahtjev, provjeri radi li se o uređivanju ili dodavanju
        expense_id = request.POST.get('expense_id')
        if expense_id:
            # Uređivanje postojećeg troška
            try:
                expense = get_object_or_404(Expense, pk=expense_id)
                # Provjeri postoje li datoteke u zahtjevu
                if request.FILES:
                    form = ExpenseForm(request.POST, request.FILES, instance=expense)
                else:
                    form = ExpenseForm(request.POST, instance=expense)
            except Exception as e:
                # U slučaju greške pri učitavanju troška
                messages.error(request, f"Greška pri učitavanju troška: {str(e)}")
                form = ExpenseForm(request.POST, request.FILES)
        else:
            # Dodavanje novog troška
            form = ExpenseForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Ako je forma ispravna, spremi trošak
            try:
                form.save()
                messages.success(request, 'Trošak uspješno spremljen')
                return redirect('expenses')
            except Exception as e:
                # U slučaju greške pri spremanju
                messages.error(request, f"Greška pri spremanju troška: {str(e)}")
        else:
            # Ako forma nije ispravna, prikaži greške i vrati formu za uređivanje
            messages.error(request, 'Problem pri obradi zahtjeva')
            context['edit_form'] = form
    
    # Pripremi prazne forme za prikaz (dodavanje i inicijalno uređivanje)
    context['form'] = ExpenseForm()
    context['edit_form'] = ExpenseForm()
    return render(request, 'expenses.html', context)

@login_required
def delete_expense(request, pk):
    # Briše trošak putem AJAX POST zahtjeva
    if request.method == 'POST':
        expense = get_object_or_404(Expense, pk=pk)
        expense.delete()
        # Vrati JSON odgovor o uspjehu
        return JsonResponse({'status': 'success'})
    # Ako nije POST zahtjev, vrati grešku
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def suppliers(request):
    # Prikazuje stranicu s dobavljačima, omogućuje dodavanje, uređivanje i brisanje
    context = {}
    # Dohvati sve dobavljače sortirane po imenu
    suppliers_list = Supplier.objects.all().order_by('supplierName')
    context['suppliers'] = suppliers_list
    
    if request.method == 'POST':
        # Obradi POST zahtjev ovisno o akciji
        action = request.POST.get('action')
        if action == 'add':
            # Dodavanje novog dobavljača
            form = SupplierForm(request.POST)
            if form.is_valid():
                supplier = form.save()
                messages.success(request, f'Supplier "{supplier.supplierName}" uspješno je dodan.')
                return redirect('suppliers')
            else:
                # Ako forma nije ispravna, vrati je u kontekst
                context['form'] = form
        
        elif action == 'edit':
            # Uređivanje postojećeg dobavljača
            supplier_id = request.POST.get('supplier_id')
            supplier = get_object_or_404(Supplier, id=supplier_id)
            form = SupplierForm(request.POST, instance=supplier)
            if form.is_valid():
                supplier = form.save()
                messages.success(request, f'Dobavljač "{supplier.supplierName}" uspješno je ažuriran.')
                return redirect('suppliers')
            else:
                # Ako forma nije ispravna, vrati je u kontekst
                context['edit_form'] = form
        
        elif action == 'delete':
            # Brisanje dobavljača
            supplier_id = request.POST.get('supplier_id')
            supplier = get_object_or_404(Supplier, id=supplier_id)
            supplier_name = supplier.supplierName
            
            # Provjeri postoje li povezani troškovi
            related_expenses = Expense.objects.filter(supplier=supplier).count()
            if related_expenses > 0:
                # Ako postoje, ne dopusti brisanje i prikaži grešku
                messages.error(request, 
                    f'Dobavljač "{supplier_name}" ne može biti obrisan jer je vezan s {related_expenses} troška.')
                return redirect('suppliers')
                
            # Ako nema povezanih troškova, obriši dobavljača
            supplier.delete()
            messages.success(request, f'Dobavljač "{supplier_name}" uspješno je obrisan.')
            return redirect('suppliers')
    
    # Ako forme nisu već postavljene u kontekstu (zbog greške), postavi prazne forme
    if 'form' not in context:
        context['form'] = SupplierForm()
    if 'edit_form' not in context:
        context['edit_form'] = SupplierForm()
    
    return render(request, 'suppliers.html', context)

@login_required
def incoming_invoice_book(request):
    # Prikazuje i generira Obrazac ulaznih računa (Obrazac U-RA)
    if request.method == 'POST':
        # Ako je POST zahtjev, obradi filtere i prikaži rezultate
        form = IncomingInvoiceBookFilterForm(request.POST)
        if form.is_valid():
            # Dohvati podatke iz forme
            company = form.cleaned_data['company']
            filter_type = form.cleaned_data['filter_type']
            
            # Odredi početni i završni datum na temelju vrste filtera
            if filter_type == 'month_year':
                month = int(form.cleaned_data['month'])
                year = int(form.cleaned_data['year'])
                _, last_day = calendar.monthrange(year, month)
                start_date = datetime(year, month, 1).date()
                end_date = datetime(year, month, last_day).date()
            else: # date_range
                start_date = form.cleaned_data['date_from']
                end_date = form.cleaned_data['date_to']
            
            # Filtriraj troškove prema odabranoj tvrtki i datumu
            expenses = Expense.objects.filter(
                subject=company,
                date__gte=start_date,
                date__lte=end_date
            ).order_by('date')
            
            # Izračunaj ukupne iznose za različite porezne osnovice i stope
            total_tax_base_0 = expenses.aggregate(Sum('tax_base_0'))['tax_base_0__sum'] or 0
            total_tax_base_5 = expenses.aggregate(Sum('tax_base_5'))['tax_base_5__sum'] or 0
            total_tax_base_13 = expenses.aggregate(Sum('tax_base_13'))['tax_base_13__sum'] or 0
            total_tax_base_25 = expenses.aggregate(Sum('tax_base_25'))['tax_base_25__sum'] or 0
            
            total_tax_5_deductible = expenses.aggregate(Sum('tax_5_deductible'))['tax_5_deductible__sum'] or 0
            total_tax_5_nondeductible = expenses.aggregate(Sum('tax_5_nondeductible'))['tax_5_nondeductible__sum'] or 0
            total_tax_13_deductible = expenses.aggregate(Sum('tax_13_deductible'))['tax_13_deductible__sum'] or 0
            total_tax_13_nondeductible = expenses.aggregate(Sum('tax_13_nondeductible'))['tax_13_nondeductible__sum'] or 0
            total_tax_25_deductible = expenses.aggregate(Sum('tax_25_deductible'))['tax_25_deductible__sum'] or 0
            total_tax_25_nondeductible = expenses.aggregate(Sum('tax_25_nondeductible'))['tax_25_nondeductible__sum'] or 0
            
            # Izračunaj ukupne sume
            total_tax_base = total_tax_base_0 + total_tax_base_5 + total_tax_base_13 + total_tax_base_25
            total_tax_deductible = total_tax_5_deductible + total_tax_13_deductible + total_tax_25_deductible
            total_tax_nondeductible = total_tax_5_nondeductible + total_tax_13_nondeductible + total_tax_25_nondeductible
            total_tax = total_tax_deductible + total_tax_nondeductible
            total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
            total_with_tax = total_amount # Ukupan iznos računa (već uključuje PDV)
            
            # Pripremi kontekst za prikaz rezultata
            context = {
                'form': form,
                'company': company,
                'start_date': start_date,
                'end_date': end_date,
                'expenses': expenses,
                'total_tax_base_0': total_tax_base_0,
                'total_tax_base_5': total_tax_base_5,
                'total_tax_base_13': total_tax_base_13,
                'total_tax_base_25': total_tax_base_25,
                'total_tax_base': total_tax_base,
                'total_tax_5_deductible': total_tax_5_deductible,
                'total_tax_5_nondeductible': total_tax_5_nondeductible,
                'total_tax_13_deductible': total_tax_13_deductible,
                'total_tax_13_nondeductible': total_tax_13_nondeductible,
                'total_tax_25_deductible': total_tax_25_deductible,
                'total_tax_25_nondeductible': total_tax_25_nondeductible,
                'total_tax_deductible': total_tax_deductible,
                'total_tax_nondeductible': total_tax_nondeductible,
                'total_tax': total_tax,
                'total_amount': total_amount,
                'total_with_tax': total_with_tax,
                'show_results': True, # Zastavica za prikaz tablice s rezultatima
                'generated_at': timezone.now() # Datum generiranja izvještaja
            }
            return render(request, 'incoming_invoice_book_print.html', context)
    else:
        # Ako je GET zahtjev, prikaži formu s inicijalnim vrijednostima (trenutni mjesec)
        today = timezone.now().date()
        form = IncomingInvoiceBookFilterForm(initial={
            'month': str(today.month),
            'year': str(today.year),
            'date_from': today.replace(day=1),
            'date_to': today
        })
    
    # Renderiraj predložak s formom
    return render(request, 'incoming_invoice_book_print.html', {'form': form, 'show_results': False})

@login_required 
def employees(request):
    # Prikazuje stranicu sa zaposlenicima, omogućuje dodavanje, uređivanje i aktivaciju/deaktivaciju
    companies = Company.objects.all()
    employees = Employee.objects.all().order_by('last_name', 'first_name')
    context = {'employees': employees}

    if request.method == 'POST':
        # Obradi POST zahtjev ovisno o akciji
        action = request.POST.get('action', 'create')
        
        if action == 'toggle_active':
            # Promjena statusa aktivnosti zaposlenika
            employee_id = request.POST.get('employee_id')
            try:
                employee = Employee.objects.get(id=employee_id)
                employee.is_active = not employee.is_active
                employee.save()
                status = 'aktiviran' if employee.is_active else 'deaktiviran'
                messages.success(request, f'Zaposlenik {employee.get_full_name()} je {status}.')
            except Employee.DoesNotExist:
                messages.error(request, 'Zaposlenik nije pronađen.')
            return redirect('employees')
        
        elif action == 'edit':
            # Uređivanje postojećeg zaposlenika
            employee_id = request.POST.get('employee_id')
            try:
                employee = Employee.objects.get(id=employee_id)
                # Proslijedi korisnika u formu za filtriranje tvrtki ako nije superuser
                form = EmployeeForm(request.POST, instance=employee, user=request.user)
                if form.is_valid():
                    employee = form.save(commit=False)
                    # Ako tvrtka nije odabrana, pokušaj dodijeliti prvu dostupnu korisniku
                    if not employee.company_id:
                        default_company = Company.objects.filter(user=request.user).first()
                        if default_company:
                            employee.company = default_company
                        else:
                            # Ako nema dostupnih tvrtki, prikaži grešku
                            messages.error(request, 'Zaposleniku mora biti pridružena tvrtka.')
                            context.update({'form': form, 'edit_mode': True, 'employee': employee})
                            return render(request, 'employees.html', context)
                    employee.save()
                    messages.success(request, 'Podaci o zaposleniku su uspješno ažurirani.')
                    return redirect('employees')
                else:
                    # Ako forma nije ispravna, prikaži grešku
                    messages.error(request, 'Greška pri spremanju podataka. Provjerite unesene vrijednosti.')
                    return redirect('employees')
            except Employee.DoesNotExist:
                messages.error(request, 'Zaposlenik nije pronađen.')
                return redirect('employees')
        
        elif action == 'create':
            # Dodavanje novog zaposlenika
            # Proslijedi korisnika u formu za filtriranje tvrtki ako nije superuser
            form = EmployeeForm(request.POST, user=request.user)
            if form.is_valid():
                employee = form.save(commit=False)
                # Ako tvrtka nije odabrana i postoje tvrtke, dodijeli prvu
                if not employee.company_id and companies.exists():
                    employee.company = companies.first()
                employee.save()
                messages.success(request, 'Zaposlenik je uspješno dodan.')
                return redirect('employees')
            else:
                # Ako forma nije ispravna, prikaži grešku
                messages.error(request, 'Greška pri spremanju podataka. Provjerite unesene vrijednosti.')
                return redirect('employees')

    # Pripremi praznu formu za dodavanje (proslijedi korisnika za filtriranje tvrtki)
    form = EmployeeForm(user=request.user)
    context.update({'form': form})
    return render(request, 'employees.html', context)

@login_required
def salaries(request):
    """Pregled i upravljanje plaćama zaposlenika"""
    
    context = {}
    
    # Dohvati sve zaposlenike sortirane po prezimenu i imenu
    employees = Employee.objects.all().order_by('last_name', 'first_name')
    
    # Filtriraj plaće po odabranom periodu (mjesec i godina) iz GET parametara
    selected_year = request.GET.get('year', timezone.now().year)
    selected_month = request.GET.get('month', timezone.now().month)
    
    try:
        # Pretvori godinu i mjesec u integer, koristi trenutni period kao fallback
        selected_year = int(selected_year)
        selected_month = int(selected_month)
    except (ValueError, TypeError):
        selected_year = timezone.now().year
        selected_month = timezone.now().month
    
    # Dohvati plaće za odabrani period, uključujući povezane podatke o zaposleniku
    salaries = Salary.objects.filter(
        period_year=selected_year,
        period_month=selected_month
    ).select_related('employee')
    
    # Obrada POST zahtjeva (kreiranje ili brisanje plaće)
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_salary':
            # Kreiranje nove plaće
            employee_id = request.POST.get('employee_id')
            hours_worked = Decimal(request.POST.get('hours_worked', 0))
            bonus = Decimal(request.POST.get('bonus', 0))
            annual_leave_days = int(request.POST.get('annual_leave_days', 0))
            annual_leave_hours = Decimal(request.POST.get('annual_leave_hours', 0))
            overtime_hours = Decimal(request.POST.get('overtime_hours', 0))
            overtime_rate_increase = Decimal(request.POST.get('overtime_rate_increase', 0))
            sick_leave_hours = Decimal(request.POST.get('sick_leave_hours', 0))
            sick_leave_rate = Decimal(request.POST.get('sick_leave_rate', 70)) / 100
            payment_date = request.POST.get('payment_date') or timezone.now().date()
            notes = request.POST.get('notes', '')

            employee = Employee.objects.get(id=employee_id)

            # Obradi neoporezive naknade
            non_taxable_payments = {}
            for limit in NonTaxablePaymentType.objects.filter(active=True):
                field_name = f'non_taxable_{limit.code}'
                amount = Decimal(request.POST.get(field_name, 0))
                if amount > 0:
                    if limit.max_monthly_amount is not None and amount > limit.max_monthly_amount:
                        messages.error(request, f'Prekoračen mjesečni limit za {limit.description}.')
                        return redirect('salaries')
                    if limit.max_annual_amount is not None and amount > limit.max_annual_amount:
                        messages.error(request, f'Prekoračen godišnji limit za {limit.description}.')
                        return redirect('salaries')
                    non_taxable_payments[limit.code] = float(amount)

            # Kreiraj novu instancu plaće
            new_salary = Salary(
                employee=employee,
                period_month=selected_month,
                period_year=selected_year,
                regular_hours=hours_worked,
                vacation_days=annual_leave_days,
                vacation_hours=annual_leave_hours,
                overtime_hours=overtime_hours,
                overtime_rate_increase=overtime_rate_increase,
                sick_leave_hours=sick_leave_hours,
                sick_leave_rate=sick_leave_rate,
                bonus=bonus,
                payment_date=payment_date,
                notes=notes,
                non_taxable_payments=non_taxable_payments,
                created_by=request.user
            )

            # Izračunaj i spremi plaću
            new_salary.calculate_salary()
            # Save the salary after calculation to ensure values are persisted
            new_salary.save()

            messages.success(request, f'Plaća za {employee.get_full_name()} za {calendar.month_name[selected_month]} {selected_year} uspješno je kreirana.')

            # Ako je zatražen PDF ispis, preusmjeri na PDF view
            if 'generate_pdf' in request.POST:
                return redirect(f'/payslip/{new_salary.id}/?format=pdf')

            return redirect('salaries')

        elif action == 'delete_salary':
            # Brisanje plaće
            salary_id = request.POST.get('salary_id')
            
            try:
                salary = Salary.objects.get(id=salary_id)
                
                # Provjeri je li plaća prijavljena u JOPPD
                if salary.joppd_status:
                    messages.warning(request, f'Plaća je već prijavljena u JOPPD sustav i ne može se obrisati.')
                    return redirect('salaries')
                
                employee_name = salary.employee.get_full_name()
                period = f"{calendar.month_name[salary.period_month]} {salary.period_year}"
                
                # Obriši plaću
                salary.delete()
                
                messages.success(request, f'Plaća za {employee_name} za {period} je uspješno obrisana.')
                
            except Salary.DoesNotExist:
                messages.error(request, 'Odabrana plaća ne postoji.')
            except Exception as e:
                messages.error(request, f'Greška prilikom brisanja plaće: {str(e)}')
            
            return redirect('salaries')
    
    
    # Mjeseci za odabir u filteru - Koristi hrvatske nazive
    croatian_months = [
        (1, 'Siječanj'), (2, 'Veljača'), (3, 'Ožujak'), (4, 'Travanj'),
        (5, 'Svibanj'), (6, 'Lipanj'), (7, 'Srpanj'), (8, 'Kolovoz'),
        (9, 'Rujan'), (10, 'Listopad'), (11, 'Studeni'), (12, 'Prosinac')
    ]
    
    # Godine za odabir u filteru (trenutna +/- 2 godine)
    current_year = timezone.now().year
    years = range(current_year - 2, current_year + 2)
    
    # Dohvati ime odabranog mjeseca iz hrvatske liste
    selected_month_name = dict(croatian_months).get(selected_month, '')

    # Dodaj sve potrebne podatke u kontekst
    context.update({
        'employees': employees,
        'salaries': salaries,
        'selected_year': selected_year,
        'selected_month': selected_month,
        'months': croatian_months, # Koristi hrvatsku listu za dropdown
        'years': years,
        'month_name': selected_month_name, # Koristi hrvatski naziv za prikaz
        'today': timezone.now().date(),  # Dodaj današnji datum za inicijalne vrijednosti
        'coefficient': TaxParameter.objects.filter(
            parameter_type='base_deduction', year=int(timezone.now().year)
        ),
    })
    
    # Dohvati porezne parametre za odabranu godinu
    tax_parameters = TaxParameter.objects.filter(year=selected_year)

    # Dodaj porezne parametre u kontekst
    context['tax_parameters'] = {param.parameter_type: param.value for param in tax_parameters}
    
    # Dohvati sve aktivne neoporezive limite
    non_taxable_limits = NonTaxablePaymentType.objects.filter(active=True)

    # Dodaj neoporezive limite u kontekst
    context['non_taxable_limits'] = non_taxable_limits
    
    return render(request, 'salaries.html', context)

@login_required
def tax_parameters(request):
    """Upravljanje poreznim parametrima, lokalnim stopama i neoporezivim primicima"""
    context = {}
    
    # Dohvati sve postojeće podatke
    tax_parameters = TaxParameter.objects.all().order_by('-year', 'parameter_type')
    local_taxes = LocalIncomeTax.objects.all().order_by('city_name')
    non_taxable_types = NonTaxablePaymentType.objects.all().order_by('name') # Dohvati neoporezive primitke
    
    context['tax_parameters'] = tax_parameters
    context['local_taxes'] = local_taxes
    context['non_taxable_types'] = non_taxable_types # Dodaj u kontekst
    context['current_year'] = timezone.now().year
    
    # Provjera i ispravak postotnih vrijednosti ako su spremljene kao decimalni broj (npr. 0.20 umjesto 20.0)
    for tax in local_taxes:
        if hasattr(tax, 'tax_rate_lower') and tax.tax_rate_lower is not None and tax.tax_rate_lower < 1.0:
            tax.tax_rate_lower *= 100
            tax.save(update_fields=['tax_rate_lower'])
        if hasattr(tax, 'tax_rate_higher') and tax.tax_rate_higher is not None and tax.tax_rate_higher < 1.0:
            tax.tax_rate_higher *= 100
            tax.save(update_fields=['tax_rate_higher'])
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_parameter':
            param_form = TaxParameterForm(request.POST)
            if param_form.is_valid():
                param = param_form.save()
                messages.success(request, 'Porezni parametar uspješno dodan.')
                return redirect('tax_parameters')
            else:
                messages.error(request, 'Greška kod dodavanja parametra. Provjerite podatke.')
                context['param_form'] = param_form
        
        elif action == 'edit_parameter':
            param_id = request.POST.get('parameter_id')
            parameter = get_object_or_404(TaxParameter, id=param_id)
            param_form = TaxParameterForm(request.POST, instance=parameter)
            if param_form.is_valid():
                param_form.save()
                messages.success(request, 'Porezni parametar uspješno ažuriran.')
                return redirect('tax_parameters')
            else:
                messages.error(request, 'Greška kod uređivanja parametra. Provjerite podatke.')
                context['edit_param_form'] = param_form # Vrati formu za prikaz grešaka u modalu
        
        elif action == 'delete_parameter':
            param_id = request.POST.get('parameter_id')
            parameter = get_object_or_404(TaxParameter, id=param_id)
            parameter.delete()
            messages.success(request, 'Porezni parametar uspješno izbrisan.')
            return redirect('tax_parameters')
            
        elif action == 'add_local_tax':
            tax_form = LocalIncomeTaxForm(request.POST)
            if tax_form.is_valid():
                tax = tax_form.save()
                messages.success(request, f'Lokalna stopa za {tax.city_name} uspješno dodana.')
                return redirect('tax_parameters')
            else:
                messages.error(request, 'Greška kod dodavanja lokalne stope. Provjerite podatke.')
                context['tax_form'] = tax_form
        
        elif action == 'edit_local_tax':
            tax_id = request.POST.get('tax_id')
            tax = get_object_or_404(LocalIncomeTax, id=tax_id)
            tax_form = LocalIncomeTaxForm(request.POST, instance=tax)
            if tax_form.is_valid():
                tax_form.save()
                messages.success(request, f'Lokalna stopa za {tax.city_name} uspješno ažurirana.')
                return redirect('tax_parameters')
            else:
                messages.error(request, 'Greška kod uređivanja lokalne stope. Provjerite podatke.')
                context['edit_tax_form'] = tax_form # Vrati formu za prikaz grešaka u modalu
        
        elif action == 'delete_local_tax':
            tax_id = request.POST.get('tax_id')
            tax = get_object_or_404(LocalIncomeTax, id=tax_id)
            tax.delete()
            messages.success(request, f'Lokalna stopa za {tax.city_name} uspješno izbrisana.')
            return redirect('tax_parameters')
        
        elif action == 'import_tax_rates':
            if 'tax_rates_file' not in request.FILES:
                messages.error(request, 'Nije odabrana datoteka za uvoz.')
                return redirect('tax_parameters')

            tax_file = request.FILES['tax_rates_file']
            tmp_path = None # Inicijaliziraj tmp_path

            try:
                # Spremi datoteku privremeno
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(tax_file.name)[1]) as tmp:
                    for chunk in tax_file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                # Koristi pandas za čitanje datoteke s dodatnim error handlingom
                if tax_file.name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(tmp_path, engine='openpyxl')
                elif tax_file.name.endswith('.csv'):
                    try:
                        df = pd.read_csv(tmp_path, sep=';', encoding='utf-8')
                    except Exception:
                        df = pd.read_csv(tmp_path, sep=',', encoding='utf-8')
                else:
                    messages.error(request, 'Nepodržani format datoteke. Molimo koristite .xlsx, .xls ili .csv.')
                    if tmp_path and os.path.exists(tmp_path): os.unlink(tmp_path)
                    return redirect('tax_parameters')

                # Pronađi nazive stupaca
                city_code_col = None
                city_name_col = None
                lower_rate_col = None
                higher_rate_col = None
                account_col = None
                nn_col = None
                city_type_col = None
                
                for col in df.columns:
                    col_lower = str(col).lower()
                    if 'šifra' in col_lower and ('grad' in col_lower or 'općin' in col_lower):
                        city_code_col = col
                    elif ('ime' in col_lower or 'naziv' in col_lower) and ('grad' in col_lower or 'općin' in col_lower):
                        city_name_col = col
                    elif 'niža' in col_lower and 'stopa' in col_lower:
                        lower_rate_col = col
                    elif 'viša' in col_lower and 'stopa' in col_lower:
                        higher_rate_col = col
                    elif 'račun' in col_lower and 'uplat' in col_lower:
                        account_col = col
                    elif 'nn' in col_lower or 'narodn' in col_lower:
                        nn_col = col
                    elif 'vrsta' in col_lower and ('jls' in col_lower or 'jedinic' in col_lower):
                        city_type_col = col
                
                # Provjeri jesu li pronađeni potrebni stupci
                if not city_name_col or not lower_rate_col or not higher_rate_col:
                    messages.error(request, 
                        f"Nisu pronađeni obavezni stupci u datoteci. Potrebni su stupci za ime grada/općine, nižu stopu i višu stopu.")
                    if tmp_path and os.path.exists(tmp_path): os.unlink(tmp_path)
                    return redirect('tax_parameters')

                # Obradi podatke - dohvati godinu iz forme
                year = int(request.POST.get('year', str(datetime.datetime.now().year)))
                valid_from = datetime.date(year, 1, 1)

                created_count = 0
                updated_count = 0

                # Iteriraj kroz retke DataFrame-a
                for index, row in df.iterrows():
                    city_name = str(row[city_name_col]).strip()
                    city_code = str(row[city_code_col]).strip() if city_code_col and not pd.isna(row[city_code_col]) else ''
                    tax_rate_lower = Decimal(str(row[lower_rate_col]).replace(',', '.'))
                    tax_rate_higher = Decimal(str(row[higher_rate_col]).replace(',', '.'))
                    account_number = str(row[account_col]) if account_col and not pd.isna(row[account_col]) else None
                    official_gazette = str(row[nn_col]) if nn_col and not pd.isna(row[nn_col]) else None
                    city_type = str(row[city_type_col]).strip().upper() if city_type_col and not pd.isna(row[city_type_col]) else 'GRAD'

                    tax_obj, created = LocalIncomeTax.objects.update_or_create(
                        city_name=city_name,
                        defaults={
                            'city_code': city_code,
                            'city_type': city_type,
                            'tax_rate': Decimal('0.00'),  # Dodaj zadanu vrijednost za tax_rate
                            'tax_rate_lower': tax_rate_lower,
                            'tax_rate_higher': tax_rate_higher,
                            'valid_from': valid_from,
                            'account_number': account_number,
                            'official_gazette': official_gazette
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                messages.success(request, f'Uspješno uvezeno {created_count} novih i ažurirano {updated_count} postojećih poreznih stopa.')

            except Exception as e:
                logger.error(f"Greška pri uvozu poreznih stopa: {e}")
                messages.error(request, f"Greška pri uvozu: {e}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

            return redirect('tax_parameters')

        elif action == 'add_non_taxable_type':
            non_tax_form = NonTaxablePaymentTypeForm(request.POST)
            if non_tax_form.is_valid():
                ntpt = non_tax_form.save()
                messages.success(request, f'Vrsta neoporezivog primitka "{ntpt.name}" uspješno dodana.')
                return redirect('tax_parameters')
            else:
                messages.error(request, 'Greška kod dodavanja neoporezivog primitka. Provjerite podatke.')
                context['non_tax_form'] = non_tax_form

    if 'param_form' not in context:
        context['param_form'] = TaxParameterForm()
    if 'edit_param_form' not in context:
        context['edit_param_form'] = TaxParameterForm() 
    if 'tax_form' not in context:
        context['tax_form'] = LocalIncomeTaxForm()
    if 'edit_tax_form' not in context:
        context['edit_tax_form'] = LocalIncomeTaxForm() 
    if 'non_tax_form' not in context:
        context['non_tax_form'] = NonTaxablePaymentTypeForm() 
    
    return render(request, 'tax_parameters.html', context)

@login_required
def get_local_tax_data(request, tax_id):
    """API endpoint za dohvaćanje podataka o lokalnoj poreznoj stopi (za AJAX)"""
    try:
        local_tax = LocalIncomeTax.objects.get(id=tax_id)
        # Vrati podatke kao JSON (trenutno nije implementirano vraćanje podataka, daljnji razvoj? Ili zahtijevati storniranje?)
    except LocalIncomeTax.DoesNotExist:
        return JsonResponse({'error': 'Local tax not found'}, status=404)
    
@login_required
def employee_api(request, employee_id):
    """API endpoint za dohvaćanje detalja o zaposleniku."""
    employee = get_object_or_404(Employee, id=employee_id)
    
    # Dohvati preostale dane godišnjeg odmora
    current_year = timezone.now().year
    vacation_days_taken = Salary.objects.filter(
        employee=employee,
        period_year=current_year
    ).aggregate(total_vacation_days=Sum('vacation_days'))['total_vacation_days'] or 0
    remaining_vacation_days = employee.annual_vacation_days - vacation_days_taken

    # Dohvati porezne stope i prag za grad zaposlenika i trenutnu godinu
    lower_tax_rate_percent = Decimal('20.00') # Default
    higher_tax_rate_percent = Decimal('30.00') # Default
    monthly_threshold = Decimal('4200.00') # Default
    try:
        from .models import LocalIncomeTax, TaxParameter
        from .utils.salary_calculator import standardize_city_name
        payment_date_obj = timezone.now().date()
        year = payment_date_obj.year

        threshold_param = TaxParameter.objects.get(parameter_type='monthly_tax_threshold', year=year)
        monthly_threshold = Decimal(str(threshold_param.value))

        local_tax = LocalIncomeTax.objects.filter(
            city_name__iexact=standardize_city_name(employee.city),
            valid_from__lte=payment_date_obj
        ).latest('valid_from')
        lower_tax_rate_percent = local_tax.tax_rate_lower
        higher_tax_rate_percent = local_tax.tax_rate_higher
    except (LocalIncomeTax.DoesNotExist, TaxParameter.DoesNotExist):
        pass # Koristi defaultne vrijednosti
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Greška pri dohvaćanju poreznih stopa za API za {employee.city} u {year}: {e}")

    data = {
        'vacation_days': remaining_vacation_days,
        'total_vacation_days': employee.annual_vacation_days,
        'tax_deduction_coefficient': str(employee.tax_deduction_coefficient),
        'hourly_rate': str(employee.hourly_rate),
        'lower_tax_rate': str(lower_tax_rate_percent), # Dodaj nižu stopu
        'higher_tax_rate': str(higher_tax_rate_percent), # Dodaj višu stopu
        'monthly_threshold': str(monthly_threshold) # Dodaj prag
    }
    return JsonResponse(data)

def salary_payslip(request, salary_id):
    """Prikaz ili generiranje PDF-a platne liste"""
    salary = get_object_or_404(Salary, id=salary_id)

    # Ako je zatražen PDF format, koristi pdf_generator
    if request.GET.get('format') == 'pdf':
        try:
            from .utils.pdf_generator import generate_payslip_pdf
            # Proslijedi request objekt ako je potreban unutar generate_payslip_pdf
            return generate_payslip_pdf(salary, request) 
        except ImportError:
             messages.error(request, "Greška pri generiranju PDF-a: pdf_generator nije pronađen.")
             return redirect('salaries') 
        except Exception as e:
             messages.error(request, f"Greška pri generiranju PDF-a: {e}")
             return redirect('salaries')


    # Za HTML prikaz, koristi pomoćnu funkciju za kontekst iz payslip_context.py
    context = get_payslip_context(salary)

    return render(request, 'salary_payslip.html', context)

@login_required
def joppd_report(request):
    """Generiranje JOPPD izvještaja (XML)"""
    context = {}
    selected_salaries = None
    total_count = 0
    # Inicijaliziraj sve potrebne varijable
    total_gross_salary = Decimal('0.00')
    total_pension_pillar_1 = Decimal('0.00')
    total_pension_pillar_2 = Decimal('0.00')
    total_income_tax = Decimal('0.00')
    total_net_salary = Decimal('0.00')
    total_health_insurance = Decimal('0.00')
    month = None
    year = None

    if request.method == 'POST':
        form = JOPPDGenerationForm(request.POST)
        if form.is_valid():
            month = int(form.cleaned_data['month'])
            year = int(form.cleaned_data['year'])

            selected_salaries = Salary.objects.filter(
                payment_date__month=month,
                payment_date__year=year
            ).select_related('employee', 'employee__company')

            if not selected_salaries.exists():
                messages.warning(request, f"Nema kreiranih plaća s datumom isplate u {month}/{year} za generiranje JOPPD.")
                context = {'form': form, 'month': month, 'year': year}
                return render(request, 'joppd_report.html', context)

            # Generiraj ukupne iznose za prikaz
            try:
                # Pretpostavi da su svi potrebni iznosi u decimalnom formatu
                if selected_salaries:
                    first_employee = selected_salaries.first().employee
                    if not first_employee or not first_employee.company:
                         raise ValueError("Nema zaposlenika ili tvrtke za odabrani period.")
                    company_subject = first_employee.company
                else:
                     raise ValueError("Nema zaposlenika za odabrani period.")


                xml_content_str = generate_joppd_xml(selected_salaries, year, month, company_subject)

                response = HttpResponse(xml_content_str, content_type='application/xml; charset=utf-8') # Ensure UTF-8
                filename = f"JOPPD_{company_subject.OIB}_{year}_{month:02d}.xml"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

                # Označi plaće kao prijavljene nakon uspješnog generiranja
                try:
                    marked_count = mark_salaries_as_reported(selected_salaries, filename)
                    messages.success(request, f"JOPPD obrazac {filename} uspješno generiran. {marked_count} plaća označeno kao prijavljeno.")
                except Exception as mark_error:
                    logger.error(f"Greška pri označavanju plaća kao prijavljenih: {mark_error}")
                    messages.warning(request, f"JOPPD obrazac {filename} je generiran, ali došlo je do greške pri označavanju plaća kao prijavljenih.")


                return response

            except Exception as e:
                logger.exception(f"Greška pri generiranju JOPPD XML-a za {month}/{year}: {e}") # Log full traceback
                messages.error(request, f"Došlo je do greške prilikom generiranja JOPPD XML datoteke: {e}")
                context = {'form': form, 'month': month, 'year': year} # Pass form and period back
                return render(request, 'joppd_report.html', context)

        else:
             context = {'form': form}
             return render(request, 'joppd_report.html', context)

    else: # GET request
        form = JOPPDGenerationForm()

    context.update({
        'form': form,
        'selected_salaries': selected_salaries,
        'month': month,
        'year': year,
        'total_count': total_count,
        'total_gross_salary': total_gross_salary,
        'total_pension_pillar_1': total_pension_pillar_1,
        'total_pension_pillar_2': total_pension_pillar_2,
        'total_income_tax': total_income_tax,
        'total_net_salary': total_net_salary,
        'total_health_insurance': total_health_insurance,
    })
    return render(request, 'joppd_report.html', context)


@login_required
def pension_info(request):
    """Prikazuje informativnu stranicu o mirovinskom sustavu"""
    return render(request, 'pension_info.html')


@login_required
def employee_api(request, employee_id):
    """API endpoint za dohvaćanje detalja o zaposleniku."""
    employee = get_object_or_404(Employee, id=employee_id)
    
    # Dohvati preostale dane godišnjeg odmora
    current_year = timezone.now().year
    vacation_days_taken = Salary.objects.filter(
        employee=employee,
        period_year=current_year
    ).aggregate(total_vacation_days=Sum('vacation_days'))['total_vacation_days'] or 0
    remaining_vacation_days = employee.annual_vacation_days - vacation_days_taken

    # Dohvati porezne stope i prag za grad zaposlenika i trenutnu godinu
    lower_tax_rate_percent = Decimal('20.00') # Default
    higher_tax_rate_percent = Decimal('30.00') # Default
    monthly_threshold = Decimal('4200.00') # Default
    try:
        from .models import LocalIncomeTax, TaxParameter
        from .utils.salary_calculator import standardize_city_name
        payment_date_obj = timezone.now().date()
        year = payment_date_obj.year

        threshold_param = TaxParameter.objects.get(parameter_type='monthly_tax_threshold', year=year)
        monthly_threshold = Decimal(str(threshold_param.value))

        local_tax = LocalIncomeTax.objects.filter(
            city_name__iexact=standardize_city_name(employee.city),
            valid_from__lte=payment_date_obj
        ).latest('valid_from')
        lower_tax_rate_percent = local_tax.tax_rate_lower
        higher_tax_rate_percent = local_tax.tax_rate_higher
    except (LocalIncomeTax.DoesNotExist, TaxParameter.DoesNotExist):
        pass # Koristi defaultne vrijednosti
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Greška pri dohvaćanju poreznih stopa za API za {employee.city} u {year}: {e}")

    data = {
        'vacation_days': remaining_vacation_days,
        'total_vacation_days': employee.annual_vacation_days,
        'tax_deduction_coefficient': str(employee.tax_deduction_coefficient),
        'hourly_rate': str(employee.hourly_rate),
        'lower_tax_rate': str(lower_tax_rate_percent), # Dodaj nižu stopu
        'higher_tax_rate': str(higher_tax_rate_percent), # Dodaj višu stopu
        'monthly_threshold': str(monthly_threshold) # Dodaj prag
    }
    return JsonResponse(data)

@login_required
def view_history(request, model_name='general', object_id=None, user_id=None):
    """Prikazuje povijest promjena za modele koji koriste simple_history"""
    
    # Inicijaliziraj listu za zapise povijesti
    history_records = []
    title = "Povijest promjena"
    
    # Mapiranje naziva modela (iz URL-a) na stvarne modele i njihove nazive
    model_map = {
        'salary': (Salary, 'Plaća'),
        'employee': (Employee, 'Zaposlenik'),
        'company': (Company, 'Subjekt'),
        'localtax': (LocalIncomeTax, 'Porezna stopa'),
        'taxparam': (TaxParameter, 'Porezni parametar'),
        'client': (Client, 'Klijent'),
        'product': (Product, 'Usluga/proizvod'),
        'offer': (Offer, 'Ponuda'),
        'invoice': (Invoice, 'Račun'),
        'inventory': (Inventory, 'Inventar'),
        'invprdt': (InvoiceProduct, 'Proizvod na računu'),
        'ofrprdt': (OfferProduct, 'Proizvod na ponudi'),
        'supplier': (Supplier, 'Dobavljač'),
        'expense': (Expense, 'Trošak'),
        'nontaxpaymtype':(NonTaxablePaymentType, 'Neoporeziv primitak'),
    }
        
    if model_name == 'user':
        # Prikaz povijesti za određenog korisnika
        history_type = 'user'
        
        # Ako je object_id postavljen, a user_id nije, koristi object_id kao user_id
        if object_id is not None and user_id is None:
            user_id = object_id
            
        if user_id:
            user = get_object_or_404(User, pk=user_id)
            title = f"Povijest korisnika: {user.get_full_name() or user.username}"
            
            # Dohvati sve modele koji koriste HistoricalRecords
            model_list = [m for m in apps.get_models() if hasattr(m, 'history')]
            
            # Iteriraj kroz modele i dohvati zapise povijesti za ovog korisnika
            for model in model_list:
                records = list(model.history.filter(history_user_id=user_id)
                            .order_by('-history_date')[:30])
                
                # Dodaj naziv modela svakom zapisu
                for record in records:
                    record.model_name = model._meta.verbose_name
                
                # Kreiraj parove (trenutni, prethodni) zapis za prikaz promjena
                for i in range(len(records)-1, 0, -1):
                    history_records.append((records[i], records[i-1]))
                
                # Dodaj prvi zapis (bez prethodnog)
                if records:
                    history_records.append((records[0], None))
            
            # Sortiraj sve zapise po datumu silazno
            if history_records:
                history_records.sort(key=lambda x: x[0].history_date, reverse=True)

    elif model_name == 'general':
        print("DEBUG: Entering 'general' branch")
        # Općeniti pregled zadnjih promjena za sve modele
        history_type = 'general'
        title = "Općeniti pregled"
        model_list = [m for m in apps.get_models() if hasattr(m, 'history')]
        
        for model in model_list:
            history_model = model.history.model# Dohvati zadnjih 20 zapisa povijesti za ovaj model, uključujući korisnika
            records = list(history_model.objects.all()
                         .select_related('history_user')
                         .order_by('-history_date')[:20])
            
            # Dodaj naziv modela svakom zapisu
            for record in records:
                record.model_name = model._meta.verbose_name
            
            # Kreiraj parove (trenutni, prethodni)
            for i in range(len(records)-1, 0, -1):
                history_records.append((records[i], records[i-1]))
            
            # Dodaj prvi zapis
            if records:
                history_records.append((records[0], None))
        
        # Sortiraj sve zapise po datumu silazno
        history_records.sort(key=lambda x: x[0].history_date, reverse=True)
        
    else:
        # Prikaz povijesti za određeni model ili specifični objekt tog modela
        history_type = 'model or object'
        model_tuple = model_map.get(model_name)
        if not model_tuple:
            # Ako model nije pronađen u mapi
            raise Http404("Model nije pronađen")
            
        model, name = model_tuple # Dohvati model i njegov naziv
        
        if object_id:
            # Pregled za specifičan objekt
            obj = get_object_or_404(model, pk=object_id)
            title = f"{name}: {obj}" # Postavi naslov stranice
            # Filtriraj povijest samo za taj objekt
            history_query = model.history.filter(id=object_id)
        else:
            # Pregled za cijeli model
            title = f"Povijest: {name}"
            # Dohvati svu povijest za taj model
            history_query = model.history.all()
        
        # Dohvati zapise povijesti i sortiraj ih po datumu silazno
        records = list(history_query.select_related('history_user').order_by('-history_date'))
        
        # Dodaj naziv modela i formatiranu reprezentaciju instance svakom zapisu
        for record in records:
            record.model_name = name
            
            # Poboljšani prikaz imena instance (ukloni " as of ...")
            if hasattr(record, 'title') and record.title:
                record.instance_name = record.title
            elif hasattr(record, 'clientName') and record.clientName:
                record.instance_name = f"{record.first_name} {record.last_name}"
            elif hasattr(record, 'number'):
                record.instance_name = record.number
            elif hasattr(record, 'name'):
                record.instance_name = record.name
            elif hasattr(record, 'description'):
                record.instance_name = record.description[:50] # Skrati opis ako je predugačak
            else:
                # Općeniti fallback - ukloni tehnički suffix iz prikaza
                obj_str = str(record).replace(" as of", "")
                if " as of " in obj_str:
                    obj_str = obj_str.split(" as of ")[0]
                record.instance_name = obj_str
        
        # Pripremi parove zapisa (trenutni, prethodni) i izračunaj promjene
        records_with_prev = []
        for i in range(len(records)):
            current_record = records[i]
            previous_record = records[i+1] if i < len(records)-1 else None
            
            # Ako je zapis tipa 'izmjena' (~), izračunaj promjene za prikaz u modalnom prozoru
            if current_record.history_type == '~' and previous_record:
                current_record.changes_display = []
                
                # Dohvati sva polja modela (osim internih polja povijesti)
                fields = {f.name: f.verbose_name or f.name for f in model._meta.fields 
                if f.name not in ['id', 'history_id', 'history_date', 'history_type', 'history_user_id', 'last_updated']}
                
                # Usporedi vrijednosti za svako polje
                for field_name, field_label in fields.items():
                    old_value = getattr(previous_record, field_name, None)
                    new_value = getattr(current_record, field_name, None)
                    
                    # Dodaj u prikaz samo ako su vrijednosti različite
                    if old_value != new_value:
                        # Formatiraj vrijednosti prije dodavanja u listu za prikaz
                        formatted_old = format_field_value(old_value)
                        formatted_new = format_field_value(new_value)
                        current_record.changes_display.append((field_label, formatted_old, formatted_new))
            
            # Ako je zapis tipa 'kreiranje' (+), pripremi prikaz inicijalnih vrijednosti
            elif current_record.history_type == '+':
                current_record.initial_values = []
                
                # Dohvati sva polja modela
                fields = {f.name: f.verbose_name or f.name for f in model._meta.fields 
                         if f.name not in ['id', 'history_id', 'history_date', 'history_type', 'history_user_id', 'last_updated']}
                
                # Dodaj vrijednosti za svako polje koje nije prazno
                for field_name, field_label in fields.items():
                    value = getattr(current_record, field_name, None)
                    if value is not None and value != '':
                        # Formatiraj vrijednost prije dodavanja
                        current_record.initial_values.append((field_label, format_field_value(value)))
            
            # Dodaj par (trenutni, prethodni) u listu
            records_with_prev.append((current_record, previous_record))
        
        history_records = records_with_prev
    
    
    # Renderiraj predložak s pripremljenim podacima povijesti
    return render(request, 'history_view.html', {
        'history_records': history_records,
        'title': title,
        'object_id': object_id,
        'history_type': history_type,
       # 'model_slug': model_list
    })


def get_field_changes(current, previous):
    """Pomoćna funkcija: Dohvaća promjene između dvije verzije zapisa povijesti"""
    if not previous:
        # Ako nema prethodnog zapisa, nema promjena
        return {}
        
    changes = {}
    # Iteriraj kroz sva polja trenutnog zapisa
    for field in current._meta.fields:
        # Ignoriraj interna polja povijesti i ID
        if field.name not in ['id', 'history_id', 'history_date', 'history_type', 'history_user_id', 'last_updated']:
            # Dohvati staru i novu vrijednost polja
            old_val = getattr(previous, field.name, None)
            new_val = getattr(current, field.name, None)
            
            # Ako su vrijednosti različite, zabilježi promjenu
            if old_val != new_val:
                # Koristi verbose_name polja ako postoji, inače koristi ime polja
                field_name = getattr(field, 'verbose_name', field.name) or field.name
                changes[field_name] = {
                    'old': format_field_value(old_val), # Formatiraj staru vrijednost
                    'new': format_field_value(new_val) # Formatiraj novu vrijednost
                }
    
    return changes

def format_field_value(value):
    """Pomoćna funkcija: Formatira vrijednost polja za prikaz u povijesti"""
    if value is None:
        return None # Vrati None ako je vrijednost None
    # Izbjegnuti sukob tipova koristeći modularni pristup
    elif isinstance(value, datetime) or isinstance(value, date): 
        # Formatiraj datum i vrijeme
        # Ako je samo date objekt, nema smisla formatirati H:M:S
        if isinstance(value, datetime):
             return value.strftime('%d.%m.%Y. %H:%M:%S')
        else: # Inače je date objekt
             return value.strftime('%d.%m.%Y.')
    elif isinstance(value, Decimal):
        # Formatiraj decimalni broj na dvije decimale
        return f"{value:.2f}"
    elif isinstance(value, User):
        # Prikazi puno ime korisnika ili korisničko ime
        return value.get_full_name() or value.username
    else:
        # Vrati vrijednost kao string za ostale tipove
        return str(value)

@login_required
def tax_changes_2025(request):
    # Prikazuje informativnu stranicu o poreznim promjenama za 2025.
    return render(request, 'tax_changes_2025.html')

@login_required
def send_invoice_email(request, invoice_id):
    """Šalje račun e-mailom klijentu."""
    if request.method == "POST":
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        client = invoice.client # Dohvati klijenta
        subject = invoice.subject # Dohvati subjekt
        products = InvoiceProduct.objects.filter(invoice=invoice) # Dohvati proizvode
        sender_name = invoice.subject.clientName
        reply_to_email = invoice.subject.emailAddress

        url = "https://hub3.bigfish.software/api/v2/barcode"
        headers = {'Content-Type': 'application/json'}
        data = {
            "renderer": "image",
            "options": { "format": "png", "color": "#000000", "bgColor": "#ffffff", "scale": 3, "ratio": 3 },
            "data": {
                "amount": int(invoice.total100()),
                "currency": invoice.currtext(),
                "sender": {
                    "name": client.clientName,
                    "street": client.addressLine1,
                    "place": client.postalCode + " " + client.province,
                },
                "receiver": {
                    "name": subject.clientName[:25],
                    "street": subject.addressLine1,
                    "place": subject.postalCode + " " + subject.town,
                    "iban": subject.IBAN,
                    "model": "00",
                    # Koristi metodu poziv_na_broj i očisti razmake/HR 00
                    "reference": invoice.poziv_na_broj().replace('HR 00 ', '').replace(' ', ''),
                },
                "purpose": "",
                "description": "Uplata po računu " + invoice.number,
            }
        }
        barcode_image = None # Inicijaliziraj u slučaju greške
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status() # Provjeri HTTP greške
            barcode_image = base64.b64encode(response.content).decode()
        except requests.exceptions.RequestException as e:
            logger.error(f"Greška pri generiranju barkoda za račun {invoice.id}: {e}")
            messages.error(request, "Greška pri generiranju barkoda za PDF.")
        except Exception as e:
             logger.error(f"Neočekivana greška pri generiranju barkoda za račun {invoice.id}: {e}")
             messages.error(request, "Neočekivana greška pri generiranju barkoda.")

        # Generiraj PDF za račun
        template = get_template('invoice_export_view.html')
        context = {
            'invoice': invoice,
            'products': products,
            'client': client,
            'subject': subject,
            'barcode_image': barcode_image,
            'request': request
        }
        html_content = template.render(context)
        pdf_file = BytesIO()
        try:
            bootstrap_css_path = os.path.join(settings.STATICFILES_DIRS[0], 'css/bootstrap.min.css')
            stylesheets = [CSS(filename=bootstrap_css_path)]
            # Proslijedi CSS WeasyPrintu
            HTML(string=html_content).write_pdf(pdf_file, stylesheets=stylesheets)
        except IndexError:
             logger.error("STATICFILES_DIRS nije konfiguriran ili je prazan.")
             messages.error(request, "Greška u konfiguraciji statičkih datoteka.")
             return redirect('invoices')
        except Exception as e:
            logger.error(f"Greška pri renderiranju PDF-a za račun {invoice.id}: {e}")
            messages.error(request, "Greška pri izradi PDF dokumenta.")
            return redirect('invoices') # Preusmjeri ako PDF ne uspije

        # Generiraj sadržaj e-maila
        email_subject = f"Račun {invoice.number} - {invoice.client.clientName}"
        email_body = render_to_string('email_templates/invoice_email.html', {
            'client_name': invoice.client.clientName,
            'invoice_number': invoice.number,
            'due_date': invoice.dueDate,
            'total_amount': invoice.price_with_vat(),
            'sender_name': sender_name, # Dodaj ime pošiljatelja u kontekst e-maila
        })

        # Pošalji e-mail
        success = send_email_with_attachment(
            subject=email_subject,
            body=email_body,
            recipient_email=client.emailAddress,
            attachment=pdf_file.getvalue(),
            attachment_name=f"Racun_{invoice.number}.pdf",
            sender_name=sender_name,
            reply_to_email=reply_to_email
        )

        if success:
            messages.success(request, f"E-mail s računom {invoice.number} uspješno poslan klijentu.")
        else:
            messages.error(request, f"Greška pri slanju e-maila za račun {invoice.number}.")

        return redirect('invoices')
    else:
        # Ako nije POST, preusmjeri ili vrati grešku
        messages.error(request, "Neispravan zahtjev.")
        return redirect('invoices')

@login_required
def mark_invoice_paid(request, invoice_id):
    """Označava račun kao plaćen i postavlja datum plaćanja na trenutni dan."""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == "POST":
        invoice.is_paid = True
        invoice.payment_date = now().date()
        invoice.save()
        messages.success(request, f"Račun {invoice.number} je označen kao plaćen.")
    return redirect('invoices')