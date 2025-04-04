from io import BytesIO
import os
from django.conf import settings
from django.template.loader import get_template, render_to_string
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal
from weasyprint import HTML
from .payslip_context import get_payslip_context 
from .email_utils import send_payslip_email

def html_to_pdf(template_src, context_dict={}):
    """Generira PDF iz HTML predloška.

    Args:
        template_src (str): Putanja do HTML predloška.
        context_dict (dict, optional): Rječnik s kontekstom za renderiranje predloška. 
                                       Zadano je prazan rječnik.

    Returns:
        HttpResponse: HTTP odgovor s PDF sadržajem ili None ako dođe do greške.
    """
    # Dohvati predložak
    template = get_template(template_src)
    # Renderiraj HTML s danim kontekstom
    html = template.render(context_dict)
    # Kreiraj BytesIO objekt za spremanje PDF-a u memoriju
    result = BytesIO()
    # Generiraj PDF koristeći xhtml2pdf
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    # Ako nema grešaka pri generiranju PDF-a
    if not pdf.err:
        # Vrati HTTP odgovor s PDF sadržajem
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    # Ako je došlo do greške, vrati None
    return None

def generate_payslip_pdf(salary, request, template_name='salary_payslip_pdf.html'):
    """Generira PDF platne liste i šalje ga putem e-maila."""
    # Dohvati kontekst za platnu listu
    context = get_payslip_context(salary)

    # Renderiraj HTML sadržaj za PDF
    template = get_template(template_name)
    html_content = template.render(context)

    # Kreiraj PDF i spremi na disk
    pdf_path = f"/tmp/platna_lista_{salary.employee.get_full_name()}_{salary.period_year}_{salary.period_month}.pdf"
    with open(pdf_path, "wb") as pdf_file:
        HTML(string=html_content, base_url=request.build_absolute_uri('/')).write_pdf(pdf_file)

    # Provjeri i formatiraj potrebne varijable
    employee_name = salary.employee.get_full_name() if hasattr(salary.employee, 'get_full_name') else "Nepoznato ime"
    period_month = f"{salary.period_month:02d}" if salary.period_month else "-"
    period_year = str(salary.period_year) if salary.period_year else "-"
    company_name = salary.employee.company.clientName if hasattr(salary.employee.company, 'clientName') else "Nepoznata tvrtka"
    issued_by_name = salary.created_by.get_full_name() if salary.created_by else "Nepoznato ime"
    reply_to_email = salary.employee.company.emailAddress if hasattr(salary.employee.company, 'emailAddress') else settings.EMAIL_HOST_USER


    # Generiraj HTML sadržaj e-maila
    message = render_to_string('email_templates/payslip_email.html', {
        'employee_name': employee_name,
        'period_month': period_month,
        'period_year': period_year,
        'company_name': company_name,
        'issued_by_name': issued_by_name,
    })

    #print(message)

    # Pošalji e-mail s PDF privitkom
    subject = f"Platna lista za {period_month}/{period_year}"
    recipient_email = salary.employee.email
    sender_name = company_name

    email_sent = send_payslip_email(subject, message, recipient_email, pdf_path, sender_name, reply_to_email, salary)

    if email_sent:
        print("E-mail uspješno poslan.")
    else:
        print("Greška pri slanju e-maila.")

    # Vrati PDF kao HTTP odgovor
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="platna_lista_{salary.employee.get_full_name()}_{salary.period_year}_{salary.period_month}.pdf"'
    HTML(string=html_content, base_url=request.build_absolute_uri('/')).write_pdf(response)
    return response
