from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from arvelloapp.models import UserProfile, SubjectMembership, Client, Invoice


User = get_user_model()


class SubjectsUsersTests(TestCase):
    def test_user_profile_auto_created(self):
        """Creating a User must auto-create a UserProfile via signal."""
        user = User.objects.create_user(username='u1', password='pass')
        # refresh from db and check profile exists
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsNotNone(user.profile)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_invoices_view_creates_company_and_membership(self):
        """Posting to invoices without a subject should create a Company and membership and assign it."""
        user = User.objects.create_user(username='issuer', password='secret')

        # create a client to reference in the invoice
        client = Client.objects.create(
            clientName='C1',
            addressLine1='Addr',
            province='GRAD ZAGREB',
            postalCode='10000',
            phoneNumber='+385123456789',
            emailAddress='c1@example.com',
            clientUniqueId='9001',
            clientType='Fizička osoba',
            OIB='12345678901',
            VATID='HR11111111111'
        )

        self.client.force_login(user)

        url = reverse('invoices')
        today = timezone.now().date().isoformat()
        post_data = {
            'title': 'T',
            'number': '1-1-25',
            'date': today,
            'dueDate': today,
            'client': str(client.id),
            # intentionally omit 'subject' so view should create one
            'notes': 'n',
        }

        resp = self.client.post(url, data=post_data, follow=True)
        self.assertIn(resp.status_code, (200, 302))

        # an invoice should have been created
        invoice = Invoice.objects.first()
        self.assertIsNotNone(invoice, 'Invoice was not created')

        # the invoice should have a subject assigned
        self.assertIsNotNone(invoice.subject)

        # the user's profile should point to an active company
        user.refresh_from_db()
        self.assertIsNotNone(user.profile.active_company)

        # membership should exist linking the user and the created company
        self.assertTrue(SubjectMembership.objects.filter(user=user, company=invoice.subject).exists())
