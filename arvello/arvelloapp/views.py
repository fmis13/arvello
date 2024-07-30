from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from django.core.cache import cache
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User, auth
from io import BytesIO
from .forms import *
from .models import *
import requests
import json
import base64
from barcode import Code128
from barcode.writer import SVGWriter

def anonymous_required(function=None, redirect_url=None):

   if not redirect_url:
       redirect_url = '/invoices'

   actual_decorator = user_passes_test(
       lambda u: u.is_anonymous,
       login_url=redirect_url
   )

   if function:
       return actual_decorator(function)
   return actual_decorator

def loginredir(request):
    return redirect('/account/login')

@login_required
def select_subject(request):
    companies = Company.objects.all()
    return render(request, 'selectSubject.html', {'companies': companies})

@login_required
def products(request):
    context = {}
    products = Product.objects.all()
    product = Product.objects.all()
    context['product'] = products

    if request.method == 'GET':
        form = ProductForm()
        context['form'] = form
        return render(request, 'products.html', context)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Nadoan je novi proizvod/usluga')
            return redirect('products')
        else:
            messages.error(request, 'Problem pri obradi zahtjeva')
            return redirect('products')
    else:
        form = ProductForm()

    return render(request, 'products.html', {'form': form}, context)

@login_required
def invoices(request):
    context = {}
    invoices = Invoice.objects.all()
    
    context['invoices'] = invoices

    if request.method == 'GET':
        form = InvoiceForm()
        context['form'] = form
        return render(request, 'invoices.html', context)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Nadodan je novi račun')
            return redirect('invoices')
        else:
            messages.error(request, 'Problem pri obradi zahtjeva')
            return redirect('invoices')
    else:
        form = InvoiceForm()

    return render(request, 'invoices.html', {'form': form}, context)

@login_required
def create_invoice(request):
    if request.method == 'POST':
        invoice_form = InvoiceForm(request.POST)
        invoice_formset = InvoiceProductFormSet(request.POST)

        if invoice_form.is_valid() and invoice_formset.is_valid():
            invoice = invoice_form.save()
            invoice_products = []
            total = 0
            for invoice_form in invoice_formset:
                invoice_product = invoice_form.save(commit=False)
                invoice_product.invoice = invoice
                invoice_product.product = invoice_form.cleaned_data["product"]
                total += Decimal(invoice_product.product.price) * invoice_product.quantity
                invoice_products.append(invoice_product)

            invoice.total = total
            invoice.save()

            for invoice_product in invoice_products:
                invoice_product.save()
            messages.success(request, 'Nadodan je novi račun')
            return redirect('invoices')
        if not invoice_formset.is_valid():
            print(invoice_formset.errors)
            messages.error(request, 'Problem pri obradi zahtjeva')
    else:
        invoice_form = InvoiceForm()
        invoice_formset = InvoiceProductFormSet(queryset=InvoiceProduct.objects.none())

    empty_form = InvoiceProductFormSet(queryset=InvoiceProduct.objects.none())
    context = {
        'invoice_form': invoice_form,
        'invoice_formset': invoice_formset,
        'empty_form': empty_form,
    }

    return render(request, 'makeinvoice.html', context)

@login_required
def create_offer(request):
    if request.method == 'POST':
        offer_form = OfferForm(request.POST)
        offer_formset = OfferProductFormSet(request.POST)

        if offer_form.is_valid() and offer_formset.is_valid():
            offer = offer_form.save()
            offer_products = []
            total = 0
            for offer_form in offer_formset:
                offer_product = offer_form.save(commit=False)
                offer_product.offer = offer
                offer_product.product = offer_form.cleaned_data["product"]
                total += Decimal(offer_product.product.price) * offer_product.quantity
                offer_products.append(offer_product)

            offer.total = total
            offer.save()

            for offer_product in offer_products:
                offer_product.save()
            messages.success(request, 'Nadodana je nova ponuda')
            return redirect('offers')
        if not offer_formset.is_valid():
            print(offer_formset.errors)
            messages.error(request, 'Problem pri obradi zahtjeva')
    else:
        offer_form = OfferForm()
        offer_formset = OfferProductFormSet(queryset=OfferProduct.objects.none())

    empty_form = OfferProductFormSet(queryset=OfferProduct.objects.none())
    context = {
        'offer_form': offer_form,
        'offer_formset': offer_formset,
        'empty_form': empty_form,
    }

    return render(request, 'makeoffer.html', context)

@login_required
def companies(request):
    context = {}
    companies = Company.objects.all()
    
    context['companies'] = companies

    if request.method == 'GET':
        form = CompanyForm()
        context['form'] = form
        return render(request, 'companies.html', context)

    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Nadodan je novi subjekt')
            return redirect('companies')
        else:
            messages.error(request, 'Problem pri obradi zahtjeva')
            return redirect('companies')
    else:
        form = CompanyForm()

    return render(request, 'companies.html', {'form': form}, context)

