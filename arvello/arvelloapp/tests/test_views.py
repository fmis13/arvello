from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class HistoryViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

    def test_history_view_accessible(self):
        response = self.client.get(reverse('view_history'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'history_view.html')

class TaxChanges2025ViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

    def test_tax_changes_view_accessible(self):
        response = self.client.get(reverse('tax_changes_2025'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tax_changes_2025.html')