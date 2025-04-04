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
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Row, Column
from decimal import Decimal, InvalidOperation

class DateInput(forms.DateInput):
    # Widget za unos datuma koji koristi HTML5 type="date"
    input_type = 'date'


class UserLoginForm(forms.Form):
    # Forma za prijavu korisnika
    username = forms.CharField(
        label="Korisničko ime",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': ' ' # Prazan placeholder za floating label efekt
        })
    )
    password = forms.CharField(
        label="Lozinka",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': ' ' # Prazan placeholder za floating label efekt
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-signin' # CSS klasa za stilizaciju forme
        self.helper.form_tag = False  # Ne renderiraj <form> tag automatski
        self.helper.form_show_labels = True # Pokaži labele polja
        self.helper.form_show_errors = True # Pokaži greške validacije
        self.helper.help_text_inline = False # Pomoćni tekst ispod polja
        self.helper.form_show_asterisk = False # Ne prikazuj zvjezdicu za obavezna polja
        self.helper.layout = Layout(
            'username',
            'password'
        )


class ClientForm(forms.ModelForm):
    # Forma za kreiranje i uređivanje klijenata
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dodaj 'form-control' klasu svim poljima za Bootstrap stilizaciju
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
    # Forma za kreiranje i uređivanje proizvoda/usluga
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dodaj 'form-control' klasu svim poljima
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
    # Forma za kreiranje i uređivanje zaglavlja računa
    dueDate = forms.DateField(required = True, label='Datum dospijeća', widget=DateInput(attrs={'class': 'form-control'}),)
    date = forms.DateField(required = True, label='Datum računa', widget=DateInput(attrs={'class': 'form-control'}),)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False # Ne renderiraj <form> tag
        # Definicija layouta pomoću Crispy Forms za bolju strukturu
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
    # Forma za stavku računa (proizvod/usluga)
    product = forms.ModelChoiceField(queryset=Product.objects.order_by('title'), label='Proizvod')
    quantity = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True, default=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False # Ne renderiraj <form> tag
        # Inicijalne vrijednosti za količinu, rabat i popust
        self.fields['quantity'].initial = '1'
        self.fields['rabat'].initial = ''
        self.fields['discount'].initial = ''
        # Definicija layouta za polja stavke i gumb za dodavanje nove stavke
        self.helper.layout = Layout(

            Row(
                Column('id', type="hidden", css_class="d-none"), # Skriveno polje za ID
                Column('DELETE', type="hidden", css_class="d-none"), # Skriveno polje za brisanje
                Column('product', css_class='form-group col-lg-3 col-md-3 col-sm-5 mb-0'),
                Column('quantity', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0', style='width: 7em'),
                Column('rabat', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0', style='width: 7em'),
                Column('discount', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0', style='width: 7em'),
                Div(HTML("""<label class='empty-div form-label'>&nbsp</label>
                            <button type="button" class="buttonDynamic btn btn-primary align-middle {% if forloop.first %}first-button{% endif %} ">+</button>"""),
                    css_class="form-group col-lg-1 col-md-1 col-sm-1 mb-0 box-btn-add-product"), css_class="formsetDynamic")
        )

    class Meta:
        model = InvoiceProduct
        fields = ['product', 'quantity', 'rabat', 'discount']
        labels = {
            'product': 'Proizvod', 'quantity': 'Količina', 'rabat': 'Rabat (%)', 'discount': 'Popust (%)'
        }

class BaseInlineInvoiceProductSet(BaseInlineFormSet):
    # Osnovni formset za stavke računa, koristi skriveni widget za brisanje
    deletion_widget = forms.HiddenInput


# Factory funkcija za kreiranje formseta za stavke računa
InvoiceProductFormSet = inlineformset_factory(
    Invoice, InvoiceProduct, form=InvoiceProductForm, formset=BaseInlineInvoiceProductSet, fields=('product', 'quantity', 'rabat', 'discount'), extra=1, can_delete=True)


class OfferForm(forms.ModelForm):
    # Forma za kreiranje i uređivanje zaglavlja ponude
    dueDate = forms.DateField(required = True, label='Datum dospijeća', widget=DateInput(attrs={'class': 'form-control'}),)
    date = forms.DateField(required = True, label='Datum ponude', widget=DateInput(attrs={'class': 'form-control'}),)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dodaj 'form-control' klasu i type='date' za polja datuma
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control',
            })
            if field.widget.__class__.__name__ == 'DateInput':
                field.widget.attrs.update({'type': 'date'})
        self.helper = FormHelper()
        self.helper.form_tag = False # Ne renderiraj <form> tag
        # Definicija layouta pomoću Crispy Forms
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
    # Forma za stavku ponude (proizvod/usluga)
    product = forms.ModelChoiceField(queryset=Product.objects.order_by('title'), label='Proizvod')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False # Ne renderiraj <form> tag
        # Inicijalne vrijednosti
        self.fields['quantity'].initial = '1'
        self.fields['rabat'].initial = ''
        self.fields['discount'].initial = ''
        # Definicija layouta za polja stavke i gumb za dodavanje nove stavke
        self.helper.layout = Layout(

            Row(
                Column('id', type="hidden", css_class="d-none"),
                Column('DELETE', type="hidden", css_class="d-none"),
                Column('product', css_class='form-group col-lg-3 col-md-3 col-sm-5 mb-0'),
                Column('quantity', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0', style='width: 7em'),
                Column('rabat', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0', style='width: 7em'),
                Column('discount', css_class='form-group col-lg-3 col-md-3 col-sm-3 mb-0', style='width: 7em'),
                Div(HTML("""<label class='empty-div form-label'>&nbsp</label>
                            <button type="button" class="buttonDynamic btn btn-primary align-middle {% if forloop.first %}first-button{% endif %} ">+</button>"""),
                    css_class="form-group col-lg-1 col-md-1 col-sm-1 mb-0 box-btn-add-product"), css_class="formsetDynamic")
        )

    class Meta:
        model = OfferProduct
        fields = ['product', 'quantity', 'rabat', 'discount']
        labels = {
            'product': 'Proizvod', 'quantity': 'Količina', 'rabat': 'Rabat (%)', 'discount': 'Popust (%)'
        }

class BaseInlineOfferProductSet(BaseInlineFormSet):
    # Osnovni formset za stavke ponude
    deletion_widget = forms.HiddenInput


# Factory funkcija za kreiranje formseta za stavke ponude
OfferProductFormSet = inlineformset_factory(
    Offer, OfferProduct, form=OfferProductForm, formset=BaseInlineOfferProductSet, fields=('product', 'quantity', 'rabat', 'discount'), extra=1, can_delete=True)


class CompanyForm(forms.ModelForm):
    # Forma za kreiranje i uređivanje tvrtke/subjekta
    IBAN = IBANFormField(label="IBAN") # Koristi localflavor za validaciju IBAN-a
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dodaj 'form-control' klasu svim poljima
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
        self.helper.form_tag = False # Ne renderiraj <form> tag
        # Koristi FloatingField za većinu polja (Bootstrap 5 efekt)
        self.helper.layout = Layout(
            *[FloatingField(field) if field != 'SustavPDVa' else Field(field) for field in self.Meta.fields]
        )
class InventoryForm(forms.ModelForm):
    # Forma za kreiranje i uređivanje stavki inventara
    class Meta:
        model = Inventory
        fields = ['title', 'quantity', 'subject']
        labels = {'title': 'Naziv proizvoda', 'quantity': 'Količina', 'subject' : 'Subjekt'}

class InvoiceFilterForm(forms.Form):
    # Forma za filtriranje izlaznih računa (KIRA)
    FILTER_CHOICES = [
        ('month_year', 'Po mjesecu i godini'),
        ('date_range', 'Po razdoblju'),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dohvati raspon godina iz postojećih računa
        year_range = Invoice.objects.aggregate(
            min_year=Min('date'),
            max_year=Max('date')
        )
        
        current_year = timezone.now().year
        
        # Odredi početnu i završnu godinu za izbor
        if year_range['min_year'] and year_range['max_year']:
            start_year = year_range['min_year'].year
            end_year = max(year_range['max_year'].year, current_year)
        else:
            # Ako nema računa, koristi samo trenutnu godinu
            start_year = current_year
            end_year = current_year
            
        # Postavi izbore za polje godine
        self.fields['year'].choices = [
            (str(x), str(x)) for x in range(start_year, end_year + 1)
        ]
        # Postavi inicijalnu vrijednost godine na trenutnu
        self.fields['year'].initial = str(current_year)

        # Definicija layouta pomoću Crispy Forms
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('company', css_class='col-md-4'),
                Column('filter_type', css_class='col-md-8'),
                css_class='mb-3'
            ),
            # Polja za filtriranje po mjesecu i godini (inicijalno vidljiva)
            Row(
                Column('year', css_class='col-md-3'),
                Column('month', css_class='col-md-3'),
                css_class='mb-3',
                id='month-year-filters'
            ),
            # Polja za filtriranje po rasponu datuma (inicijalno skrivena)
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
        choices=[], # Dinamički se popunjava u __init__
        label='Godina',
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False, # Obavezno samo ako je filter_type 'month_year'
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
        required=False, # Obavezno samo ako je filter_type 'month_year'
        error_messages={
            'invalid_choice': 'Odabrani mjesec nije važeća'
        }
    )
    
    date_from = forms.DateField(
        label='Od datuma',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False, # Obavezno samo ako je filter_type 'date_range'
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
        required=False, # Nije obavezno ako se filtrira po mjesecu/godini
        error_messages={
            'invalid': 'Neispravan format datuma'
        }
    )

    def clean(self):
        # Validacija forme - provjera obaveznih polja ovisno o tipu filtera
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
                
            # Provjera da li je početni datum prije završnog
            if date_from and date_to and date_from > date_to:
                self.add_error('date_from', 'Početni datum mora biti prije završnog datuma')
                
        return cleaned_data

class ExpenseForm(forms.ModelForm):
    # Forma za kreiranje i uređivanje troškova (jednostavnija verzija)
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
            'date': DateInput() # Koristi prilagođeni DateInput widget
        }

class SupplierForm(forms.ModelForm):
    # Forma za kreiranje i uređivanje dobavljača
    class Meta:
        model = Supplier
        fields = ['supplierName', 'addressLine1', 'town', 'province', 'postalCode', 
                 'phoneNumber', 'emailAddress', 'businessType', 'OIB', 'IBAN', 'notes']
        widgets = {
            'supplierName': forms.TextInput(attrs={'class': 'form-control'}),
            'addressLine1': forms.TextInput(attrs={'class': 'form-control'}),
            'town': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.Select(attrs={'class': 'form-control'}),
            'postalCode': forms.TextInput(attrs={'class': 'form-control'}),
            'phoneNumber': forms.TextInput(attrs={'class': 'form-control'}),
            'emailAddress': forms.EmailInput(attrs={'class': 'form-control'}),
            'businessType': forms.Select(attrs={'class': 'form-control'}),
            'OIB': forms.TextInput(attrs={'class': 'form-control'}),
            'IBAN': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post' # Metoda slanja forme
        # Definicija layouta pomoću Crispy Forms
        self.helper.layout = Layout(
            Row(
                Column('supplierName', css_class='form-group col-md-6 mb-0'),
                Column('businessType', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('addressLine1', css_class='form-group col-md-6 mb-0'),
                Column('town', css_class='form-group col-md-3 mb-0'),
                Column('postalCode', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('province', css_class='form-group col-md-6 mb-0'),
                Column('OIB', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('phoneNumber', css_class='form-group col-md-6 mb-0'),
                Column('emailAddress', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('IBAN', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            'notes',
            ButtonHolder(
                Submit('submit', 'Save', css_class='btn btn-primary') # Gumb za spremanje
            )
        )

class ExpenseForm(forms.ModelForm):
    # Forma za kreiranje i uređivanje troškova (detaljnija verzija s poreznim osnovicama)
    class Meta:
        model = Expense
        # Uključuje polja za porezne osnovice i odbitni/neodbitni PDV
        fields = ['title', 'amount', 'currency', 'date', 'category', 'description', 'subject',
                 'supplier', 'invoice_number', 'invoice_date', 'receipt',
                 'tax_base_0', 'tax_base_5', 'tax_base_13', 'tax_base_25',
                 'tax_5_deductible', 'tax_5_nondeductible',
                 'tax_13_deductible', 'tax_13_nondeductible',
                 'tax_25_deductible', 'tax_25_nondeductible']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'receipt': forms.FileInput(attrs={'class': 'form-control-file'}),
            'tax_base_0': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_base_5': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_base_13': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_base_25': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_5_deductible': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_5_nondeductible': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_13_deductible': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_13_nondeductible': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_25_deductible': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_25_nondeductible': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class IncomingInvoiceBookFilterForm(forms.Form):
    # Forma za filtriranje ulaznih računa (Knjiga U-RA)
    FILTER_CHOICES = [
        ('month_year', 'Po mjesecu i godini'),
        ('date_range', 'Po datumskom rasponu')
    ]
    
    MONTH_CHOICES = [
        ('1', 'Siječanj'),
        ('2', 'Veljača'),
        ('3', 'Ožujak'),
        ('4', 'Travanj'),
        ('5', 'Svibanj'),
        ('6', 'Lipanj'),
        ('7', 'Srpanj'),
        ('8', 'Kolovoz'),
        ('9', 'Rujan'),
        ('10', 'Listopad'),
        ('11', 'Studeni'),
        ('12', 'Prosinac'),
    ]
    
    # Godine od 2020 do 2030
    YEAR_CHOICES = [(str(year), str(year)) for year in range(2020, 2031)]
    
    company = forms.ModelChoiceField(
        queryset=None, # Queryset se postavlja u __init__
        required=True,
        label='Tvrtka',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    filter_type = forms.ChoiceField(
        choices=FILTER_CHOICES,
        widget=forms.RadioSelect(),
        initial='month_year',
        label='Način filtriranja'
    )
    
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        label='Mjesec',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        label='Godina',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        label='Od datuma',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False # Nije obavezno ako se filtrira po mjesecu/godini
    )
    
    date_to = forms.DateField(
        label='Do datuma',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False # Nije obavezno ako se filtrira po mjesecu/godini
    )
    
    def __init__(self, *args, **kwargs):
        from .models import Company # Lokalni import da se izbjegne circular dependency
        super().__init__(*args, **kwargs)
        # Postavi queryset za polje tvrtke
        self.fields['company'].queryset = Company.objects.all()

class EmployeeForm(forms.ModelForm):
    # Forma za kreiranje i uređivanje zaposlenika
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Datum rođenja'
    )
    date_of_employment = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Datum zaposlenja'
    )
    
    class Meta:
        model = Employee
        exclude = ['date_created', 'last_updated'] # Isključi automatski generirana polja
        widgets = {
            'address': forms.TextInput(attrs={'placeholder': 'Ulica i kućni broj'}),
            'city': forms.TextInput(attrs={'placeholder': 'Grad'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Poštanski broj'}),
            'oib': forms.TextInput(attrs={'placeholder': '00000000000', 'maxlength': '11'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@example.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+385...'}),
            'iban': forms.TextInput(attrs={'placeholder': 'HRxxxxxxxxxxxxxxxxxxxxxxx'}),
            'hourly_rate': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'work_experience_percentage': forms.NumberInput(attrs={'min': '0', 'step': '0.1', 'max': '20'}),
            'tax_deduction_coefficient': forms.NumberInput(attrs={'min': '1', 'step': '0.1'}),
            'annual_vacation_days': forms.NumberInput(attrs={'min': '0', 'max': '30'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Dohvati korisnika iz argumenata ako postoji
        super(EmployeeForm, self).__init__(*args, **kwargs)
        
        # Ako korisnik nije superuser, filtriraj dostupne tvrtke samo na one kojima pripada
        if user and not user.is_superuser:
            self.fields['company'].queryset = Company.objects.filter(users=user)


class SalaryCreationForm(forms.Form):
    # Forma za inicijalno kreiranje obračuna plaće (pojednostavljena)
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        label='Zaposlenik',
        empty_label='Odaberite zaposlenika' # Prazna opcija
    )
    period_month = forms.ChoiceField(
        choices=[(i, calendar.month_name[i]) for i in range(1, 13)], # Mjeseci 1-12
        label='Mjesec'
    )
    period_year = forms.ChoiceField(
        label='Godina' # Izbori se popunjavaju dinamički
    )
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Datum isplate',
        initial=timezone.now().date # Inicijalno postavi na današnji datum
    )
    hours_worked = forms.DecimalField(
        max_digits=6, 
        decimal_places=2,
        label='Odrađeni sati',
        widget=forms.NumberInput(attrs={'min': '0', 'step': '0.5'})
    )
    bonus = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        label='Stimulacija (EUR)',
        initial=0, # Inicijalno 0
        required=False, # Nije obavezno polje
        widget=forms.NumberInput(attrs={'min': '0', 'step': '0.01'})
    )
    annual_leave_days = forms.IntegerField(
        label='Korišteni dani GO',
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={'min': '0', 'max': '30'})
    )
    annual_leave_hours = forms.IntegerField(
        label='Korišteni sati GO',
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={'min': '0'})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Napomene',
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super(SalaryCreationForm, self).__init__(*args, **kwargs)
        # Dinamički generiraj godine (trenutna ±2)
        current_year = timezone.now().year
        self.fields['period_year'].choices = [(y, str(y)) for y in range(current_year-2, current_year+2)]
        self.fields['period_year'].initial = current_year
        self.fields['period_month'].initial = timezone.now().month
        
        # Dodaj JavaScript event handlere za dinamičko dohvaćanje podataka i izračune na frontendu
        self.fields['employee'].widget.attrs.update({
            'class': 'form-select',
            'onchange': 'fetchEmployeeData(this.value)' # Pozovi JS funkciju za dohvat podataka o zaposleniku
        })
        self.fields['hours_worked'].widget.attrs.update({
            'onchange': 'calculateRegularAmount()', # Pozovi JS funkciju za izračun iznosa redovnog rada
            'class': 'form-control'
        })
        self.fields['annual_leave_days'].widget.attrs.update({
            'onchange': 'calculateAnnualLeaveHours()', # Pozovi JS funkciju za izračun sati GO
            'class': 'form-control'
        })
        self.fields['annual_leave_hours'].widget.attrs.update({
            'onchange': 'calculateAnnualLeaveAmount()', # Pozovi JS funkciju za izračun iznosa GO
            'class': 'form-control'
        })
        self.fields['bonus'].widget.attrs.update({
            'onchange': 'calculateTotalAmount()', # Pozovi JS funkciju za izračun ukupnog iznosa
            'class': 'form-control'
        })


class SalaryFilterForm(forms.Form):
    # Forma za filtriranje pregleda plaća po mjesecu i godini
    month = forms.ChoiceField(
        choices=[(i, calendar.month_name[i]) for i in range(1, 13)],
        label='Mjesec',
        initial=timezone.now().month # Inicijalno trenutni mjesec
    )
    year = forms.ChoiceField(
        label='Godina',
        initial=timezone.now().year # Inicijalno trenutna godina
    )
    
    def __init__(self, *args, **kwargs):
        super(SalaryFilterForm, self).__init__(*args, **kwargs)
        # Dinamički generiraj godine (trenutna ±2)
        current_year = timezone.now().year
        self.fields['year'].choices = [(y, str(y)) for y in range(current_year-2, current_year+2)]


class TaxParameterForm(forms.ModelForm):
    # Forma za kreiranje i uređivanje poreznih parametara
    class Meta:
        model = TaxParameter
        fields = ['parameter_type', 'value', 'year', 'description']
        widgets = {
            'parameter_type': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}), # Omogući unos do 6 decimala
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False # Ne renderiraj <form> tag
        # Trenutna godina
        current_year = timezone.now().year
        # Postavi godine za izbor (trenutna i 3 prethodne + 1 buduća)
        self.fields['year'].widget = forms.Select(
            attrs={'class': 'form-control'},
            choices=[(y, y) for y in range(current_year-3, current_year+2)]
        )
        
        # Definicija layouta pomoću Crispy Forms
        self.helper.layout = Layout(
            Row(
                Column('parameter_type', css_class='form-group col-md-6 mb-0'),
                Column('year', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('value', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
            ),
            'description',
        )


class LocalIncomeTaxForm(forms.ModelForm):
    # Forma za kreiranje i uređivanje lokalnih poreznih stopa (prirez/porez na dohodak)
    class Meta:
        model = LocalIncomeTax
        fields = ['city_name', 'city_code', 'city_type', 'tax_rate', 'tax_rate_lower', 
                 'tax_rate_higher', 'valid_from', 'valid_until', 'account_number', 'official_gazette']
        widgets = {
            'city_name': forms.TextInput(attrs={'class': 'form-control'}),
            'city_code': forms.TextInput(attrs={'class': 'form-control'}),
            'city_type': forms.Select(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}), # Prirez (do 2024)
            'tax_rate_lower': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}), # Niža stopa (od 2024)
            'tax_rate_higher': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}), # Viša stopa (od 2024)
            'valid_from': DateInput(attrs={'class': 'form-control'}),
            'valid_until': DateInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'official_gazette': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'city_name': 'Ime grada/općine',
            'city_code': 'Šifra grada/općine',
            'city_type': 'Vrsta JLS',
            'tax_rate': 'Stopa prireza (do 2024.)',
            'tax_rate_lower': 'Niža porezna stopa (%)',
            'tax_rate_higher': 'Viša porezna stopa (%)',
            'valid_from': 'Vrijedi od',
            'valid_until': 'Vrijedi do',
            'account_number': 'Uplatni račun',
            'official_gazette': 'Broj Narodnih novina'
        }

    def clean(self):
        # Validacija: Provjera granica poreznih stopa za 2025. i kasnije
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        tax_rate_lower = cleaned_data.get('tax_rate_lower')
        tax_rate_higher = cleaned_data.get('tax_rate_higher')
        city_type = cleaned_data.get('city_type')
        
        if valid_from and valid_from.year >= 2025:
            instance = getattr(self, 'instance', None)
            # Dohvati limite ovisno o tipu JLS (Jedinica Lokalne Samouprave)
            if instance and instance.pk:
                limits = instance.get_rate_limits_2025()
            else:
                # Default limiti ako instanca još ne postoji
                if city_type == 'OPCINA':
                    limits = {'lower_min': 15, 'lower_max': 20, 'higher_min': 25, 'higher_max': 30}
                elif city_type == 'GRAD':
                    limits = {'lower_min': 15, 'lower_max': 21, 'higher_min': 25, 'higher_max': 31}
                elif city_type == 'VELIKI_GRAD':
                    limits = {'lower_min': 15, 'lower_max': 22, 'higher_min': 25, 'higher_max': 32}
                elif city_type == 'ZAGREB':
                    limits = {'lower_min': 15, 'lower_max': 23, 'higher_min': 25, 'higher_max': 33}
                else:
                    limits = {'lower_min': 15, 'lower_max': 20, 'higher_min': 25, 'higher_max': 30} # Fallback
            
            # Provjeri je li niža stopa unutar granica
            if tax_rate_lower < limits['lower_min'] or tax_rate_lower > limits['lower_max']:
                self.add_error('tax_rate_lower', 
                              f"Za 2025. godinu, niža stopa mora biti između {limits['lower_min']}% i {limits['lower_max']}% za odabrani tip JLS.")
            
            # Provjeri je li viša stopa unutar granica
            if tax_rate_higher < limits['higher_min'] or tax_rate_higher > limits['higher_max']:
                self.add_error('tax_rate_higher', 
                              f"Za 2025. godinu, viša stopa mora biti između {limits['higher_min']}% i {limits['higher_max']}% za odabrani tip JLS.")
        
        return cleaned_data
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False # Ne renderiraj <form> tag
        # Definicija layouta pomoću Crispy Forms
        self.helper.layout = Layout(
            Row(
                Column('city_name', css_class='form-group col-md-4 mb-0'),
                Column('city_code', css_class='form-group col-md-4 mb-0'),
                Column('city_type', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('tax_rate', css_class='form-group col-md-4 mb-0'),
                Column('tax_rate_lower', css_class='form-group col-md-4 mb-0'),
                Column('tax_rate_higher', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('valid_from', css_class='form-group col-md-6 mb-0'),
                Column('valid_until', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('account_number', css_class='form-group col-md-6 mb-0'),
                Column('official_gazette', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
        )


class SalaryPeriodFilterForm(forms.Form):
    # Forma za filtriranje plaća po periodu (mjesec, godina) i zaposleniku
    month = forms.ChoiceField(
        choices=[(i, calendar.month_name[i]) for i in range(1, 13)],
        required=False, # Mjesec nije obavezan (može se filtrirati samo po godini)
        label='Mjesec',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    year = forms.ChoiceField(
        required=True, # Godina je obavezna
        label='Godina',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        required=False, # Zaposlenik nije obavezan (prikaži za sve)
        empty_label="Svi zaposlenici", # Opcija za prikaz svih
        label='Zaposlenik',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dinamički generiraj godine (trenutna i 5 prethodnih)
        current_year = timezone.now().year
        self.fields['year'].choices = [(str(year), str(year)) for year in range(current_year - 5, current_year + 1)]
        self.fields['year'].initial = str(current_year) # Inicijalno trenutna godina
        
        # Definicija layouta pomoću Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'get' # Koristi GET metodu za filtriranje
        self.helper.layout = Layout(
            Row(
                Column('year', css_class='form-group col-md-4 mb-0'),
                Column('month', css_class='form-group col-md-4 mb-0'),
                Column('employee', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Filtriraj', css_class='btn btn-primary') # Gumb za filtriranje
        )


class JOPPDGenerationForm(forms.Form):
    # Forma za odabir perioda za generiranje JOPPD obrasca
    month = forms.ChoiceField(
        choices=[(i, calendar.month_name[i]) for i in range(1, 13)],
        required=True,
        label='Mjesec',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    year = forms.ChoiceField(
        required=True,
        label='Godina',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dinamički generiraj godine (trenutna i 3 prethodne)
        current_year = timezone.now().year
        self.fields['year'].choices = [(str(year), str(year)) for year in range(current_year - 3, current_year + 1)]
        self.fields['year'].initial = str(current_year)
        
        # Definicija layouta pomoću Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'post' # Koristi POST metodu
        self.helper.layout = Layout(
            Row(
                Column('month', css_class='form-group col-md-6 mb-0'),
                Column('year', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Generiraj', css_class='btn btn-primary') # Gumb za generiranje
        )

class SalaryForm(forms.ModelForm):
    # Forma za detaljno uređivanje obračuna plaće
    class Meta:
        model = Salary
        # Polja koja se mogu uređivati
        fields = [
            'employee', 'period_month', 'period_year', 'regular_hours',
            'vacation_hours', 'sick_leave_hours', 'sick_leave_rate', 'overtime_hours', 
            'overtime_rate_increase', 'bonus', 'payment_date', 'notes'
        ]
        widgets = {
            'regular_hours': forms.NumberInput(attrs={'min': '0', 'step': '1'}),
            'sick_leave_hours': forms.NumberInput(attrs={'min': '0', 'step': '1'}),
            'sick_leave_rate': forms.NumberInput(attrs={'min': '50', 'step': '0.5'}),
            'overtime_hours': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'overtime_rate_increase': forms.NumberInput(attrs={'min': '0', 'step': '0.5'}), # Faktor uvećanja satnice za prekovremene
            'bonus': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'vacation_hours': forms.NumberInput(attrs={'min': '0', 'step': '1'}), # Sati godišnjeg
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        # Validacija i konverzija decimalnih polja
        cleaned_data = super().clean()
        
        decimal_fields = ['regular_hours', 'sick_leave_hours', 'sick_leave_rate', 'overtime_hours', 
                         'overtime_rate_increase', 'bonus']
        
        for field in decimal_fields:
            value = cleaned_data.get(field)
                        
            if value is not None:
                try:
                    # Pokušaj konvertirati vrijednost u Decimal
                    cleaned_value = Decimal(str(value))
                    cleaned_data[field] = cleaned_value
                except (TypeError, ValueError, InvalidOperation) as e:
                    # Ako konverzija ne uspije, dodaj grešku
                    self.add_error(field, f'Neispravan decimalni broj za {field}')
        
        return cleaned_data

    def save(self, commit=True):
        # Spremanje instance uz osiguravanje da su decimalna polja tipa Decimal
        instance = super().save(commit=False) # Spremi formu bez commita u bazu
        
        decimal_fields = ['regular_hours', 'sick_leave_hours', 'sick_leave_rate', 'overtime_hours', 
                         'overtime_rate_increase', 'bonus']
        
        for field in decimal_fields:
            value = getattr(instance, field)
                        
            if value is not None:
                try:
                    # Konvertiraj vrijednost u Decimal prije spremanja
                    decimal_value = Decimal(str(value))
                    setattr(instance, field, decimal_value)
                except Exception as e:
                    # Ako dođe do greške, dodaj grešku u formu
                    self.add_error(field, f'Greška pri konverziji {field}: {str(e)}')
        
        if commit:
            # Ako je commit=True, spremi instancu u bazu
            instance.save()
        return instance

class NonTaxablePaymentTypeForm(forms.ModelForm):
    """Forma za dodavanje nove vrste neoporezivog primitka."""
    class Meta:
        model = NonTaxablePaymentType
        fields = ['name', 'code', 'description', 'max_monthly_amount', 'max_annual_amount', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Npr. Prigodna nagrada (božićnica, regres...)'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Npr. PRIGODNA_NAGRADA'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Detaljniji opis (opcionalno)'}),
            'max_monthly_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_annual_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Naziv primitka',
            'code': 'Interna šifra (jedinstvena)',
            'description': 'Opis',
            'max_monthly_amount': 'Maks. mjesečni iznos (EUR, opcionalno)',
            'max_annual_amount': 'Maks. godišnji iznos (EUR, opcionalno)',
            'active': 'Aktivan (prikazuje se kod obračuna plaće)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False # Ne renderiraj <form> tag unutar crispy taga
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-6 mb-3'),
                Column('code', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                 Column('description', css_class='form-group col-md-12 mb-3'),
            ),
            Row(
                Column('max_monthly_amount', css_class='form-group col-md-6 mb-3'),
                Column('max_annual_amount', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                 Column('active', css_class='form-check form-switch col-md-12 mb-3'), # Koristi form-switch za bolji izgled checkboxa
            )
            # Gumb za spremanje se dodaje izvan {% crispy %} taga u predlošku
        )

    def clean_code(self):
        # Osiguraj da je kod jedinstven i velikim slovima bez razmaka
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().replace(' ', '_')
            # Provjeri jedinstvenost, isključujući trenutnu instancu ako uređujemo
            query = NonTaxablePaymentType.objects.filter(code=code)
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise forms.ValidationError("Šifra već postoji. Molimo unesite jedinstvenu šifru.")
        return code