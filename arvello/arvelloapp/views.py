from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from reportlab.pdfgen import canvas
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User, auth
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

def invoices(request):
    invoices = Invoice.objects.all()
    return render(request, 'invoices.html', {'invoices': invoices})

def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'invoice_detail.html', {'invoice': invoice})

def invoice_status(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'invoice_status.html', {'invoice': invoice})

def products(request):
    products = Product.objects.all()
    return render(request, 'products.html', {'product': products})

def create_invoice(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            client = get_object_or_404(Client, pk=request.POST.get('client'))
            invoice = form.save(commit=False)
            invoice.save()
            return HttpResponseRedirect('/invoices/')
    else:
        form = InvoiceForm()

    return render(request, 'invoice_form.html', {'form': form})


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

def export_invoice_to_pdf(request, invoice_id):
    # Finish!
    invoice = Invoice.objects.get(id=invoice_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_id}.pdf"'
    p = canvas.Canvas(response)

    # Add content to the PDF document!
    p.drawString(100, 750, f'Invoice Title: {invoice.title}')
    p.drawString(100, 700, f'Invoice Status: {invoice.status}')
    # Add other invoice details!
    p.showPage()
    p.save()
    return response

@login_required
def logout(request):
    auth.logout(request)
    return redirect('/login')

