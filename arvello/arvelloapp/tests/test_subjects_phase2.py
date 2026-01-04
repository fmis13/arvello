from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from arvelloapp.models import Company, SubjectMembership, Client
from arvelloapp.helpers import ensure_user_has_subject
from django.utils import timezone

User = get_user_model()


class SubjectsPhase2Tests(TestCase):
    def test_ensure_user_has_subject_creates_and_assigns(self):
        user = User.objects.create_user(username='subuser', password='pass')
        # ensure helper creates a subject and membership
        subject = ensure_user_has_subject(user)
        self.assertIsNotNone(subject)
        self.assertTrue(SubjectMembership.objects.filter(user=user, company=subject).exists())
        user.refresh_from_db()
        self.assertIsNotNone(user.profile.active_subject)
        self.assertEqual(user.profile.active_subject, subject)

    def test_invoice_create_assigns_subject_when_missing(self):
        user = User.objects.create_user(username='invuser', password='pass')
        client = Client.objects.create(
            clientName='C1', addressLine1='Addr', province='GRAD ZAGREB', postalCode='10000',
            phoneNumber='+385123456789', emailAddress='c1@example.com', clientUniqueId='9002', clientType='Fizička osoba', VATID='HR22222222222'
        )
        self.client.force_login(user)
        url = reverse('invoices')
        today = timezone.now().date().isoformat()
        post_data = {
            'title': 'T', 'number': '1-1-25', 'date': today, 'dueDate': today, 'client': str(client.id), 'notes': 'n'
        }
        resp = self.client.post(url, data=post_data, follow=True)
        self.assertIn(resp.status_code, (200, 302))
        from arvelloapp.models import Invoice
        invoice = Invoice.objects.first()
        self.assertIsNotNone(invoice)
        # invoice.subject should equal user's active_subject
        user.refresh_from_db()
        self.assertIsNotNone(user.profile.active_subject)
        self.assertEqual(invoice.subject, user.profile.active_subject)

    def test_subject_switch_api_membership_and_forbidden(self):
        user = User.objects.create_user(username='swuser', password='pass')
        other = User.objects.create_user(username='other', password='pass')
        company = Company.objects.create(
            clientName='SwitchCo', addressLine1='A', town='Z', province='GRAD ZAGREB', postalCode='10000', phoneNumber='', emailAddress='', clientUniqueId='1234', clientType='Pravna osoba'
        )
        # create membership for user only
        SubjectMembership.objects.create(user=user, company=company, role=SubjectMembership.ROLE_ADMIN)

        # member can switch
        self.client.force_login(user)
        url = reverse('subject-switch')
        resp = self.client.post(url, data={'subject_id': str(company.id)})
        self.assertEqual(resp.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.profile.active_subject.id, company.id)

        # non-member cannot
        self.client.force_login(other)
        resp2 = self.client.post(url, data={'subject_id': str(company.id)})
        self.assertEqual(resp2.status_code, 403)

    def test_subject_create_view_sets_owner_and_active(self):
        user = User.objects.create_user(username='creator', password='pass')
        self.client.force_login(user)
        url = reverse('subject-create')
        resp = self.client.post(url, data={'clientName': 'NewSub', 'addressLine1': 'Addr', 'town': 'Zagreb'}, follow=True)
        # created
        self.assertIn(resp.status_code, (200, 302))
        c = Company.objects.filter(clientName='NewSub').first()
        self.assertIsNotNone(c)
        self.assertTrue(SubjectMembership.objects.filter(user=user, company=c, role=SubjectMembership.ROLE_OWNER).exists())
        user.refresh_from_db()
        self.assertEqual(user.profile.active_subject, c)
