from decimal import Decimal
import xml.etree.ElementTree as ET
from django.utils import timezone
from arvelloapp.models import *
from lxml import etree
from datetime import datetime, date
import uuid
from django.db.models import Sum

def get_monthly_tax_threshold(year):
    """Dohvati mjesečni prag za porez iz TaxParameter modela za zadanu godinu."""
    try:
        # Pokušaj pronaći parametar za mjesečni prag poreza za danu godinu
        tax_param = TaxParameter.objects.get(
            parameter_type='monthly_tax_threshold',
            year=year
        )
        # Vrati vrijednost praga kao Decimal
        return Decimal(str(tax_param.value))
    except TaxParameter.DoesNotExist:
        # Ako parametar nije pronađen, vrati zadanu (default) vrijednost
        return Decimal('5000.00')  # default ako ne postoji

def generate_joppd_xml(salaries, year, month, company_subject):
    """
    Generira JOPPD XML na temelju QuerySet-a plaća i dodatnih podataka.

    Args:
        salaries (QuerySet): QuerySet Salary objekata.
        year (int): Godina za koju se generira izvještaj.
        month (int): Mjesec za koji se generira izvještaj.
        company_subject (Company): Objekt tvrtke koja podnosi izvještaj.

    Returns:
        str: Generirani XML kao string.
    """
    # Definiraj namespace i root element
    nsmap = {
        None: "http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacJOPPD/v1-1",
        "meta": "http://e-porezna.porezna-uprava.hr/sheme/Metapodaci/v2-0"
    }
    root = etree.Element("ObrazacJOPPD", nsmap=nsmap, attrib={"verzijaSheme": "1.1"})

    # Konstruiraj 'data' rječnik iz prosljeđenih argumenata
    report_date = date(year, month, 1) # Koristi prvi dan mjeseca kao referencu
    report_id = f"{year}{month:02d}01" # Primjer oznake izvješća (prilagoditi po potrebi)

    # Izračunaj ukupne doprinose za Stranu A
    totals = salaries.aggregate(
        total_pension_pillar_1=Sum('pension_pillar_1'),
        total_pension_pillar_2=Sum('pension_pillar_2'),
        total_health_insurance=Sum('health_insurance'),
        total_income_tax=Sum('income_tax')
        # Dodaj ostale sume ako su potrebne za <Doprinosi> tag
    )

    data = {
        "author": company_subject.clientName, # Koristi ime tvrtke kao autora
        "report_date": report_date.strftime("%Y-%m-%d"),
        "report_id": report_id,
        "report_type": "1", # Prilagoditi prema potrebi (npr. 1 za originalni)
        "submitter": {
            "name": company_subject.clientName,
            "address": {
                "city": company_subject.town,
                "street": company_subject.addressLine1,
                "number": "" # Dodati ako postoji zasebno polje za broj (ne zasad)
            },
            "email": company_subject.emailAddress,
            "oib": company_subject.OIB,
            "label": "1" # Oznaka podnositelja (npr. 1 za Poslodavac, u teoriji je uvijek tako)
        },
        "contributions": {
            # Mapiraj agregirane sume na odgovarajuće XML tagove
            "MIO1": totals.get('total_pension_pillar_1', Decimal('0.00')) or Decimal('0.00'),
            "MIO2": totals.get('total_pension_pillar_2', Decimal('0.00')) or Decimal('0.00'),
            "ZO": totals.get('total_health_insurance', Decimal('0.00')) or Decimal('0.00'),
            "Porez": totals.get('total_income_tax', Decimal('0.00')) or Decimal('0.00'),
            # Dodaj ostale potrebne sume...
        },
        "recipients": [] # Lista za podatke o primateljima (Strana B)
    }
    # Kraj konstrukcije 'data' rječnika


    # Metapodaci (koristi podatke iz 'data' rječnika)
    meta = etree.SubElement(root, "{http://e-porezna.porezna-uprava.hr/sheme/Metapodaci/v2-0}Metapodaci")
    etree.SubElement(meta, "{http://purl.org/dc/elements/1.1/title}Naslov").text = "Izvješće o primicima, porezu na dohodak i prirezu te doprinosima za obvezna osiguranja"
    etree.SubElement(meta, "{http://purl.org/dc/elements/1.1/creator}Autor").text = data["author"]
    etree.SubElement(meta, "{http://purl.org/dc/elements/1.1/date}Datum").text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    etree.SubElement(meta, "{http://purl.org/dc/elements/1.1/format}Format").text = "text/xml"
    etree.SubElement(meta, "{http://purl.org/dc/elements/1.1/language}Jezik").text = "hr-HR"
    etree.SubElement(meta, "{http://purl.org/dc/elements/1.1/identifier}Identifikator").text = str(uuid.uuid4())
    etree.SubElement(meta, "{http://purl.org/dc/terms/conformsTo}Uskladjenost").text = "ObrazacJOPPD-v1-1"
    etree.SubElement(meta, "{http://purl.org/dc/elements/1.1/type}Tip").text = "Elektronički obrazac"
    etree.SubElement(meta, "{http://purl.org/dc/elements/1.1/Adresant}Adresant").text = "Ministarstvo Financija, Porezna uprava, Zagreb"

    # Strana A (koristi podatke iz 'data' rječnika)
    strana_a = etree.SubElement(root, "StranaA")
    etree.SubElement(strana_a, "DatumIzvjesca").text = data["report_date"]
    etree.SubElement(strana_a, "OznakaIzvjesca").text = data["report_id"]
    etree.SubElement(strana_a, "VrstaIzvjesca").text = data["report_type"]

    # Podnositelj izvješća (koristi podatke iz 'data' rječnika)
    podnositelj = etree.SubElement(strana_a, "PodnositeljIzvjesca")
    etree.SubElement(podnositelj, "Naziv").text = data["submitter"]["name"]
    adresa = etree.SubElement(podnositelj, "Adresa")
    etree.SubElement(adresa, "Mjesto").text = data["submitter"]["address"]["city"]
    etree.SubElement(adresa, "Ulica").text = data["submitter"]["address"]["street"]
    etree.SubElement(adresa, "Broj").text = data["submitter"]["address"]["number"]
    etree.SubElement(podnositelj, "Email").text = data["submitter"]["email"]
    etree.SubElement(podnositelj, "OIB").text = data["submitter"]["oib"]
    etree.SubElement(podnositelj, "Oznaka").text = data["submitter"]["label"]

    # Doprinosi (koristi podatke iz 'data' rječnika)
    doprinosi = etree.SubElement(strana_a, "Doprinosi")
    for key, value in data["contributions"].items():
        etree.SubElement(doprinosi, key).text = f"{value:.2f}"

    # Strana B - Iteriraj kroz QuerySet plaća
    strana_b = etree.SubElement(root, "StranaB")
    rb = 0 # Redni broj primatelja
    for salary in salaries:
        rb += 1
        employee = salary.employee
        # Dohvati mjesečni prag za godinu plaće
        monthly_threshold = get_monthly_tax_threshold(salary.period_year)

        # Izračunaj osnovicu za doprinose (Bruto plaća)
        osnovica_doprinosi = salary.gross_salary

        # Izračunaj osnovicu za porez (Dohodak - Osobni odbitak)
        dohodak = salary.gross_salary - salary.pension_pillar_1 - salary.pension_pillar_2
        osobni_odbitak = employee.calculate_personal_deduction()
        porezna_osnovica = max(Decimal(0), dohodak - osobni_odbitak)

        # Izračunaj iznos poreza po nižoj i višoj stopi
        iznos_porez_niza = salary.lower_tax_amount
        iznos_porez_visa = salary.higher_tax_amount

        # Pripremi podatke za primatelja
        recipient_data = {
            "P1": str(rb),
            "P2": employee.oib,
            "P3": f"{employee.last_name} {employee.first_name}",
            "P4": "1", # Oznaka stjecatelja (npr. 1 za Radnik)
            "P5": "0001", # Oznaka primitka/obveze doprinosa (npr. 0001 za Plaća)
            "P61": "0000", # Oznaka prvog/zadnjeg mjeseca (prilagoditi ako treba)
            "P62": "0000", # Oznaka prvog/zadnjeg mjeseca (prilagoditi ako treba)
            "P71": salary.regular_hours + salary.vacation_hours + salary.sick_leave_hours + salary.overtime_hours, # Ukupni sati rada (provjeriti logiku)
            "P72": 0, # Sati prekovremenog (ako se zasebno iskazuju)
            "P8": f"{salary.gross_salary:.2f}", # Bruto plaća
            "P91": f"{salary.pension_pillar_1:.2f}", # Doprinos MIO I. stup
            "P92": f"{salary.pension_pillar_2:.2f}", # Doprinos MIO II. stup
            "P101": f"{dohodak:.2f}", # Dohodak
            "P102": f"{osobni_odbitak:.2f}", # Osobni odbitak
            "P103": f"{porezna_osnovica:.2f}", # Porezna osnovica
            "P104": f"{iznos_porez_niza:.2f}", # Iznos poreza (niža stopa)
            "P105": f"{iznos_porez_visa:.2f}", # Iznos poreza (viša stopa)
            "P106": "0.00", # Iznos prireza (dodati izračun ako postoji)
            "P11": f"{salary.net_salary:.2f}", # Neto plaća
            "P12": "1", # Način isplate (npr. 1 za Tekući račun)
            # Dodati ostala obavezna i opcionalna polja prema JOPPD specifikaciji
        }

        p = etree.SubElement(strana_b, "Primatelji")
        for key, value in recipient_data.items():
            # Preskoči prazne vrijednosti ako nisu obavezne po shemi
            if value is not None and value != '':
                 etree.SubElement(p, key).text = str(value)

    # Generiraj XML string
    return etree.tostring(root, pretty_print=True, encoding="UTF-8", xml_declaration=True).decode("utf-8")

def mark_salaries_as_reported(salaries, joppd_reference):
    """Označi plaće kao prijavljene u JOPPD sustav."""
    count = 0
    for salary in salaries:
        salary.joppd_status = True
        salary.joppd_reference = joppd_reference
        salary.save(update_fields=['joppd_status', 'joppd_reference'])
        count += 1
    return count

def validate_joppd_xml(xml_content, xsd_path):
    """
    Validira JOPPD XML koristeći XSD.

    Args:
        xml_content (str): XML sadržaj kao string.
        xsd_path (str): Putanja do XSD datoteke.

    Returns:
        bool: True ako je XML ispravan, False inače.
    """
    with open(xsd_path, 'rb') as xsd_file:
        schema = etree.XMLSchema(etree.parse(xsd_file))
        xml_doc = etree.fromstring(xml_content.encode("utf-8"))
        return schema.validate(xml_doc)
