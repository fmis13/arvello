from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, FileResponse
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
def invoices(request):
    invoices = Invoice.objects.all()
    return render(request, 'invoices.html', {'invoices': invoices})

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
            messages.success(request, 'Nadoan je novi račun')
            return redirect('invoices')
        else:
            messages.error(request, 'Problem pri obradi zahtjeva')
            return redirect('invoices')
    else:
        form = InvoiceForm()

    return render(request, 'invoices.html', {'form': form}, context)


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
    pdfmetrics.registerFont(TTFont('OpenSansLight', 'static/OpenSans-Light.ttf'))
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
# All of this is temporary, will be replaced with a template
    p.drawString(100, 750, f"Interni identifikator računa: {invoice.id}")
    p.drawString(100, 850, f"Invoice ID: {invoice.id}")
    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()

    response = FileResponse(BytesIO(pdf), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'
    return response

@login_required
def logout(request):
    auth.logout(request)
    return redirect('/login')

