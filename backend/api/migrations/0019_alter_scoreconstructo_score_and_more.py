# Generated by Django 5.1.3 on 2025-01-14 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_customuser_region_customuser_departamento_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scoreconstructo',
            name='score',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='scoreindicador',
            name='score',
            field=models.FloatField(),
        ),
    ]
