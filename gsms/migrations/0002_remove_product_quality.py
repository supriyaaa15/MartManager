# Generated by Django 5.1.5 on 2025-03-15 11:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gsms', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='quality',
        ),
    ]