@login_required
def offers(request):
    context = {}
    offers = Offer.objects.all()
    
    context['offers'] = offers

    if request.method == 'GET':
        form = OfferForm()
        context['form'] = form
        return render(request, 'offers.html', context)

    if request.method == 'POST':
        form = OfferForm(request.POST, request.FILES)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Nadodana je nova ponuda')
            return redirect('offers')
        else:
            messages.error(request, 'Problem pri obradi zahtjeva')
            return redirect('offers')
    else:
        form = OfferForm()

    return render(request, 'offers.html', {'form': form}, context)


@login_required
def clients(request):
    context = {}
    clients = Client.objects.all()
    
    context['clients'] = clients

    if request.method == 'GET':
        form = ClientForm()
        context['form'] = form
        return render(request, 'clients.html', context)

    if request.method == 'POST':
        form = ClientForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()

            messages.success(request, 'Nadodan je novi klijent')
            return redirect('clients')
        else:
            messages.error(request, 'Problem pri obradi zahtjeva')
            return redirect('clients')


    return render(request, 'clients.html', context)

@anonymous_required
def login(request):
    context = {}
    if request.method == 'GET':
        form = UserLoginForm()
        context['form'] = form
        return render(request, 'login.html', context)

    if request.method == 'POST':
        form = UserLoginForm(request.POST)

        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)

            return redirect('/invoices')
        else:
            context['form'] = form
            messages.error(request, 'Netočne vjerodajnice')
            return redirect('login')


    return render(request, 'login.html', context)

@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    subject = invoice.subject
    product = InvoiceProduct.objects.filter(invoice=invoice)
    client = invoice.client
    url = "https://hub3.bigfish.software/api/v2/barcode"
    headers = {'Content-Type': 'application/json'}
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
            "amount": int(invoice.total100()),
            "currency": invoice.currtext(),
            "sender": {
                "name": client.clientName,
                "street": client.addressLine1,
                "place": client.postalCode + " " + client.province,
            },
            "receiver": {
                "name": subject.clientName,
                "street": subject.addressLine1,
                "place": subject.postalCode + " " + subject.province,
                "iban": subject.IBAN,
                "model": "00",
                "reference": invoice.client.clientUniqueId + "-" + invoice.number.replace('/', '-'),
            },
            "purpose": "",
            "description": "Uplata po računu " + invoice.number,
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    barcode_image = base64.b64encode(response.content).decode()
    print(response.status_code)
    print(response.content)
    return render(request, 'invoice_export_view.html', {'invoice': invoice, 'products': product, 'client': client, 'subject': subject, 'barcode_image': barcode_image})

@login_required
def offer_pdf(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    subject = offer.subject
    product = OfferProduct.objects.filter(offer=offer)
    client = offer.client
    url = "https://hub3.bigfish.software/api/v2/barcode"
    headers = {'Content-Type': 'application/json'}
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
            "amount": int(offer.total100()),
            "currency": offer.currtext(),
            "sender": {
                "name": client.clientName,
                "street": client.addressLine1,
                "place": client.postalCode + " " + client.province,
            },
            "receiver": {
                "name": subject.clientName,
                "street": subject.addressLine1,
                "place": subject.postalCode + " " + subject.province,
                "iban": subject.IBAN,
                "model": "00",
                "reference": offer.client.clientUniqueId + "-" + offer.number.replace('/', '-'),
            },
            "purpose": "",
            "description": "Uplata po ponudi " + offer.number,
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    barcode_image = base64.b64encode(response.content).decode()
    print(response.status_code)
    print(response.content)
    return render(request, 'offer_export_view.html', {'offer': offer, 'products': product, 'client': client, 'subject': subject, 'barcode_image': barcode_image})

@login_required
def inventory_label(request, pk):
    item = get_object_or_404(Inventory, pk=pk)
    barcode = Code128(str(pk), writer=SVGWriter())
    barcode_output = BytesIO()
    barcode.write(barcode_output)
    barcode_svg = barcode_output.getvalue().decode()
    return render(request, 'label.html', {'item': item, 'barcode_svg': barcode_svg})

@login_required
def product_label(request, pk):
    item = get_object_or_404(Product, pk=pk)
    barcode = Code128(str(item.barid), writer=SVGWriter())
    barcode_output = BytesIO()
    barcode.write(barcode_output)
    barcode_svg = barcode_output.getvalue().decode()
    return render(request, 'label.html', {'item': item, 'barcode_svg': barcode_svg})

@login_required
def logout(request):
    auth.logout(request)
    return redirect('/accounts/login')

@login_required
def inventory(request):
    context = {}
    inventory = Inventory.objects.all()
    
    context['inventory'] = inventory

    if request.method == 'GET':
        form = InventoryForm()
        context['form'] = form
        return render(request, 'inventory.html', context)

    if request.method == 'POST':
        form = InventoryForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()

            messages.success(request, 'Nadodan je novi predmet u inventar')
            return redirect('inventory')
        else:
            messages.error(request, 'Problem pri obradi zahtjeva')
            return redirect('inventory')


    return render(request, 'inventory.html', {'form': form}, context)
