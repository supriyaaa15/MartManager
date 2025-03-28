# Generated by Django 5.1.5 on 2025-03-27 12:07

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gsms', '0008_alter_transaction_supplier'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='pay_method',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='supplier',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='gsms.supplier'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='total_amt',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='trans_date',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
