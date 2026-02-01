import os
import logging
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def get_email_backend_for_company(company):
    """
    Vraća email backend konfiguriran za specifičnu tvrtku.
    Ako tvrtka ima konfiguriranu email postavku, koristi je.
    Inače koristi globalne postavke iz settings.py.
    """
    try:
        from arvelloapp.models import EmailConfig
        email_config = EmailConfig.objects.get(company=company, is_active=True)
        
        return get_connection(
            host=email_config.smtp_host,
            port=email_config.smtp_port,
            username=email_config.smtp_user,
            password=email_config.smtp_password,
            use_tls=email_config.use_tls,
            use_ssl=email_config.use_ssl,
        ), email_config
    except Exception:
        # Fallback na globalne postavke
        return None, None


def send_test_email(email_config, recipient_email):
    """
    Šalje testni email koristeći danu konfiguraciju.
    
    Args:
        email_config: EmailConfig objekt
        recipient_email: Email adresa primatelja
        
    Returns:
        tuple: (bool success, str message)
    """
    try:
        connection = get_connection(
            host=email_config.smtp_host,
            port=email_config.smtp_port,
            username=email_config.smtp_user,
            password=email_config.smtp_password,
            use_tls=email_config.use_tls,
            use_ssl=email_config.use_ssl,
        )
        
        email = EmailMessage(
            subject='Arvello - Test email konfiguracije',
            body=f'''<html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>🎉 Email konfiguracija uspješno testirana!</h2>
                <p>Ovaj email potvrđuje da je vaša email konfiguracija za <strong>{email_config.company.clientName}</strong> ispravno postavljena.</p>
                <hr>
                <p><strong>Detalji konfiguracije:</strong></p>
                <ul>
                    <li>SMTP poslužitelj: {email_config.smtp_host}</li>
                    <li>Port: {email_config.smtp_port}</li>
                    <li>TLS: {"Da" if email_config.use_tls else "Ne"}</li>
                    <li>SSL: {"Da" if email_config.use_ssl else "Ne"}</li>
                </ul>
                <p style="color: #666; font-size: 12px;">Ovaj email je automatski generiran iz Arvello sustava.</p>
            </body>
            </html>''',
            from_email=email_config.get_from_email_formatted(),
            to=[recipient_email],
            connection=connection,
        )
        email.content_subtype = "html"
        email.send()
        return True, 'Testni email uspješno poslan!'
    except Exception as e:
        return False, f'Greška pri slanju testnog emaila: {str(e)}'


def send_payslip_email(subject, message, recipient_email, pdf_path, sender_name, reply_to_email, salary):
    """
    Šalje e-mail s PDF privitkom koristeći HTML predložak.
    Koristi email konfiguraciju za tvrtku ako postoji.

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
        # Pokušaj dohvatiti email konfiguraciju za tvrtku
        connection, email_config = get_email_backend_for_company(salary.employee.company)
        
        # Odredi from_email na temelju konfiguracije
        if email_config:
            from_email = email_config.get_from_email_formatted()
        else:
            from_email = f"{sender_name} <{settings.EMAIL_HOST_USER}>"
        
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
            from_email=from_email,
            to=[recipient_email],
            reply_to=[reply_to_email],
            connection=connection,
        )
        email.content_subtype = "html"  # Postavi sadržaj na HTML
        email.attach_file(pdf_path)
        email.send()
        return True
    except Exception as e:
        logger.error(f"Greška pri slanju e-maila: {e}")
        return False

def send_email_with_attachment(subject, body, recipient_email, attachment, attachment_name, sender_name, reply_to_email, company=None):
    """
    Šalje e-mail s privitkom.
    Koristi email konfiguraciju za tvrtku ako je proslijeđena.
    """
    try:
        connection = None
        from_email = f"{sender_name} <{settings.EMAIL_HOST_USER}>"
        
        # Ako je proslijeđena tvrtka, pokušaj dohvatiti njenu email konfiguraciju
        if company:
            connection, email_config = get_email_backend_for_company(company)
            if email_config:
                from_email = email_config.get_from_email_formatted()
        
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[recipient_email],
            reply_to=[reply_to_email],
            connection=connection,
        )
        email.attach(attachment_name, attachment, 'application/pdf')
        email.content_subtype = "html"
        email.send()
        return True
    except Exception as e:
        logger.error(f"Greška pri slanju e-maila: {e}")
        return False
