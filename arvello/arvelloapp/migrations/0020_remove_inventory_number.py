# Generated by Django 4.2.8 on 2024-03-23 10:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('arvelloapp', '0019_alter_inventory_number'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventory',
            name='number',
        ),
    ]