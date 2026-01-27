from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from arvelloapp.models import UserProfile, Payslip, Company, Employee, Client, SubjectMembership
from uuid import uuid4

User = get_user_model()


def make_company(suffix="1"):
    # use deterministic 4-char id from uuid for clientUniqueId
    uid = uuid4().hex[:4]
    return Company.objects.create(
        clientName=f"Company {suffix}",
        addressLine1="Street 1",
        town="Zagreb",
        province="GRAD ZAGREB",
        postalCode="10000",
        phoneNumber="+38512345678",
        emailAddress=f"c{suffix}@example.test",
        clientUniqueId=uid,
        clientType="Pravna osoba",
    )


def make_client(suffix="1"):
    return Client.objects.create(
        clientName=f"Client {suffix}",
        addressLine1="Street 1",
        province="GRAD ZAGREB",
        postalCode="10000",
        phoneNumber="+38512345678",
        emailAddress=f"client{suffix}@example.test",
        clientUniqueId=str(2000 + int(suffix))[-4:],
        clientType="Pravna osoba",
        VATID=f"HR0000000000{suffix}",
    )


class PalaceBackendTests(TestCase):
    def test_userprofile_auto_created(self):
        user = User.objects.create_user(username='u_profile', password='pass')
        # Profile should be auto-created by post_save signal
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_create_payslip_links_to_employee_and_subject(self):
        # create company and employee
        company = make_company('10')
        employee = Employee.objects.create(
            first_name='John', last_name='Doe', date_of_birth='1990-01-01',
            email='john@example.test', phone='+38511111111', oib='12345678901',
            address='Addr', city='Zagreb', postal_code='10000', company=company,
            hourly_rate='10.00', date_of_employment='2020-01-01', job_title='Dev', iban='HR1210010051863000160',
            tax_deduction_coefficient='1.0', work_experience_percentage='0.0', annual_vacation_days=20,
            pension_pillar=2, pension_pillar_3=False
        )

        initial_count = Payslip.objects.count()
        payslip = Payslip.objects.create(
            employee=employee,
            subject=company,
            period_month=12,
            period_year=2025,
            gross='2000.00',
            net='1500.00',
            taxes='500.00',
            status='final'
        )
        self.assertEqual(Payslip.objects.count(), initial_count + 1)
        self.assertEqual(payslip.employee, employee)
        self.assertEqual(payslip.subject, company)

    def test_invoice_helper_assigns_subject_when_missing(self):
        # Simulate helper: if user has no active_subject/company, create one and assign
        def assign_default_subject_for_user(user):
            profile = getattr(user, 'profile', None)
            if profile is None:
                profile = UserProfile.objects.create(user=user)
            if profile.active_subject:
                return profile.active_subject
            # create default subject and assign
            c = make_company('inv')
            profile.active_subject = c
            profile.active_company = c
            profile.save()
            # ensure membership exists
            SubjectMembership.objects.create(user=user, company=c, role=SubjectMembership.ROLE_OWNER)
            return c

        user = User.objects.create_user(username='invoice_user', password='pass')
        client = make_client('3')

        # "View" would call helper when subject omitted
        subject = assign_default_subject_for_user(user)
        from arvelloapp.models import Invoice
        invoice = Invoice.objects.create(
            title='Test', number='INV/0001', dueDate='2025-12-01', notes='n', client=client, subject=subject, date='2025-12-01'
        )
        self.assertIsNotNone(invoice.subject)
        self.assertEqual(invoice.subject, subject)
        # membership should exist
        self.assertTrue(SubjectMembership.objects.filter(user=user, company=subject).exists())

    def test_subject_membership_uniqueness(self):
        user = User.objects.create_user(username='muser', password='pass')
        c = make_company('u')
        SubjectMembership.objects.create(user=user, company=c, role=SubjectMembership.ROLE_ADMIN)
        # duplicate should raise IntegrityError at DB level
        with self.assertRaises(IntegrityError):
            SubjectMembership.objects.create(user=user, company=c, role=SubjectMembership.ROLE_ADMIN)
