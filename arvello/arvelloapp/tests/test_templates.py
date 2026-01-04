from django.test import TestCase
from django.template.loader import render_to_string
from django.test.client import RequestFactory
from types import SimpleNamespace
from datetime import date


class InvoiceTemplateTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_empty_title_shows_symbol(self):
        request = self.rf.get('/')
        request.user = SimpleNamespace(id=1)
        invoice = SimpleNamespace(
            title=None,
            client=SimpleNamespace(clientName='ACME'),
            number='R001',
            subject=SimpleNamespace(clientName='Test Co'),
            dueDate=date(2025,1,1),
            notes='Note',
            is_paid=False,
            get_overdue_status=None,
            id=1,
        )
        html = render_to_string('invoices.html', {'invoices': [invoice]}, request=request)
        self.assertIn('∅', html)

    def test_notes_are_truncated_and_title_attribute_exists(self):
        request = self.rf.get('/')
        request.user = SimpleNamespace(id=1)
        long_note = 'X' * 200
        invoice = SimpleNamespace(
            title='Invoice',
            client=SimpleNamespace(clientName='ACME'),
            number='R002',
            subject=SimpleNamespace(clientName='Test Co'),
            dueDate=date(2025,1,1),
            notes=long_note,
            is_paid=False,
            get_overdue_status=None,
            id=2,
        )
        html = render_to_string('invoices.html', {'invoices': [invoice]}, request=request)
        self.assertIn('title="' + long_note[:10], html)  # title contains full notes (escaped)
        self.assertIn('…', html)  # truncated content uses ellipsis
