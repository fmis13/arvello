# Generated by Django 4.2.8 on 2024-01-16 23:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arvelloapp', '0003_alter_invoice_client'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='taxPercent',
            field=models.FloatField(blank=True, default=0.25, null=True),
        ),
    ]