# Generated by Django 5.1.3 on 2024-12-23 18:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_retrochatgpt_cuestionario_retrochatgpt_aplicacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='datosaplicacion',
            name='fecha_limite',
            field=models.DateField(blank=True, null=True),
        ),
    ]
