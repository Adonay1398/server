# Generated by Django 5.1.3 on 2025-01-03 17:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_remove_reporte_promedio_constructos_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='datosaplicacion',
            name='reporte_generado',
            field=models.BooleanField(default=False),
        ),
    ]
