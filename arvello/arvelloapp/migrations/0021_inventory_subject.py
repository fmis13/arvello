# Generated by Django 4.2.8 on 2024-03-27 19:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('arvelloapp', '0020_remove_inventory_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='arvelloapp.company'),
        ),
    ]
