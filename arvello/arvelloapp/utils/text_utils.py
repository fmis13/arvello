import re

def standardize_city_name(city_name):
    """
    Standardizira ime grada za dosljednu pretragu i usporedbu.

    Koraci:
    - Uklanja višestruke razmake.
    - Pretvara sva slova u velika.
    - Zamjenjuje hrvatske dijakritičke znakove (Š, Đ, Č, Ć, Ž) s njihovim 
      osnovnim latiničnim ekvivalentima (S, D, C, C, Z).
    - Uklanja sve znakove koji nisu slova (A-Z), brojevi (0-9) ili razmaci.

    Args:
        city_name (str): Ime grada koje treba standardizirati.

    Returns:
        str: Standardizirano ime grada ili prazan string ako je ulaz None ili prazan.
    """
    # Ako je ulazni string None ili prazan, vrati prazan string
    if not city_name:
        return ""
        
    # Pretvori u velika slova
    city = city_name.upper()
    
    # Zamijeni hrvatske znakove
    replacements = {
        'Š': 'S', 'Đ': 'D', 'Č': 'C', 
        'Ć': 'C', 'Ž': 'Z'
    }
    for old, new in replacements.items():
        city = city.replace(old, new)
    
    # Očisti specijalne znakove (sve osim slova, brojeva i razmaka)
    city = re.sub(r'[^A-Z0-9\s]', '', city)
    
    # Ukloni višestruke razmake (zamijeni s jednim razmakom)
    city = ' '.join(city.split())
    
    # Vrati standardizirani naziv grada
    return city
