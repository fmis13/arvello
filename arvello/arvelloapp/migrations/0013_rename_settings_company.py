# Generated by Django 4.2.8 on 2024-02-21 16:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arvelloapp', '0012_alter_invoice_date'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Settings',
            new_name='Company',
        ),
    ]
