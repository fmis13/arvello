import os
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string

def send_payslip_email(subject, message, recipient_email, pdf_path, sender_name, reply_to_email, salary):
    """
    Šalje e-mail s PDF privitkom koristeći HTML predložak.

    Args:
        subject (str): Naslov e-maila.
        message (str): Poruka e-maila.
        recipient_email (str): E-mail adresa primatelja.
        pdf_path (str): Putanja do PDF datoteke za privitak.
        sender_name (str): Ime pošiljatelja (npr. ime firme).
        reply_to_email (str): E-mail adresa za odgovor.
        salary (Salary): Objekt modela Salary koji sadrži podatke o plaći.

    Returns:
        bool: True ako je e-mail uspješno poslan, False inače.
    """
    try:
        # Renderiraj HTML predložak koristeći podatke iz modela Salary
        html_message = render_to_string('email_templates/payslip_email.html', 
            context={
            'employee_name': salary.employee.get_full_name(),
            'period_month': f"{salary.period_month:02d}",
            'period_year': salary.period_year,
            'company_name': salary.employee.company.clientName,
            'issued_by_name': salary.created_by.get_full_name(),
        })

        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=f"{sender_name} <{settings.EMAIL_HOST_USER}>",
            to=[recipient_email],
            reply_to=[reply_to_email],
        )
        email.content_subtype = "html"  # Postavi sadržaj na HTML
        email.attach_file(pdf_path)
        email.send()
        return True
    except Exception as e:
        print(f"Greška pri slanju e-maila: {e}")
        return False

def send_email_with_attachment(subject, body, recipient_email, attachment, attachment_name, sender_name, reply_to_email):
    """Šalje e-mail s privitkom."""
    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=f"{sender_name} <{settings.EMAIL_HOST_USER}>",
            to=[recipient_email],
            reply_to=[reply_to_email],
        )
        email.attach(attachment_name, attachment, 'application/pdf')
        email.content_subtype = "html"
        email.send()
        return True
    except Exception as e:
        print(f"Greška pri slanju e-maila: {e}")
        return False
