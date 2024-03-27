from django import forms
from django.contrib.auth.models import User
from .models import *
from django.core.exceptions import ValidationError

class DateInput(forms.DateInput):
    input_type = 'date'


class UserLoginForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'id': 'floatingInput', 'class': 'form-control mb-3'}), required=True)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'floatingPassword', 'class': 'form-control mb-3'}), required=True)
    class Meta:
        model=User
        fields=['username','password']



class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['clientName', 'addressLine1', 'province', 'postalCode', 'phoneNumber', 'emailAddress', 'clientUniqueId', 'clientType', 'OIB', 'VATID']
        labels = {
            'clientName': 'Ime klijenta', 'addressLine1': 'Adresa',
            'province': 'Županija', 'postalCode': 'Poštanski broj',
            'phoneNumber': 'Broj telefona', 'emailAddress': 'Email adresa',
            'clientUniqueId': 'Jedinstveni ID klijenta', 'clientType': 'Vrsta klijenta',
            'OIB': 'OIB', 'VATID': 'VAT ID',
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'description', 'quantity', 'price', 'taxPercent', 'currency']
        labels = {
            'title': 'Naziv proizvoda', 'description': 'Opis proizvoda',
            'quantity': 'Količina', 'price': 'Cijena', 'currency': 'Valuta', 'taxPercent': 'Porez (%)',
        }


class InvoiceForm(forms.ModelForm):
    dueDate = forms.DateField(required = True, label='Datum dospijeća', widget=DateInput(attrs={'class': 'form-control'}),)
    date = forms.DateField(required = True, label='Datum računa', widget=DateInput(attrs={'class': 'form-control'}),)
    class Meta:
        model = Invoice
        fields = ['title', 'number', 'dueDate', 'notes', 'client', 'product', 'date', 'subject']
        labels = {
            'title': 'Naslov', 'number': 'Broj računa',
            'dueDate': 'Datum dospijeća', 'date': 'Datum računa', 'notes': 'Napomene',
            'client': 'Klijent', 'product': 'Proizvod', 'subject': 'Subjekt'
        }

class OfferForm(forms.ModelForm):
    dueDate = forms.DateField(required = True, label='Datum dospijeća', widget=DateInput(attrs={'class': 'form-control'}),)
    date = forms.DateField(required = True, label='Datum ponude', widget=DateInput(attrs={'class': 'form-control'}),)
    class Meta:
        model = Offer
        fields = ['title', 'number', 'dueDate', 'notes', 'client', 'product', 'date', 'subject']
        labels = {
            'title': 'Naslov', 'number': 'Broj računa',
            'dueDate': 'Datum dospijeća', 'notes': 'Napomene',
            'client': 'Klijent', 'product': 'Proizvod', 'date': 'Datum ponude', 'subject': 'Subjekt'
        }

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['clientName', 'addressLine1', 'town', 'province', 'postalCode', 'phoneNumber', 'emailAddress', 'clientUniqueId', 'clientType', 'OIB', 'SustavPDVa', 'IBAN']
        labels = {
            'clientName': 'Ime subjekta', 'addressLine1': 'Adresa', 'town': 'Grad',
            'province': 'Županija', 'postalCode': 'Poštanski broj',
            'phoneNumber': 'Tel. broj', 'emailAddress': 'Email adresa',
            'clientUniqueId': 'ID subjekta', 'clientType': 'Tip subjekta',
            'OIB': 'OIB', 'SustavPDVa': 'Je li subjekt u sustavu PDV-a?',
        }

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['title', 'quantity']
        labels = {'title': 'Naziv proizvoda', 'quantity': 'Količina',}
