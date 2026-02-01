from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from .models import FiscalDocument, FiscalRequest, FiscalResponse, FiscalConfig, FiscalCertificate, FiscalLocation, FiscalDevice
from .services.fiscal_service import FiscalService
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import os


class FiscalConfigForm(forms.ModelForm):
    """Custom form for FiscalConfig with validation."""
    
    class Meta:
        model = FiscalConfig
        fields = '__all__'
    
    def clean_certificate_file(self):
        """Validate certificate file."""
        cert_file = self.cleaned_data.get('certificate_file')
        if cert_file:
            # Check file extension
            if not cert_file.name.lower().endswith(('.pem', '.crt', '.cer')):
                raise ValidationError('Certificate file must be a .pem, .crt, or .cer file.')
            
            # Try to load and validate certificate
            try:
                cert_data = cert_file.read()
                cert = x509.load_pem_x509_certificate(cert_data, default_backend())
                # Certificate is valid
            except Exception as e:
                raise ValidationError(f'Invalid certificate file: {str(e)}')
        
        return cert_file
    
    def clean_private_key_file(self):
        """Validate private key file."""
        key_file = self.cleaned_data.get('private_key_file')
        if key_file:
            # Check file extension
            if not key_file.name.lower().endswith(('.key', '.pem')):
                raise ValidationError('Private key file must be a .key or .pem file.')
            
            # Try to load private key
            try:
                key_data = key_file.read()
                # Note: We can't easily validate private key without password
                # but we can check if it's a valid PEM format
                if not (b'-----BEGIN' in key_data and b'PRIVATE KEY-----' in key_data):
                    raise ValidationError('File does not appear to be a valid private key.')
            except Exception as e:
                raise ValidationError(f'Invalid private key file: {str(e)}')
        
        return key_file
    
    def clean(self):
        """Validate form fields together."""
        cleaned_data = super().clean()
        adapter = cleaned_data.get('adapter')
        mode = cleaned_data.get('mode')
        
        # Validate required fields based on adapter and mode
        if mode == 'production':
            if adapter in ['fiskalizacija_v1', 'fiskalizacija_v2']:
                if not cleaned_data.get('endpoint'):
                    raise ValidationError('Endpoint is required for production mode.')
                
                if adapter == 'fiskalizacija_v1' and not cleaned_data.get('certificate_file'):
                    raise ValidationError('Certificate file is required for Fiskalizacija v1 in production mode.')
                
                if adapter == 'fiskalizacija_v2' and not cleaned_data.get('secret'):
                    raise ValidationError('Secret is required for Fiskalizacija v2 in production mode.')
        
        return cleaned_data


@admin.register(FiscalDocument)
class FiscalDocumentAdmin(admin.ModelAdmin):
    list_display = ('document_type', 'document_id', 'company_id', 'status', 'created_at')
    search_fields = ('document_id', 'company_id')


@admin.register(FiscalRequest)
class FiscalRequestAdmin(admin.ModelAdmin):
    list_display = ('fiscal_document', 'idempotency_key', 'status', 'attempt_count', 'created_at')
    search_fields = ('idempotency_key',)
    readonly_fields = ('payload',)
    # actions = ['resend_requests']

    # def resend_requests(self, request, queryset):
    #     """Admin action to enqueue resend of selected FiscalRequest objects."""
    #     count = 0
    #     for fr in queryset:
    #         try:
    #             send_fiscal_request.delay(fr.id)
    #             count += 1
    #         except Exception:
    #             # fallback: try synchronous send
    #             try:
    #                 adapter = FiscalService.get_adapter_for_company(fr.fiscal_document.company_id)
    #                 signed = adapter.sign_payload(fr.payload or {})
    #                 raw = adapter.send(signed)
    #                 parsed = adapter.parse_response(raw)
    #                 from .models import FiscalResponse
    #                 FiscalResponse.objects.create(fiscal_request=fr, raw_response=str(raw), parsed=parsed)
    #                 fr.status = 'sent' if parsed.get('ok') else 'failed'
    #                 fr.save()
    #                 count += 1
    #             except Exception:
    #                 continue
    #     self.message_user(request, f"Enqueued resend for {count} requests.")
    # resend_requests.short_description = 'Resend selected fiscal requests (enqueue)'


@admin.register(FiscalResponse)
class FiscalResponseAdmin(admin.ModelAdmin):
    list_display = ('fiscal_request', 'response_code', 'received_at')
    readonly_fields = ('raw_response', 'parsed')


