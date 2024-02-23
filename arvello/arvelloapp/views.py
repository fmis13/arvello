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
    cache.clear()
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
def companies(request):
    context = {}
    companies = Company.objects.all()
    cache.clear()
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
    cache.clear()
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
    cache.clear()
    context['clients'] = clients

    if request.method == 'GET':
        form = ClientForm()
        context['form'] = form
        return render(request, 'clients.html', context)

    if request.method == 'POST':
        form = ClientForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()

            messages.success(request, 'New Client Added')
            return redirect('clients')
        else:
            messages.error(request, 'Problem processing your request')
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
    product = invoice.product.all()
    client = invoice.client
    return render(request, 'invoice_export_view.html', {'invoice': invoice, 'products': product, 'client': client, 'subject': subject})

def offer_pdf(request, pk):
    offer = get_object_or_404(Offer, pk=pk)
    subject = offer.subject
    product = offer.product.all()
    client = offer.client
    return render(request, 'offer_export_view.html', {'offer': offer, 'producs': product, 'client': client, 'subject': subject})


@login_required
def logout(request):
    auth.logout(request)
    return redirect('/login')

