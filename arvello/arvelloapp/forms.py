from django import forms
from django.contrib.auth.models import User
from .models import *
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, HTML, Layout, Row
from django.forms import BaseInlineFormSet, inlineformset_factory, ModelForm
from django.forms.widgets import NumberInput
from localflavor.generic.forms import IBANFormField
from crispy_bootstrap5.bootstrap5 import FloatingField, Field
from django.utils import timezone
from django.db.models import Min, Max
import calendar

class DateInput(forms.DateInput):
    input_type = 'date'


class UserLoginForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'id': 'floatingInput', 'class': 'form-control mb-3'}), required=True)
    password = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'floatingPassword', 'class': 'form-control mb-3'}), required=True)
    class Meta:
        model=User
        fields=['username','password']



class ClientForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
            
    class Meta:
        model = Product
        fields = ['title', 'description', 'price', 'taxPercent', 'currency', 'barid']
        labels = {
            'title': 'Naziv proizvoda', 'description': 'Opis proizvoda',
            'price': 'Cijena', 'currency': 'Valuta', 'taxPercent': 'Porez (%)',
            'barid': 'ID (za barkod)', 'Product': 'Proizvod'
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
    product = forms.ModelChoiceField(queryset=Product.objects.order_by('title'), label='Proizvod')
    quantity = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, default=1)

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
                Column('quantity', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0', style='width: 7em'),
                Column('rabat', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0', style='width: 7em'),
                Column('discount', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0', style='width: 7em'),
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
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control',
            })
            if field.widget.__class__.__name__ == 'DateInput':
                field.widget.attrs.update({'type': 'date'})
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
            'title': 'Naslov', 'number': 'Broj ponude',
            'dueDate': 'Datum dospijeća', 'notes': 'Napomene',
            'client': 'Klijent', 'product': 'Proizvod', 'date': 'Datum ponude', 'subject': 'Subjekt'
        }

class OfferProductForm(ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.order_by('title'), label='Proizvod')

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
                Column('quantity', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0', style='width: 7em'),
                Column('rabat', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0', style='width: 7em'),
                Column('discount', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0', style='width: 7em'),
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
    IBAN = IBANFormField(label="IBAN")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            *[FloatingField(field) if field != 'SustavPDVa' else Field(field) for field in self.Meta.fields]
        )
class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['title', 'quantity', 'subject']
        labels = {'title': 'Naziv proizvoda', 'quantity': 'Količina', 'subject' : 'Subjekt'}

class InvoiceFilterForm(forms.Form):
    FILTER_CHOICES = [
        ('month_year', 'Po mjesecu i godini'),
        ('date_range', 'Po razdoblju'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dohvati raspon godina iz računa
        year_range = Invoice.objects.aggregate(
            min_year=Min('date'),
            max_year=Max('date')
        )
        
        current_year = timezone.now().year
        
        # Ukoliko postoje računi, koristi godine iz računa
        if year_range['min_year'] and year_range['max_year']:
            start_year = year_range['min_year'].year
            end_year = max(year_range['max_year'].year, current_year)
        else:
            # U protivnom, koristi trenutnu godinu
            start_year = current_year
            end_year = current_year
            
        self.fields['year'].choices = [
            (str(x), str(x)) for x in range(start_year, end_year + 1)
        ]
        # zadana godina - sadašnja godina
        self.fields['year'].initial = str(current_year)

        # crispy
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('company', css_class='col-md-4'),
                Column('filter_type', css_class='col-md-8'),
                css_class='mb-3'
            ),
            Row(
                Column('year', css_class='col-md-3'),
                Column('month', css_class='col-md-3'),
                css_class='mb-3',
                id='month-year-filters'
            ),
            Row(
                Column('date_from', css_class='col-md-3'),
                Column('date_to', css_class='col-md-3'),
                css_class='mb-3',
                id='date-range-filters'
            )
        )

    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        label='Tvrtka',
        widget=forms.Select(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Molimo odaberite tvrtku',
            'invalid_choice': 'Odabrana tvrtka nije važeća'
        }
    )
    
    filter_type = forms.ChoiceField(
        choices=FILTER_CHOICES,
        label='Način filtriranja',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='month_year',
        error_messages={
            'required': 'Molimo odaberite način filtriranja',
            'invalid_choice': 'Odabrani način filtriranja nije važeći'
        }
    )
    
    year = forms.ChoiceField(
        choices=[],
        label='Godina',
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        error_messages={
            'invalid_choice': 'Odabrana godina nije važeća'
        }
    )
    
    month = forms.ChoiceField(
        choices=[
            ('1', 'Siječanj'), ('2', 'Veljača'), ('3', 'Ožujak'),
            ('4', 'Travanj'), ('5', 'Svibanj'), ('6', 'Lipanj'),
            ('7', 'Srpanj'), ('8', 'Kolovoz'), ('9', 'Rujan'),
            ('10', 'Listopad'), ('11', 'Studeni'), ('12', 'Prosinac')
        ],
        label='Mjesec',
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        error_messages={
            'invalid_choice': 'Odabrani mjesec nije važeći'
        }
    )
    
    date_from = forms.DateField(
        label='Od datuma',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        error_messages={
            'invalid': 'Neispravan format datuma'
        }
    )
    
    date_to = forms.DateField(
        label='Do datuma',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        error_messages={
            'invalid': 'Neispravan format datuma'
        }
    )

    def clean(self):
        cleaned_data = super().clean()
        filter_type = cleaned_data.get('filter_type')
        
        if filter_type == 'month_year':
            year = cleaned_data.get('year')
            month = cleaned_data.get('month')
            if not year:
                self.add_error('year', 'Godina je obavezna za mjesečni prikaz')
            if not month:
                self.add_error('month', 'Mjesec je obavezan za mjesečni prikaz')
                
        elif filter_type == 'date_range':
            date_from = cleaned_data.get('date_from')
            date_to = cleaned_data.get('date_to')
            
            if not date_from:
                self.add_error('date_from', 'Početni datum je obavezan za razdoblje')
            if not date_to:
                self.add_error('date_to', 'Završni datum je obavezan za razdoblje')
                
            if date_from and date_to and date_from > date_to:
                self.add_error('date_from', 'Početni datum mora biti prije završnog datuma')
                
        return cleaned_data

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'currency', 'date', 'category', 'description', 'subject', 'receipt']
        labels = {
            'title': 'Naziv troška',
            'amount': 'Iznos',
            'currency': 'Valuta',
            'date': 'Datum',
            'category': 'Kategorija',
            'description': 'Opis',
            'subject': 'Subjekt',
            'receipt': 'Račun (slika/PDF)'
        }
        widgets = {
            'date': DateInput()
        }