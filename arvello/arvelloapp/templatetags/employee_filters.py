from django import template

register = template.Library()

@register.filter
def map_attr(queryset, attr):
    """Vraća listu vrijednosti za zadani atribut iz queryseta.

    Primjer korištenja u predlošku:
    {{ my_queryset|map_attr:'id' }}
    """
    # Koristi list comprehension za dohvaćanje atributa svakog objekta u querysetu
    return [getattr(obj, attr) for obj in queryset]

@register.filter
def filter_not_in(queryset, comma_separated_ids):
    """Filtrira queryset tako da isključi objekte čiji su ID-evi u listi odvojenoj zarezima.

    Args:
        queryset: Django QuerySet koji se filtrira.
        comma_separated_ids (str): String s ID-evima odvojenim zarezima.

    Returns:
        QuerySet: Filtrirani QuerySet.

    Primjer korištenja u predlošku:
    {{ all_employees|filter_not_in:selected_employee_ids }}
    """
    # Ako string s ID-evima nije zadan ili je prazan, vrati originalni queryset
    if not comma_separated_ids:
        return queryset
    
    # Pretvori string ID-eva u listu integera
    # Filtriraj prazne stringove koji mogu nastati ako postoje dupli zarezi
    exclude_ids = [int(id) for id in comma_separated_ids.split(',') if id]
    
    # Isključi objekte s ID-evima iz generirane liste
    return queryset.exclude(id__in=exclude_ids)
