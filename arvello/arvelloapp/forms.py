from django import forms
from django.contrib.auth.models import User
from .models import *
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, HTML, Layout, Row
from django.forms import BaseInlineFormSet, inlineformset_factory, ModelForm
from django.forms.widgets import NumberInput

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
        fields = ['title', 'description', 'price', 'taxPercent', 'currency']
        labels = {
            'title': 'Naziv proizvoda', 'description': 'Opis proizvoda',
            'price': 'Cijena', 'currency': 'Valuta', 'taxPercent': 'Porez (%)',
        }


class InvoiceForm(forms.ModelForm):
    dueDate = forms.DateField(required = True, label='Datum dospijeća', widget=DateInput(attrs={'class': 'form-control'}),)
    date = forms.DateField(required = True, label='Datum računa', widget=DateInput(attrs={'class': 'form-control'}),)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-lg-3 col-md-3 col-sm-6 mb-0'),   
                Column('number', css_class='form-group col-lg-3 col-md-3 col-sm-6 mb-0'),
                Column('date', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0'),
                Column('dueDate', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0'),
                Column('client', css_class='form-group col-lg-3 col-md-3 col-sm-6 mb-0'),
                Column('subject', css_class='form-group col-lg-3 col-md-3 col-sm-6 mb-0'),
                Column('notes', css_class='form-group col-lg-3 col-md-3 col-sm-6 mb-0'),
                css_class='form-row'
            )
        )
    class Meta:
        model = Invoice
        fields = ['title', 'number', 'dueDate', 'notes', 'client', 'date', 'subject']
        labels = {
            'title': 'Naslov', 'number': 'Broj računa',
            'dueDate': 'Datum dospijeća', 'date': 'Datum računa', 'notes': 'Napomene',
            'client': 'Klijent', 'product': 'Proizvod', 'subject': 'Subjekt'
        }

class InvoiceProductForm(ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.order_by('title'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields['quantity'].initial = '1'
        self.fields['rabat'].initial = ''
        self.fields['discount'].initial = ''
        self.helper.layout = Layout(

            Row(
                Column('id', type="hidden", css_class="d-none"),
                Column('DELETE', type="hidden", css_class="d-none"),
                Column('product', css_class='form-group col-lg-3 col-md-3 col-sm-5 mb-0'),
                Column('quantity', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0'),
                Column('rabat', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0'),
                Column('discount', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0'),
                Div(HTML("""<label class='empty-div form-label'>&nbsp</label>
                            <button type="button" class="buttonDynamic btn btn-primary align-middle {% if forloop.first %}first-button{% endif %}">+</button>"""),
                    css_class="form-group col-lg-1 col-md-1 col-sm-1 mb-0 box-btn-add-product"), css_class="formsetDynamic")
        )

    class Meta:
        model = InvoiceProduct
        fields = ['product', 'quantity', 'rabat', 'discount']
        labels = {
            'product': 'Proizvod', 'quantity': 'Količina', 'rabat': 'Rabat (%)', 'discount': 'Popust (%)'
        }

class BaseInlineInvoiceProductSet(BaseInlineFormSet):
    deletion_widget = forms.HiddenInput


InvoiceProductFormSet = inlineformset_factory(
    Invoice, InvoiceProduct, form=InvoiceProductForm, formset=BaseInlineInvoiceProductSet, fields=('product', 'quantity', 'rabat', 'discount'), extra=1, can_delete=True)


class OfferForm(forms.ModelForm):
    dueDate = forms.DateField(required = True, label='Datum dospijeća', widget=DateInput(attrs={'class': 'form-control'}),)
    date = forms.DateField(required = True, label='Datum ponude', widget=DateInput(attrs={'class': 'form-control'}),)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-lg-3 col-md-3 col-sm-6 mb-0'),   
                Column('number', css_class='form-group col-lg-3 col-md-3 col-sm-6 mb-0'),
                Column('date', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0'),
                Column('dueDate', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0'),
                Column('client', css_class='form-group col-lg-3 col-md-3 col-sm-6 mb-0'),
                Column('subject', css_class='form-group col-lg-3 col-md-3 col-sm-6 mb-0'),
                Column('notes', css_class='form-group col-lg-3 col-md-3 col-sm-6 mb-0'),
                css_class='form-row'
            )
        )
    class Meta:
        model = Offer
        fields = ['title', 'number', 'dueDate', 'notes', 'client', 'date', 'subject']
        labels = {
            'title': 'Naslov', 'number': 'Broj računa',
            'dueDate': 'Datum dospijeća', 'notes': 'Napomene',
            'client': 'Klijent', 'product': 'Proizvod', 'date': 'Datum ponude', 'subject': 'Subjekt'
        }

class OfferProductForm(ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.order_by('title'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields['quantity'].initial = '1'
        self.fields['rabat'].initial = ''
        self.fields['discount'].initial = ''
        self.helper.layout = Layout(

            Row(
                Column('id', type="hidden", css_class="d-none"),
                Column('DELETE', type="hidden", css_class="d-none"),
                Column('product', css_class='form-group col-lg-3 col-md-3 col-sm-5 mb-0'),
                Column('quantity', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0'),
                Column('rabat', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0'),
                Column('discount', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0'),
                Div(HTML("""<label class='empty-div form-label'>&nbsp</label>
                            <button type="button" class="buttonDynamic btn btn-primary align-middle {% if forloop.first %}first-button{% endif %}">+</button>"""),
                    css_class="form-group col-lg-1 col-md-1 col-sm-1 mb-0 box-btn-add-product"), css_class="formsetDynamic")
        )

    class Meta:
        model = OfferProduct
        fields = ['product', 'quantity', 'rabat', 'discount']
        labels = {
            'product': 'Proizvod', 'quantity': 'Količina', 'rabat': 'Rabat (%)', 'discount': 'Popust (%)'
        }

class BaseInlineOfferProductSet(BaseInlineFormSet):
    deletion_widget = forms.HiddenInput


OfferProductFormSet = inlineformset_factory(
    Offer, OfferProduct, form=OfferProductForm, formset=BaseInlineOfferProductSet, fields=('product', 'quantity', 'rabat', 'discount'), extra=1, can_delete=True)


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
        fields = ['title', 'quantity', 'subject']
        labels = {'title': 'Naziv proizvoda', 'quantity': 'Količina', 'subject' : 'Subjekt'}
