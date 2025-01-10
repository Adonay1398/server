# Generated by Django 5.1.3 on 2025-01-10 08:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_reporte_region'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='Region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.region'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='departamento',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.departamento'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='instituto',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.instituto'),
        ),
    ]