@admin.register(FiscalConfig)
class FiscalConfigAdmin(admin.ModelAdmin):
    form = FiscalConfigForm
    list_display = ('company_id', 'adapter', 'mode', 'endpoint', 'has_certificate', 'has_private_key', 'created_at')
    list_filter = ('adapter', 'mode')
    search_fields = ('company_id',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('company_id', 'adapter', 'mode'),
        }),
        ('Connection Settings', {
            'fields': ('endpoint', 'secret'),
            'description': 'Configure the fiscal service endpoint and authentication.',
        }),
        ('Certificates', {
            'fields': ('certificate_file', 'private_key_file'),
            'description': 'Upload certificate and private key files for Fiskalizacija v1.',
        }),
        ('Metadata', {
            'fields': ('meta',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['test_fiscal_connection', 'download_certificate_info']
    
    def has_certificate(self, obj):
        return bool(obj.certificate_file)
    has_certificate.short_description = 'Certificate'
    has_certificate.boolean = True
    
    def has_private_key(self, obj):
        return bool(obj.private_key_file)
    has_private_key.short_description = 'Private Key'
    has_private_key.boolean = True
    
    def test_fiscal_connection(self, request, queryset):
        """Test fiscal connection for selected configurations."""
        results = []
        for config in queryset:
            try:
                adapter = FiscalService.get_adapter_for_company(config.company_id)
                # Try a health check or simple test
                if hasattr(adapter, 'health_check'):
                    success = adapter.health_check()
                else:
                    # For adapters without health_check, try to send a test payload
                    test_payload = {'test': True, 'company_id': config.company_id}
                    signed = adapter.sign_payload(test_payload)
                    if config.mode == 'sandbox':
                        # In sandbox mode, just test signing
                        results.append(f"✓ {config.company_id}: Sandbox mode - signing OK")
                    else:
                        # Try actual send (this might fail in production without real data)
                        raw_response = adapter.send(signed)
                        parsed = adapter.parse_response(raw_response)
                        if parsed.get('ok') or parsed.get('status') == 'OK':
                            results.append(f"✓ {config.company_id}: Connection successful")
                        else:
                            results.append(f"⚠ {config.company_id}: Connection failed - {parsed}")
                if not success:
                    results.append(f"✗ {config.company_id}: Health check failed")
            except Exception as e:
                results.append(f"✗ {config.company_id}: Error - {str(e)}")
        
        if results:
            self.message_user(request, "Connection test results:\n" + "\n".join(results))
        else:
            self.message_user(request, "No configurations selected for testing.")
    
    test_fiscal_connection.short_description = "Test fiscal connection"
    
    def download_certificate_info(self, request, queryset):
        """Download certificate information for selected configs."""
        # This would generate a report of certificate details
        # For now, just show a message
        configs_with_certs = [c for c in queryset if c.certificate_file]
        if configs_with_certs:
            self.message_user(request, f"Found {len(configs_with_certs)} configurations with certificates. Certificate info download not yet implemented.")
        else:
            self.message_user(request, "No configurations with certificates found.")
    
    download_certificate_info.short_description = "Download certificate info"


@admin.register(FiscalCertificate)
class FiscalCertificateAdmin(admin.ModelAdmin):
    list_display = ('owner', 'active', 'valid_from', 'valid_to')


class FiscalDeviceInline(admin.TabularInline):
    model = FiscalDevice
    extra = 1
    fields = ('device_id', 'name', 'manufacturer', 'model', 'current_sequence', 'is_active')


@admin.register(FiscalLocation)
class FiscalLocationAdmin(admin.ModelAdmin):
    list_display = ('location_id', 'name', 'fiscal_config', 'location_type', 'city', 'is_active')
    list_filter = ('location_type', 'is_active', 'fiscal_config')
    search_fields = ('location_id', 'name', 'city')
    inlines = [FiscalDeviceInline]
    
    fieldsets = (
        ('Osnovne informacije', {
            'fields': ('fiscal_config', 'location_id', 'name', 'location_type'),
        }),
        ('Adresa', {
            'fields': ('address', 'city', 'postal_code'),
        }),
        ('Dodatno', {
            'fields': ('working_hours', 'registered_at_tax_authority', 'registration_date', 'is_active'),
        }),
    )


@admin.register(FiscalDevice)
class FiscalDeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'name', 'location', 'manufacturer', 'current_sequence', 'is_active')
    list_filter = ('is_active', 'location__fiscal_config')
    search_fields = ('device_id', 'name', 'serial_number')
    
    fieldsets = (
        ('Osnovne informacije', {
            'fields': ('location', 'device_id', 'name'),
        }),
        ('Detalji uređaja', {
            'fields': ('manufacturer', 'model', 'serial_number'),
        }),
        ('Numeracija', {
            'fields': ('current_sequence',),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
    )
