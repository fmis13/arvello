from django import forms
from django.contrib.auth.models import User
from django.forms import widgets
from .models import *
import json
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
        fields = ['title', 'description', 'quantity', 'price', 'currency']
        labels = {
            'title': 'Naziv proizvoda', 'description': 'Opis proizvoda',
            'quantity': 'Količina', 'price': 'Cijena', 'currency': 'Valuta',
        }


class InvoiceForm(forms.ModelForm):
    dueDate = forms.DateField(required = True, label='Datum dospijeća', widget=DateInput(attrs={'class': 'form-control'}),)
    class Meta:
        model = Invoice
        fields = ['title', 'number', 'dueDate', 'paymentTerms', 'status', 'notes', 'client', 'product']
        labels = {
            'title': 'Naslov', 'number': 'Broj računa',
            'dueDate': 'Datum dospijeća', 'paymentTerms': 'Dogovor o dospijeću',
            'status': 'Status', 'notes': 'Napomene', 'client': 'Klijent', 'product': 'Proizvod',
        }

class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = ['clientName', 'addressLine1', 'province', 'postalCode', 'phoneNumber', 'emailAddress', 'clientUniqueId', 'clientType', 'OIB', 'VATID']