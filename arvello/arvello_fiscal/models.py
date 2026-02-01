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
    
    STATUS_CHOICES = [
        ('unconfigured', 'Nije konfigurirano'),
        ('configured', 'Konfigurirano'),
        ('connected', 'Povezano'),
        ('error', 'Greška'),
    ]
    
    company_id = models.CharField(max_length=64, unique=True, help_text="Unique identifier for the company")
    mode = models.CharField(max_length=16, choices=MODE_CHOICES, default='sandbox', help_text="Environment mode")
    adapter = models.CharField(max_length=64, choices=ADAPTER_CHOICES, default='sandbox', help_text="Fiscal adapter to use")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unconfigured', help_text="Current connection status")
    
    # Configuration fields
    endpoint = models.URLField(blank=True, null=True, help_text="API endpoint URL for fiscal service")
    secret = models.CharField(max_length=256, blank=True, null=True, help_text="Secret key for authentication (JWT, etc.)")
    
    # Certificate files
    certificate_file = models.FileField(upload_to='fiscal_certs/', blank=True, null=True, help_text="Certificate file (.pem, .crt)")
    private_key_file = models.FileField(upload_to='fiscal_certs/', blank=True, null=True, help_text="Private key file (.key, .pem)")
    certificate_password = models.CharField(max_length=256, blank=True, null=True, help_text="Password for certificate (if encrypted)")
    certificate_valid_until = models.DateField(blank=True, null=True, help_text="Certificate expiry date")
    
    # Fiscal operator (operator OIB)
    operator_oib = models.CharField(max_length=11, blank=True, null=True, help_text="OIB of the fiscal operator")
    
    # Additional metadata
    meta = JSONField(null=True, blank=True, help_text="Additional configuration data")
    
    # Connection test info
    last_test_at = models.DateTimeField(blank=True, null=True, help_text="Last connection test timestamp")
    last_test_result = models.TextField(blank=True, null=True, help_text="Last connection test result")
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fiscal Config'
        verbose_name_plural = 'Fiscal Configs'
        ordering = ['company_id']

    def __str__(self):
        return f"{self.company_id} - {self.get_adapter_display()} ({self.get_mode_display()})"
    
    def get_locations(self):
        """Get all business locations for this config."""
        return self.locations.all()
    
    def get_devices(self):
        """Get all payment devices for this config."""
        return FiscalDevice.objects.filter(location__fiscal_config=self)
    
    def is_configured(self):
        """Check if basic configuration is complete."""
        if self.mode == 'sandbox':
            return True
        if self.adapter == 'fiskalizacija_v1':
            return bool(self.certificate_file and self.private_key_file)
        if self.adapter == 'fiskalizacija_v2':
            return bool(self.secret and self.endpoint)
        return False
    
    def update_status(self, new_status, test_result=None):
        """Update connection status and test result."""
        self.status = new_status
        self.last_test_at = timezone.now()
        if test_result:
            self.last_test_result = test_result
        self.save(update_fields=['status', 'last_test_at', 'last_test_result', 'updated_at'])


class FiscalLocation(models.Model):
    """Business location (Poslovni prostor) for fiscalization."""
    
    LOCATION_TYPE_CHOICES = [
        ('fixed', 'Stalni poslovni prostor'),
        ('mobile', 'Mobilni poslovni prostor'),
        ('internet', 'Internet trgovina'),
        ('vending', 'Automat'),
    ]
    
    fiscal_config = models.ForeignKey(FiscalConfig, on_delete=models.CASCADE, related_name='locations')
    
    # Location identifier (oznaka poslovnog prostora)
    location_id = models.CharField(max_length=20, help_text="Oznaka poslovnog prostora (npr. POS1, SHOP1)")
    name = models.CharField(max_length=100, help_text="Naziv poslovnog prostora")
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPE_CHOICES, default='fixed')
    
    # Address (required for fixed locations)
    address = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
    
    # Additional info
    working_hours = models.CharField(max_length=200, blank=True, null=True, help_text="Radno vrijeme")
    registered_at_tax_authority = models.BooleanField(default=False, help_text="Prijavljeno Poreznoj upravi")
    registration_date = models.DateField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Fiscal Location'
        verbose_name_plural = 'Fiscal Locations'
        unique_together = ['fiscal_config', 'location_id']
        ordering = ['location_id']
    
    def __str__(self):
        return f"{self.location_id} - {self.name}"


class FiscalDevice(models.Model):
    """Payment device (Naplatni uređaj) for fiscalization."""
    
    location = models.ForeignKey(FiscalLocation, on_delete=models.CASCADE, related_name='devices')
    
    # Device identifier (oznaka naplatnog uređaja)
    device_id = models.CharField(max_length=20, help_text="Oznaka naplatnog uređaja (npr. 1, 2, KASA1)")
    name = models.CharField(max_length=100, help_text="Naziv uređaja")
    
    # Device info
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Current invoice sequence number
    current_sequence = models.IntegerField(default=0, help_text="Trenutni redni broj računa")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Fiscal Device'
        verbose_name_plural = 'Fiscal Devices'
        unique_together = ['location', 'device_id']
        ordering = ['device_id']
    
    def __str__(self):
        return f"{self.device_id} - {self.name} ({self.location.location_id})"
    
    def get_next_sequence(self):
        """Get and increment the next invoice sequence number."""
        self.current_sequence += 1
        self.save(update_fields=['current_sequence', 'updated_at'])
        return self.current_sequence
