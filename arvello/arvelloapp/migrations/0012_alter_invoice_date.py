# Generated by Django 4.2.8 on 2024-02-21 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arvelloapp', '0011_invoice_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
