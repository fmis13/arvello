from decimal import Decimal
import xml.etree.ElementTree as ET
from django.utils import timezone
from arvelloapp.models import *
from lxml import etree
from datetime import datetime
import uuid

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

def generate_joppd_xml(data):
    """
    Generira JOPPD XML na temelju danih podataka.

    Args:
        data (dict): Podaci za generiranje JOPPD izvještaja.

    Returns:
        str: Generirani XML kao string.
    """
    # Definiraj namespace i root element
    nsmap = {
        None: "http://e-porezna.porezna-uprava.hr/sheme/zahtjevi/ObrazacJOPPD/v1-1",
        "meta": "http://e-porezna.porezna-uprava.hr/sheme/Metapodaci/v2-0"
    }
    root = etree.Element("ObrazacJOPPD", nsmap=nsmap, attrib={"verzijaSheme": "1.1"})

    # Metapodaci
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

    # Strana A
    strana_a = etree.SubElement(root, "StranaA")
    etree.SubElement(strana_a, "DatumIzvjesca").text = data["report_date"]
    etree.SubElement(strana_a, "OznakaIzvjesca").text = data["report_id"]
    etree.SubElement(strana_a, "VrstaIzvjesca").text = data["report_type"]

    # Podnositelj izvješća
    podnositelj = etree.SubElement(strana_a, "PodnositeljIzvjesca")
    etree.SubElement(podnositelj, "Naziv").text = data["submitter"]["name"]
    adresa = etree.SubElement(podnositelj, "Adresa")
    etree.SubElement(adresa, "Mjesto").text = data["submitter"]["address"]["city"]
    etree.SubElement(adresa, "Ulica").text = data["submitter"]["address"]["street"]
    etree.SubElement(adresa, "Broj").text = data["submitter"]["address"]["number"]
    etree.SubElement(podnositelj, "Email").text = data["submitter"]["email"]
    etree.SubElement(podnositelj, "OIB").text = data["submitter"]["oib"]
    etree.SubElement(podnositelj, "Oznaka").text = data["submitter"]["label"]

    # Doprinosi
    doprinosi = etree.SubElement(strana_a, "Doprinosi")
    for key, value in data["contributions"].items():
        etree.SubElement(doprinosi, key).text = f"{value:.2f}"

    # Strana B
    strana_b = etree.SubElement(root, "StranaB")
    for recipient in data["recipients"]:
        p = etree.SubElement(strana_b, "Primatelji")
        for key, value in recipient.items():
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
