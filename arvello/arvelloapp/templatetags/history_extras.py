from django import template
from django.urls import reverse

register = template.Library()

@register.filter
def get_field(obj, field_name):
    """Dohvaća vrijednost polja objekta.

    Args:
        obj: Objekt iz kojeg se dohvaća vrijednost.
        field_name (str): Naziv polja.

    Returns:
        Vrijednost polja ili None ako polje ne postoji ili dođe do greške.
    """
    try:
        # Pokušaj dohvatiti vrijednost atributa (polja)
        return getattr(obj, field_name)
    except (AttributeError, TypeError):
        # U slučaju greške (npr. atribut ne postoji), vrati None
        return None

@register.filter
def get_model_fields(record):
    """Vraća listu polja modela za prikaz, isključujući interna polja povijesti.

    Args:
        record: Instanca modela (ili zapisa povijesti).

    Returns:
        list: Lista objekata polja (Field objects) modela.
    """
    # Definiraj skup polja koja treba isključiti (interna polja simple_history)
    excluded_fields = {'id', 'history_id', 'history_date', 'history_type', 'history_user_id', 'history_change_reason'}
    # Vrati listu polja čija imena nisu u skupu isključenih polja
    return [f for f in record._meta.fields if f.name not in excluded_fields]

@register.filter
def get_field_changes(current, previous):
    """Dohvaća promjene između dvije verzije zapisa povijesti.

    Args:
        current: Trenutna verzija zapisa povijesti.
        previous: Prethodna verzija zapisa povijesti (može biti None).

    Returns:
        dict: Rječnik s promjenama, gdje je ključ naziv polja, a vrijednost 
              rječnik s 'name', 'old' i 'new' vrijednostima.
    """
    # Ako nema prethodne verzije, nema promjena
    if not previous:
        return {}
    
    changes = {}
    # Iteriraj kroz sva polja trenutnog zapisa
    for field in current._meta.fields:
        # Isključi interna polja povijesti i ID
        if field.name not in {'id', 'history_id', 'history_date', 'history_type', 'history_user_id', 'history_change_reason'}:
            # Dohvati staru i novu vrijednost polja
            old_value = getattr(previous, field.name, None)
            new_value = getattr(current, field.name, None)
            # Ako su vrijednosti različite, zabilježi promjenu
            if old_value != new_value:
                changes[field.name] = {
                    # Koristi verbose_name polja ako postoji, inače ime polja
                    'name': field.verbose_name or field.name,
                    # Formatiraj staru vrijednost (prikaži "(prazno)" za None)
                    'old': old_value if old_value is not None else "(prazno)",
                    # Formatiraj novu vrijednost (prikaži "(prazno)" za None)
                    'new': new_value if new_value is not None else "(prazno)"
                }
    return changes

@register.filter
def format_field_value(value):
    """Formatira vrijednost polja za čitljiv prikaz u predlošku.

    Args:
        value: Vrijednost polja.

    Returns:
        str: Formatirana vrijednost kao string.
    """
    # Ako je vrijednost None, vrati "(prazno)"
    if value is None:
        return "(prazno)"
    # Ako je vrijednost boolean, vrati "Da" ili "Ne"
    if isinstance(value, bool):
        return "Da" if value else "Ne"
    # Za sve ostale tipove, vrati string reprezentaciju
    return str(value)

@register.simple_tag
def get_history_url(model_name, object_id=None):
    """Generira URL za prikaz povijesti modela ili specifičnog objekta.

    Args:
        model_name (str): Naziv modela (npr. 'Salary', 'Employee').
        object_id (int, optional): ID specifičnog objekta. Ako je None, generira 
                                   URL za povijest cijelog modela.

    Returns:
        str: Generirani URL.
    """
    # Mapiranje naziva modela na URL slugove korištene u urls.py
    model_map = {
        'Salary': 'salary',
        'Employee': 'employee',
        'Company': 'company',
        'LocalIncomeTax': 'localtax',
        'TaxParameter': 'taxparam',
        'Client': 'client',
        'Product': 'product',
        'Offer': 'offer',
        'Invoice': 'invoice',
        'Inventory': 'inventory',
        'InvoiceProduct': 'invprdt',
        'OfferProduct': 'ofrprdt',
        'Supplier': 'supplier',
        'Expense': 'expense',
        'NonTaxablePaymentType': 'nontaxpaymtype',
        'NonTaxableAdditionLimit': 'nontaxaddlim',
    }
    
    # Dohvati slug iz mape
    model_slug = model_map.get(model_name)
    # Ako model nije u mapi, vrati URL za općeniti pregled povijesti
    if not model_slug:
        return reverse('view_history')
        
    # Ako je zadan ID objekta, generiraj URL za detaljni prikaz povijesti objekta
    if object_id:
        return reverse('view_history_detail', kwargs={'model_name': model_slug, 'object_id': object_id})
    # Inače, generiraj URL za prikaz povijesti cijelog modela
    return reverse('view_history_model', kwargs={'model_name': model_slug})

@register.simple_tag
def get_user_history_url(user_id):
    """Generira URL za prikaz povijesti izmjena određenog korisnika.

    Args:
        user_id (int): ID korisnika.

    Returns:
        str: Generirani URL.
    """
    # Vrati fiksni URL format s ID-em korisnika
    return f"/history/user/{user_id}/"

@register.filter
def model_verbose_name(instance):
    """Vraća čitljiv naziv modela (verbose_name) za danu instancu.

    Koristi se u history_view.html za prikaz naziva modela.

    Args:
        instance: Instanca modela.

    Returns:
        str: verbose_name modela ili "Objekt" ako nije dostupan.
    """
    # Provjeri postoji li instanca i ima li _meta atribut
    if instance and hasattr(instance, '_meta'):
        # Vrati verbose_name definiran u modelu
        return instance._meta.verbose_name
    # Ako nema instance ili _meta, vrati generički naziv
    return "Objekt"
