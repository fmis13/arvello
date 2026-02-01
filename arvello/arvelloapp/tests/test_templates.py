from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, timedelta
from arvelloapp.models import Invoice, Client, Company

class InvoiceTemplateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        # Ensure user has a subject (helpers.ensure_user_has_subject will create one on view load),
        # but create a explicit client to attach to invoices
        self.company = Company.objects.create(
            clientName='Test Subject',
            addressLine1='Test Address',
            town='TestTown',
            province='GRAD ZAGREB',
            postalCode='10000',
            phoneNumber='',
            emailAddress='',
            clientUniqueId='9999',
            clientType='Pravna osoba'
        )
        self.client_obj = Client.objects.create(
            clientName='Test Client',
            addressLine1='Client Address',
            province='GRAD ZAGREB',
            postalCode='10000',
            phoneNumber='',
            emailAddress='client@example.com',
            clientUniqueId='0001',
            clientType='Pravna osoba',
            VATID='HR1234567890123'
        )

    def test_empty_title_renders_empty_value(self):
        # Create invoice with no title
        inv = Invoice.objects.create(
            title=None,
            number='INV-0001',
            dueDate=date.today(),
            date=date.today(),
            client=self.client_obj,
            subject=self.company,
        )
        resp = self.client.get(reverse('invoices'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'class="empty-value"')
        self.assertContains(resp, '(prazno)')
        self.assertContains(resp, '∅')

    def test_overdue_row_has_overdue_class(self):
        # Create an overdue invoice (2 days late -> warning)
        past = date.today() - timedelta(days=2)
        inv = Invoice.objects.create(
            title='Overdue Invoice',
            number='INV-0002',
            dueDate=past,
            date=past,
            client=self.client_obj,
            subject=self.company,
            is_paid=False,
        )
        resp = self.client.get(reverse('invoices'))
        self.assertEqual(resp.status_code, 200)
        # The row should include the class for warning
        self.assertContains(resp, 'row-overdue-warning')

    def test_overdue_row_danger_class(self):
        # Create an overdue invoice more than 30 days late -> danger
        past = date.today() - timedelta(days=40)
        inv = Invoice.objects.create(
            title='Danger Overdue Invoice',
            number='INV-0005',
            dueDate=past,
            date=past,
            client=self.client_obj,
            subject=self.company,
            is_paid=False,
        )
        resp = self.client.get(reverse('invoices'))
        self.assertEqual(resp.status_code, 200)
        # The row should include the danger class
        self.assertContains(resp, 'row-overdue-danger')

    def test_due_date_formatted(self):
        d = date(2025, 12, 31)
        inv = Invoice.objects.create(
            title='DateTest',
            number='INV-0003',
            dueDate=d,
            date=d,
            client=self.client_obj,
            subject=self.company,
        )
        resp = self.client.get(reverse('invoices'))
        self.assertContains(resp, '31.12.2025.')

    def test_notes_have_title_attribute(self):
        long_notes = 'x' * 100
        inv = Invoice.objects.create(
            title='NotesTest',
            number='INV-0004',
            dueDate=date.today(),
            date=date.today(),
            client=self.client_obj,
            subject=self.company,
            notes=long_notes,
        )
        resp = self.client.get(reverse('invoices'))
        self.assertContains(resp, 'title="')
        self.assertContains(resp, long_notes)

    def test_invoice_row_has_break_word_class(self):
        """When there is an invoice, the title/notes cells get the break-word class."""
        inv = Invoice.objects.create(
            title='A long title that needs wrapping',
            number='INV-9999',
            dueDate=date.today(),
            date=date.today(),
            client=self.client_obj,
            subject=self.company,
            notes='Long notes here that should be breakable',
        )
        resp = self.client.get(reverse('invoices'))
        self.assertContains(resp, '<td class="wrap break-word">')
        self.assertContains(resp, 'Long notes here that should be breakable')
    def test_invoices_table_has_wrap_and_actions_classes(self):
        """Check the invoice list table uses the `wrap` and `actions` classes."""
        resp = self.client.get(reverse('invoices'))
        self.assertEqual(resp.status_code, 200)
        # table itself should have the wrap class and be marked as invoice-table
        self.assertContains(resp, 'class="table table-hover mb-0 wrap invoice-table"')
        # header cells should include wrap+break-word on title and actions on the actions column
        self.assertContains(resp, '<th scope="col" class="col-title wrap break-word">')
        self.assertContains(resp, '<th scope="col" class="text-center text-nowrap actions-col actions" style="min-width: 180px;">Akcije</th>')
        # title and notes header cells should be marked to allow breaking (row td tested separately)
        # (Individual row td presence is verified in a separate test when an invoice exists)

    def test_ui_css_contains_wrap_and_actions_rules(self):
        """Simple smoke test that the CSS file was updated with wrap and actions rules."""
        from django.conf import settings
        import os
        import glob
        # Try to find ui.css anywhere under the project (robust to different BASE_DIR layouts)
        candidates = glob.glob(os.path.join(settings.BASE_DIR, '**', 'static', 'css', 'ui.css'), recursive=True)
        self.assertTrue(len(candidates) > 0, f"Could not find ui.css under {settings.BASE_DIR}")
        css_path = candidates[0]
        with open(css_path, 'r') as fh:
            css = fh.read()
        self.assertIn('.table.wrap', css)
        self.assertIn('overflow-wrap: anywhere', css)
        self.assertIn('.table .actions', css)
        # Invoice-table specific rules
        self.assertIn('.invoice-table', css)
        self.assertIn('.invoice-table .actions', css)
        self.assertIn('.break-word', css)
