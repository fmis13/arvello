from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import JSONField


class FiscalDocument(models.Model):
    # Generic pointer to a domain document (Invoice/Receipt/Salary) via contenttypes could be added later
    document_type = models.CharField(max_length=32)
    document_id = models.CharField(max_length=64)
    company_id = models.CharField(max_length=64)
    status = models.CharField(max_length=32, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Fiscal Document'
        verbose_name_plural = 'Fiscal Documents'


class FiscalRequest(models.Model):
    fiscal_document = models.ForeignKey(FiscalDocument, on_delete=models.CASCADE, related_name='requests')
    idempotency_key = models.CharField(max_length=128, db_index=True)
    payload = JSONField(null=True, blank=True)
    attempt_count = models.IntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, default='queued')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Fiscal Request'
        verbose_name_plural = 'Fiscal Requests'


class FiscalResponse(models.Model):
    fiscal_request = models.ForeignKey(FiscalRequest, on_delete=models.CASCADE, related_name='responses')
    raw_response = models.TextField(null=True, blank=True)
    response_code = models.CharField(max_length=64, null=True, blank=True)
    parsed = JSONField(null=True, blank=True)
    received_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Fiscal Response'
        verbose_name_plural = 'Fiscal Responses'


class FiscalCertificate(models.Model):
    owner = models.CharField(max_length=128)
    cert_meta = JSONField(null=True, blank=True)
    active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Fiscal Certificate'
        verbose_name_plural = 'Fiscal Certificates'


class FiscalConfig(models.Model):
    ADAPTER_CHOICES = [
        ('sandbox', 'Sandbox'),
        ('fiskalizacija_v1', 'Fiskalizacija v1 (XML/SOAP)'),
        ('fiskalizacija_v2', 'Fiskalizacija v2 (JSON/REST)'),
    ]
    
    MODE_CHOICES = [
        ('sandbox', 'Sandbox'),
        ('production', 'Production'),
    ]
    
    company_id = models.CharField(max_length=64, unique=True, help_text="Unique identifier for the company")
    mode = models.CharField(max_length=16, choices=MODE_CHOICES, default='sandbox', help_text="Environment mode")
    adapter = models.CharField(max_length=64, choices=ADAPTER_CHOICES, default='sandbox', help_text="Fiscal adapter to use")
    
    # Configuration fields
    endpoint = models.URLField(blank=True, null=True, help_text="API endpoint URL for fiscal service")
    secret = models.CharField(max_length=256, blank=True, null=True, help_text="Secret key for authentication (JWT, etc.)")
    
    # Certificate files
    certificate_file = models.FileField(upload_to='fiscal_certs/', blank=True, null=True, help_text="Certificate file (.pem, .crt)")
    private_key_file = models.FileField(upload_to='fiscal_certs/', blank=True, null=True, help_text="Private key file (.key, .pem)")
    
    # Additional metadata
    meta = JSONField(null=True, blank=True, help_text="Additional configuration data")
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fiscal Config'
        verbose_name_plural = 'Fiscal Configs'
        ordering = ['company_id']

    def __str__(self):
        return f"{self.company_id} - {self.get_adapter_display()} ({self.get_mode_display()})"
