from decimal import Decimal, InvalidOperation

def safe_decimal(value, default=Decimal('0')):
    """
    Sigurno pretvara ulaznu vrijednost u Decimal tip.

    Args:
        value: Vrijednost koja se pretvara (može biti string, broj, None, itd.).
        default (Decimal, optional): Vrijednost koja se vraća ako pretvorba ne uspije. 
                                     Zadano je Decimal('0').

    Returns:
        Decimal: Pretvorjena Decimal vrijednost ili zadana vrijednost u slučaju greške.
    """
    
    # Ako je ulazna vrijednost None, vrati zadanu vrijednost
    if value is None:
        return default
    
    try:
        # Pokušaj pretvoriti vrijednost u string (za svaki slučaj) i zatim u Decimal
        result = Decimal(str(value))
        return result
    except (ValueError, TypeError, InvalidOperation) as e:
        # Ako dođe do greške tijekom pretvorbe (npr. neispravan format),
        # vrati zadanu vrijednost.
        return default
